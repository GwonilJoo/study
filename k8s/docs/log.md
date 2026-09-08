# 쿠버네티스 학습 정리 (1일차)

> 작성일: 2026-09-07
> 환경: macOS + Docker + kind
> 상태: 로컬 클러스터 구성 완료, 기본 동작 확인 완료

---

## 1. 어떻게 여기까지 왔는가

처음 질문은 "GPU 서버를 클라우드로 쓰면 요금이 얼마인가"였고, 거기서 "여러 서비스를 운영하려면 어떤 구성이 좋은가" → "쿠버네티스를 공부하면서 해보고 싶다"로 이어졌다.

논의 끝에 정한 학습 경로는 이렇다.

```
[1단계] 로컬 (kind)          ← 현재 위치
   ↓  쿠버네티스 개념과 동작 이해
[2단계] AWS EC2 + kubeadm
   ↓  실제 인프라, 설치 과정, 네트워크
[3단계] 필요해지면 EKS / RKE2
```

**핵심 판단: 로컬과 실서버를 분리한다.**
처음부터 AWS에서 시작하면 쿠버네티스 문제인지 AWS 네트워크 문제인지 구분이 안 돼서 진도가 안 난다. 로컬에서 쿠버네티스만 먼저 익히고, 인프라는 나중에 따로 붙인다.

---

## 2. 알아야 할 기본 용어

### 클러스터 (Cluster)

서버 여러 대를 하나처럼 묶어 쓰는 것. "3번 서버에 이거 올려줘"가 아니라 "이거 3개 돌려줘"라고 말하면 배치는 시스템이 알아서 한다.

### 노드 (Node)

클러스터에 속한 컴퓨터 한 대. 두 종류가 있다.

| 종류                          | 역할                                         |
| ----------------------------- | -------------------------------------------- |
| 컨트롤 플레인 (control-plane) | 지휘. 어디에 놓을지 결정하고 상태를 기억한다 |
| 워커 (worker)                 | 실제로 컨테이너가 돌아가는 곳                |

### 파드 (Pod)

실행 중인 컨테이너 한 개. 쿠버네티스가 다루는 가장 작은 단위.

- 도커 컨테이너와 거의 같다. 지금은 "파드 = 컨테이너 하나"로 봐도 된다
- **언제든 죽는다.** 이름도 매번 바뀐다 (`web-5fc9f4bf66-7frll`)
- 그래서 파드를 직접 만들어 쓰는 일은 거의 없다

### 디플로이먼트 (Deployment)

**"이 프로그램을 몇 개 돌려줘"라는 주문서.** 실무에서 앱을 올릴 때 만드는 게 거의 항상 이것.

파드를 직접 만드는 게 아니라 주문서를 등록하는 것이고, 쿠버네티스가 그 주문에 맞춰 파드를 만들고 유지한다.

### 서비스 (Service)

여러 파드로 가는 고정된 입구. 파드는 죽고 살아나며 IP가 계속 바뀌므로, 바뀌지 않는 이름과 IP가 필요하다. 부하 분산도 겸한다.

**→ 아직 실습하지 않음. 다음 단계.**

### 네임스페이스 (Namespace)

클러스터 안의 폴더.

| 네임스페이스              | 들어 있는 것         |
| ------------------------- | -------------------- |
| `default`                 | 내 앱                |
| `kube-system`             | 쿠버네티스 자체 부품 |
| `monitoring`, `argocd` 등 | 관리 도구들 (관례)   |

### 관계도

```
디플로이먼트  "nginx 3개 돌려줘"
      │
      ├── 파드 (노드1)
      ├── 파드 (노드2)
      └── 파드 (노드2)
            ▲
            │ 트래픽 분배
         서비스  "web이라는 이름으로 접속"
```

**디플로이먼트가 파드를 만들고, 서비스가 그 파드들로 안내한다.**

---

## 3. 쿠버네티스 내부 구조

### 컨트롤 플레인 구성요소

| 이름                     | 역할                                                                         |
| ------------------------ | ---------------------------------------------------------------------------- |
| kube-apiserver           | 모든 것의 정문. 컴포넌트 간 직접 통신은 없고 전부 여기를 거친다              |
| etcd                     | 클러스터 전체 상태 저장소. 유일한 진실의 원천. **여기만 백업하면 복구 가능** |
| kube-scheduler           | 파드를 어느 노드에 놓을지 **결정만** 한다                                    |
| kube-controller-manager  | 원하는 상태와 현재 상태를 비교해 차이를 메우는 컨트롤러 묶음                 |
| cloud-controller-manager | 클라우드 연동 (LoadBalancer 생성 등)                                         |

