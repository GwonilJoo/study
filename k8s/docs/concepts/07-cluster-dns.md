# 클러스터 DNS와 네임스페이스

> 출발점: `http://web`은 어디서 되는 주소인가. 노트북에서는 왜 안 되나 (2026-09-07)
> 대상: Kubernetes v1.37.0, CoreDNS

## 한 줄 요약

`web`이라는 이름이 통하는 것은 **클러스터 안에 DNS 서버가 따로 떠 있기 때문**이다. 그리고 그 이름은 클러스터 안에서만 통한다.

## 내용

### 두 단계를 구분해야 한다

`http://web`으로 접속할 때 벌어지는 일은 단계가 둘이고, **기준이 서로 다르다.**

| 단계 | 하는 일 | 기준 | 누가 |
| --- | --- | --- | --- |
| **1단계** | `web` → `10.96.217.194` | **서비스의 이름** | CoreDNS |
| **2단계** | `10.96.217.194` → 파드 IP 중 하나 | **라벨 (`app=web`)** | kube-proxy |

**1단계는 라벨과 아무 상관이 없다.** 서비스 이름만 본다.

반례로 확인된다. 서비스의 selector를 엉뚱한 값으로 바꿔도 `web`은 여전히 `10.96.217.194`로 잘 풀린다. DNS는 멀쩡하고, 2단계에서 갈 곳이 없어 접속만 실패한다.

이 구분이 진단에서 중요하다. **"이름을 못 찾는 것"과 "이름은 찾았는데 뒤에 아무도 없는 것"은 원인도 해결책도 다르다.**

### DNS 서버의 정체

```bash
kubectl -n kube-system get pods -l k8s-app=kube-dns
kubectl -n kube-system get svc kube-dns
```

```
coredns-559f6c778d-mk69l   Running   10.244.0.2
coredns-559f6c778d-qbxc9   Running   10.244.0.4

kube-dns   ClusterIP   10.96.0.10   53/UDP,53/TCP,9153/TCP
```

**CoreDNS**가 파드로 2개 떠 있다. 흥미로운 점은 **DNS 자신도 서비스로 노출돼 있다는 것**이다 — 이름은 `kube-dns`인데 실제 구현은 CoreDNS다(옛 이름이 남은 것).

### 파드는 DNS 설정을 갖고 태어난다

실제 파드 안의 `/etc/resolv.conf`다.

```
search default.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
```

`nameserver`가 위의 `kube-dns` 서비스 주소다. 파드가 만들어질 때 kubelet이 넣어준다.

### `web`은 줄임말이다

정식 이름은 이렇게 생겼다.

```
web . default . svc . cluster.local
 │      │        │        │
 │      │        │        └─ 클러스터 기본 도메인
 │      │        └─ 서비스라는 뜻
 │      └─ 네임스페이스
 └─ 서비스 이름
```

`search` 줄에 `default.svc.cluster.local`이 들어 있어서 `web`만 써도 자동으로 뒤가 붙는다.

**다른 네임스페이스의 서비스는 줄여 쓸 수 없다.**

| 쓰는 곳 | 쓰는 이름 |
| --- | --- |
| 같은 네임스페이스 | `web` |
| 다른 네임스페이스 | `grafana.monitoring` |
| 완전한 이름 | `grafana.monitoring.svc.cluster.local` |

### 네임스페이스는 클러스터 안의 폴더다

| 네임스페이스 | 들어 있는 것 |
| --- | --- |
| `default` | 내 앱 |
| `kube-system` | 쿠버네티스 자체 부품 (CoreDNS, kube-proxy 등) |
| `monitoring`, `argocd` 등 | 관리 도구들 (관례) |

```bash
kubectl get pods -A              # 모든 네임스페이스
kubectl get pods -n kube-system  # 특정 네임스페이스
```

### 클러스터 안과 밖의 경계 — 실측

노트북에서 직접 시도한 결과다.

```
노트북 → http://web             실패 (curl 종료코드 28 = 시간 초과)
노트북 → http://10.96.217.194   실패 (curl 종료코드 7 = 연결 불가)
노트북 → nslookup web           127.0.53.53 (엉뚱한 주소)
```

이름도 안 풀리고 ClusterIP로 직접 찔러도 안 된다. 노트북은 CoreDNS를 보지 않고, ClusterIP는 클러스터 내부에서만 유효한 가짜 주소이기 때문이다.

그래서 클러스터 안에서 확인하려면 **클러스터 안에 있는 무언가**가 요청을 보내야 한다. 그 용도가 일회용 busybox 파드다 → [03-pod.md](03-pod.md)

> ⚠️ 확인 필요: `127.0.53.53`은 DNS 이름 충돌을 알리는 예약 주소로 알고 있으나 근거를 확인하지 않았다.

## 왜 이렇게 설계됐나

**"주소를 설정 파일에 적는 일"을 없애려는 것이다.**

전통적인 방식에서는 앱이 붙을 DB 주소를 설정 파일이나 환경변수에 적는다. 서버가 바뀌면 설정을 고치고 재배포해야 한다.

클러스터 DNS는 그 자리를 **서비스 이름**으로 대체한다. `db`라고만 적어두면 DB 파드가 몇 개든 어디로 옮겨가든 코드도 설정도 그대로다. 파드를 일회용으로 취급하는 설계([03-pod.md](03-pod.md))가 성립하려면 이 조각이 반드시 필요하다.

네임스페이스를 이름에 넣은 것도 같은 이유다. `dev`와 `prod`에 완전히 같은 매니페스트를 배포해도 각자 자기 네임스페이스의 `db`를 보게 된다. **환경별로 설정을 바꿀 필요가 없다.**

## 이 설명이 깨지는 조건

- **`options ndots:5`가 성능에 영향을 준다.** 점(.)이 5개 미만인 이름은 `search` 목록을 먼저 다 시도한다. `google.com` 같은 외부 도메인을 조회하면 실패 조회가 여러 번 발생한다. 트래픽이 많으면 문제가 된다
- **CoreDNS가 죽으면 이름 해석이 전부 멈춘다.** 이미 맺어진 연결은 살아 있지만 새 연결은 안 된다. 그래서 기본 2개가 떠 있다
- **파드에도 DNS 이름이 붙을 수 있다.** 다만 일반 디플로이먼트 파드에는 안정적인 이름이 없다. StatefulSet에서만 의미가 있다
- **`kubectl port-forward`는 DNS와 무관하다.** 노트북과 파드 사이에 임시 터널을 뚫는 것이라 이름 해석 과정을 건너뛴다. 임시 디버깅용이지 정식 접속 방법이 아니다

## 근거

- [Kubernetes 공식 문서 — DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- 실측: `kubectl exec web-... -- cat /etc/resolv.conf` (2026-09-07)
- 실측: 노트북에서 `curl`/`nslookup` 실패 확인 (2026-09-07)
- 세션 기록: [logs/day-01.md](../../logs/day-01.md)
