# 실습 매니페스트

1일차에 **명령어로 했던 것을 YAML 파일로 옮긴 것.** 명령어와 결과물은 같지만, 파일로 두면 뭘 배포했는지 남고 깃으로 이력을 볼 수 있다.

> 검증: 전부 `kubectl apply --dry-run=server`로 v1.37.0 API 서버에 통과 확인 (2026-09-07)

## 파일 ↔ 명령어 대응

| 파일 | 대응하는 명령어 | 관련 개념 |
| --- | --- | --- |
| `01-web-deployment.yml` | `kubectl create deployment web --image=nginx --replicas=3` | [04-deployment-replicaset](../docs/concepts/04-deployment-replicaset.md) |
| `02-web-service.yml` | `kubectl expose deployment web --port=80` | [06-service](../docs/concepts/06-service.md) |
| `03-heavy-pending.yml` | (1일차 `heavy.yaml`) | [08-resources](../docs/concepts/08-resources-requests-limits.md) |
| `04-loadtest-pod.yml` | `kubectl run loadtest --image=busybox --restart=Never -- sh -c '...'` | [06-service](../docs/concepts/06-service.md) |
| `05-web-nodeport.yml` | `kubectl expose deployment web --name=web-np --port=80 --type=NodePort` | [06-service](../docs/concepts/06-service.md) |
| `06-web-loadbalancer.yml` | `kubectl expose deployment web --name=web-lb --port=80 --type=LoadBalancer` | [06-service](../docs/concepts/06-service.md) |

## 처음부터 재현하기

```bash
# 0. 클러스터 (없거나 망가졌을 때만)
kind create cluster --name study --config ../kind-config.yml
kubectl get nodes

# 1. 앱 배포
kubectl apply -f 01-web-deployment.yml
kubectl get pods -o wide --show-labels

# 2. 서비스 생성
kubectl apply -f 02-web-service.yml
kubectl describe svc web              # Endpoints 줄 확인

# 3. 이름으로 접속 (클러스터 안에서)
kubectl run test --image=busybox:1.38.0 -it --rm --restart=Never -- wget -qO- http://web

# 4. 부하 분산 관찰
for p in $(kubectl get pods -l app=web -o name); do
  kubectl exec $p -- sh -c 'echo $HOSTNAME > /usr/share/nginx/html/index.html'
done
kubectl apply -f 04-loadtest-pod.yml
kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/loadtest --timeout=120s
kubectl logs loadtest | sort | uniq -c
kubectl delete -f 04-loadtest-pod.yml

# 5. 서비스 타입 3종 비교
kubectl apply -f 05-web-nodeport.yml
kubectl apply -f 06-web-loadbalancer.yml
kubectl get svc          # LoadBalancer 의 EXTERNAL-IP 는 영원히 <pending>

#    파드가 0개인 노드로 들어가도 다른 노드 파드로 넘어가는지
for p in $(kubectl get pods -l app=web -o name); do
  kubectl exec $p -- sh -c 'echo $HOSTNAME > /usr/share/nginx/html/index.html'
done
docker exec study-control-plane sh -c \
  'for i in $(seq 1 30); do curl -s localhost:30080; done' | sort | uniq -c

kubectl delete -f 06-web-loadbalancer.yml -f 05-web-nodeport.yml

# 6. 자원 부족으로 Pending 만들어보기
kubectl apply -f 03-heavy-pending.yml
kubectl get pods
kubectl describe pod -l app=heavy | grep -E "^Node:|PodScheduled"
kubectl delete -f 03-heavy-pending.yml
```

## 정리

```bash
kubectl delete -f 06-web-loadbalancer.yml --ignore-not-found
kubectl delete -f 05-web-nodeport.yml --ignore-not-found
kubectl delete -f 04-loadtest-pod.yml --ignore-not-found
kubectl delete -f 03-heavy-pending.yml --ignore-not-found
kubectl delete -f 02-web-service.yml --ignore-not-found
kubectl delete -f 01-web-deployment.yml --ignore-not-found
```

전부 지우려면 클러스터째 버리는 쪽이 빠르다. `kind delete cluster --name study`

## 알아둘 것

### 이미지 버전을 고정했다

명령어로 만들 때는 `nginx`(= `nginx:latest`)가 쓰였지만, 파일에는 실제로 돌던 버전을 박아뒀다.

| 이미지 | 고정한 태그 |
| --- | --- |
| nginx | `nginx:1.31.5` |
| busybox | `busybox:1.38.0` |

`latest`는 언제 바뀔지 모른다. **몇 달 뒤에 이 파일을 다시 돌렸을 때 같은 결과가 나와야 실험 기록으로서 의미가 있다.**

### 기존 오브젝트에 apply 하면 경고가 뜬다

이미 `kubectl create`/`kubectl expose`로 만들어둔 상태에서 `apply`하면 이 경고가 나온다.

```
Warning: resource deployments/web is missing the
kubectl.kubernetes.io/last-applied-configuration annotation which is required
by kubectl apply. ... The missing annotation will be patched automatically.
```

**오류가 아니다.** 명령형으로 만든 오브젝트에는 "직전에 적용한 내용"이 기록돼 있지 않아서, apply가 무엇을 지워야 할지 판단할 근거가 없다는 뜻이다. 자동으로 채워지고 다음부터는 안 뜬다.

명령형과 선언형을 섞으면 이런 마찰이 생긴다. **한 오브젝트는 한 방식으로만 다루는 편이 낫다.**

### `01`을 적용하면 롤링 업데이트가 일어난다

현재 떠 있는 파드는 `nginx:latest`인데 파일은 `nginx:1.31.5`다. 이미지 문자열이 다르므로 파드 템플릿이 바뀐 것으로 판정되고, `pod-template-hash`가 바뀌면서 파드가 전부 교체된다.

교체되면 4번 실습에서 넣었던 `index.html`도 사라진다. 순서대로 하면 문제없다.

### `--dry-run=server`로 먼저 확인할 수 있다

실제로 적용하지 않고 API 서버에 검증만 시킨다. YAML 문법과 스키마 오류를 미리 잡는다.

```bash
kubectl apply --dry-run=server -f 01-web-deployment.yml
```
