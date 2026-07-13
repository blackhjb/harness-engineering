---
name: harness-state
description: The contract for the .harness/ directory — exact schema and lifecycle of every file, the state.json JSON schema, playbook/log/inbox formats, context budget, and canonical section lists. Use whenever any agent or command reads or writes anything under .harness/ (GOAL.md, analysis.md, prd.md, design.md, plan.md, state.json, playbook.md, logs/, retro/) so artifacts stay consistent across agents.
---

# harness-state: the .harness/ directory contract

`.harness/` is the harness's file-system-as-memory; agents are stateless between runs. Two universal rules:

1. Every agent reads `.harness/GOAL.md` and `.harness/playbook.md` BEFORE any task.
2. Results go to files, not just chat — not in `.harness/` (or the codebase) = did not happen.

All `.harness/` content is Korean; code identifiers, file paths, technical terms as-is. This skill is the SINGLE schema authority for `.harness/` — its section lists and formats override any other file. Scaffolding creates files directly from the section lists below.

## Directory map

| Path | Purpose | Primary writer | Written when |
|------|---------|----------------|--------------|
| `GOAL.md` | Goal, success criteria, constraints, out-of-scope | /harness:goal (with user) | Goal phase; frozen after user confirm (changes = logged human decision) |
| `analysis.md` | Current state, risks, unknowns | analyst | Analyze |
| `prd.md` | Requirements, stories, priorities | planner | Plan |
| `design.md` | Architecture, API/data contracts, UX spec | architect + product-designer | Design; build gated on user approval |
| `plan.md` | Task table: id, owner, deps, acceptance, status | orchestrator ONLY | End of plan; status updated through build |
| `state.json` | Machine-readable phase + task state | orchestrator (`tasks[]`); commands: `phase`/`approvals`/`verify` | Every phase/task transition |
| `playbook.md` | Curated insight bullets (ACE), read by ALL agents | harness-improver; created by /harness:goal | Retro (curation) |
| `logs/YYYY-MM-DD.md` | ONE shared append-only daily log, ALL agents | every agent (append) | Continuously |
| `retro/inbox.md` | Raw candidate insights | any agent (append) | After failures/learnings |
| `retro/YYYY-MM-DD.md` | Retro report + edit proposals | harness-improver | Retro |
| `retro/playbook-archive.md` | Retired bullets (full text, append-only) | harness-improver | Retro; cold storage |
| `logs/archive/` | Logs mined by past retros | harness-improver | Retro; cold storage |

## state.json schema

```json
{
  "goal_id": "string — <yyyymmdd>-<short-slug>",
  "base_ref": "string|null — git commit SHA at goal start (set by /harness:goal via git rev-parse HEAD); diff base for code review",
  "phase": "goal | analyze | plan | design | build | verify | retro | done",
  "iteration": "integer ≥ 1 — increments on each /harness:goal over an existing .harness/",
  "updated_at": "ISO-8601 — refreshed on EVERY write",
  "approvals": { "design": "boolean", "plan": "boolean" },
  "verify": { "verdict": "\"PASS\" | \"FAIL\" | null", "date": "ISO-8601 | null" },
  "tasks": [
    {
      "id": "T-NNN — matches plan.md",
      "owner": "backend-dev | frontend-dev | ai-agent-dev | qa | code-reviewer | sre | planner | analyst | architect | product-designer",
      "status": "pending | in_progress | blocked | review | done | failed",
      "artifacts": ["file paths this task created/modified"]
    }
  ]
}
```

Rules:
- The `owner` 10-role list = the SINGLE agent-role enum source; other files reference it, never restate it.
- `tasks[]` mirrors plan.md's table; on disagreement fix both, log it.
- plan.md and `tasks[]`: orchestrator-only. Commands may set `phase`/`approvals`/`verify`. Every other agent REPORTs to its dispatcher, never edits plan.md/state.json — qa and code-reviewer return structured defect reports + log entries; only the orchestrator turns findings into fix tasks.
- `approvals.design`/`approvals.plan`: set ONLY on an explicit user yes; they gate all build dispatches. `verify.verdict`: set only by the verify command.
- Write the whole file atomically (read, modify, write back complete JSON).

## playbook.md bullet format

```
[PB-001] (workflow) 병렬 디스패치 전 반드시 plan.md 의존성 컬럼을 재확인한다 — 2026-07-02 wave 2에서 의존 작업 동시 실행으로 충돌.
[PB-003] (retired: gradle 8 업그레이드로 해소)
```

- ID `PB-NNN`, monotonic, never reused. Scope (the ONE scope enum, shared with inbox entries): analysis / planning / design / backend / frontend / ai-agent / qa / review / sre / cost / workflow / global.
- Bullets are operational ("when Y, do X"), ideally with evidence date. Add/merge/retire only — never rewrite wholesale. Curation authority: harness-improver; any agent may PROPOSE via retro/inbox.md.

## Log format (logs/YYYY-MM-DD.md, append-only)

ONE shared file per day for ALL agents — NO per-agent/per-task logs; "today's log" = this file. Writer = the `[agent-name]` in each entry header; commands use the command name there (e.g. `## HH:MM [goal] goal-set`).

