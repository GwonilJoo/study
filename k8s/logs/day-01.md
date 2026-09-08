# 1일차 — 클러스터 만들고 부수기, 그리고 서비스

> 날짜: 2026-09-07
> 환경: macOS + Docker + kind, Kubernetes v1.37.0, kube-proxy `iptables` 모드
> 다룬 개념: [01-kind-local-env](../docs/concepts/01-kind-local-env.md), [02-cluster-node-architecture](../docs/concepts/02-cluster-node-architecture.md), [03-pod](../docs/concepts/03-pod.md), [04-deployment-replicaset](../docs/concepts/04-deployment-replicaset.md), [05-label-selector](../docs/concepts/05-label-selector.md), [06-service](../docs/concepts/06-service.md), [07-cluster-dns](../docs/concepts/07-cluster-dns.md), [08-resources](../docs/concepts/08-resources-requests-limits.md), [09-troubleshooting](../docs/concepts/09-troubleshooting.md)

> **기록 방식에 대한 참고**: 전반부(클러스터·파드)는 실습 전에 예측을 남기지 않았다. 그 구간의 "예상" 항목은 **비어 있거나, 대화에서 실제로 놀랐다고 표현된 부분만** 적었다. 후반부(서비스)부터 **예측을 먼저 기록하는 방식**으로 바꿨다.

---

## 어떻게 여기까지 왔나

최초 질문은 "GPU 서버를 클라우드로 쓰면 요금이 얼마인가"였다. 거기서 "여러 서비스를 운영하려면 어떤 구성이 좋은가" → "쿠버네티스를 공부하면서 해보고 싶다"로 이어졌다.

정한 학습 경로:

```
[1단계] 로컬 (kind)          ← 현재 위치
   ↓  쿠버네티스 개념과 동작 이해
[2단계] AWS EC2 + kubeadm
   ↓  실제 인프라, 설치 과정, 네트워크
[3단계] 필요해지면 EKS / RKE2
```

**핵심 판단: 로컬과 실서버를 분리한다.** 처음부터 AWS에서 시작하면 쿠버네티스 문제인지 AWS 네트워크 문제인지 구분이 안 돼서 진도가 안 난다.

---
---

# 전반부 — 클러스터와 파드

## 환경 구성

```bash
brew install kind kubectl
kind create cluster --name study --config kind-config.yml
kubectl get nodes
```

```
NAME                  STATUS   ROLES           VERSION
study-control-plane   Ready    control-plane   v1.37.0
study-worker          Ready    <none>          v1.37.0
study-worker2         Ready    <none>          v1.37.0
```

생성 로그의 단계들이 곧 쿠버네티스 설치 과정이었다 (CNI 설치, 워커 조인 등). AWS에서 손으로 해야 할 일을 kind가 대신 한 것.

---

## 실습 1 — 앱 띄우기

**한 것**

```bash
kubectl create deployment web --image=nginx --replicas=3
kubectl get pods -o wide
```

**결과** 파드 3개가 두 워커에 나뉘어 배치됐다. `-o wide`의 `NODE` 칸으로 확인.

**배운 것** 노드를 지정하지 않았는데 스케줄러가 알아서 배치했다. "3번 서버에 올려줘"가 아니라 "3개 돌려줘"라고 말하는 방식.

---

## 실습 2 — 파드 죽여보기

**한 것**

```bash
kubectl delete pod <파드이름>
kubectl get pods
```

**예상** (기록 없음. 도커 경험 기준이라면 그냥 사라졌어야 함)

**결과** 지웠는데 **여전히 3개.** 하나가 새 이름·새 IP로 생겼다.

**왜** `--replicas=3`으로 "3개 원한다"를 등록해뒀다. 현재가 2개가 되니 컨트롤 루프가 차이를 메웠다. **누가 명령해서가 아니라 루프가 계속 돌기 때문.**

→ 이 관찰이 후반부에서 서비스가 필요한 이유로 그대로 이어졌다 (IP가 바뀐다).

---

## 실습 3 — 노드 죽여보기 ★

**한 것**

```bash
docker stop study-worker2
kubectl get nodes
kubectl get pods -o wide -w
```

**결과 타임라인**

