# 서비스 (Service)

> 출발점: `kubectl port-forward`는 임시 디버깅용이라는데, 정식 접속 방법은 무엇인가 (2026-09-07)
> 대상: Kubernetes v1.37.0, kube-proxy `iptables` 모드

## 한 줄 요약

여러 파드로 가는 **바뀌지 않는 입구**. 파드는 죽고 살아나며 IP가 계속 바뀌므로 고정된 이름과 IP가 필요하다. 부하 분산도 겸한다.

## 내용

### 만들기

```bash
kubectl expose deployment web --port=80        # 명령형
kubectl apply -f manifests/02-web-service.yml  # 선언형
```

```
NAME   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
web    ClusterIP   10.96.217.194   <none>        80/TCP    6m52s
```

`--port=80`만 적었는데 selector가 `app: web`으로 채워진다. 디플로이먼트의 selector를 그대로 복사한 것이다.

### 서비스는 프로세스가 아니다

**어디에도 "서비스"라는 프로그램은 떠 있지 않다.** 서비스는 저장된 선언일 뿐이고, 역할이 셋으로 나뉜다.

| 누가 | 무엇을 |
| --- | --- |
| **서비스** | "`app=web`인 파드로 보내라"는 **선언**. 그냥 문서 |
| **엔드포인트슬라이스 컨트롤러** | 그 선언을 읽고 **실제 명단을 만들어 계속 갱신** |
| **kube-proxy** | 각 노드에서 명단을 보고 **패킷을 돌리는 규칙을 설치** |

### 엔드포인트 — selector가 실제로 골라낸 결과

selector는 선언이고, 그것이 실제로 어떤 파드를 집어냈는지는 따로 볼 수 있다.

```bash
kubectl describe svc web          # 가장 자주 쓰는 방법
kubectl get endpointslice -l kubernetes.io/service-name=web
```

```
Selector:    app=web
IP:          10.96.217.194
Endpoints:   10.244.1.3:80,10.244.1.4:80,10.244.1.5:80
```

> **서비스가 동작하지 않을 때 가장 먼저 볼 곳이 이 `Endpoints` 줄이다.** 비어 있으면 selector가 파드를 하나도 못 찾은 것이고, 십중팔구 라벨 오타다.

엔드포인트슬라이스 속에는 IP 말고도 더 들어 있다.

```yaml
kind: EndpointSlice
endpoints:
  - addresses: [10.244.1.3]
    conditions:
      ready: true          # ← 트래픽 받을 준비가 됐나
      serving: true
      terminating: false
    nodeName: study-worker
    targetRef:             # ← 이 IP가 어느 파드의 것인지
      kind: Pod
      name: web-5fc9f4bf66-m9wb5
```

`ready: false`인 파드는 명단에 있어도 트래픽을 받지 않는다. 이 칸을 결정하는 것이 나중에 배울 readinessProbe다.

### 왜 "슬라이스(조각)"인가

명단이 길어지면 여러 조각으로 쪼갠다. **한 조각의 기본 상한은 100개**다.

```
# 이 클러스터의 kube-controller-manager 바이너리가 출력한 값
--max-endpoints-per-slice int32   ... (default 100)
```

파드 3개면 조각 하나(`web-5h2mq`)로 끝난다. 250개면 조각 3개가 된다. 조각과 서비스는 `kubernetes.io/service-name: web` 라벨로 연결된다.

옛 방식인 `kubectl get endpoints`도 아직 동작하지만 경고가 뜬다.

```
Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice
```

새로 배우는 입장에서는 **`endpointslice`만 기억하면 된다.**

### ClusterIP는 가짜 IP다

`10.96.217.194`이라는 주소를 가진 기계는 어디에도 없다. kube-proxy가 노드마다 깔아둔 규칙이 패킷의 목적지를 바꿔치기할 뿐이다.

워커 노드의 iptables를 직접 덤프한 결과다.

```
-A KUBE-SERVICES -d 10.96.217.194/32 -p tcp --dport 80 -j KUBE-SVC-LOLE4ISW44XBNF3G

-A KUBE-SVC-... --probability 0.33333333349 -j KUBE-SEP-...   → 10.244.1.3:80
-A KUBE-SVC-... --probability 0.50000000000 -j KUBE-SEP-...   → 10.244.1.4:80
-A KUBE-SVC-...                             -j KUBE-SEP-...   → 10.244.1.5:80

-A KUBE-SEP-MHDQ23KUGG7EGFMW -j DNAT --to-destination 10.244.1.3:80
```

**순번대로 돌리는 것이 아니라 매 접속마다 확률로 뽑는다.** 확률이 `1/3 → 1/2 → 나머지`로 이어지는 것이 요령이다.

