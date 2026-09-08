# 진단과 삽질 기록

> 출발점: 실습 중 실제로 막혔던 지점들 (2026-09-07)
> 대상: Kubernetes v1.37.0

## 한 줄 요약

증상이 같아도 원인은 여러 가지다. **어느 단계에서 끊겼는지부터 좁히고 나서** 원인을 찾는다.

## 내용

### `Pending` 진단 순서

```bash
kubectl describe pod <파드이름>
```

1. **`Node:` 칸이 비어 있나?** → 스케줄링 실패. 자리가 없는 것
2. **`Node:`에 이름이 있는데 `Pending`인가?** → 이미 배치는 됐다. 이미지를 받는 중이거나 볼륨 문제
3. **Events 확인** → 구체적 이유

1번과 2번은 완전히 다른 상황이다. **1번은 자원 문제, 2번은 이미지·볼륨 문제.** 여기서 갈라놓지 않으면 엉뚱한 곳을 판다.

실제로 본 출력:

```
Node:             <none>          ← 배정된 노드 없음 = 스케줄링 실패
Status:           Pending
Requests:
  memory:     100Gi
Conditions:
  PodScheduled   False
Controlled By:    ReplicaSet/heavy-77bbb8d8b8
QoS Class:        Burstable
```

### 서비스가 안 될 때

```bash
kubectl describe svc web
```

**`Endpoints:` 줄부터 본다.**

| 증상 | 원인 | 다음 확인 |
| --- | --- | --- |
| `Endpoints:` 가 비어 있음 | selector가 파드를 못 찾음 | `kubectl get pods --show-labels`로 라벨 오타 확인 |
| 엔드포인트는 있는데 접속 실패 | 포트 불일치 또는 파드 자체 문제 | `targetPort`와 컨테이너 포트 대조 |
| 이름 해석 실패 | DNS 문제, 또는 **클러스터 바깥에서 시도** | [07-cluster-dns.md](07-cluster-dns.md) |

"이름을 못 찾는 것"과 "이름은 찾았는데 뒤에 아무도 없는 것"은 원인도 해결책도 다르다.

### 이벤트 조회 — `describe`보다 낫다

```bash
kubectl get events --sort-by=.lastTimestamp
kubectl get events --field-selector reason=FailedScheduling
kubectl get events --field-selector involvedObject.name=<파드이름>
```

`describe pod -l app=xxx`처럼 **여러 파드를 라벨로 묶어 조회하면 Events가 누락되는 경우가 있다.** 파드 하나를 이름으로 지정하거나 `get events`를 직접 쓴다. 실무에서도 `get events` 쪽을 더 많이 쓴다.

### 노드 장애는 즉시 감지되지 않는다

`docker stop study-worker2` 실습에서 관측한 타임라인:

| 시점 | 상태 |
| --- | --- |
| 0초 | `docker stop` 실행 |
| **약 40초** | 노드가 `NotReady` |
| **5분** | 파드가 `Terminating`, 다른 노드에 새 파드 생성 |

설정된 기본값을 바이너리에서 직접 확인한 결과:

```
kube-controller-manager --node-monitor-grace-period    (default 50s)
kube-apiserver --default-not-ready-toleration-seconds  (default 300)
kube-apiserver --default-unreachable-toleration-seconds (default 300)
```

이 클러스터는 두 값 모두 덮어쓰지 않았다. 5분(300초)은 파드 스펙에도 그대로 박혀 있다.

```json
[{"key":"node.kubernetes.io/not-ready","effect":"NoExecute","tolerationSeconds":300},
 {"key":"node.kubernetes.io/unreachable","effect":"NoExecute","tolerationSeconds":300}]
```

> ⚠️ 확인 필요: 관측된 `NotReady` 전환은 약 40초였는데 설정 기본값은 50초다. 마지막 하트비트 시점부터 시간을 세기 때문에 `docker stop` 시점 기준으로는 더 짧게 보일 수 있다고 이해하고 있으나, 검증하지 않았다.

**5분을 기다리는 이유:** 응답이 없을 때 "죽었다"와 "네트워크만 끊겼다"를 구분할 방법이 없다. 성급히 판단해서 파드를 다른 곳에 또 만들었는데 원래 것까지 살아나면 6개가 되는 사고가 난다.

**노드가 죽었는데 파드가 `Running`으로 보이는 이유:** 파드 상태를 보고하는 것은 그 노드의 kubelet인데 보고가 끊겼다. 컨트롤 플레인에 남은 것은 마지막 보고, 즉 "잘 돌고 있음"이다. **화면의 `Running`은 철 지난 정보다.**