```
## HH:MM [agent-name] event-type
- 내용: what happened, in Korean
- 증거: command run + result excerpt, or file paths (required for result/verify events)
```

Event types: `session-start`, `decision`, `dispatch`, `result`, `failure`, `gate`, `escalation`, `verify`, `goal-set`, `retro-complete`. Never edit/delete past entries; corrections = new entries referencing the old one.

## retro/inbox.md entry format

```
- [ ] (scope, agent, YYYY-MM-DD) 관찰한 패턴 한 줄 — 표면 오류와 의심되는 원인
```

The `- [ ]` checkbox is mandatory (build's retro nudge counts unchecked boxes); `scope` from the enum above. Any agent appends after a failure, retry, or surprising success. harness-improver MOVES processed lines into the retro report and DELETES them here (never checks off in place); it removes ONLY promoted or explicitly retired lines — below-threshold lines (single occurrence, non-High severity) STAY as occurrence evidence.

## Context budget (token control — hard rules)

The harness must get smarter WITHOUT per-task context growing; learning lives in a fixed-size curated playbook.

1. **playbook.md capped**: max 30 active bullets (~120 lines). Over budget → merge/retire lowest-value bullets before adding. Bullets retired in a PREVIOUS retro move (full text) to `retro/playbook-archive.md` at the next retro, leaving tombstone `[PB-NNN] (archived)`, pruned once unreferenced.
2. **Scope-filtered reading**: apply only bullets matching own scope + `global`/`workflow`; skim the rest, never quote them into outputs.
3. **Fixed read-set per task**: GOAL.md + playbook.md + own plan.md task row + documents the role owns/consumes (e.g. dev → design.md). NEVER read `logs/`, `retro/`, or archives in normal work — past decisions live in the owning DOCUMENTS (design.md ADR / prd.md / GOAL.md), never mined from logs.
4. **Logs: write-heavy, read-rarely**: only harness-improver reads them (only newer than the last retro report), then moves them to `logs/archive/`. `/harness:status` reads only today's log.
5. **Archives = cold storage**: read only when a human asks.

## Lifecycle rules

1. `/harness:goal` scaffolds everything; preserves playbook.md, retro/, logs/ across iterations.
2. Phases move only forward except: verify FAIL → build, and any phase → goal (new iteration). The transition's writer updates state.json in the same turn.
3. Document ownership is exclusive per phase (table above); others read but do not edit — log disagreements and escalate.
4. Task status flow (English values only): `pending → in_progress → (review) → done`, branches `blocked`/`failed`. Only evidence-backed transitions to `done`.
5. Gates: design approval before build, verify PASS before done, human approval before applying harness edit proposals.
6. User decisions: PRIMARY record = the owning document (architecture → design.md ADR, scope/priority → prd.md, goal-level → GOAL.md); the `decision` log entry is secondary — "never re-ask" is enforced via the documents, not logs.

## Canonical required sections per document

Scaffold directly from these lists; keep every section even if empty, marked "해당 없음":

- **GOAL.md**: 한 줄 목표 · 배경 · 성공 기준 표(SC-n / 기준 / 측정 방법 / 목표치) · 제약 · 기한 · 범위 제외 · 승인
- **analysis.md**: 요약 · 현재 상태(파일 경로 근거) · 아는 것 · 알아내야 하는 것(U-n · 확인 방법 · 차단 여부) · 가정([확인]/[추정]/[불명] + 신뢰도) · 리스크 표(R-n · 가능성 상/중/하 · 영향 상/중/하 · 조기 신호 · 대응) · 권고
- **prd.md**: 문제 정의 · 타겟 사용자 · 사용자 스토리 표(US-n · 우선순위 P0-P2 · Given/When/Then 인수 조건) · 기능 요구사항(FR-n) · 비기능 요구사항(NFR-n — 정량 수치) · 스코프 컷·범위 제외 · 릴리스 슬라이스 · 규제·개인정보 체크 · 미해결 질문. Priorities: P0/P1/P2 only (P0 = must-ship); no other scale in artifacts.
- **design.md** (numbered, in order): 1 시스템 컨텍스트 · 2 품질 속성 우선순위 · 3 아키텍처 스타일 · 4 컴포넌트/모듈 책임 · 5 API 계약 · 6 데이터 모델 · 7 에러/장애 전략 · 8 UX 설계 (사용자 대상 기능일 때 — product-designer 작성; the ONLY UX section name) · 9 기술 선택 · 10 NFR 예산 · 11 설계 결정 (ADR) · 12 승인 (BUILD 게이트 체크박스 → state.json approvals.design)
- **plan.md**: 작업 표(T-NNN / 작업 / 담당 / 의존성 / 인수 조건 / 상태) · 병렬 실행 웨이브 · 커버리지 확인 · 리스크와 대비책. Status = the English enum above; 담당 = the state.json role list.

Initial content (fresh scaffold): `playbook.md` = header `# Playbook` + one format comment (`<!-- 형식: [PB-NNN] (scope) 운영 가능한 인사이트 — 근거 날짜 -->`); `retro/inbox.md` = header `# Retro Inbox` + one format comment (`<!-- 형식: - [ ] (scope, agent, YYYY-MM-DD) 관찰한 패턴 한 줄 — 표면 오류와 의심되는 원인 -->`).