- 첫 규칙에 걸릴 확률 1/3
- 안 걸린 2/3 중 1/2 → 전체의 1/3
- 남은 것 전부 → 전체의 1/3

결과적으로 균등하지만 **회수가 적으면 치우쳐 보인다.**

### 부하 분산 실측

파드마다 다른 내용을 넣어 구분되게 만든 뒤 30번 요청했다.

```bash
for p in $(kubectl get pods -l app=web -o name); do
  kubectl exec $p -- sh -c 'echo $HOSTNAME > /usr/share/nginx/html/index.html'
done

kubectl run loadtest --image=busybox --restart=Never -- \
  sh -c 'for i in $(seq 1 30); do wget -qO- http://web; done'
kubectl logs loadtest | sort | uniq -c
kubectl delete pod loadtest
```

```
14  web-5fc9f4bf66-l7vsv
 7  web-5fc9f4bf66-m9wb5
 9  web-5fc9f4bf66-r9tlv
```

치우쳐 보이지만 통계적으로는 정상이다.

```
기대값 10회, 이론상 표준편차 2.58회
카이제곱 = 2.60 (자유도 2), p = 0.273
→ "균등 분배가 아니다"라고 말할 근거 없음
```

### 서비스 타입 세 가지 — 고르는 게 아니라 쌓인다

| 타입 | 용도 | kind에서 |
| --- | --- | --- |
| `ClusterIP` | 클러스터 내부 전용 (기본값) | 정상 동작 |
| `NodePort` | 모든 노드의 포트로 외부 노출 | 동작하나 `extraPortMappings` 필요 |
| `LoadBalancer` | 클라우드 로드밸런서 연동 | **영원히 `<pending>`** |

**셋 중 하나를 고르는 것이 아니다. 위로 갈수록 아래 것을 포함한다.**

```
LoadBalancer = ClusterIP + NodePort + 외부 로드밸런서
   NodePort  = ClusterIP + 노드 포트
   ClusterIP = 클러스터 내부 IP
```

실측 (2026-09-08). 요청하지 않았는데 값이 채워져 있다.

```
NAME     TYPE           CLUSTER-IP      NODEPORT
web      ClusterIP      10.96.217.194   <none>
web-np   NodePort       10.96.158.200   31776
web-lb   LoadBalancer   10.96.202.135   32200   ← NodePort 도 같이 생김
```

로드밸런서는 결국 "노드의 포트로 트래픽을 보내는 장치"라서 NodePort 가 먼저 있어야 한다.
`LoadBalancer` 에 ClusterIP 가 있는 이유는 **클러스터 안에서 부를 때** 쓰라고다. 밖으로 나갔다 돌아올 이유가 없다.

### NodePort 는 모든 노드에 열린다

파드가 있는 노드뿐 아니라 **전부**다. 파드가 0개인 control-plane 에서 30번 요청한 결과:

```
 9  web-…-5kppn   (study-worker2)
12  web-…-9fwgr   (study-worker2)
 9  web-…-ql6k9   (study-worker)
기대값 10, 카이제곱 0.60 (자유도 2), p = 0.741
```

**파드가 하나도 없는 노드가 다른 노드의 파드로 전부 넘겨줬다.** 모든 노드의 kube-proxy 가
같은 엔드포인트 명단을 복제해 갖기 때문이다 → [10-kube-proxy-iptables.md](10-kube-proxy-iptables.md)

### LoadBalancer 가 `<pending>` 인 이유

실제 로드밸런서를 만들어줄 `cloud-controller-manager` 가 kind 에 없다.

```
Events:  <none>       ← 에러조차 안 난다
```

**실패가 아니라 "처리 중"으로 영구 정지한 상태다.** `kubectl apply` 성공이 "접수했다"이지
"실제로 됐다"가 아니라는 것의 또 다른 사례. AWS 단계로 넘어가야 하는 이유와 직결된다.

### externalTrafficPolicy — 이중 분산을 끄는 스위치

`LoadBalancer` 를 쓰면 분배가 두 번 일어난다.

```
로드밸런서 (노드 단위)  →  노드의 iptables (파드 단위)  →  파드
```

낭비처럼 보이지만 **두 층이 감추는 대상이 다르다.**

| 층 | 감추는 것 | 상대는 못 하는 일 |
| --- | --- | --- |
| 로드밸런서 | **노드 장애** | iptables 는 자기 노드가 죽은 걸 알릴 수 없다 |
| iptables | **파드 장애** | 로드밸런서는 파드 단위를 모른다 |

