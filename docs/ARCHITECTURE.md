# ARCHITECTURE — 설계 결정

## 기사 패턴 → 하네스 매핑

Lilian Weng의 "Harness Engineering for Self-Improvement"(2026-07)의 핵심 패턴을 다음과 같이 구현했다.

| 기사 패턴 | 하네스 구현 |
|-----------|------------|
| Pattern 1: Workflow Automation (goal-oriented loop) | 8개 커맨드가 plan→execute→observe→improve 루프를 고정: `/harness:goal → analyze → plan → build → verify → retro` (+ `status`, S-size용 경량 경로 `quick`) |
| Pattern 2: File System as Persistent Memory | 프로젝트마다 `.harness/` 디렉토리. 모든 산출물·상태·로그를 파일로 영속화 → 세션 중단 후에도 복구, 컨텍스트 오염 방지 |
| Pattern 3: Sub-agent & Backend Jobs | orchestrator가 독립 태스크를 역할 에이전트에게 병렬 디스패치. 결과는 채팅이 아닌 파일로 회수 (inspectable parallelism) |
| ACE (Agentic Context Engineering) | `.harness/playbook.md` — 전체 재작성 금지, `[PB-nnn]` 단위 증분 큐레이션으로 context collapse 방지. 모든 에이전트가 작업 전 필독 |
| Self-Harness (weakness mining → bounded proposal → validation) | harness-improver가 logs/·retro/inbox.md에서 실패 패턴 마이닝 → 제한된 편집안 제안 → 사람 승인 후 적용 |
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

## 스킬 9종

harness-state(상태 계약·템플릿), co-creation(핵심 분기점 질문 프로토콜), spring-boot-dev, frontend-dev,
ai-agent-dev, data-pipeline, mlops-gcp, testing-qa, product-spec.
스킬 = 재사용 도메인 지식, 에이전트 = 역할·판단. 지식을 스킬로 분리해 에이전트 프롬프트 비대화를 방지.

## 컨텍스트 예산

학습은 무한히 쌓지 않는다. 플레이북은 활성 30불릿 캡의 고정 크기로 유지하고,
은퇴 불릿은 `retro/playbook-archive.md`, 오래된 로그는 `logs/archive/` 콜드 스토리지로 이동해 에이전트가 읽지 않는다.
디스패치 1회 고정비는 약 6~10K 입력 토큰(에이전트 프롬프트 + 스킬 + `.harness/` 문서).
작은 작업은 경량 경로 `/harness:quick`(디스패치 1회)으로 전체 루프 비용을 생략한다.

## 이식성 설계

- **git repo 하나 = 플러그인 마켓플레이스**: `.claude-plugin/marketplace.json` + `plugins/harness/`
- 새 환경: `/plugin marketplace add blackhjb/harness-engineering` → `/plugin install harness@harness-engineering`
- 오프라인/수동: `install.sh [프로젝트경로 | --user]` 로 `.claude/{agents,skills,commands}` 에 복사 (커맨드는 `harness-` 접두사, `/harness-goal` 형태)
- 프로젝트 종속 상태(`.harness/`)와 이식 가능한 설정(플러그인)을 분리 — 플러그인은 어디서나 동일, 상태는 프로젝트에 남음

## Codex 호환

- 원본은 `plugins/harness/` 하나. Codex 쪽 산출물 — `.agents/skills/` 심링크 9종, `cmd-*` 커맨드 래퍼 스킬 8종, `.codex/agents/` 에이전트 TOML 12종 — 은 전부 `tools/sync-codex.sh`가 생성한다. 생성물은 수동 편집 금지, 수정은 원본에서 하고 스크립트를 재실행.
- 공통 분모는 Anthropic Agent Skills 표준: Codex(2025-12+)가 `$REPO_ROOT/.agents/skills`를 네이티브로 발견하므로 스킬 9종은 심링크만으로 두 도구에 공유된다.
- Claude 커맨드는 Codex에서 `cmd-*` 래퍼 스킬(`$cmd-goal` 호출)로, 서브에이전트는 동명 TOML로 매핑된다. Codex는 자동 위임이 없어 AGENTS.md가 명시적 스폰 규칙과 `.harness/` 계약 요약을 안내한다.

## 주요 게이트 (사람 개입 지점)

기사 Future Challenges #7 (humans move up the stack) 반영:
1. GOAL 확정 — 성공 기준 승인
2. plan 승인 — 설계·태스크 분해 승인 없이 build 불가
3. 파괴적 작업 — 운영 배포·리소스 삭제·IAM 확장
4. 하네스 편집 적용 — retro 제안은 diff 단위로 사람이 승인
