# 쿠버네티스 학습

로컬(kind)에서 시작해 AWS로 넘어가는 것을 목표로 하는 개인 학습 기록.

> **대상 버전**: Kubernetes v1.37.0 (kind), macOS + Docker
> **현재 위치**: 1단계(로컬 kind) **Day 2 완료 / 다음 Day 3** — 전체 계획은 [docs/roadmap.md](docs/roadmap.md)
> **목표**: 사내 클러스터 구축·운영 + 디버깅, 그리고 CKA

```
[1단계] 로컬 (kind)          ← 현재 위치
   ↓  쿠버네티스 개념과 동작 이해
[2단계] AWS EC2 + kubeadm
   ↓  실제 인프라, 설치 과정, 네트워크
[3단계] 필요해지면 EKS / RKE2
```

---

## 구조

```
k8s/
├── CLAUDE.md             # 학습 진행 규칙. 매 세션 자동으로 읽힌다
├── .claude/skills/quiz/  # /quiz 복습 명령
├── kind-config.yml       # 클러스터 정의 (노드 3대)
├── docs/
│   ├── roadmap.md        # 전체 학습 계획 ← 며칠차에 뭘 하는가
│   ├── concepts/         # 개념별 정리 노트 ← 무엇을 이해했는가
│   ├── handoff.md        # 세션 인수인계용
│   └── log.md            # (구) 1일차 원본 기록. concepts/ 와 logs/ 로 분리됨
├── logs/                 # 날짜별 세션 기록 ← 무엇을 예측하고 무엇이 틀렸는가
└── manifests/            # 실습용 YAML ← 손으로 다시 돌릴 수 있는가
```

**복습**: `/quiz` 를 입력하면 아래 "복습 대기"와 "검증하지 않은 채 남은 것"에서 항목을 골라
정답을 보여주지 않고 다시 질문한다. 통과하면 체크된다.

**`docs/concepts/`와 `logs/`의 역할이 다르다.** 개념 노트는 정리된 결론이고, 세션 기록은 그 결론에 도달한 과정(틀린 예측 포함)이다. 틀린 기록을 지우지 않는다.

---

## 개념 노트

| # | 노트 | 한 줄 |
| --- | --- | --- |
| 01 | [로컬 학습 환경 — kind](docs/concepts/01-kind-local-env.md) | 도커 컨테이너 하나를 노드 한 대처럼 쓴다 |
| 02 | [클러스터와 노드, 내부 구조](docs/concepts/02-cluster-node-architecture.md) | 모든 통신은 API 서버를 거치고, 컨트롤 루프가 차이를 메운다 |
| 03 | [파드](docs/concepts/03-pod.md) | 언제든 죽고 이름도 IP도 바뀐다. 그래서 나머지 개념이 파생된다 |
| 04 | [디플로이먼트와 레플리카셋](docs/concepts/04-deployment-replicaset.md) | "몇 개 유지"와 "어떤 버전으로 교체"를 계층으로 분리했다 |
| 05 | [라벨과 selector](docs/concepts/05-label-selector.md) | 오브젝트끼리 연결되는 유일한 방식. 이름으로 가리키지 않는다 |
| 06 | [서비스](docs/concepts/06-service.md) | 바뀌지 않는 입구. 프로세스가 아니라 노드마다 복제된 규칙이다 |
| 07 | [클러스터 DNS와 네임스페이스](docs/concepts/07-cluster-dns.md) | 이름 해석(1단계)과 라벨 매칭(2단계)은 다른 단계다 |
| 08 | [requests / limits](docs/concepts/08-resources-requests-limits.md) | 스케줄러는 실제 사용량이 아니라 선언된 요청량만 본다 |
| 09 | [진단과 삽질 기록](docs/concepts/09-troubleshooting.md) | 원인을 찾기 전에 어느 단계에서 끊겼는지부터 좁힌다 |
| 10 | [kube-proxy와 iptables](docs/concepts/10-kube-proxy-iptables.md) | 판단은 로컬에서, 규칙은 전역에서. 중앙 프록시가 없다 |

