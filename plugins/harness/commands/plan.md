---
description: PLAN + DESIGN phases — planner writes prd.md, architect (plus product-designer for user-facing work) writes design.md, 코디네이터 breaks it into plan.md tasks; ends at a user approval gate before build
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
- Delegate to `architect`: read GOAL/wiki-INDEX/analysis/prd; write `.harness/design.md` per the 12 sections in `agents/architect.md` (정본: `harness-ledger` §Canonical required sections) — all except `8. UX 설계`. **§9 기술 선택에는 이 goal 의 서비스 유형 판별과 구현 디스패치가 열 특화 스킬 slug 를 반드시 명시한다** (LLM 에이전트=ai-agent-dev · Python=python-service · Java=spring-boot-dev · 배치=data-pipeline) — §9 가 비면 build 디스패치가 막힌다 (build.md 게이트, 사용자 정책 2026-08-18).
- **소규모 축약(measured surface ≤8 files)**: write §5 API 계약 · §8 UX 설계 · §11 ADR in full and keep the remaining sections to one line each (or "해당 없음"). Those three are what implementers and reviewers actually read back; a full 12-section expansion on a 5-file change is cost with no consumer (로그 2026-08-06).
- If user-facing: delegate to `product-designer` IN PARALLEL (same message) to write the `8. UX 설계` section (screens, flows, states, error/empty/loading cases) to its own file; whoever merges owns reconciliation. **병합 시 식별자·문안 대조가 의무**: list every field name, label, copy key and state name the two authors used, and where they name the same thing differently, unify to the contract source (§5) and log the correction. Two agents writing one document WILL diverge on names and neither notices alone — the merge is the only place it can be caught (로그 2026-08-06).
Then check design.md answers every P0 story and does not contradict GOAL.md on any user-observable behavior; send gaps back to the architect once.
- **ADR 근거에 `goal.md` §2-B 등급 검사를 그대로 건다.** ADR 이 ①배치 가능성(「여기 두면 사이클·의존이 없다」) ②처분 무효과(「이 호출은 삭제해도 결과가 같다」) ③자 적합성 중 하나를 주장하면, **근거 명령의 pathspec 이 대상 파일 하나뿐인 ADR 은 `[미검증]`** 이고 그 결정에 태스크를 결박하지 않는다 — 필요조건 1축(사이클 없음·하드코딩 있음·타입 포함관계)을 확인하고 충분조건으로 확장하지 않는다. 제출 시 ADR 행마다 `근거 pathspec 파일 수 = N` 을 적는다 (2026-08-27 iter52: ADR 4건 중 단일파일 근거 1건이 곧 실패한 1건, T-005 재디스패치 `cause=design`).

## Stage 3 — Task breakdown (코디네이터)
**태스크가 ≤3건이면 plan.md 를 만들지 않는다** — state.json `tasks[]` 하나로 장부가 성립하고, 두 곳을 동기화하는 비용만 남는다. 이 경우 plan.md 없이 코디네이터가 직접 디스패치하되, **build 착수 전에 「GOAL §1-C 표적 심볼 목록 ∖ `tasks[]` 인수조건이 지목한 심볼 집합」을 차집합으로 내고 그 값이 빈 집합임을 로그 `gate` 항목에 1줄로 적는다** — 비지 않으면 그 심볼을 태스크에 배정하거나 GOAL 「범위 제외」로 옮긴 뒤에만 착수한다. `tasks[]` 는 배정된 것만 담아 **빠진 것을 구조적으로 보여주지 못한다**(실측 2026-08-25 iter43: 표적 12 중 `mfaq.clause_direct_bypass_applied` 만 미배정 → SC-1 분자 3/5, verify FAIL).
그 외에는 코디네이터가 직접 작성: read all of the above; write `.harness/plan.md` — task table (T-NNN, 작업, 담당, 의존성, 인수 조건, 상태=pending), parallel wave grouping, risks. Rules to pass along: every task sized for one agent session; acceptance criteria checkable by a command or file inspection; owners from the harness-state state.json role list; every P0 requirement covered by at least one task.
- **의존성 열은 BUILD 의존만 적는다 — 배포 순서는 의존이 아니다.** A build dependency exists only when (a) the tasks share one working tree and both produce commits, or (b) the later task consumes an artifact the earlier one produces (a file, a generated type, a measured value). "Provider deploys first" is a *release* constraint: record it in the 리스크·대비책 section, never as a dependency edge. Separate repos have separate working trees, so once the contract is fixed in design.md they build **in parallel** — the consumer codes against the documented contract, not against the provider's commit (로그 2026-08-06).
- **qa/code-reviewer 태스크는 plan.md 에 편성하지 않는다** — `/harness:verify` is their single execution point. Planning them as build tasks runs the same suites and the same diff review twice; verify cannot skip them, so the build copy is the redundant one. (A *targeted* qa task is allowed only when a specific measurement must happen mid-build to unblock a later task — name the blocked task in 인수 조건.) 코디네이터 mirrors tasks into state.json `tasks[]` (plan.md and `tasks[]` are 코디네이터 전용).

