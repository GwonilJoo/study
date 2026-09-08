# 2일차 — 라벨 떼어내기, 서비스 타입 3종, kube-proxy 내부

> 날짜: 2026-09-08
> 환경: macOS + Docker + kind, Kubernetes v1.37.0, kube-proxy `iptables` 모드 (백엔드 `nf_tables`)
> 다룬 개념: [05-label-selector](../docs/concepts/05-label-selector.md), [06-service](../docs/concepts/06-service.md), [10-kube-proxy-iptables](../docs/concepts/10-kube-proxy-iptables.md)
> 계획 대비: 로드맵의 Day 2는 "라벨 떼어내기 + 서비스 타입 3종"이었는데, 질문이 이어지며 **kube-proxy 내부 구조까지** 들어갔다.

---

## 시작 상태

```
web 디플로이먼트 3/3   (파드 전부 study-worker 에 몰림)
서비스 web (ClusterIP) 10.96.217.194
```

---

## 실습 1 — 파드 라벨 떼어내기

**예측**

> 파드 3개 중 하나의 라벨을 `app=web` → `app=broken` 으로 바꾸면?

내 답: **레플리카 지정 개수보다 하나가 적어졌으므로 파드가 새로 하나 생성된다.**
이어서: **파드는 4개, 엔드포인트는 3개.**

**결과 — 두 예측 모두 정확**

```
web-...-l7vsv   app=broken,pod-template-hash=5fc9f4bf66   Running  10.244.1.5   ← 고아
web-...-llqk7   app=web,   pod-template-hash=5fc9f4bf66   Running  10.244.2.10  ← 새로 생김
web-...-m9wb5   app=web,   ...                            Running  10.244.1.3
web-...-r9tlv   app=web,   ...                            Running  10.244.1.4

엔드포인트: 10.244.1.3, 10.244.1.4, 10.244.2.10   ← 1.5 빠지고 2.10 들어옴
레플리카셋: DESIRED 3 / CURRENT 3 / READY 3
```

**추가로 확인한 것 세 가지**

① **레플리카셋이 고아를 "놓아줬다"(release).** 소유권 표시를 스스로 지웠다.

```
l7vsv 의 ownerReferences:  (비어 있음)
llqk7 의 ownerReferences:  ReplicaSet/web-5fc9f4bf66  controller=true
```

② **레플리카셋은 고아의 존재를 모른다.** 파드는 4개인데 `replicas: 3 / ready: 3`으로 만족한 상태.
→ **`kubectl get rs`가 정상이라고 파드가 3개라는 뜻이 아니다.**

③ **고아는 죽지 않고 계속 nginx 를 서비스한다.** 트래픽만 안 온다.
→ 이것이 사고가 아니라 **정식 디버깅 기법**이다. 문제 파드를 트래픽에서 떼되 죽이지 않고 들여다볼 수 있다.

---

## 실습 2 — 디플로이먼트를 지우면 고아는?

**예측** 살아있을 것 같다 → **맞음.**

```bash
kubectl delete deployment web
```

```
web-...-l7vsv  (app=broken)  Running    ← 소유자가 없으니 청소 대상도 아님
(나머지 3개는 레플리카셋과 함께 사라짐)
```

**그리고 서비스는 남았다.**

```
Selector:    app=web
Endpoints:            ← 텅 빔
```

### 예측 — 이 상태에서 `http://web` 에 접속하면?

| | 보기 |
| --- | --- |
| A | DNS 에러 |
| B | 한참 기다리다 시간 초과 |
| C | **즉시 연결 거부** |
| D | 고아 파드가 응답 |

내 답: **C** → **정답.**

```
wget: can't connect to remote host (10.96.217.194): Connection refused
STATUS: Error   AGE: 6s      (-T 10 을 줬는데 6초 만에 끝남)
```

**에러 한 줄에 두 정보가 있다.**

```
can't connect to remote host (10.96.217.194): Connection refused
                              └─ IP가 찍힘 = DNS 성공    └─ 2단계 실패
```

### 왜 시간 초과가 아니라 즉시 거부인가

```
-A KUBE-SERVICES -d 10.96.217.194/32 --dport 80
   --comment "default/web has no endpoints"
   -j REJECT --reject-with icmp-port-unreachable
```

엔드포인트가 0이 되면 `nat` 의 분배 규칙이 통째로 사라지고 `filter` 에 REJECT 한 줄이 남는다.
**빨리 실패하는 게 조용히 매달려 있는 것보다 낫다**는 판단.

### 증상별 진단표