### 워커 구성요소

| 이름       | 역할                                                  |
| ---------- | ----------------------------------------------------- |
| kubelet    | 노드의 에이전트. 파드를 실제로 띄우고 상태를 보고한다 |
| containerd | 컨테이너 런타임                                       |
| kube-proxy | 서비스 트래픽을 파드로 넘기는 규칙을 세팅             |

### 배포 흐름

`kubectl apply` 실행 시:

1. kubectl → **API 서버** (인증·인가·검증)
2. API 서버가 **etcd**에 "원하는 상태" 기록 → **여기서 kubectl은 성공을 리턴**
3. **컨트롤러**가 감지 → ReplicaSet → Pod 생성 (아직 노드 미배정)
4. **스케줄러**가 노드 결정
5. 해당 노드의 **kubelet**이 컨테이너 실행

> **`kubectl apply` 성공은 "접수했다"는 뜻이지 "실제로 떴다"는 뜻이 아니다.**

### 컨트롤 루프

모든 컨트롤러는 같은 패턴을 무한 반복한다.

```
원하는 상태를 읽고 → 현재 상태를 관찰하고 → 차이를 좁힌다
```

파드를 강제로 지워도 다시 살아나는 이유. 누가 명령해서가 아니라 루프가 계속 돌기 때문.

---

## 4. 환경 구성

### 필요한 도구 3개

| 도구    | 역할                                                   |
| ------- | ------------------------------------------------------ |
| Docker  | 노드가 될 컨테이너를 돌림                              |
| kind    | 그 컨테이너들로 클러스터를 만듦 (Kubernetes IN Docker) |
| kubectl | 만들어진 클러스터에 명령을 내림                        |

```
kubectl  ──명령──▶  클러스터
                      ▲ 만듦
                    kind
                      ▲ 컨테이너 제공
                    Docker
```

kind는 `create`와 `delete`만 쓰고, 그 뒤로는 계속 kubectl만 사용한다.

### 설치

```bash
brew install kind kubectl
```

### 클러스터 설정 파일

`kind-config.yaml`

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

- `kind:`는 도구 이름이 아니라 "종류"라는 뜻의 영어 단어
- `nodes:` 아래 `-` 하나가 노드 하나. **줄 수가 곧 노드 개수**
- 설정 파일 없이 `kind create cluster`만 하면 노드 1대짜리가 생긴다. 3대로 만들려면 파일이 필요

**YAML 주의: 들여쓰기가 문법이다. 탭 키는 에러.** 에러가 나면 대부분 들여쓰기 문제.

### 생성

```bash
kind create cluster --name study --config kind-config.yaml
```

생성 중 출력되는 단계들이 곧 쿠버네티스 설치 과정이다.

```
✓ Ensuring node image
✓ Preparing nodes
✓ Writing configuration
✓ Starting control-plane
✓ Installing CNI          ← 없으면 노드가 NotReady
✓ Installing StorageClass
✓ Joining worker nodes
```

AWS에서 손으로 해야 할 것(스왑 끄기, 커널 설정, 방화벽, CNI 설치)을 kind가 전부 처리해준다.

### 현재 클러스터

```
NAME                  STATUS   ROLES           VERSION
study-control-plane   Ready    control-plane   v1.37.0
study-worker          Ready    <none>          v1.37.0
study-worker2         Ready    <none>          v1.37.0
```

---

## 5. 실습 기록

### 실습 1: 앱 띄우기

```bash
kubectl create deployment web --image=nginx --replicas=3
kubectl get pods -o wide
```

파드 3개가 두 워커에 나뉘어 배치됨. `-o wide`의 `NODE` 칸으로 확인.

### 실습 2: 파드 죽여보기

```bash
kubectl delete pod <파드이름>
kubectl get pods
```

**결과:** 지웠는데 여전히 3개. 하나가 새로 생겼다.

**이유:** `--replicas=3`으로 "3개 원한다"고 등록해뒀다. 현재가 2개가 되니 컨트롤 루프가 차이를 메웠다. 도커였다면 그냥 사라졌을 것.

### 실습 3: 노드 죽여보기 ★

```bash
docker stop study-worker2
kubectl get nodes    # 약 40초 후 NotReady
kubectl get pods -o wide -w
```

**타임라인**

| 시점    | 상태                                           |
| ------- | ---------------------------------------------- |
| 0초     | `docker stop` 실행                             |
| ~40초   | 노드가 `NotReady`                              |
| **5분** | 파드가 `Terminating`, 다른 노드에 새 파드 생성 |