각 노트는 **"왜 이렇게 설계됐나"**와 **"이 설명이 깨지는 조건"**을 반드시 포함한다. 이 둘이 비어 있으면 아직 이해한 게 아니다.

## 세션 기록

| 날짜 | 기록 | 다룬 것 |
| --- | --- | --- |
| 2026-09-07 | [1일차](logs/day-01.md) | **전반부** 클러스터 생성, 파드/노드 죽이기, 스케일, `Pending` 만들기<br>**후반부** 서비스, 라벨/selector, 엔드포인트슬라이스, 클러스터 DNS, 부하 분산 측정 |
| 2026-09-08 | [2일차](logs/day-02.md) | 라벨 떼어내기(고아 파드), 서비스 타입 3종, `externalTrafficPolicy`, kube-proxy/iptables 내부, 규칙 생성 시점 |

## 실습 매니페스트

[manifests/README.md](manifests/README.md) — 명령어로 했던 것을 YAML로 옮긴 것. 처음부터 재현하는 순서 포함.

---

## 아직 모르는 것 / 다음에 할 것

**바로 다음**

- [ ] **Day 3 — ConfigMap / Secret**
- [ ] `kind-config.yml` 에 `extraPortMappings` 넣고 재생성 → NodePort 를 노트북에서 실제 접속 (Day 10 인그레스 때 함께)

**전체 계획** → [docs/roadmap.md](docs/roadmap.md)

하루 2시간 × 41일. 1단계 로컬(kind) 14일 → 2단계 AWS 10일 → 3단계 운영 7일 → 4단계 CKA 대비 10일.
날짜별 주제와 진행 체크는 로드맵 파일에서 관리한다.

**검증하지 않은 채 남은 것** (노트에 `⚠️ 확인 필요`로 표시돼 있음)

- [ ] 컨테이너 재시작 시 파드 IP가 유지되는가 — [03-pod.md](docs/concepts/03-pod.md)
- [ ] 서비스 selector만 `LabelSelector`가 아닌 이유 — [05-label-selector.md](docs/concepts/05-label-selector.md)
- [ ] 노드 `NotReady` 전환이 설정값 50초보다 빨리 관측된 이유 — [09-troubleshooting.md](docs/concepts/09-troubleshooting.md)
- [ ] `127.0.53.53`의 정체 — [07-cluster-dns.md](docs/concepts/07-cluster-dns.md)
- [ ] `ipvs` / `nftables` 모드의 성능 특성 — [10-kube-proxy-iptables.md](docs/concepts/10-kube-proxy-iptables.md)
- [ ] control-plane 이 실제로 로드밸런서 대상에서 빠지는지 (kind 에는 LB가 없어 미확인) — [06-service.md](docs/concepts/06-service.md)

**복습 대기** (오답 노트)

`logs/day-01.md`
- [ ] `localhost:8080`의 정체를 확인하지 않고 단정한 것
- [ ] DNS 해석과 라벨 selector를 같은 단계로 본 것

`logs/day-02.md`
- [ ] NodePort 는 그 노드의 파드에게만 보낸다고 생각한 것
- [ ] 재분배가 "클러스터 차원"에서 일어난다고 생각한 것
- [ ] `healthCheckNodePort` 와 `externalTrafficPolicy` 의 인과를 뒤집은 것

---

## 클러스터 재생성

```bash
kind delete cluster --name study
kind create cluster --name study --config kind-config.yml
kubectl get nodes
```

30초면 다시 만든다. **망가뜨리는 것을 두려워하지 않는다.** 로컬로 시작한 이유가 이것이다.

---

> 이 저장소의 노트 초안은 사용자 요청으로 Claude가 작성했다. 사실관계는 실측·공식 문서로 검증했으나 **설명의 관점과 구성은 검토가 필요하다.** 읽으면서 자기 언어로 고쳐 쓰는 것이 목적이다.
