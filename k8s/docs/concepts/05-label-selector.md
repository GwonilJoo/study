# 라벨과 selector

> 출발점: 서비스는 어떤 파드가 자기 뒤에 있는지 어떻게 알아내는가 (2026-09-07)
> 대상: Kubernetes v1.37.0

## 한 줄 요약

쿠버네티스에서 오브젝트끼리 연결되는 **유일한 방식**이 라벨이다. 이름이나 IP로 가리키지 않는다. 이름도 IP도 계속 바뀌기 때문이다.

## 내용

### 라벨은 그냥 키:값이다

```bash
kubectl get pods --show-labels
```

```
NAME                   LABELS
web-5fc9f4bf66-l7vsv   app=web,pod-template-hash=5fc9f4bf66
web-5fc9f4bf66-m9wb5   app=web,pod-template-hash=5fc9f4bf66
web-5fc9f4bf66-r9tlv   app=web,pod-template-hash=5fc9f4bf66
```

`app=web`은 적은 적이 없어도 붙어 있다. `kubectl create deployment web`이 디플로이먼트 이름을 따서 자동으로 넣은 것이다.

### 두 라벨의 역할이 다르다

| 라벨 | 목적 | 누가 쓰나 |
| --- | --- | --- |
| `app=web` | 버전과 상관없이 **전부 묶으려고** | 서비스 |
| `pod-template-hash` | 옛 버전과 새 버전을 **구분하려고** | 레플리카셋 |

**서비스는 일부러 `pod-template-hash`를 보지 않는다.** 롤링 업데이트 중에도 옛 파드든 새 파드든 뜬 것 아무한테나 트래픽을 보내야 접속이 안 끊기기 때문이다. 해시까지 보게 하면 배포하는 순간 서비스가 텅 빈다.

### selector 문법이 두 가지다

이 클러스터의 API 서버에 직접 물어 확인한 내용이다 (`kubectl explain`).

| | 타입 | 쓰는 법 |
| --- | --- | --- |
| **서비스**의 selector | `map[string]string` | `selector: {app: web}` — **평평하게** |
| **디플로이먼트**의 selector | `LabelSelector` | `selector.matchLabels: {app: web}` — **한 단계 더** |

```yaml
# 서비스
spec:
  selector:
    app: web

# 디플로이먼트
spec:
  selector:
    matchLabels:
      app: web
```

**서비스에 `matchLabels`를 적으면 에러가 난다.** 처음 YAML을 쓸 때 가장 자주 틀리는 지점이다.

디플로이먼트 쪽은 `matchExpressions`도 쓸 수 있어서 "app이 web 또는 api인 것" 같은 조건이 가능하다. 서비스는 **정확히 일치하는 것만** 고른다.

> ⚠️ 확인 필요: 왜 서비스 쪽만 단순한 형태인지(API 역사와 호환성 문제로 추정)는 근거를 확인하지 않았다.

### 라벨로 조회하기

```bash
kubectl get pods -l app=web
kubectl get endpointslice -l kubernetes.io/service-name=web
kubectl label pod <파드> app=broken --overwrite
```

## 왜 이렇게 설계됐나

**"누가 누구를 가리키는가"를 이름이 아니라 조건으로 표현했다.**

이름으로 가리키면 대상이 바뀔 때마다 가리키는 쪽을 고쳐야 한다. 파드 이름은 매번 바뀌므로 서비스는 배포 때마다 수정돼야 한다. 성립하지 않는다.

라벨은 **가리키는 쪽이 대상을 모른 채로 연결을 유지한다.** 서비스는 "app=web인 것들"이라고만 선언하고, 그 조건에 맞는 파드가 늘든 줄든 바뀌든 신경 쓰지 않는다. 파드도 자기가 어느 서비스에 속하는지 모른다. **양쪽 다 상대를 모른다.**

이 느슨함이 확장 지점이 된다. 새로운 종류의 오브젝트가 추가돼도 기존 오브젝트를 고칠 필요가 없다. 라벨만 맞추면 붙는다.

## 이 설명이 깨지는 조건

- **라벨을 바꾸면 두 가지가 동시에 일어난다.** 실측으로 확인했다 (2026-09-08).

  파드 하나의 `app=web` 을 `app=broken` 으로 바꾸자:

  1. **서비스 엔드포인트에서 빠졌다.** `10.244.1.5` 가 명단에서 사라짐
  2. **레플리카셋의 관리 대상에서도 빠졌다.** 개수가 모자란 것으로 보고 새 파드를 만듦 → **파드 4개, 엔드포인트 3개**

  ```
  l7vsv 의 ownerReferences:  (비어 있음)          ← 레플리카셋이 놓아줬다(release)
  llqk7 의 ownerReferences:  ReplicaSet/web-…     ← 새 파드는 소유됨
  ```

  **레플리카셋은 고아의 존재를 모른다.** 파드는 4개인데 `replicas: 3 / ready: 3` 으로 만족한 상태다.
  → `kubectl get rs` 가 정상이라고 파드가 3개라는 뜻이 아니다.

  **고아는 죽지 않고 계속 서비스한다.** 트래픽만 안 온다. 그리고 소유자가 없으므로
  **디플로이먼트를 지워도 살아남는다** (이것도 확인함).

  이건 사고가 아니라 **의도된 디버깅 기법**이다. 문제 있는 파드를 트래픽에서 떼어내되
  죽이지 않고 들여다볼 수 있다. 죽이면 증거가 사라진다.

  ```bash
  kubectl label pod <문제파드> app=debug --overwrite
  ```
- **selector는 겹쳐도 막지 않는다.** 서로 다른 두 서비스가 같은 파드를 가리킬 수 있다. 의도한 것이면 유용하지만, 오타로 겹치면 원인을 찾기 어렵다
- **라벨 오타는 에러를 내지 않는다.** `app: web`을 `app: wev`로 적어도 오브젝트는 정상 생성된다. 단지 아무것도 안 골라질 뿐이고, 증상은 "접속이 안 됨"으로만 나타난다 → [09-troubleshooting.md](09-troubleshooting.md)

## 근거

- [Kubernetes 공식 문서 — Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
- 실측: `kubectl explain service.spec.selector`, `kubectl explain deployment.spec.selector` (v1.37.0, 2026-09-07)
- 세션 기록: [logs/day-01.md](../../logs/day-01.md)