| 시점 | 상태 |
| --- | --- |
| 0초 | `docker stop` 실행 |
| 약 40초 | 노드가 `NotReady` |
| **5분** | 파드가 `Terminating`, 다른 노드에 새 파드 생성 |

**막혔던 지점** `docker stop` 직후 파드가 그대로라 뭔가 잘못된 줄 알았다. 실제로는 **아직 5분이 안 지난 것뿐.** 먼저 `kubectl get nodes`가 `NotReady`로 바뀌는지 확인해야 했다. 노드가 `Ready`면 파드는 절대 안 움직인다.

**왜 5분인가** 응답이 없을 때 "죽었다"와 "네트워크만 끊겼다"를 구분할 방법이 없다. 성급히 판단해서 파드를 또 만들었다가 원래 것까지 살아나면 6개가 되는 사고가 난다.

**왜 노드가 죽었는데 파드가 `Running`인가** 파드 상태를 보고하는 것은 그 노드의 kubelet인데 보고가 끊겼다. 남은 것은 마지막 보고다. **화면의 `Running`은 철 지난 정보.**

```bash
docker start study-worker2   # 복구
```

노드가 돌아와도 **파드는 자동으로 되돌아오지 않는다.** 이미 다른 곳에서 잘 돌고 있으니 옮길 이유가 없다.

> 후속 검증(후반부): 위 40초/5분의 근거를 바이너리에서 직접 확인했다. **설정 기본값은 50초였고 관측값은 약 40초로 달랐다.** → [09-troubleshooting.md](../docs/concepts/09-troubleshooting.md)

---

## 실습 4 — 개수 조절

```bash
kubectl scale deployment web --replicas=6
kubectl scale deployment web --replicas=2
```

명령 한 줄, 몇 초. 트래픽이 몰릴 때 늘리는 동작이 이것.

---

## 실습 5 — 자원 부족으로 `Pending` 만들기 ★

**한 것** 처음으로 YAML 파일 + `kubectl apply` 방식을 썼다.

```yaml
resources:
  requests:
    memory: 100Gi
```

```bash
kubectl apply -f heavy.yaml
kubectl get pods
```

**예상** 자원이 부족하면 어떻게든 밀어넣거나 에러가 날 것

**결과** 3개 전부 `Pending`. 에러도 아니고 강제 배치도 아니다. **자리가 생길 때까지 조용히 기다린다.**

**진단 과정에서 배운 것**

```
Node:             <none>          ← 배정된 노드 없음 = 스케줄링 실패
Status:           Pending
Requests:
  memory:     100Gi
Conditions:
  PodScheduled   False
QoS Class:        Burstable
```

`Node:` 칸이 비었는지 여부로 "자리가 없는 것"과 "배치는 됐는데 이미지·볼륨 문제"를 구분한다.

**막혔던 지점** `describe pod -l app=heavy`로 조회하니 Events 섹션이 안 나왔다. 여러 파드를 라벨로 묶어 조회하면 누락될 수 있다. `kubectl get events`를 직접 쓰는 쪽이 확실하다.

---

## 전반부에 정리한 개념

- 클러스터 / 노드 / 파드 / 디플로이먼트 / 서비스 (서비스는 개념만, 실습은 후반부)
- 컨트롤 플레인 구성요소 5개, 워커 구성요소 3개
- `kubectl apply` 성공 = "접수했다"이지 "실제로 떴다"가 아니다
- 컨트롤 루프: 원하는 상태 읽고 → 현재 상태 관찰하고 → 차이를 좁힌다
- requests / limits / QoS Class
- `Pending`(요청 과다)과 `OOMKilled`(상한 부족)은 원인이 정반대

---
---

# 후반부 — 서비스

여기서부터 **예측을 먼저 기록하는 방식**으로 바꿨다.

## 중간 점검

| 항목 | 결과 |
| --- | --- |
| 노드 3개 | 전부 `Ready`, v1.37.0 |
| `web` 디플로이먼트 | `3/3` |
| `heavy` 디플로이먼트 | 전반부 잔여물. 정리함 |
| 파드 배치 | 3개 전부 `study-worker`에 몰려 있음 (실습 3에서 worker2를 죽였다 살린 흔적) |