## Stage 4 — Approval gate (do not skip)
Present in Korean: prd.md priorities summary, design.md key decisions and tradeoffs, and the full plan.md task table with waves. Ask explicitly: "이 설계와 계획을 승인하시겠습니까? 수정할 부분이 있으면 알려주세요."
- Before presenting, cross-check GOAL.md/prd.md against design.md for the SAME proposition stated differently — above all "what does the user see when the feature is off, the gate fails, or the default applies". Such a contradiction yields identical code under either reading, so task decomposition never surfaces it; list every mismatch in the approval request as a decision the user must settle.
- **대조 축은 둘이다. 두 번째는 수량이다**: design 이 GOAL 의 수량 제약(「순삭제 ±0」·「신규 계측기 0」·「분기 델타 0」·「신규 파일 0」)에 **예외를 승인**하면, 그 예외의 **정수**(부착 행수·신설 파일수)를 뽑아 GOAL 해당 SC 목표치의 정수와 **산술 대조**한다 — 합이 목표치를 넘으면 승인 요청에 「GOAL SC-N 목표치를 X → Y 로 개정」을 **같은 턴의 결정 항목으로 올리고**, 개정 없이는 `approvals.design` 을 세우지 않는다. 이 모순은 사용자 가시 행동 축에서 보이지 않고 build 도 통과시키므로 **verify 가 FAIL 로 되돌려주는 것이 유일한 검출 경로**가 된다(2026-08-27 iter51: 승인된 `record_gate` 1행 + WHY 주석 → 실측 −4, verdict FAIL 후 목표치를 낮춰서만 PASS).
- **SC 분모를 부분집합으로 쪼개는 결정 항목(「전건 판정 = 차등 N + 제외 M」)은 승인 요청에 `N+M == 분모` 산술을 값으로 적고, 각 부분에 그 부분을 재도출하는 계수 명령 1줄을 붙인다.** 부분합이 어긋나거나 어느 한 부분의 계수 명령이 없으면 `approvals.design` 을 세우지 않는다 — 열거로 승인된 부분집합은 집행자에게 계약이 되고, 차집합에 남은 행은 **아무 태스크에도 배정되지 않은 채 verify 까지 간다**(2026-08-27 iter52: 8+20 을 승인했으나 실제 8+1+2+17, blocks-goal 2건).
- On approval: set state.json `approvals.design` = true and `approvals.plan` = true, refresh `updated_at`, log the approval, and point to `/harness:build`.
- On change requests: route each to the owning agent (planner/architect/product-designer) 또는 코디네이터, then re-present. Never set approvals without an explicit yes.

## Question rules
질문은 `co-creation` 스킬을 따른다; 기록된 결정은 재질의하지 않는다.