**5분을 기다리는 이유:** 응답이 없을 때 "죽었다"와 "네트워크만 끊겼다"를 구분할 방법이 없다. 성급히 판단해서 파드를 다른 곳에 또 만들었다가 원래 것까지 살아나면 6개가 되는 사고가 난다.

**노드가 죽었는데 파드가 `Running`으로 보이는 이유:** 파드 상태를 보고하는 건 그 노드의 kubelet인데, 노드가 죽어 보고가 끊겼다. 컨트롤 플레인에 남은 건 마지막 보고, 즉 "잘 돌고 있음". **화면의 `Running`은 철 지난 정보.**

```bash
docker start study-worker2   # 복구
```

노드가 돌아와도 파드는 자동으로 되돌아오지 않는다. 이미 다른 곳에서 잘 돌고 있으니 옮길 이유가 없다.

### 실습 4: 개수 조절

```bash
kubectl scale deployment web --replicas=6
kubectl scale deployment web --replicas=2
```

실제 서비스에서 "트래픽 몰릴 때 늘리는" 동작. 명령어 한 줄, 몇 초.

### 실습 5: 자원 부족 (Pending) ★

`heavy.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: heavy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: heavy
  template:
    metadata:
      labels:
        app: heavy
    spec:
      containers:
        - name: nginx
          image: nginx
          resources:
            requests:
              memory: 100Gi
```

```bash
kubectl apply -f heavy.yaml
kubectl get pods    # 3개 전부 Pending
```

**결과:** 100GB를 요청했으니 어떤 노드도 줄 수 없어 전부 `Pending`.

**중요:** 쿠버네티스는 자원이 부족하면 억지로 밀어넣지 않는다. 자리가 생길 때까지 기다린다. 노드를 늘리거나 요구량을 줄이면 몇 초 안에 배치된다.

이 실습에서 처음으로 **YAML 파일 + `kubectl apply`** 방식을 사용했다. 이게 실무 정식 방법이다. 파일이 남으니 뭘 배포했는지 알 수 있고 깃으로 관리할 수 있다.

---

## 6. requests / limits

|              | 의미                                    | 초과하면                           |
| ------------ | --------------------------------------- | ---------------------------------- |
| **requests** | "최소 이만큼 필요" — 스케줄러가 보는 값 | (초과 개념 없음)                   |
| **limits**   | "이 이상 못 씀"                         | 메모리: 강제 종료 / CPU: 속도 제한 |

**스케줄러는 requests만 본다.** 실제 사용량이 아니라 요청량으로 계산한다. 노드 여유가 3GB이고 파드마다 1GB를 요청하면 3개까지만 들어간다. 4번째는 실제 메모리가 남아 있든 없든 `Pending`.

**메모리와 CPU가 다르다.** CPU는 상한을 넘으면 느려질 뿐이지만, 메모리는 넘으면 죽는다. 회수할 방법이 없기 때문.

### QoS Class

`describe pod` 출력에 나온다. 메모리 부족 시 죽이는 순서를 결정한다.

| Class        | 조건              | 위험도             |
| ------------ | ----------------- | ------------------ |
| `Guaranteed` | requests = limits | 가장 안전          |
| `Burstable`  | requests만 있음   | 중간               |
| `BestEffort` | 둘 다 없음        | **가장 먼저 죽임** |

**requests를 안 적으면 더 위험하다.** 아무것도 안 적으면 "자원 필요 없음"으로 간주해 무제한으로 밀어넣고, 노드 메모리가 터지면 `OOMKilled`가 된다.

### 두 실패 모드

| 상태        | 원인                         | 성격        |
| ----------- | ---------------------------- | ----------- |
| `Pending`   | 자원 요청이 과해 자리가 없음 | 얌전한 실패 |
| `OOMKilled` | 상한이 부족해 죽음           | 난폭한 실패 |

**원인이 정반대다.** 이 두 단어를 기억할 것.

---

## 7. 진단 방법

### Pending 진단 순서

```bash
kubectl describe pod <파드이름>
```

1. **`Node:` 칸이 비어 있나?** → 스케줄링 실패 (자리가 없음)
2. **`Node:`에 이름이 있는데 Pending인가?** → 이미지 받는 중이거나 볼륨 문제
3. **Events 확인** → 구체적 이유

1번과 2번은 완전히 다른 상황이다. 1번은 자원 문제, 2번은 이미지·볼륨 문제.

### 실제로 본 출력

```
Node:             <none>          ← 배정된 노드 없음 = 스케줄링 실패
Status:           Pending
Requests:
  memory:     100Gi               ← 100GB 요구
Conditions:
  PodScheduled   False            ← 배치 완료? 아니오
Controlled By:    ReplicaSet/heavy-77bbb8d8b8
Tolerations:      ... for 300s    ← 노드 장애 시 5분 대기의 근거
QoS Class:        Burstable
```