| 증상 | 끊긴 곳 |
| --- | --- |
| `bad address 'web'` | 1단계. DNS |
| `Connection refused` **즉시** | 2단계. **엔드포인트가 비었다** → 라벨 확인 |
| 한참 기다리다 timeout | 엔드포인트는 있는데 파드가 응답 안 함 / 포트 틀림 / 정책 차단 |

### 삽질 — 로그가 비어 있었다

`wget` 을 `weget` 으로 오타. `kubectl logs test` 가 아무것도 안 찍힘.

```
STATUS: StartError
exec: "weget": executable file not found in $PATH
```

**`kubectl logs` 가 비어 있다고 "출력이 없다"는 뜻이 아니다. 컨테이너가 아예 안 떴을 수 있다.**
로그가 비면 **`kubectl get pod` 의 STATUS 부터** 본다.

---

## 실습 3 — NodePort

**예측**

> `NodePort` 서비스를 만들면 `CLUSTER-IP` 칸에 뭐가 찍힐까? (A: 비어 있다 / B: IP가 생긴다)

내 답: **B** → **정답.**

```
NAME     TYPE           CLUSTER-IP      NODEPORT
web      ClusterIP      10.96.217.194   <none>
web-np   NodePort       10.96.158.200   31776
web-lb   LoadBalancer   10.96.202.135   32200   ← 요청 안 했는데 NodePort도 생김
```

**타입은 셋 중 하나를 고르는 게 아니라 쌓인다.**

```
LoadBalancer = ClusterIP + NodePort + 외부 로드밸런서
   NodePort  = ClusterIP + 노드 포트
   ClusterIP = 클러스터 내부 IP
```

### 노트북에서 접속 — 실패

```
curl -m 5 http://localhost:31776
curl: (7) Failed to connect ... after 0 ms
```

kind 노드는 도커 컨테이너인데 포트 매핑이 없다. macOS는 Docker Desktop 이 리눅스 VM 안에서 도는 장벽이 하나 더 있다.
**막힌 건 쿠버네티스가 아니라 맥과 도커 컨테이너 사이.**

### ★ 반증 실험 — NodePort는 그 노드의 파드에만 가는가

내 예측: **"nodeport로 들어온 것은 특정 노드에 있는 파드들에게만 간다"** → **틀림.**

`study-control-plane` 에는 `web` 파드가 **0개**다. 여기로 30번 요청했다.

```bash
docker exec study-control-plane sh -c \
  'for i in $(seq 1 30); do curl -s localhost:31776; done' | sort | uniq -c
```

```
 9  web-765d857f6b-5kppn   ← study-worker2
12  web-765d857f6b-9fwgr   ← study-worker2
 9  web-765d857f6b-ql6k9   ← study-worker
```

```
기대값 10회, 카이제곱 = 0.60 (자유도 2), p = 0.741  → 균등과 어긋날 근거 없음
```

**파드가 하나도 없는 노드가 다른 노드의 파드 3개로 전부 넘겨줬다.**

이유: 모든 노드의 kube-proxy 가 **같은 엔드포인트슬라이스를 읽어 똑같은 규칙을 복제**한다. "내 노드에 파드가 있는지"는 판단 기준이 아니다.

---

## 실습 4 — LoadBalancer

```
web-lb   LoadBalancer   10.96.202.135   <pending>   80:32200/TCP
```

**1분을 기다려도 안 바뀐다. 영원히 안 바뀐다.**

```bash
kubectl get pods -n kube-system | grep -i cloud
# 없음
```

`cloud-controller-manager` 가 없어서다. 주문은 접수됐는데 처리할 주체가 없다.

```
Events:  <none>       ← 에러조차 안 남. "실패"가 아니라 "처리 중"으로 영구 정지
```

→ **AWS 단계(Day 20)로 가야 하는 이유.**

---

## 실습 5 — externalTrafficPolicy 실측

### 질문: 이중 분산은 낭비 아닌가

> "외부 로드 밸런서가 트래픽을 노드 N개에 분산해주는데, 이걸 다시 iptables에서 분산하면 다시 전체 노드 대상으로 분배되는거잖아"

**타당한 지적이고, 실제로 비용이다.** 다만 두 층이 감추는 대상이 다르다.

```
로드밸런서  →  노드 장애를 감춘다   (iptables 는 못 함)
iptables   →  파드 장애를 감춘다   (로드밸런서는 못 함)
```

그리고 그 비용을 없애는 설정이 `externalTrafficPolicy: Local` 이다.

### 실측 — healthCheckNodePort 는 자동으로 생긴다

`externalTrafficPolicy` **만** 패치하고 `healthCheckNodePort` 는 건드리지 않았다.

```
변경 전
  web-np   NodePort       Cluster   <none>
  web-lb   LoadBalancer   Cluster   <none>

변경 후
  web-np   NodePort       Local     <none>      ← 안 생김
  web-lb   LoadBalancer   Local     32647       ← 자동 배정
```

