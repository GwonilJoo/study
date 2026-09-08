# requests / limits 와 스케줄링

> 출발점: 자원을 과하게 요청하면 어떻게 되는지 일부러 만들어봄 (2026-09-07)
> 대상: Kubernetes v1.37.0

## 한 줄 요약

**스케줄러는 실제 사용량이 아니라 `requests`에 적힌 요청량만 본다.** 그리고 자원이 부족하면 억지로 밀어넣지 않고 기다린다.

## 내용

### 둘의 차이

| | 의미 | 초과하면 |
| --- | --- | --- |
| **requests** | "최소 이만큼 필요" — 스케줄러가 보는 값 | (초과 개념 없음) |
| **limits** | "이 이상 못 씀" | 메모리: 강제 종료 / CPU: 속도 제한 |

**메모리와 CPU의 성격이 다르다.** CPU는 상한을 넘으면 느려질 뿐이지만, **메모리는 넘으면 죽는다.** 이미 쓴 메모리를 회수할 방법이 없기 때문이다.

### 스케줄러는 요청량으로만 계산한다

노드 여유가 3GB이고 파드마다 1GB를 요청하면 3개까지만 들어간다. **4번째는 실제 메모리가 텅 비어 있어도 `Pending`이다.**

반대로 requests를 적게 적고 실제로 많이 쓰면, 스케줄러는 자리가 있다고 판단해 계속 밀어넣는다. 노드가 터진다.

### 실험: 자원 부족 만들기

`manifests/03-heavy-pending.yml`

```yaml
resources:
  requests:
    memory: 100Gi
```

```bash
kubectl apply -f manifests/03-heavy-pending.yml
kubectl get pods    # 3개 전부 Pending
```

100GB를 줄 수 있는 노드가 없으니 전부 `Pending`이다. **쿠버네티스는 자리가 생길 때까지 기다린다.** 노드를 늘리거나 요구량을 줄이면 몇 초 안에 배치된다.

### QoS Class

`kubectl describe pod` 출력에 나온다. 노드 메모리가 부족할 때 **누구부터 죽일지**의 순서다.

| Class | 조건 | 위험도 |
| --- | --- | --- |
| `Guaranteed` | requests = limits | 가장 안전 |
| `Burstable` | requests만 있음 | 중간 |
| `BestEffort` | 둘 다 없음 | **가장 먼저 죽는다** |

**아무것도 안 적는 것이 가장 위험하다.** "자원이 필요 없다"로 간주돼 무제한으로 밀려 들어가고, 노드가 터질 때 1순위로 죽는다.

### 두 실패 모드는 원인이 정반대다

| 상태 | 원인 | 성격 |
| --- | --- | --- |
| `Pending` | 요청이 **과해서** 자리가 없음 | 얌전한 실패 |
| `OOMKilled` | 상한이 **부족해서** 죽음 | 난폭한 실패 |

이 두 단어를 헷갈리면 정반대 방향으로 고치게 된다.

## 왜 이렇게 설계됐나

**"실제 사용량"으로 스케줄링하면 배치 결정을 신뢰할 수 없다.**

실제 사용량은 시시각각 변한다. 배치하는 순간 한가하던 파드가 1분 뒤 메모리를 다 쓸 수 있다. 그 값을 기준으로 결정하면, 결정이 내려진 직후에 이미 틀린 결정이 된다.

`requests`는 **개발자가 미리 선언한 약속**이다. 변하지 않으므로 스케줄러가 단순한 뺄셈으로 결정할 수 있고, 결정이 나중에 뒤집히지 않는다. 대신 **약속을 정확히 적는 책임이 사람에게 넘어온다.** 이것이 실무에서 requests/limits가 자주 문제를 일으키는 이유다.

`Pending`으로 기다리게 만든 것도 같은 판단이다. 억지로 밀어넣어 노드 전체를 터뜨리는 것보다, 파드 하나가 안 뜨는 편이 낫다. **부분적 실패를 전면적 장애로 키우지 않는다.**

## 이 설명이 깨지는 조건

- **`kubectl set resources`로 자원을 추가해도 기존 파드는 그대로다.** 새로 만들어지는 파드부터 적용된다. 1일차에 명령으로 자원을 추가했는데 전부 `Running`이었던 이유. 처음부터 YAML에 넣어야 명확하다
- **CPU limits는 논쟁이 있다.** 상한에 걸리면 실제로 쓸 CPU가 남아 있어도 강제로 느려진다. 지연에 민감한 앱에서는 CPU limits를 아예 안 거는 쪽이 낫다는 주장이 있다
- **`Pending`이 항상 자원 문제는 아니다.** 노드 셀렉터, taint, 볼륨 문제로도 `Pending`이 된다. 구분법은 [09-troubleshooting.md](09-troubleshooting.md)
- **kind에서는 노드 자원이 곧 노트북 자원이다.** 노드 3대로 보이지만 실제 여유는 노트북 한 대분이다

## 근거

- [Kubernetes 공식 문서 — Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Kubernetes 공식 문서 — Pod Quality of Service Classes](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/)
- 실측: `manifests/03-heavy-pending.yml` 적용 → 파드 3개 전부 `Pending`, `PodScheduled: False` (2026-09-07)
- 세션 기록: [logs/day-01.md](../../logs/day-01.md)
