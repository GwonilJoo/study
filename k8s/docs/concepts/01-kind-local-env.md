# 로컬 학습 환경 — kind

> 출발점: AWS에서 바로 시작하면 쿠버네티스 문제인지 AWS 네트워크 문제인지 구분이 안 돼서 진도가 안 난다 (2026-09-07)
> 대상: kind + Kubernetes v1.37.0, macOS + Docker

## 한 줄 요약

kind는 **도커 컨테이너 하나를 노드 한 대처럼 쓰는** 도구다. 노트북 한 대 위에 진짜 쿠버네티스 클러스터를 30초 만에 만들고 부순다.

## 내용

### 도구 세 개의 역할

| 도구 | 역할 |
| --- | --- |
| Docker | 노드가 될 컨테이너를 돌린다 |
| kind | 그 컨테이너들로 클러스터를 만든다 (Kubernetes IN Docker) |
| kubectl | 만들어진 클러스터에 명령을 내린다 |

```
kubectl  ──명령──▶  클러스터
                      ▲ 만듦
                    kind
                      ▲ 컨테이너 제공
                    Docker
```

kind는 `create`와 `delete`만 쓰고, 그 뒤로는 계속 kubectl만 쓴다.

### 설정 파일

`kind-config.yml`

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

- 최상단 `kind:`는 도구 이름이 아니라 "종류"라는 뜻의 필드다. 도구 kind와 이름이 겹칠 뿐이다
- `nodes:` 아래 `-` 하나가 노드 하나. **줄 수가 곧 노드 개수**
- 설정 파일 없이 `kind create cluster`만 하면 노드 1대짜리가 생긴다

YAML은 들여쓰기가 문법이다. 탭 문자는 에러다.

### 생성과 재생성

```bash
kind create cluster --name study --config kind-config.yml
kind delete cluster --name study
kind get clusters
docker ps --format '{{.Names}}'   # 노드 = 컨테이너인 것을 눈으로 확인
```

생성 중 출력되는 단계가 곧 쿠버네티스 설치 과정이다.

```
✓ Ensuring node image
✓ Preparing nodes
✓ Writing configuration
✓ Starting control-plane
✓ Installing CNI          ← 없으면 노드가 NotReady
✓ Installing StorageClass
✓ Joining worker nodes
```

AWS에서 손으로 해야 할 것(스왑 끄기, 커널 설정, 방화벽, CNI 설치)을 kind가 전부 대신 한다.

**CNI**: 파드끼리 통신하게 해주는 네트워크 부품. 쿠버네티스 본체에는 없어서 따로 설치해야 하고, 없으면 노드가 `Ready`가 되지 않는다.

### 망가뜨려도 되는 이유

30초면 다시 만든다. 이게 로컬로 시작한 이유다. 실험은 과감하게 한다.

## 왜 이렇게 설계됐나

쿠버네티스 노드가 되기 위한 최소 조건은 "kubelet과 컨테이너 런타임이 도는 리눅스 환경"이다. **가상머신이어야 할 이유가 없다.** 컨테이너도 그 조건을 만족한다.

그래서 kind는 노드마다 VM을 띄우는 대신 컨테이너를 띄운다. VM 부팅에 걸릴 시간이 없어지고, 노드 3대짜리 클러스터가 메모리 몇 GB로 끝난다. "노드 = 물리 서버"라는 통념을 버린 것이 이 도구의 핵심 아이디어다.

## 이 설명이 깨지는 조건

- **노드 3대라도 물리적으로는 노트북 한 대다.** 노드 장애 실습은 되지만, 실제 이중화의 효과는 없다
- **`type: LoadBalancer` 서비스가 동작하지 않는다.** 영원히 `<pending>`에 걸린다. 클라우드의 `cloud-controller-manager`가 없어서다 → [06-service.md](06-service.md)
- **진짜 네트워크가 아니다.** 방화벽·서브넷·실제 IP를 다룰 일이 없다. 이 부분은 AWS 단계에서만 배울 수 있다
- **워커 노드는 바깥으로 열린 포트가 하나도 없다.** 확인한 값:
  ```
  study-control-plane   127.0.0.1:62562->6443/tcp   ← kubectl이 쓰는 통로
  study-worker          (매핑 없음)
  study-worker2         (매핑 없음)
  ```
  NodePort로 외부 접속을 하려면 `extraPortMappings`를 넣고 클러스터를 재생성해야 한다

그럼에도 **kind가 만드는 쿠버네티스는 진짜다.** 내부적으로 kubeadm을 쓰고, 컨트롤 플레인 구성요소가 그대로 파드로 뜬다. 여기서 배운 kubectl·YAML·동작 원리는 AWS나 사내망 클러스터에서 그대로 통한다. 프로덕션에 안 쓸 뿐이다.

## 근거

- [kind — Quick Start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- 실측: `docker ps --format '{{.Names}}\t{{.Ports}}'` (2026-09-07) — 워커 노드 포트 매핑 없음 확인
- 세션 기록: [logs/day-01.md](../../logs/day-01.md)