문서와 실제가 달랐던 점: 작업 디렉터리는 `~/k8s`가 아니라 이 저장소 경로, 설정 파일은 `kind-config.yaml`이 아니라 **`kind-config.yml`**.

---

## Q1. 파드 IP를 그냥 적어두고 쓰면 왜 안 되나

**내 답**
> 파드 ip는 지속성이 없기 때문. 파드가 죽으면, 새로운 파드가 생성되는데, ip가 달라짐. 그리고 3개의 파드로 일일이 접속하는 것이 아닌 하나의 ip를 통해서 라우팅하기 위함

**판정: 정답.** 서비스가 존재하는 이유 두 가지(고정 주소 + 부하 분산)를 다 짚었다.

**보강 — 표현이 부정확했던 부분**

"파드가 죽으면"이 아니라 **"파드 객체가 새로 만들어지면"**이다.

| 상황 | 파드 IP |
| --- | --- |
| 컨테이너가 죽어서 재시작 (`RESTARTS` 증가) | 유지 |
| `delete pod` 후 새로 생성 | 바뀜 |
| 노드 장애로 다른 노드에 재생성 | 바뀜 |

> ⚠️ 미검증 — 첫 줄은 실측하지 않았다. 나중에 확인할 것.

---

## Q2. 서비스는 어떤 파드가 자기 뒤에 있는지 어떻게 알아내나

**내 답**
> 라벨로 찾는 것 같은데, 서비스에도 selector를 적는 건가?

**판정: 정답.**

**보강 — 문법이 두 가지다.** 이 클러스터의 API 서버에 직접 물어 확인했다.

```bash
kubectl explain service.spec.selector      # map[string]string
kubectl explain deployment.spec.selector   # LabelSelector
```

```yaml
# 서비스 — 평평하게
spec:
  selector:
    app: web

# 디플로이먼트 — 한 단계 더
spec:
  selector:
    matchLabels:
      app: web
```

서비스에 `matchLabels`를 적으면 에러.

---

## Q3. `kubectl expose`는 selector에 넣을 라벨을 어디서 가져오나

**내 답**
> deployment에서 가져오는 것 같아. 그런데, 나는 deployment web 생성할때 yml로 생성하지 않았는데

**판정: 정답 + 좋은 반문.**

**보강 — "YAML로 안 만들었다" ≠ "YAML이 없다"**

`kubectl create deployment`는 kubectl이 **대신 YAML을 만들어 API 서버에 보내는 것**이다. 적지 않은 값(라벨 포함)이 자동으로 채워진다. YAML은 저장 형식이지 만드는 방법이 아니다.

도커에서 `docker run -d --name web nginx` 한 줄만 쳐도 `docker inspect`에 수십 개 값이 나오는 것과 같다.

**확인**

```bash
kubectl get pods --show-labels
# app=web,pod-template-hash=5fc9f4bf66     ← 적은 적 없는 라벨

kubectl get deployment web -o yaml | grep -A4 matchLabels
#   selector:
#     matchLabels:
#       app: web
```

---

## Q4. 서비스 selector에 `pod-template-hash`까지 들어갔다면?

**내 답**
> pod-template-hash는 파드 설정값이 바뀌면 바뀌어버려서 기존 서비스가 무용지물이 될것같네

**판정: 정답.**

**보강 — 롤링 업데이트**

이미지를 새 버전으로 바꾸면 파드를 한꺼번에 갈지 않고 하나씩 교체한다. 교체 중에는 옛 버전과 새 버전 파드가 **동시에 존재**한다.

| 라벨 | 목적 |
| --- | --- |
| `pod-template-hash` | 옛/새 버전을 **구분**. 없으면 두 레플리카셋이 서로 남의 파드를 자기 것으로 착각 |
| `app=web` | 버전 상관없이 **전부 묶음**. 서비스가 이걸 쓰는 이유 |

**서비스는 일부러 버전을 가리지 않는다.** 교체 중에도 접속이 끊기면 안 되니까.

---

## 실습 6 — 서비스 만들고 이름으로 접속

```bash
kubectl expose deployment web --port=80
kubectl get svc
```

