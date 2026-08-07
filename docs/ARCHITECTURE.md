# ARCHITECTURE — 설계 결정

## 기사 패턴 → 하네스 매핑

Lilian Weng의 "Harness Engineering for Self-Improvement"(2026-07)의 핵심 패턴을 다음과 같이 구현했다.

| 기사 패턴 | 하네스 구현 |
|-----------|------------|
| Pattern 1: Workflow Automation (goal-oriented loop) | 8개 커맨드가 plan→execute→observe→improve 루프를 고정: `/harness:goal → analyze → plan → build → verify → retro` (+ `status`, S-size용 경량 경로 `quick`) |
| Pattern 2: File System as Persistent Memory | 프로젝트마다 `.harness/` 디렉토리. 모든 산출물·상태·로그를 파일로 영속화 → 세션 중단 후에도 복구, 컨텍스트 오염 방지 |
| Pattern 3: Sub-agent & Backend Jobs | orchestrator가 독립 태스크를 역할 에이전트에게 병렬 디스패치. 결과는 채팅이 아닌 파일로 회수 (inspectable parallelism) |
| ACE (Agentic Context Engineering) | `.harness/wiki/` — 지식을 노드(1파일 = 1인사이트 엔티티) 단위로 분해한 **자기 진화 위키**. 모든 에이전트가 증거 발생 즉시 노드를 생성·강화·승격(사람 게이트 없음), INDEX 1줄 훅 + scope 필터 로딩으로 고정 예산 유지, 증분 큐레이션으로 context collapse 방지 |
| Self-Harness (weakness mining → bounded proposal → validation) | harness-improver가 logs/·candidate 노드에서 실패 패턴 마이닝 → 위키 큐레이션(병합/은퇴)은 직접, 프롬프트·게이트 편집안은 사람 승인 후 적용 |
| Reward hacking / 안전 경계 | 평가·권한은 개선 루프 밖에 위치: 승인 게이트·안전 규칙은 편집 불가 표면 |

## 에이전트 로스터 (12종)

### 요청 역할 6종
| 에이전트 | 역할 | 소유 산출물 |
|---------|------|-------------|
| planner | 기획자 (PM) | `.harness/prd.md` |
| analyst | 분석자 | `.harness/analysis.md` |
| architect | 설계자 | `.harness/design.md` (기술) |
| product-designer | 상품설계자 | `.harness/design.md` (UX) |
| backend-dev / frontend-dev / ai-agent-dev | 개발자 (스택별 3종) | 코드 + 테스트 |
| qa | QA | 검증 verdict (logs/) |