그래도 홉이 하나 더 생기고 클라이언트 IP 를 잃는 것은 사실이다. 그래서 스위치가 있다.

| | `Cluster` (기본값) | `Local` |
| --- | --- | --- |
| 외부 트래픽의 백엔드 | **전체 엔드포인트** | 그 노드의 엔드포인트만 |
| 노드 간 이동 | 있음 | 없음 |
| 클라이언트 IP | 노드 IP로 덮임 (`KUBE-MARK-MASQ`) | **보존** |
| 분배 | 균등 (33/33/33) | 노드별 파드 수에 좌우 (예: 50/25/25) |
| `healthCheckNodePort` | 없음 | **자동 생성** |

**`healthCheckNodePort` 는 내가 설정하는 게 아니라 결과물이다.** 실측:

```
externalTrafficPolicy 만 패치한 결과
  web-np   NodePort       Local     healthCheckNodePort <none>   ← 안 생김
  web-lb   LoadBalancer   Local     healthCheckNodePort 32647    ← 자동 배정
```

로드밸런서가 이 포트로 각 노드에 "너 이 서비스 파드 갖고 있냐"를 묻고, 없는 노드를 대상에서 뺀다.
`NodePort` 타입에는 물어볼 로드밸런서가 없으므로 생기지 않는다.

**`Local` 은 밖에서 들어온 트래픽에만 적용된다.** 클러스터 안에서 온 것은 `Local` 이어도 전체 분배를 받는다.

> "traffic sent to an External IP or LoadBalancer IP from within the cluster will always get **Cluster** semantics" — 공식 문서

### control-plane 은 로드밸런서 대상에서 빠진다

```
node.kubernetes.io/exclude-from-external-load-balancers    ← 라벨이 붙어 있다
```

**NodePort 는 열려 있지만**(직접 접속하면 응답한다) **클라우드 로드밸런서는 이 노드를 대상 목록에서 뺀다.**
control-plane 에 앱 파드가 없는 것은 별개 이유다 — `node-role.kubernetes.io/control-plane:NoSchedule` taint.

> ⚠️ 확인 필요: kind 에는 로드밸런서가 없어 실제 제외 동작은 확인하지 못했다. 라벨 존재까지만 확인.

## 왜 이렇게 설계됐나

**"고정된 입구"를 프로그램이 아니라 규칙으로 구현했다.**

입구를 실제 프록시 프로세스로 만들면 그 프로세스가 병목이자 단일 장애점이 된다. 모든 트래픽이 한 곳을 거치므로 노드가 많아질수록 나빠진다.

kube-proxy는 대신 **모든 노드에 똑같은 규칙을 복제해 둔다.** 파드가 어느 노드에서 요청하든 자기 노드의 커널이 목적지를 바꿔준다. 중간에 거칠 프로세스가 없고, 노드가 늘어나도 성능이 그대로다. 서비스가 프로세스가 아니라 선언인 이유가 이것이다.

명단 갱신을 별도 컨트롤러로 분리한 것도 같은 맥락이다. kube-proxy는 파드를 감시하지 않고 명단만 읽는다. 감시는 컨트롤러 하나가 대표로 한다.

## 이 설명이 깨지는 조건

- **`iptables` 모드일 때의 이야기다.** 모드는 `kubectl -n kube-system get cm kube-proxy -o yaml | grep mode`로 확인한다. `ipvs`나 `nftables` 모드는 분배 방식이 다르다
- **부하 분산은 접속(connection) 단위다.** HTTP Keep-Alive나 gRPC처럼 연결을 오래 유지하면 **한 파드에 계속 붙는다.** 요청 수가 아무리 많아도 분산되지 않는다. 실무에서 자주 겪는 함정이다
- **클러스터 바깥에서는 ClusterIP도 이름도 통하지 않는다** → [07-cluster-dns.md](07-cluster-dns.md)
- **`ready: false`인 파드는 명단에서 빠진다.** 엔드포인트가 비어 보이는데 파드는 `Running`이라면 이 조건을 의심한다

## 근거

- [Kubernetes 공식 문서 — Service](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes 공식 문서 — EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/) — "the control plane creates and manages EndpointSlices to have no more than 100 endpoints each"
- [Kubernetes 공식 문서 — Virtual IPs and Service Proxies](https://kubernetes.io/docs/reference/networking/virtual-ips/)
- 실측: `docker exec study-worker iptables-save -t nat | grep default/web` (2026-09-07)
- 실측: 부하 분산 30회 → 14/7/9, 카이제곱 2.60, p=0.273 (2026-09-07)
- 세션 기록: [logs/day-01.md](../../logs/day-01.md)
