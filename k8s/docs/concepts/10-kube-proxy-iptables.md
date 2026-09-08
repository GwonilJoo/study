# kube-proxy 와 iptables

> 출발점: "서비스는 프로세스가 아니라 규칙"이라는 말의 실체가 뭔지 (2026-09-08)
> 대상: Kubernetes v1.37.0, kube-proxy `iptables` 모드, iptables v1.8.11 (`nf_tables` 백엔드)

## 한 줄 요약

서비스 라우팅은 **각 노드 커널의 iptables 규칙**으로 구현된다. 중앙에 프록시 프로세스가 없고, 모든 노드가 같은 규칙을 복제해 갖는다.

## 내용

### 체인 이름과 역할

| 이름 | 정체 |
| --- | --- |
| `KUBE-SERVICES` | 모든 서비스 트래픽의 입구. `PREROUTING`/`OUTPUT` 에서 점프 |
| `KUBE-NODEPORTS` | NodePort 전용 입구. `KUBE-SERVICES` 의 **마지막** 규칙에서 점프 |
| `KUBE-EXT-<해시>` | 외부 유입 처리 체인 |
| `KUBE-SVC-<해시>` | **서비스 체인.** 확률로 백엔드를 고른다. 서비스 하나당 하나 |
| `KUBE-SVL-<해시>` | **서비스 로컬 체인.** `externalTrafficPolicy: Local` 일 때만 생김 |
| `KUBE-SEP-<해시>` | **서비스 엔드포인트 체인.** 파드 하나당 하나. 실제 `DNAT` 수행 |
| `KUBE-MARK-MASQ` | 출발지 IP를 노드 IP로 바꾸라는 표시 |

`SVC` = Service, `SEP` = Service EndPoint, `SVL` = Service LocaL, `EXT` = External.

### 두 경로가 한 곳에서 만난다

```
ClusterIP 로 들어옴
  PREROUTING → KUBE-SERVICES → KUBE-SVC-<해시>
                                     │
NodePort 로 들어옴                    │  같은 체인
  PREROUTING → KUBE-SERVICES ────────┤
             → KUBE-NODEPORTS        │
             → KUBE-EXT-<해시> ───────┘
                                     ▼
                              KUBE-SEP-<해시> → DNAT 파드IP:포트
```

**같은 체인을 쓴다 = 백엔드 목록이 완전히 같다.** 그래서 NodePort 로 들어와도 노드를 가리지 않는다.

### 분배는 순번이 아니라 확률이다

```
-A KUBE-SVC-4UDS… --probability 0.33333333349 -j KUBE-SEP-…  → 10.244.1.8:80
-A KUBE-SVC-4UDS… --probability 0.50000000000 -j KUBE-SEP-…  → 10.244.2.13:80
-A KUBE-SVC-4UDS…                             -j KUBE-SEP-…  → 10.244.2.14:80
```

`1/3` → 남은 것의 `1/2` → 나머지 전부. 결과적으로 균등하지만 **회수가 적으면 치우쳐 보인다.**

### 엔드포인트가 0이면 REJECT

```
-A KUBE-SERVICES -d <ClusterIP>/32 --dport 80
   --comment "default/web has no endpoints"
   -j REJECT --reject-with icmp-port-unreachable
```

`nat` 의 분배 규칙이 통째로 사라지고 `filter` 에 REJECT 한 줄이 남는다. 그래서 **시간 초과가 아니라 즉시 거부**된다.

### externalTrafficPolicy: Local 일 때

```
KUBE-EXT-<해시>
  ├─ -s <파드CIDR>      (파드에서 온 것)  → KUBE-SVC-<해시>   전체 엔드포인트
  ├─ --src-type LOCAL   (노드 자신)      → KUBE-SVC-<해시>   전체 엔드포인트
  └─ (그 외 = 진짜 외부)                 → KUBE-SVL-<해시>   그 노드 것만
```

**`KUBE-SVC` 는 그대로 전체를 유지한다.** `KUBE-SVL` 이라는 별도 체인이 생기고, 외부 트래픽만 그리로 간다.

로컬 엔드포인트가 없는 노드에는 **`KUBE-SVL` 체인 자체가 만들어지지 않고**, `KUBE-EXT` 에도 그리로 가는 줄이 없다. 외부 트래픽은 거기서 끊긴다.

### 규칙은 언제 만들어지는가

**kube-proxy 가 감시하는 것은 파드가 아니라 Service 와 EndpointSlice 다.** 실험으로 확인했다.

| 한 것 | `nat` | `filter` |
| --- | --- | --- |
| 파드만 생성 (서비스 없음, Ready 확인) | **0** | **0** |
| 아무 파드도 안 맞는 서비스 생성 | 0 | **REJECT 1줄** |
| 서비스 selector 를 그 파드에 맞게 패치 | **DNAT 규칙들** | REJECT 사라짐 |

```
파드 Ready → 엔드포인트슬라이스 컨트롤러가 명단 갱신 → kube-proxy 감지 → 규칙 재작성
                                                       └─ 여기서 처음 반응
```

### 모든 파드가 들어가는 것은 아니다

**규칙 수 = 서비스 × 엔드포인트 × 포트.** 파드 수가 아니다.

파드 16개짜리 클러스터에서 실측한 DNAT 목적지:

```
  3 --to-destination 10.244.2.14:80    ┐ web 파드. 서비스 3개가 각각 잡아 3번씩
  3 --to-destination 10.244.2.13:80    ├
  3 --to-destination 10.244.1.8:80     ┘
  2 --to-destination 10.244.0.4:53     ┐ CoreDNS. 포트마다 따로
  2 --to-destination 10.244.0.2:53     ┘
  1 --to-destination 172.24.0.2:6443   ── API 서버
```

`kindnet`·`kube-proxy`(데몬셋)·`local-path-provisioner` 는 **서비스가 없어서 iptables 에 없다.**

## 조회 방법

규칙은 각 노드의 커널에 있다. `kubectl` 로는 볼 수 없다.

```bash
# kind — 노드가 도커 컨테이너
docker exec study-worker iptables -t nat -S

# 실서버 — SSH 로 들어가서
sudo iptables -t nat -S
```

### 서비스 하나만 보기 (가장 자주 씀)

```bash
docker exec study-worker iptables-save -t nat | grep "default/web-np"
```

**서비스 이름이 규칙 주석에 `<네임스페이스>/<서비스이름>` 형식으로 박혀 있다.**

### 체인 이름 찾아 그 체인만 보기

```bash
CH=$(docker exec study-worker iptables-save -t nat \
     | grep "web-np cluster IP" | grep -o 'KUBE-SVC-[A-Z0-9]*')
docker exec study-worker iptables -t nat -S $CH
```

### 트래픽이 실제로 흘렀는지 — 카운터

```bash
docker exec study-worker iptables -t nat -L KUBE-SERVICES -n -v
```

```
 pkts bytes target                     destination      comment
    0     0 KUBE-SVC-LOLE4ISW44XBNF3G  10.96.217.194    /* default/web cluster IP */
```

- **`pkts` 가 0** → 트래픽이 여기까지 오지도 않았다. 앞단을 봐야 한다
- **`pkts` 는 느는데 응답이 없다** → 규칙은 탔다. 파드 쪽 문제

`iptables -t nat -Z` 로 카운터를 초기화하고 다시 잴 수 있다.

### 옵션 정리

| 옵션 | 뜻 |
| --- | --- |
| `-t nat` / `-t filter` | 테이블 선택. **REJECT 는 `filter` 에 있다** |
| `-S [체인]` | 규칙을 명령 형식으로 출력. **구조 파악용** |
| `-L -n -v` | 표 형식 + 카운터. **트래픽 확인용** |
| `iptables-save -t nat` | 전체 덤프. grep 하기 좋음 |
| `-Z` | 카운터 초기화 |

## 왜 이렇게 설계됐나

**중앙 프록시를 두지 않으려는 것이다.**

입구를 실제 프록시 프로세스로 만들면 모든 트래픽이 한 곳을 지난다. 그 프로세스가 병목이자 단일 장애점이 되고, 노드가 늘어날수록 나빠진다.

대신 **모든 노드에 같은 규칙을 복제해 둔다.** 어느 노드에서 요청하든 자기 노드의 커널이 목적지를 바꿔준다. 중간에 거칠 프로세스가 없고, 노드가 늘어도 성능이 그대로다.

**판단은 로컬에서, 규칙은 전역에서.** 이것이 "서비스는 프로세스가 아니라 선언"이라는 말의 실체다.

명단 갱신을 별도 컨트롤러로 분리한 것도 같은 맥락이다. kube-proxy 는 파드를 감시하지 않고 명단만 읽는다. 감시는 엔드포인트슬라이스 컨트롤러 하나가 대표로 한다.

## 이 설명이 깨지는 조건

- **규칙 수가 서비스 × 파드에 비례해 늘어난다.** iptables 는 규칙을 위에서부터 훑고, 엔드포인트가 하나 바뀌면 규칙 전체를 다시 쓴다. 대규모에서는 느려진다
  > ⚠️ 확인 필요: `ipvs`(커널 로드밸런서, 해시 테이블) 와 `nftables` 모드의 성능 특성은 검증하지 않았다
- **`iptables` 명령이 실제로는 `nftables` 를 감싼 껍데기다.** `iptables --version` 이 `(nf_tables)` 로 나온다. `iptables` 로 보이는 것과 `nft list ruleset` 으로 보이는 것이 다를 수 있다
- **전파가 즉각적이지 않다.** 파드가 종료 절차에 들어갔는데 규칙에는 아직 남아 있는 순간이 있다. 배포 중 순간 에러의 원인
- **`Local` 정책에서 클러스터 내부 트래픽은 예외다.** 파드나 노드 자신이 보낸 것은 `Local` 이어도 전체 분배(`Cluster` 의미)를 받는다

## 근거

- [Kubernetes 공식 문서 — Virtual IPs and Service Proxies](https://kubernetes.io/docs/reference/networking/virtual-ips/)
- 실측: `docker exec study-worker iptables-save -t nat|filter` (2026-09-08)
- 실측: control-plane(web 파드 0개)에서 NodePort 30회 요청 → 9/12/9, p=0.741 (2026-09-08)
- 실측: 파드/서비스 생성 3단계 실험으로 규칙 생성 시점 확인 (2026-09-08)
- 세션 기록: [logs/day-02.md](../../logs/day-02.md)
