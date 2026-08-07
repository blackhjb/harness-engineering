---
description: PLAN + DESIGN phases — planner writes prd.md, architect (plus product-designer for user-facing work) writes design.md, orchestrator breaks it into plan.md tasks; ends at a user approval gate before build
argument-hint: "[optional notes or emphasis]"
---

Run the harness PLAN (기획) and DESIGN (설계) phases. User notes: $ARGUMENTS

Respond in Korean. All artifacts in Korean per the harness-state skill.

## Preconditions
`.harness/GOAL.md` and `.harness/analysis.md` must exist and be filled in (not empty scaffolds); otherwise stop and point to `/harness:goal` or `/harness:analyze`. If analysis.md lists a blocking item in 알아내야 하는 것 (차단 여부 "예"), surface it to the user before proceeding.

## Stage 1 — PRD (기본 생략)
Set state.json `phase` = "plan". **planner 를 부르지 않는 것이 기본값이다** — GOAL.md 의 SC 표가 정본이고, prd 고유 catch 는 실측 0건이다. 다음 중 하나가 실제로 필요할 때만 planner 를 디스패치한다: 신규 사용자 스토리 · 우선순위 절단 · 릴리스 슬라이싱. 작성하는 경우 GOAL·prd·design 이 같은 명제를 다르게 말하지 않는지 승인 전에 대조한다.

## Stage 2 — Design (architect, + product-designer when user-facing)
**표면 ≤3파일 또는 신규 ADR 0건이면 architect 를 부르지 않는다** — 코디네이터가 `design.md` §5·§8·§11 만 직접 쓴다. 그 규모에서 12섹션은 소비자가 없다.
Set state.json `phase` = "design". Determine from prd.md whether the work has user-facing UI.
- Delegate to `architect`: read GOAL/wiki-INDEX/analysis/prd; write `.harness/design.md` per the harness-state skill's canonical 12 sections — all except `8. UX 설계`.
- **소규모 축약(measured surface ≤8 files)**: write §5 API 계약 · §8 UX 설계 · §11 ADR in full and keep the remaining sections to one line each (or "해당 없음"). Those three are what implementers and reviewers actually read back; a full 12-section expansion on a 5-file change is cost with no consumer (incident 2026-08-06: §1~§4·§6·§9·§10 were written, compressed to fit the 150-line cap, and never referenced by a build task).
- If user-facing: delegate to `product-designer` IN PARALLEL (same message) to write the `8. UX 설계` section (screens, flows, states, error/empty/loading cases) to its own file; whoever merges owns reconciliation. **병합 시 식별자·문안 대조가 의무**: list every field name, label, copy key and state name the two authors used, and where they name the same thing differently, unify to the contract source (§5) and log the correction. Two agents writing one document WILL diverge on names and neither notices alone — the merge is the only place it can be caught (실측 2026-08-06: `isMember` vs `joined`, and a GOAL 목표치 "라벨 1개" vs §8 라벨 2종).
Then check design.md answers every P0 story and does not contradict GOAL.md on any user-observable behavior; send gaps back to the architect once.

## Stage 3 — Task breakdown (orchestrator)
**태스크가 ≤3건이면 plan.md 를 만들지 않는다** — state.json `tasks[]` 하나로 장부가 성립하고, 두 곳을 동기화하는 비용만 남는다. 이 경우 orchestrator 없이 코디네이터가 직접 디스패치한다.
그 외에는 `orchestrator` 에 위임: read all of the above; write `.harness/plan.md` — task table (T-NNN, 작업, 담당, 의존성, 인수 조건, 상태=pending), parallel wave grouping, risks. Rules to pass along: every task sized for one agent session; acceptance criteria checkable by a command or file inspection; owners from the harness-state state.json role list; every P0 requirement covered by at least one task.
- **의존성 열은 BUILD 의존만 적는다 — 배포 순서는 의존이 아니다.** A build dependency exists only when (a) the tasks share one working tree and both produce commits, or (b) the later task consumes an artifact the earlier one produces (a file, a generated type, a measured value). "Provider deploys first" is a *release* constraint: record it in the 리스크·대비책 section, never as a dependency edge. Separate repos have separate working trees, so once the contract is fixed in design.md they build **in parallel** — the consumer codes against the documented contract, not against the provider's commit (incident 2026-08-06: a deploy-order constraint copied into the dependency column serialized the frontend behind the backend for ~30 min of pure idle).
- **qa/code-reviewer 태스크는 plan.md 에 편성하지 않는다** — `/harness:verify` is their single execution point. Planning them as build tasks runs the same suites and the same diff review twice; verify cannot skip them, so the build copy is the redundant one. (A *targeted* qa task is allowed only when a specific measurement must happen mid-build to unblock a later task — name the blocked task in 인수 조건.) Orchestrator mirrors tasks into state.json `tasks[]` (plan.md and `tasks[]` are orchestrator-only).

## Stage 4 — Approval gate (do not skip)
Present in Korean: prd.md priorities summary, design.md key decisions and tradeoffs, and the full plan.md task table with waves. Ask explicitly: "이 설계와 계획을 승인하시겠습니까? 수정할 부분이 있으면 알려주세요."
- Before presenting, cross-check GOAL.md/prd.md against design.md for the SAME proposition stated differently — above all "what does the user see when the feature is off, the gate fails, or the default applies". Such a contradiction yields identical code under either reading, so task decomposition never surfaces it; list every mismatch in the approval request as a decision the user must settle.
- On approval: set state.json `approvals.design` = true and `approvals.plan` = true, refresh `updated_at`, log the approval, and point to `/harness:build`.
- On change requests: route each to the owning agent (planner/architect/product-designer/orchestrator), then re-present. Never set approvals without an explicit yes.

## Question rules (co-creation)
All user questions in this phase follow the `co-creation` skill (key branch points only, batched options with a recommended default, decisions recorded in the owning document and never re-asked).