### 무엇이 응답하는지 확인하는 법

브라우저 화면만 보면 착각한다. 실제로 `localhost:8080`이 nginx인 줄 알았으나 전혀 다른 프로세스였다.

```bash
curl -sI http://localhost:8080          # server: 헤더로 정체 확인
lsof -nP -iTCP:8080 -sTCP:LISTEN        # 그 포트를 잡고 있는 프로세스
docker ps --format '{{.Names}}\t{{.Ports}}'   # 컨테이너 포트 매핑
```

```
server: uvicorn     ← nginx라면 nginx라고 적힌다
PID 55980  .../uvicorn app.ui:app --port 8080
```

### 삽질 기록

| 증상 | 원인 |
| --- | --- |
| `docker stop` 했는데 파드가 그대로 | 아직 5분이 안 지났다. **먼저 `kubectl get nodes`가 NotReady로 바뀌는지 확인**해야 한다. 노드가 Ready면 파드는 절대 안 움직인다 |
| `Terminating`에서 안 사라짐 | 지우는 절차를 수행할 kubelet이 죽어 있어서. `docker start`로 노드를 살리거나 `--force --grace-period=0` |
| `set resources`로 자원 추가했는데 다 Running | 기존 파드는 유지된 채 새 파드만 Pending이 된다. 처음부터 YAML에 넣어야 명확 |
| `describe pod -l app=xxx`에 Events가 없음 | 여러 파드 묶어 조회 시 누락. `get events`로 직접 조회 |
| `kubectl run -it`로 30번 요청했는데 6줄만 나옴 | attach 전환 과정에서 출력 유실. **측정에는 `-it`를 쓰지 말고 `kubectl logs`로 읽는다** |
| 브라우저에서 nginx가 보임 | 쿠버네티스와 무관한 다른 프로세스였음. `curl -sI`로 `server:` 헤더 확인 |

### 조회 명령 모음

```bash
kubectl get pods -A                     # 모든 네임스페이스
kubectl get pods -o wide                # 노드 배치 확인
kubectl get pods --show-labels          # 라벨 확인
kubectl get pods -w                     # 변화 실시간 관찰
kubectl logs <파드>                      # 파드가 남긴 출력
kubectl describe pod <파드>
kubectl describe svc <서비스>
kubectl describe node <노드> | grep -A8 "Allocated resources"
kubectl get events --sort-by=.lastTimestamp
kubectl explain <리소스>.<필드>           # API 서버에 직접 스키마 질의
```

**`kubectl explain`은 기억에 의존하지 않고 확인하는 방법이다.** 버전이 정확히 일치하는 답을 준다.

## 왜 이렇게 설계됐나

**감지를 일부러 느리게 만들었다.**

분산 시스템에서 "응답이 없다"는 정보만으로는 상대가 죽었는지 네트워크가 끊겼는지 구분할 수 없다. 원리적으로 불가능하다.

빠르게 판정하면 오판이 늘고, 오판의 대가가 크다. 살아 있는 노드를 죽었다고 보고 파드를 다시 띄우면 같은 파드가 두 벌 돌게 된다. DB에 쓰는 앱이라면 데이터가 깨진다.

그래서 **가용성보다 안전을 택했다.** 5분 동안은 "아마 살아 있을 것"으로 간주한다. 더 빠른 복구가 필요하면 값을 줄일 수 있지만, 오판 위험을 같이 받는 거래다.

## 이 설명이 깨지는 조건

- **타이밍 값은 전부 설정 가능하다.** 위 숫자는 이 클러스터에서 확인한 기본값이고, 관리형 쿠버네티스(EKS 등)는 다르게 설정돼 있을 수 있다. `--help`로 확인한다
- **이벤트는 영구 보존되지 않는다.** 기본 보존 기간이 지나면 사라진다. 사후 분석이 필요하면 로그 수집이 따로 있어야 한다
- **`kubectl logs`는 현재 컨테이너의 로그만 준다.** 재시작된 경우 이전 로그는 `kubectl logs --previous`로 봐야 한다

## 근거

- [kube-controller-manager 레퍼런스](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/)
- 실측: `kube-controller-manager --help`, `kube-apiserver --help`를 클러스터 안에서 직접 실행 (v1.37.0, 2026-09-07)
- 실측: `kubectl get pod -l app=web -o jsonpath='{.items[0].spec.tolerations}'` → `tolerationSeconds: 300` (2026-09-07)
- 세션 기록: [logs/day-01.md](../../logs/day-01.md)