### 확장 역할 4종 — 추가 이유
| 에이전트 | 추가 이유 |
|---------|----------|
| orchestrator | 기사의 핵심은 "루프를 누가 돌리는가". 계획 분해·병렬 디스패치·게이트 집행·상태 유지의 주체가 없으면 하네스가 아니라 프롬프트 모음에 불과함 |
| code-reviewer | QA는 동작을 검증하고, 리뷰어는 코드의 12개월 뒤 건강을 지킴(기사 Future Challenges #6: 레포 장기 건강성). 1인 개발이라 동료 리뷰가 없는 것을 보완 — 보안 점검 포함 |
| sre | 사용자가 서비스 운영까지 담당. 배포·롤백·시크릿·모니터링은 개발과 다른 사고방식이 필요하고, 파괴적 작업 승인 게이트의 소유자 |
| harness-improver | 기사 주제인 self-improvement 자체. 이게 없으면 하네스가 정적 설정에 머무름. ACE 큐레이터 + Self-Harness 제안자 역할 |

## 스킬 11종 (레시피북)

공용: harness-state(모든 디스패치가 읽는 계약), harness-ledger(state.json·문서 정본 — orchestrator·커맨드·improver 전용), co-creation.
스택: spring-boot-dev, python-service, frontend-dev, ai-agent-dev, data-pipeline, mlops-gcp.
방법: testing-qa, product-spec.

스킬 = 재사용 도메인 지식, 에이전트 = 역할·판단. **선택은 description(인덱스 한 줄)으로, 읽기는 섹션 단위로** —
`grep -n '^## '` 로 목차를 얻고 필요한 레시피만 연다. 1 디스패치 = 1 스택 스킬.

## 컨텍스트 예산

학습은 무한히 쌓지 않는다. 지식은 `.harness/wiki/` 노드로 분해되고(active ≤ 40 · scope당 ≤ 8 · 노드 본문 ≤ 10줄 · INDEX ≤ 80줄),
에이전트는 INDEX 1줄 훅만 상시 읽고 자기 scope + global/workflow 노드만 연다. 은퇴 노드는 위키 안에 tombstone 으로 남고(INDEX 에서 제외),
오래된 로그는 `logs/archive/` 콜드 스토리지로 이동해 에이전트가 읽지 않는다.
디스패치 1회 읽기 예산은 **≤3,500단어**(에이전트 + 스택 스킬 1개 + harness-state). 1.3.0 실측: 2,053~3,523단어.
작은 작업은 경량 경로 `/harness:quick`(디스패치 1회)으로 전체 루프 비용을 생략한다.

**설계 결정 (2026-08-04, 위키 전환)**: 초기 구현은 평면 `playbook.md`(전 에이전트 통째 필독) + `retro/inbox.md`(산문 백로그)였다.
2일 실전에서 플레이북 불릿이 사고 서사를 흡수하며 비대해지고(불릿당 ~850B) inbox 백로그 93건이 회고 사이에 방치되어,
디스패치 고정비가 목표의 3~5배(실측 30K+ 토큰)로 상승했다. 원인은 규칙 부재가 아니라 **지식의 단위가 파일이 아니라 문서**였던 것 —
노드 단위로 쪼개면 읽기는 scope 필터로, 진화(생성→강화→승격)는 회고를 기다리지 않고 상시로, 압축(병합/은퇴)은 큐레이터 소관으로 분리된다.
inbox 는 candidate 노드로 대체되어 관찰→승격이 같은 자료구조 안에서 일어난다.

## 이식성 설계

- **git repo 하나 = 플러그인 마켓플레이스**: `.claude-plugin/marketplace.json` + `plugins/harness/`
- 새 환경: `/plugin marketplace add blackhjb/harness-engineering` → `/plugin install harness@harness-engineering`
- 오프라인/수동: `install.sh [프로젝트경로 | --user]` 로 `.claude/{agents,skills,commands}` 에 복사 (커맨드는 `harness-` 접두사, `/harness-goal` 형태)
- 프로젝트 종속 상태(`.harness/`)와 이식 가능한 설정(플러그인)을 분리 — 플러그인은 어디서나 동일, 상태는 프로젝트에 남음

## Codex 호환

- 원본은 `plugins/harness/` 하나. Codex 쪽 산출물 — `.agents/skills/` 심링크 11종, `cmd-*` 커맨드 래퍼 스킬 8종, `.codex/agents/` 에이전트 TOML 12종 — 은 전부 `tools/sync-codex.sh`가 생성한다. 생성물은 수동 편집 금지, 수정은 원본에서 하고 스크립트를 재실행.
- 공통 분모는 Anthropic Agent Skills 표준: Codex(2025-12+)가 `$REPO_ROOT/.agents/skills`를 네이티브로 발견하므로 스킬 11종은 심링크만으로 두 도구에 공유된다.
- Claude 커맨드는 Codex에서 `cmd-*` 래퍼 스킬(`$cmd-goal` 호출)로, 서브에이전트는 동명 TOML로 매핑된다. Codex는 자동 위임이 없어 AGENTS.md가 명시적 스폰 규칙과 `.harness/` 계약 요약을 안내한다.

## 주요 게이트 (사람 개입 지점)

기사 Future Challenges #7 (humans move up the stack) 반영:
1. GOAL 확정 — 성공 기준 승인
2. plan 승인 — 설계·태스크 분해 승인 없이 build 불가
3. 파괴적 작업 — 운영 배포·리소스 삭제·IAM 확장
4. 하네스 편집 적용 — retro 제안은 diff 단위로 사람이 승인