```
NAME   TYPE        CLUSTER-IP      PORT(S)   AGE
web    ClusterIP   10.96.217.194   80/TCP    6m52s
```

**엔드포인트 — selector가 실제로 골라낸 결과**

```
Endpoints:   10.244.1.3:80,10.244.1.4:80,10.244.1.5:80
```

파드 IP 3개와 정확히 일치. `app: web` 한 줄로 찾아냈다.

**이름으로 접속**

```bash
kubectl run test --image=busybox -it --rm --restart=Never -- wget -qO- http://web
```

**결과: `Welcome to nginx!`** — IP를 하나도 적지 않고 `http://web`이라는 이름만으로 접속됐다.

같은 HTML이 두 번 나오고 경고가 떴다.

```
warning: couldn't attach to pod/test, falling back to streaming logs:
container is in CONTAINER_EXITED state
```

`-it`로 붙기도 전에 wget이 끝나서 kubectl이 로그 읽기로 전환한 것. 오류는 아니지만 **이게 다음 실습을 망친다.**

---

## 실습 7 — 부하 분산 (1차: 실패)

**예상** 30번 요청하면 파드 3개에 대략 10회씩 나뉠 것. 다만 `iptables` 모드는 확률 방식이라 정확히 균등하지는 않을 것.

**실제**

```bash
kubectl run test --image=busybox -it --rm --restart=Never -- \
  sh -c 'for i in $(seq 1 10); do wget -qO- http://web; done'
```

```
web-...-r9tlv     ← 로그로 읽어온 부분
web-...-r9tlv
web-...-r9tlv
--- attach로 전환 ---
web-...-m9wb5
web-...-l7vsv
web-...-r9tlv
```

**10번 요청했는데 6줄만 나왔다.** attach 전환 구간에서 4줄이 유실됐다.

**실패 원인: 실험 설계 오류.** `-it`를 쓴 것이 잘못이었다. 측정이 목적이면 붙지 말고 로그를 나중에 읽어야 한다.

**그래도 증명된 것** 파드 3개가 전부 응답에 참여했다. 부하 분산이 동작한다는 사실 자체는 확인됐고 비율만 못 믿는 상태.

---

## 실습 8 — 부하 분산 (2차: 재설계)

**바꾼 것** `-it` 제거, `kubectl logs`로 사후 조회. `--rm`은 `-it`와 함께여야 하므로 직접 삭제.

```bash
for p in $(kubectl get pods -l app=web -o name); do
  kubectl exec $p -- sh -c 'echo $HOSTNAME > /usr/share/nginx/html/index.html'
done

kubectl run loadtest --image=busybox --restart=Never -- \
  sh -c 'for i in $(seq 1 30); do wget -qO- http://web; done'
kubectl logs loadtest | sort | uniq -c
kubectl delete pod loadtest
```

**결과** 합계 30. 유실 없음.

```
14  web-5fc9f4bf66-l7vsv
 7  web-5fc9f4bf66-m9wb5
 9  web-5fc9f4bf66-r9tlv
```

**치우친 것인가? 계산으로 확인**

```
기대값 10회, 이론상 표준편차 2.58회
  14회 → +1.55 표준편차
   7회 → -1.16 표준편차
   9회 → -0.39 표준편차
카이제곱 = 2.60 (자유도 2), p = 0.273
```

**p = 0.27. "균등 분배가 아니다"라고 말할 근거가 없다.** 동전 30번 던져 앞면 17번 나온 정도의 흔한 편차.

**근거 — iptables 규칙 직접 확인**

```bash
docker exec study-worker iptables-save -t nat | grep default/web
```

```
-A KUBE-SERVICES -d 10.96.217.194/32 -p tcp --dport 80 -j KUBE-SVC-LOLE...
-A KUBE-SVC-... --probability 0.33333333349 -j ... → 10.244.1.3:80
-A KUBE-SVC-... --probability 0.50000000000 -j ... → 10.244.1.4:80
-A KUBE-SVC-...                             -j ... → 10.244.1.5:80
```

**순번이 아니라 확률이다.** `1/3 → 남은 것의 1/2 → 나머지 전부`로 이어져 결과적으로 균등해진다. ClusterIP는 DNAT 대상일 뿐 실제 인터페이스가 없다는 것도 여기서 확인된다.

