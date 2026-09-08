# 디플로이먼트와 레플리카셋

> 출발점: 파드는 언제든 죽는데 서비스는 어떻게 계속 떠 있나 (2026-09-07)
> 대상: Kubernetes v1.37.0

## 한 줄 요약

디플로이먼트는 **"이 프로그램을 몇 개 돌려줘"라는 주문서**다. 파드를 직접 만드는 게 아니라 주문을 등록하는 것이고, 컨트롤 루프가 그 주문에 맞춰 파드를 만들고 유지한다.

## 내용

### 3단 구조

```
디플로이먼트   "nginx를 3개, 이 버전으로"      ← 사람이 만든다
     │
레플리카셋     "이 템플릿의 파드를 3개 유지"    ← 디플로이먼트가 만든다
     │
   파드 × 3                                   ← 레플리카셋이 만든다
```

`kubectl get deployments`에는 디플로이먼트만 보이지만, 그 아래에 레플리카셋이 항상 끼어 있다. 파드 이름 가운데의 `5fc9f4bf66`이 그 레플리카셋을 가리킨다.

### 만드는 두 가지 방법

```bash
# 명령형
kubectl create deployment web --image=nginx --replicas=3

# 선언형 (실무 정식 방법)
kubectl apply -f manifests/01-web-deployment.yml
```

**둘의 결과물은 완전히 같다.** kubectl이 명령을 받아 YAML을 만들어 API 서버에 보내기 때문이다. YAML은 "저장 형식"이지 "만드는 방법"이 아니다.

명령으로 만든 것도 언제든 YAML로 되꺼낼 수 있다.

```bash
kubectl get deployment web -o yaml
```

도커에서 `docker run -d --name web nginx` 한 줄만 쳐도 `docker inspect web`에 수십 개 설정값이 나오는 것과 같다. 안 적었을 뿐 값은 채워져 있다.

그래도 **파일로 관리하는 쪽이 낫다.** 뭘 배포했는지 남고, 깃으로 이력을 볼 수 있고, 리뷰가 된다.

### 자동으로 채워지는 값

`kubectl create deployment web`은 적지 않은 값을 채워 넣는다. 그중 하나가 라벨이다.

```yaml
spec:
  selector:
    matchLabels:
      app: web        # ← 디플로이먼트 이름에서 자동 생성
  template:
    metadata:
      labels:
        app: web      # ← 같은 값이 파드에도
```

### 개수 조절

```bash
kubectl scale deployment web --replicas=6
kubectl scale deployment web --replicas=2
```

명령 한 줄, 몇 초. 트래픽이 몰릴 때 늘리는 동작이 이것이다.

### pod-template-hash와 롤링 업데이트

이미지를 새 버전으로 바꾸면 파드를 한꺼번에 갈아치우지 않는다. **새 파드를 띄우고 → 뜨면 옛 파드를 죽이고 → 반복**한다. 이것이 **롤링 업데이트**다.

교체 도중에는 옛 버전과 새 버전 파드가 **동시에 존재**한다. 그래서 레플리카셋도 두 개가 공존한다.

여기서 `pod-template-hash`가 필요해진다.

```
레플리카셋(구) selector:  app=web + pod-template-hash=5fc9f4bf66
레플리카셋(신) selector:  app=web + pod-template-hash=7a1c2d3e4f
```

이 해시가 없으면 두 레플리카셋의 selector가 똑같아져서, **서로 상대방의 파드를 자기 것으로 착각한다.** 각자 "3개 유지"를 시도하면서 남의 파드를 지우는 사고가 난다.

해시는 파드 템플릿의 내용에서 계산된다. 이미지 태그가 바뀌면 해시도 바뀐다.

## 왜 이렇게 설계됐나

**"몇 개 유지"와 "어떤 버전으로 교체"는 다른 문제이고, 그래서 계층을 나눴다.**

레플리카셋은 오직 개수만 책임진다 — 자기 selector에 맞는 파드가 N개인지 세고 모자라면 만든다. 버전이라는 개념 자체가 없다.

디플로이먼트는 그 위에서 레플리카셋을 두 개 굴린다. 새 레플리카셋의 replicas를 올리고 옛 레플리카셋의 replicas를 내리는 것만으로 무중단 배포가 된다. 롤백은 그 반대로 하면 된다.

**개수 유지 로직을 배포 로직과 섞지 않았기 때문에 둘 다 단순해졌다.** 그래서 레플리카셋을 직접 만질 일이 없다.

## 이 설명이 깨지는 조건

- **레플리카셋을 직접 만들 수는 있지만 하지 않는다.** 롤링 업데이트를 잃는다
- **`kubectl scale`로 바꾼 값은 YAML에 반영되지 않는다.** 나중에 `kubectl apply -f`를 하면 파일의 replicas로 되돌아간다. 명령형과 선언형을 섞으면 이런 충돌이 난다
- **이미 떠 있는 파드의 설정은 디플로이먼트를 고쳐도 즉시 바뀌지 않는다.** 새 파드부터 적용된다. 1일차에 `kubectl set resources`로 자원을 추가했을 때 기존 파드가 전부 `Running`으로 남아 있던 이유다
- **파드 IP가 유지되지 않듯, 노드 배치도 유지되지 않는다.** 노드를 죽였다 살려도 파드는 원래 자리로 돌아오지 않는다. 이미 다른 곳에서 잘 돌고 있으므로 옮길 이유가 없다

## 근거

- [Kubernetes 공식 문서 — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes 공식 문서 — ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- 실측: `kubectl get deployment web -o yaml` — 명령으로 만든 디플로이먼트에 `app: web` 자동 생성 확인 (2026-09-07)
- 세션 기록: [logs/day-01.md](../../logs/day-01.md)
