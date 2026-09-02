# Hunter Harness

1인 개발자를 위한 목표 지향(goal-driven) 멀티 에이전트 개발 하네스.
Java/Spring Boot 백엔드, React/TS 프론트, Python LLM 에이전트, 데이터 파이프라인, GCP 운영까지
기획→분석→설계→구현→검증→회고 전 과정을 10개 역할 에이전트가 분담한다(루프 운영은 코디네이터 = 메인 세션).

설계 근거: Lilian Weng, [Harness Engineering for Self-Improvement](https://lilianweng.github.io/posts/2026-07-04-harness/) (2026-07)

저장소: `github.com/blackhjb/harness-engineering`

## Claude Code에서 추가·사용

### 1) 마켓플레이스로 설치 (권장 — 어느 PC/계정이든 한 줄)

Claude Code 안에서:

```
/plugin marketplace add blackhjb/harness-engineering
/plugin install harness@harness-engineering
```

- 첫 줄이 이 repo를 마켓플레이스로 등록하고, 둘째 줄이 `harness` 플러그인을 설치한다.
- 비공개 repo면 먼저 로컬에 clone 후 절대경로로 등록해도 된다: `/plugin marketplace add /path/to/harness-engineering`
- 업데이트: `/plugin marketplace update harness-engineering` → `/plugin install harness@harness-engineering`
- 설치 확인: `/plugin` (목록에 harness 표시) 또는 `/harness:goal` 입력 시 자동완성.

설치되면 커맨드는 콜론 형태 `/harness:goal`, `/harness:build` … 로 호출된다.

### 2) install.sh (마켓플레이스를 못 쓰는 환경용 폴백)

플러그인 내용을 Claude Code가 자동 로드하는 경로(`.claude/agents|skills|commands/`)에 직접 복사한다:

```bash
git clone git@github.com:blackhjb/harness-engineering.git
cd harness-engineering
./install.sh /path/to/your-project   # 특정 프로젝트에만
./install.sh --user                  # 모든 프로젝트 공용 (~/.claude/)
```

> 이 방식에선 커맨드가 하이픈 형태 `/harness-goal`, `/harness-quick` … 로 호출된다(콜론 형태는 마켓플레이스 설치 전용). 업데이트·삭제는 직접 관리.

## Codex에서 추가·사용

Codex(2025-12+)는 Anthropic Agent Skills 표준을 네이티브 지원한다 — 별도 설치 없이 clone + trust만으로 인식된다.

```bash
git clone git@github.com:blackhjb/harness-engineering.git
cd harness-engineering
codex          # repo 루트에서 실행 → trust 승인
```

trust를 승인하면 repo 안의 다음이 자동 인식된다:

- `.agents/skills/` — 스킬 11종 + 커맨드 래퍼 8종(`cmd-goal` 등)
- `.codex/agents/` — 에이전트 10종 (TOML)
- `AGENTS.md` — 하네스 규약(한국어 응답, `.harness/` 계약, 워크플로우)

사용법:

- 커맨드는 스킬 호출로: `$cmd-goal 주문 API에 멱등성 키 지원 추가` → `$cmd-analyze` → `$cmd-plan` → `$cmd-build` → `$cmd-verify` → `$cmd-retro`, 작은 작업은 `$cmd-quick`.
- Codex는 자동 위임이 없으므로, 워크플로우가 "X에게 위임"이라고 하면 `.codex/agents/`의 해당 이름 에이전트를 직접 지정해 스폰한다.
- 스킬·에이전트·커맨드 원본(`plugins/harness/`)을 수정했다면 `bash tools/sync-codex.sh`를 재실행해 Codex 산출물(`.agents/`, `.codex/agents/`)을 다시 생성한다.

MCP 경유(선택): `codex mcp add harness-skills -- npx -y skills-mcp -s "$PWD/plugins/harness/skills"` — 네이티브 스킬 지원이 있어 보통 불필요. Codex Web(cloud)의 스킬 지원 여부는 미확인.

## 하네스 자체를 수정할 때 (기여자용)

이 repo 를 clone 했다면 커밋 훅을 한 번 설치한다 — 미러 미동기·버전 갈림을 커밋 시점에 막는다:

```bash
git config core.hooksPath tools/hooks
```

`plugins/harness/` 를 고친 커밋은 ①`bash tools/sync-codex.sh` 재실행 ②`plugin.json` + `marketplace.json` **양쪽** version 범프 ③같은 이름의 `.codex/agents/*.toml` 동반 ④`python3 tools/check-canon.py` exit 0 을 만족해야 한다. 전체 절차는 `/harness:retro` 의 「적용 완료 6단계」가 정본이다.

## 빠른 시작

```
/harness:goal 주문 API에 멱등성 키 지원 추가
/harness:analyze
/harness:plan        # ← 승인 게이트
/harness:build       # 병렬 구현
/harness:verify      # PASS/FAIL
/harness:retro       # 하네스 자기개선
```

진행 확인: `/harness:status`
작은 작업(단일 파일 수정 등): `/harness:quick 오타 수정` — 전체 루프 생략

## 구성

### 저장소 구조

```
.claude-plugin/       마켓플레이스 매니페스트 (Claude Code)
plugins/harness/      원본(source of truth) — agents/ · commands/ · skills/
AGENTS.md             Codex 진입점 (하네스 규약 요약)
.agents/skills/       Codex용 스킬 — 원본 심링크 11종 + cmd-* 커맨드 래퍼 8종 (생성물)
.codex/               Codex 설정(config.toml) + 에이전트 TOML 10종 (생성물)
tools/sync-codex.sh   Codex 산출물 재생성 스크립트 (원본 수정 후 재실행)
docs/                 설계 문서 (GOAL · DIAGNOSIS · ARCHITECTURE · PROCESS)
install.sh            방법 2 폴백 설치 스크립트
```

### 커맨드 8종 (워크플로우)
| 커맨드 | 단계 |
|--------|------|
| `/harness:goal` | 목표·성공 기준 확정, `.harness/` 생성 |
| `/harness:analyze` | 분석 (analyst) |
| `/harness:plan` | 기획+설계+태스크 분해 (planner→architect→코디네이터), 승인 게이트 |
| `/harness:build` | 병렬 구현 (코디네이터 디스패치) |
| `/harness:verify` | 검증 (qa SC별 팬아웃 + code-reviewer 1인, 비가역 경계면 codex 적대 리뷰 조건부) |
| `/harness:retro` | 회고·하네스 개선 (harness-improver) |
| `/harness:status` | 상태 보고 |
| `/harness:quick` | S-size 단일 작업 경량 경로 — analyze/plan 생략, 에이전트 1명 디스패치 |

### 에이전트 10종 (실리콘밸리 10년+ 시니어 페르소나)
| 에이전트 | 역할 |
|---------|------|
| planner | 기획자(PM) — PRD, 우선순위, 최소 슬라이스 |
| analyst | 분석자 — 현황·리스크·근본원인 |
| architect | 설계자 — 아키텍처·API 계약·ADR |
| product-designer | 상품설계자 — UX 플로우·화면 상태 스펙 |
| backend-dev | 서버 구현(스택 중립) — Java/Spring · Python/FastAPI · 배치 |
| frontend-dev | React/TypeScript |
| ai-agent-dev | Python LLM 파이프라인/에이전트 (Vertex AI) |
| qa | 성공 기준 대비 검증, PASS/FAIL |
| code-reviewer | 코드 품질·보안·레포 장기 건강성 |
| harness-improver | 실패 마이닝→플레이북·하네스 개선 제안 |

### 스킬 11종 (도메인 플레이북)
harness-state · harness-ledger · co-creation · spring-boot-dev · python-service · frontend-dev · ai-agent-dev · data-pipeline · mlops-gcp · testing-qa · product-spec

> **co-creation**: 핵심 분기점에서만 선택지(2~4개)+추천안+트레이드오프 형식으로 사용자에게 질문하고, 답변을 ADR/PRD에 기록해 같은 질문을 반복하지 않는 공동 제작 프로토콜.

## `.harness/` — 파일 기반 영속 메모리

프로젝트마다 생성되는 상태 디렉토리. 세션이 끊겨도 여기서 복구한다.

```
.harness/
├── GOAL.md          목표·성공 기준·제약
├── analysis.md      분석 결과
├── prd.md           기획(PRD)
├── design.md        설계(기술+UX)
├── plan.md          태스크 표 (담당/의존성/수용기준)
├── state.json       루프 상태·승인 게이트
├── wiki/            자기 진화 지식 위키 — 1노드(파일) = 1인사이트, 어느 에이전트든 생성·강화·승격
│   └── INDEX.md     노드당 1줄 훅 — 에이전트는 INDEX + 자기 scope 노드만 읽음 (은퇴 노드는 INDEX 제외)
├── logs/            실행 로그 — 하루 한 파일 (logs/YYYY-MM-DD.md, append-only)
│   └── archive/     오래된 로그 콜드 스토리지 (에이전트가 읽지 않음)
└── retro/           회고 리포트·레거시 아카이브
```

> `.harness/logs/` 는 커밋 여부 선택. 나머지는 커밋 권장(팀 확장 시 그대로 공유됨). 아래 「프로젝트 준비」 참조.

## 프로젝트 준비 (CLAUDE.md · .gitignore)

하네스를 쓰는 프로젝트의 `CLAUDE.md`에 아래 3줄을 넣어 두면 어느 세션에서든 규약이 바로 적용된다:

```markdown
- 이 프로젝트는 harness 플러그인으로 개발한다.
- 작업 시작은 /harness:goal (기능 단위) 또는 /harness:quick (작은 수정). 상태는 .harness/ 가 진실.
- 파일 스키마·게이트 규약은 harness-state 스킬 참조.
```

`.gitignore` 권장 스니펫:

```gitignore
.harness/logs/
.DS_Store
```

- `GOAL.md` · `prd.md` · `design.md` · `plan.md` · `wiki/` 는 **커밋 권장** — 프로젝트의 의사결정 기록이자 팀 확장 시 그대로 공유되는 자산이다. (단, 프로젝트가 `.harness/` 전체를 의도적으로 로컬 전용(gitignore)으로 두는 결정도 유효 — harness-state 스킬의 예외 조항 참조.)

## 토큰 비용 (정직한 안내)

멀티 에이전트 하네스는 공짜가 아니다. 디스패치 1회 고정비 ≈ 에이전트 프롬프트 1~2K + 스킬 2~3K + `.harness/` 문서 2~4K ≈ **6~10K 입력 토큰**. 전체 7단계 루프(디스패치 약 8회)는 출력 토큰을 제외하고 **약 80~150K 입력 토큰**이 든다.

내장된 완화 장치:
- 위키 캡(active ≤ 40 · scope당 ≤ 8 · 노드 ≤ 10줄 · INDEX ≤ 80줄) + INDEX 훅 기반 scope 필터 로딩 (계속 자라는 컨텍스트 없음)
- 에이전트가 파일을 직접 읽음 — 디스패치 브리프에 내용을 붙여 넣지 않음
- 아카이브(`logs/archive/`, `retro/` 내 레거시 아카이브)는 절대 읽지 않는 콜드 스토리지
- Claude Code의 프롬프트 캐싱이 반복 읽기 비용을 줄임
- `/harness:quick` — 디스패치 1회 ≈ 8~10K 토큰의 경량 경로

경험칙: **기능 추가·계약 변경은 full 루프, 그보다 작은 것은 전부 quick.**

## 문서

- [docs/GOAL.md](docs/GOAL.md) — 이 하네스 자체의 GOAL + 품질 지표 M1~M5
- [docs/DIAGNOSIS-2026-08-10.md](docs/DIAGNOSIS-2026-08-10.md) — 현재 상태 진단과 수정 순서
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 설계 결정·기사 패턴 매핑
- [docs/PROCESS.md](docs/PROCESS.md) — 단계별 사용 프로세스