**`LoadBalancer` 타입에서만 생긴다.** `NodePort` 타입은 앞단에 헬스체크할 로드밸런서가 없으니 필요가 없다.

### 발견 — `KUBE-SVL` 체인

`Local` 로 바꾸자 **처음 보는 체인**이 생겼다. `SVL` = Service Local.

```
study-worker
  KUBE-EXT-4IMN…
    ├─ -s 10.244.0.0/16 (파드에서 온 것) → KUBE-SVC-4IMN…   ← 전체 3개
    ├─ --src-type LOCAL (노드 자신)      → KUBE-SVC-4IMN…   ← 전체 3개
    └─ (그 외 = 진짜 외부)               → KUBE-SVL-4IMN…   ★
  KUBE-SVL-4IMN…  → 10.244.1.8:80                     (1개)

study-worker2
  KUBE-SVL-4IMN…  → 10.244.2.13:80 / 10.244.2.14:80   (2개)

study-control-plane
  KUBE-SVL-4IMN…  → No chain (아예 없음)
  KUBE-EXT 에 SVL 로 가는 줄도 없음 → 외부 트래픽은 여기서 끊김
```

**`KUBE-SVC` 는 그대로 전체 명단을 유지하고, `KUBE-SVL` 이 따로 생긴다.**

그리고 **클러스터 안에서 온 트래픽은 `Local` 이어도 전체 분배를 받는다.** 공식 문서와 일치한다.

> "traffic sent to an External IP or LoadBalancer IP from within the cluster will always get **Cluster** semantics"

### control-plane 이 로드밸런서 대상에서 빠지는 이유

```
node.kubernetes.io/exclude-from-external-load-balancers    ← 라벨이 붙어 있음
taints: [{"key":"node-role.kubernetes.io/control-plane","effect":"NoSchedule"}]
```

**NodePort 는 열려 있지만(직접 접속하면 됨), 클라우드 로드밸런서는 이 노드를 대상 목록에서 뺀다.**

> ⚠️ 미검증: kind 에는 로드밸런서가 없어 실제 제외 동작은 확인하지 못했다. 라벨이 붙어 있다는 것까지만 확인.

---

## 실습 6 — iptables 규칙은 언제 생기는가

**질문: 파드 생성 시점인가, 서비스 생성 시점인가?**

3단계로 만들어 가며 확인했다.

| 단계 | 한 것 | nat | filter |
| --- | --- | --- | --- |
| ① | 파드만 생성 (`app=demo`, 서비스 없음). Ready 까지 확인 | **0** | **0** |
| ② | 아무 파드도 안 맞는 서비스 생성 | 0 | **REJECT 1줄** |
| ③ | 서비스 selector 를 `app=demo` 로 패치 | **DNAT 규칙들** | REJECT 사라짐 |

**파드가 정상적으로 떠서 IP까지 받았는데 iptables 는 아무 변화가 없었다.** ③에서는 파드를 건드리지 않고 서비스만 고쳤는데 규칙이 통째로 바뀌었다.

**kube-proxy 가 감시하는 것은 파드가 아니라 Service 와 EndpointSlice 다.**

```
파드 Ready → 엔드포인트슬라이스 컨트롤러가 명단 갱신 → kube-proxy 감지 → 규칙 재작성
                                                        └─ 여기서 처음 반응
```

**전파에 단계가 여러 개라 즉각적이지 않다.** 파드가 종료 절차에 들어갔는데 iptables 에는 아직 남아 있는 순간이 있고, 그래서 배포 중 순간 에러가 난다. (대응은 Day 4 Probe 에서)

---

## 실습 7 — iptables 에 모든 파드가 있는가

**아니다. 서비스의 백엔드가 된 파드만 있다.**

```
클러스터 파드      16개
iptables 목적지     5개 (+ apiserver 1개)
```

```
  3 --to-destination 10.244.2.14:80    ┐ web 파드. 서비스 3개가 각각 잡아서
  3 --to-destination 10.244.2.13:80    ├ 3번씩 등장
  3 --to-destination 10.244.1.8:80     ┘
  2 --to-destination 10.244.0.4:53     ┐ CoreDNS (kube-dns 서비스)
  2 --to-destination 10.244.0.2:53     ┘ 포트마다 따로
  1 --to-destination 172.24.0.2:6443   ── kubernetes 서비스 (API 서버)
```

**규칙 수 = 서비스 × 엔드포인트 × 포트.** 파드 수가 아니다.

들어가지 않은 파드: `kindnet`, `kube-proxy`(데몬셋), `local-path-provisioner` — **서비스가 없다.**

