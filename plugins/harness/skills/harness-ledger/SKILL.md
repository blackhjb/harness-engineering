---
name: harness-ledger
description: 하네스 장부 계약 — state.json 스키마와 owner enum, 문서별 정본 섹션 목록, 페이즈·태스크 수명주기, 위키 노드 마이그레이션. orchestrator·커맨드·harness-improver 만 읽는다. dev·qa·review 에이전트는 harness-state 만 읽으면 된다.
---

# harness-ledger: 장부와 문서 계약

`harness-state` 가 공용 계약(디렉터리·위키·로그·컨텍스트 예산)을 정의하고, 이 스킬은 **장부를 쓰는 주체**만 필요한 세부를 담는다. 읽는 주체: `orchestrator`, `/harness:*` 커맨드, `harness-improver`.

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
      "status": "pending | in_progress | blocked | review | done | failed | deferred",
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
- `deferred` ≠ `pending`: a deferral is a DECISION (reason + where it is re-planned), never a leftover. NEVER park deferred work as `pending` — an unexecuted task and a deferred task must be distinguishable from status alone (incident: a planned task was silently skipped and verify PASSed because both looked `pending`).
- state.json MUST be git-tracked: at scaffold time, if the repo's `.gitignore` excludes it (e.g. `*.json`), add a `!.harness/state.json` exception. An untracked state file cannot be recovered after a destructive git operation (dangling-blob recovery only works for staged files). EXCEPTION: a project may deliberately keep ALL of `.harness/` local-only (gitignored) — that is a recorded human decision (GOAL 제약 or a `decision` log entry), never an agent's. In such a repo the destructive-git ban above is the ledger's ONLY protection; treat `.harness/` as unrecoverable and never propose re-tracking it.

### Migration from a legacy ledger (once per project, improver-owned)

Each active `[PB-NNN]` bullet → one active node with `source: PB-NNN`; retired/archived bullets stay in their archive file. Inbox lines → candidate nodes ONLY where the pattern recurs; single-occurrence lines move to `retro/inbox-archive-<date>.md` as occurrence evidence. Then DELETE `playbook.md` and `retro/inbox.md` and build INDEX.md from the surviving nodes.

## Lifecycle rules

1. `/harness:goal` scaffolds everything; preserves wiki/, retro/, logs/ (accumulated learning) across iterations.
2. Phases move only forward except: verify FAIL → build, and any phase → goal (new iteration). The transition's writer updates state.json in the same turn.
3. Document ownership is exclusive per phase (table above); others read but do not edit — log disagreements and escalate.
4. Task status flow (English values only): `pending → in_progress → (review) → done`, branches `blocked`/`failed`. Only evidence-backed transitions to `done`.
5. Gates: design approval before build, verify PASS before done, human approval before applying harness edit proposals.
6. User decisions: PRIMARY record = the owning document (architecture → design.md ADR, scope/priority → prd.md, goal-level → GOAL.md); the `decision` log entry is secondary — "never re-ask" is enforced via the documents, not logs.
7. **Backward propagation**: when build/verify work REFUTES a premise recorded upstream (a GOAL measurement, an analysis F-NNN fact, a design assumption), the orchestrator corrects the owning document IN THE SAME TURN — a one-line 정정 with the refuting evidence, never a silent divergence. Stale premises left in documents poison every later read (incident: 7 refuted premises had to be hunted down by hand across 5 documents).
8. **Quick route (규모 비례)**: a goal that `/harness:goal` triages as quick 경로 (no contract/architecture impact, mechanical diff, command-checkable SCs) keeps analysis.md/prd.md/design.md/plan.md as "해당 없음 — quick 경로" stubs and runs as `/harness:quick` batches; phase closes goal → done directly. What is NOT waived: every SC still gets its measurement command + value in a `verify` log entry, state.json `verify.verdict` is still set, and guard changes still require a positive control. Ceremony scales with the change; evidence does not (incident: ~300 changed lines consumed ~1.4M subagent tokens, mostly on documents and wave management — the defects were all caught by verification, none by ceremony).

## Canonical required sections per document

Scaffold directly from these lists; keep every section even if empty, marked "해당 없음":

- **GOAL.md**: 한 줄 목표 · 배경 · 성공 기준 표(SC-n / 기준 / 측정 방법 / 목표치) · 제약 · 기한 · 범위 제외 · 승인
- **analysis.md**: 요약 · 현재 상태(파일 경로 근거) · 아는 것(**each fact gets an ID `F-NNN` + file:line evidence** — downstream documents REFERENCE `F-NNN`, never copy the fact's prose; a refuted fact is corrected HERE first, then every referencing doc gets a one-line 정정 note in the same turn) · 알아내야 하는 것(U-n · 확인 방법 · 차단 여부) · 가정([확인]/[추정]/[불명] + 신뢰도) · 리스크 표(R-n · 가능성 상/중/하 · 영향 상/중/하 · 조기 신호 · 대응) · 권고
- **prd.md**: 문제 정의 · 타겟 사용자 · 사용자 스토리 표(US-n · 우선순위 P0-P2 · Given/When/Then 인수 조건) · 기능 요구사항(FR-n) · 비기능 요구사항(NFR-n — 정량 수치) · 스코프 컷·범위 제외 · 릴리스 슬라이스 · 규제·개인정보 체크 · 미해결 질문. Priorities: P0/P1/P2 only (P0 = must-ship); no other scale in artifacts.
- **design.md** (numbered, in order): 1 시스템 컨텍스트 · 2 품질 속성 우선순위 · 3 아키텍처 스타일 · 4 컴포넌트/모듈 책임 · 5 API 계약 · 6 데이터 모델 · 7 에러/장애 전략 · 8 UX 설계 (사용자 대상 기능일 때 — product-designer 작성; the ONLY UX section name) · 9 기술 선택 · 10 NFR 예산 · 11 설계 결정 (ADR) · 12 승인 (BUILD 게이트 체크박스 → state.json approvals.design)
- **plan.md**: 작업 표(T-NNN / 작업 / 담당 / 의존성 / 인수 조건 / 상태 / **증거**) · 병렬 실행 웨이브 · 커버리지 확인 · 리스크와 대비책. Status = the English enum above; 담당 = the state.json role list. 증거 column: `done` = commit sha or log entry ref · `deferred` = 사유 + 재편성 위치 · `blocked` = 차단 원인. A row whose status can't be justified by its 증거 cell is treated as NOT done.

Initial content (fresh scaffold): `wiki/INDEX.md` = header `# Wiki Index` + one format comment (`<!-- 형식: - [scope] [[slug]] — 한 줄 훅 (candidate) · 노드 파일은 <scope>--<slug>.md -->`).