`Events:` 섹션이 안 나올 수 있다. **`-l` 라벨로 여러 파드를 묶어 describe하면 이벤트가 누락되는 경우가 있다.** 파드 하나를 이름으로 지정하거나, 이벤트를 직접 조회할 것.

### 이벤트 조회 (더 확실함)

```bash
kubectl get events --sort-by=.lastTimestamp
kubectl get events --field-selector reason=FailedScheduling
kubectl get events --field-selector involvedObject.name=<파드이름>
```

**`describe`에 의존하지 말고 `get events`를 쓰는 게 낫다.** 실무에서도 이걸 더 많이 쓴다.

### 그 외

```bash
kubectl get pods -A                                    # 모든 네임스페이스
kubectl get pods -o wide                               # 노드 배치 확인
kubectl get pods -w                                    # 변화 실시간 관찰
kubectl describe node <노드> | grep -A8 "Allocated resources"   # 노드 여유 확인
```

---

## 8. 명령어 요약

### 클러스터

```bash
kind create cluster --name study --config kind-config.yaml
kind delete cluster --name study
kind get clusters
docker ps --format '{{.Names}}'      # 노드 = 컨테이너 확인
```

### 조회

```bash
kubectl get nodes
kubectl get pods [-o wide] [-A] [-w] [-n 네임스페이스]
kubectl get deployments
kubectl get events --sort-by=.lastTimestamp
kubectl describe pod <이름>
kubectl describe node <이름>
```

### 배포

```bash
kubectl create deployment web --image=nginx --replicas=3
kubectl scale deployment web --replicas=6
kubectl apply -f 파일.yaml
kubectl delete deployment web
kubectl delete pod <이름> [--force --grace-period=0]
kubectl port-forward deployment/web 8080:80
```

### 구조 들여다보기

```bash
kubectl get pods -n kube-system                              # 컨트롤 플레인 부품
docker exec study-control-plane ls /etc/kubernetes/manifests  # 스태틱 파드 매니페스트
```

---

## 9. 삽질 기록

| 증상                                             | 원인                                                                                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `docker stop study-worker2` 했는데 파드가 그대로 | 아직 5분이 안 지났다. **먼저 `kubectl get nodes`가 NotReady로 바뀌는지 확인**해야 한다. 노드가 Ready면 파드는 절대 안 움직인다 |
| `Terminating`에서 안 사라짐                      | 지우는 절차를 수행할 kubelet이 죽어 있어서. `docker start`로 노드를 살리거나 `--force --grace-period=0`                        |
| `set resources`로 자원 추가했는데 다 Running     | 기존 파드는 유지된 채 새 파드만 Pending이 된다. 처음부터 YAML에 넣어야 명확                                                    |
| `describe pod -l app=xxx`에 Events가 없음        | 여러 파드 묶어 조회 시 누락. `get events`로 직접 조회                                                                          |

---

## 10. 아직 안 한 것

### 다음 단계

- [ ] **서비스(Service)** — 기본 개념 중 유일하게 미실습. `port-forward` 없이 접속하는 방법
- [ ] ConfigMap / Secret
- [ ] 인그레스 (Ingress)
- [ ] PVC (파드가 죽어도 남는 저장 공간)
- [ ] Helm (쿠버네티스판 패키지 설치 도구)

### 알아둘 이름들

- **레플리카셋(ReplicaSet)** — 디플로이먼트가 내부적으로 쓰는 것. 파드 이름 중간의 `5fc9f4bf66`이 이것
- **데몬셋(DaemonSet)** — 모든 노드에 정확히 하나씩 띄우는 방식
- **CNI** — 파드끼리 통신하게 해주는 네트워크 부품. 없으면 노드가 NotReady

### 로컬(kind)의 한계

- `type: LoadBalancer`가 안 된다 (`<pending>`). 로컬에 로드밸런서가 없어서. 그래서 `port-forward`를 썼다
- 진짜 네트워크가 아니다. 방화벽·서브넷·실제 IP를 다룰 일이 없다
- 노드 3대라도 물리적으로는 노트북 한 대. 장애 대비 측면에서는 의미가 없다

> **kind가 만드는 쿠버네티스는 진짜다.** 내부적으로 kubeadm을 쓰고, 컨트롤 플레인 컴포넌트가 그대로 파드로 뜬다. 여기서 배운 kubectl, YAML, 동작 원리는 AWS나 사내망 클러스터에서 100% 그대로 통한다. 프로덕션에 안 쓰는 것뿐.