`etcd`·`kube-scheduler`·`kube-controller-manager` 도 서비스가 없다. 다만 `hostNetwork: true` 라서 파드 IP가 노드 IP(`172.24.0.2`)와 같아, 단순 grep 으로는 API 서버 규칙과 구분되지 않는다.

---

## 오답 노트

### ① NodePort 는 그 노드의 파드에게만 트래픽을 보내는가

- **내가 한 답**: nodeport로 들어온 것은 특정 노드에 있는 파드들에게만 간다
- **실제**: 기본값(`externalTrafficPolicy: Cluster`)에서는 노드를 가리지 않는다. `web` 파드가 0개인 control-plane 에서 30번 요청 → 3개 파드가 9/12/9 로 응답 (p=0.741)
- **왜 틀렸나**: "노드의 포트"라는 말 때문에 그 노드 안에서 끝난다고 생각했다. 실제로는 모든 노드의 kube-proxy 가 **같은 엔드포인트 명단을 복제**해 갖고 있다
- **단**, `externalTrafficPolicy: Local` 로 바꾸면 내 예상대로 동작한다 (기본값이 아님). 완전히 틀린 직관이 아니라 기본값이 아닌 쪽을 떠올린 것
- 관련: [06-service.md](../docs/concepts/06-service.md), [10-kube-proxy-iptables.md](../docs/concepts/10-kube-proxy-iptables.md)
- [ ] 복습

### ② 재분배가 "클러스터 차원"에서 일어난다고 생각했다

- **내가 한 답**: "쿠버네티스가 관리하는 클러스터에서 재로드밸런싱이 되는 것"
- **실제**: 중앙에서 하는 게 아니다. **트래픽을 받은 그 노드가 자기 커널의 iptables 규칙으로 혼자 결정**한다. 재분배를 담당하는 중앙 컴포넌트는 없다
- **왜 틀렸나**: 모든 노드가 같은 결과를 내니 중앙에 조정자가 있다고 생각했다. 실제로는 **같은 규칙이 복제돼 있을 뿐 판단은 로컬**이다
- **왜 중요한가**: 중앙 프록시를 두지 않은 것이 이 설계의 핵심이다. 병목도 단일 장애점도 없다
- 덧붙임: "해당 노드 내의 파드로 가는 게 아니라"도 부정확. **갈 수도 있다**(1/3). "노드를 가리지 않는다"이지 "자기 노드를 피한다"가 아니다
- [ ] 복습

### ③ healthCheckNodePort 와 externalTrafficPolicy 의 인과를 뒤집었다

- **내가 한 답**: "해당 노드 내 파드들에게 트래픽이 전송되게 하려면 healthCheckNodePort를 사용해야 하고, externalTrafficPolicy를 local로 변경해야 한다"
- **실제**: `externalTrafficPolicy: Local` 로 바꾸면 **`healthCheckNodePort` 는 자동으로 배정된다.** 내가 쓰는 게 아니라 결과물이다. 그리고 **`LoadBalancer` 타입에서만** 생긴다 (`NodePort` 타입은 `Local` 로 해도 안 생김) — 실측 확인
- **왜 틀렸나**: 두 필드를 "둘 다 설정해야 하는 조건"으로 나란히 봤다. 실제로는 원인 하나와 결과 하나다
- **고쳐 쓰면**: "`externalTrafficPolicy: Local` 로 바꾸면 된다. `LoadBalancer` 타입이면 `healthCheckNodePort` 가 알아서 따라온다"
- [ ] 복습

---

## Claude 설명의 오류 (기록용)

기록의 신뢰도를 위해 남긴다.

1. **"`Local` 이면 각 노드의 `KUBE-SVC` 에 그 노드 파드만 들어간다"** — 틀렸다. `KUBE-SVC` 는 전체를 유지하고 **별도의 `KUBE-SVL` 체인**이 생긴다. 실제로 덤프해서 발견
2. **LoadBalancer 그림에서 control-plane 에도 `1/3` 을 보내는 것으로 그림** — `exclude-from-external-load-balancers` 라벨 때문에 제외 대상이다. 두 노드에 `1/2` 씩이 맞다
3. **`Local` 그림의 화살표가 제외된 노드를 가리킴** — 배치 실수

---

## 다음에 할 것

**Day 3 — ConfigMap / Secret** (로드맵 기준)

이번에 미뤄둔 것:

- [ ] `kind-config.yml` 에 `extraPortMappings` 넣고 재생성 → NodePort 를 노트북에서 실제로 접속
      **Day 10(인그레스) 시작할 때 함께 한다.** 그때 어차피 필요하다
- [ ] `ipvs` / `nftables` 모드의 성능 특성 (⚠️ 미검증, 지금 진도와 무관)