---
---

## 오답 노트

### ① `localhost:8080`이 nginx인 줄 알았다

**내가 한 답**
> 현재 localhost:8080하면 nginx가 접속되는데 왜그러지? 나는 이전에 port-forward를 껐는데

**실제** nginx가 아니었다. 쿠버네티스와 무관한 다른 프로세스였다.

```
server: uvicorn
PID 55980  .../vnexis/apps/poc/.venv/bin/uvicorn app.ui:app --port 8080
<title>vnexis poc · gRPC 콘솔</title>
```

워커 노드는 바깥으로 열린 포트가 하나도 없다. `port-forward`를 끈 것이 맞았고, 클러스터의 nginx는 접근 불가 상태가 맞았다.

**왜 틀렸나** 브라우저에 뭔가 뜬 것만 보고 "아까 그것"이라고 단정했다. **응답하는 쪽의 정체를 확인하지 않았다.**

**교훈**
```bash
curl -sI http://localhost:8080          # server: 헤더
lsof -nP -iTCP:8080 -sTCP:LISTEN        # 프로세스
```

- [ ] 복습

### ② DNS 해석과 라벨 selector를 같은 단계로 생각했다

**내가 한 답**
> 결국 web은 아까 label을 통해서 해당 서비스 ip로 접근한다는 의미인가?

**실제** 단계가 둘이고 기준이 다르다.

| 단계 | 하는 일 | 기준 | 누가 |
| --- | --- | --- | --- |
| 1단계 | `web` → `10.96.217.194` | **서비스 이름** | CoreDNS |
| 2단계 | `10.96.217.194` → 파드 IP | **라벨** | kube-proxy |

**반례** 서비스 selector를 엉뚱한 값으로 바꿔도 `web`은 여전히 잘 풀린다. DNS는 멀쩡하고 2단계에서만 실패한다.

**왜 틀렸나** "접속된다"는 결과 하나로 뭉뚱그려서, 이름 해석과 트래픽 전달을 한 덩어리로 봤다.

**왜 중요한가** 진단이 갈린다. "이름을 못 찾는 것"과 "이름은 찾았는데 뒤에 아무도 없는 것"은 고치는 법이 다르다.

- [ ] 복습

---

## 곁가지로 확인한 것

**클러스터 안/밖 경계** — 노트북에서 직접 시도

```
노트북 → http://web             실패 (curl 종료코드 28 = 시간 초과)
노트북 → http://10.96.217.194   실패 (curl 종료코드 7 = 연결 불가)
노트북 → nslookup web           127.0.53.53 (엉뚱한 주소)
```

**파드의 DNS 설정**

```bash
kubectl exec <파드> -- cat /etc/resolv.conf
```
```
search default.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
```

`web`은 `web.default.svc.cluster.local`의 줄임말. **다른 네임스페이스는 줄여 쓸 수 없다** (`grafana.monitoring`).

**엔드포인트슬라이스의 이름** `web-5h2mq` = `서비스이름-무작위`. 한 조각당 기본 100개까지 담고 넘으면 쪼갠다 (바이너리 `--max-endpoints-per-slice` 기본값 100 + 공식 문서로 교차 확인).

**busybox 크기** 1.93MB (같은 노드의 nginx는 65.1MB).

---

## 다음에 할 것

**중단 지점: 라벨을 떼어내는 실험.** 예측까지만 하고 실행하지 않았다.

> 파드 3개 중 하나의 라벨을 `app=web` → `app=broken`으로 바꾸면 무슨 일이 일어나는가?
> 힌트: **두 가지**가 동시에 일어난다. 하나는 서비스와 관련, 하나는 서비스와 무관.

```bash
kubectl label pod <파드이름> app=broken --overwrite
kubectl describe svc web | grep Endpoints
kubectl get pods --show-labels
```

그다음:

- [ ] 서비스 타입 `NodePort` / `LoadBalancer` 확인 (`LoadBalancer`가 `<pending>`에 걸리는 것 관찰)
- [ ] ConfigMap / Secret
- [ ] 인그레스
- [ ] PVC
- [ ] Helm
