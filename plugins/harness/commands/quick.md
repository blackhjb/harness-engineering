---
description: Lightweight path for S/M-size mechanical work (bugfix, config change, guard/test additions, small refactor batch) — minimal ceremony, full verification rigor; refuses anything that needs the full loop
argument-hint: "<one-line task, e.g. 'fix NPE in OrderService.cancel'>"
---

Run a harness QUICK task: $ARGUMENTS

Respond in Korean. This path skips analyze/plan/design ceremony for genuinely small work — it does NOT skip the harness's memory discipline, and it NEVER skips verification rigor (경량화는 문서·오케스트레이션에만 적용되고 검증 증거에는 적용되지 않는다).

## 1. Preconditions
`.harness/` and `.harness/state.json` must exist. If not, stop and point to `/harness:goal` — quick tasks still need GOAL.md and the wiki as context.
**코디네이터 자신도 위키를 읽는다** — 시작 시 `.harness/wiki/INDEX.md` + 손댈 영역 scope 노드(+ `global`/`workflow`). 3.2 의 Coordinator-direct 경로는 서브에이전트를 거치지 않으므로 이 선독 없이는 위키가 그 편집에 도달하지 못한다.

## 2. Classify (hard gate)
Quick 대역의 임계값 정본은 `goal.md` §2 다(계약 breaking 없음 · 아키텍처 결정 0 · 기계적 diff · 명령 판정 가능 SC). 여기서 다시 정의하지 않는다. REFUSE and redirect to the full loop (`/harness:analyze` → `/harness:plan`) if the task:
- creates or changes an API/data contract (new endpoint, schema/migration, message shape), or
- requires an architecture decision (new module boundary, tech choice, non-mechanical coupling change that propagates behavior across modules), or
- changes data models, or
- is ambiguous enough that a wrong guess is expensive.
When refusing, say why in one line and name the command to run instead. Do not offer to bypass this gate.

## 3. Execute
1. Append a quick-task entry to today's daily log (`## HH:MM [quick] dispatch`, task one-liner, why it qualifies as quick).
2. Do the work — one of:
   - **Coordinator-direct** — 메인 직접 대역(`build.md` 정의: ≤3파일·≤40줄·판정 0건·역편집 복구 가능)에 들면 메인 루프에서 직접 고치고 그렇게 로그한다; 아니면
   - **Dispatch ONE dev agent** — backend-dev, frontend-dev, ai-agent-dev, or sre (인프라·배포·롤백 표면). 10분+ 예상이면 background 로 띄우고 알림으로 전진(20/45분 집행은 orchestrator 의 비동기 루프 규칙과 동일) — with this brief:
     - Read `.harness/GOAL.md` and `wiki/INDEX.md` (open own-scope + global/workflow nodes) FIRST (mandatory), plus the design.md sections relevant to the touched area (API 계약 / 데이터 모델 / 에러 전략 as applicable).
     - No plan.md task exists for quick mode — this brief IS your task assignment and acceptance criteria; the "work only your plan.md task" rule is waived.
     - Make the change; run focused tests for the touched code.
     - Append a result entry with evidence to today's log; insights as wiki nodes (create/reinforce/promote per the `harness-state` skill).
   - **디스패치 단가 규율**: ①확인된 사실은 `file:line` 과 함께 싣고 "재검증 말고 여기서 출발" ②전제가 깨지면 구현 말고 중단·보고 ③영역이 겹치면 신규 스폰 대신 직전 에이전트 재사용 ④하위 모델 티어는 기계적·되돌리기 쉬움·판정 없음 전건 충족 시에만(리뷰·분석·판정·보안 표면 하향 금지).
3. **Proportional verification (mandatory, not reducible):**
   - Always: run the project's test suite (or dispatch `qa` for a focused check if the suite is heavy); confirm green with real output, plus the project's import/boot smoke if one is established. Exception — documentation-only changes: skip the suite; a reviewer glance (or self-check of rendered content and links) suffices, and the report states this exception was used.
   - If the change adds or modifies a guard/lint/test-that-must-catch: a **positive control is mandatory** — inject a known violation → red (exit code) → revert → green, logged with commands and outputs. 대조군은 **사용자 관측 행동을 지키는 가드에만** 붙인다 — 수집 하한 단언 등으로 vacuity 가 이미 막힌 가드는 생략하고 판단 근거를 로그에 1줄 (로그 2026-08-06). **주입했는데 red 0건이면 대조군 포기가 아니라 픽스처의 판별력을 의심**하라 — 결함이 드러나는 최소 픽스처로 교체하고 로그에 남긴다(설계법: wiki `frontend--grouping-preserves-first-appearance-order`).
   - For a multi-file batch: ONE `code-reviewer` pass over the final diff before calling it done (single file, a NIT-level tweak: reviewer optional). **이것은 게이트다** — 리뷰어 미실행 상태로 done·PASS 를 선언하지 않는다. 실행하지 않았다면 그 사유를 로그 종결 항목에 명시하고 verdict 를 보류한다.
4. If this quick run completes a quick-routed GOAL (state.json goal whose route was set to quick by `/harness:goal`): measure EVERY SC in GOAL.md with its stated command, append a `verify` log entry with the values **plus the goal 결산** (`git diff --shortstat <base_ref>..HEAD`, commit count, dispatch count, observed subagent tokens — same fields as the full loop's verdict entry; retro mines these for ceremony-vs-diff disproportion), set state.json `verify` = {verdict, date} and `phase` = "done" on PASS. This closure is the command/coordinator's job — never the dev agent's.
   **종결 체크리스트(전건 기재 필수)**: SC 전건 측정값 · 결산 · **배치↔산출물 사상**(각 배치를 커밋 sha 또는 `deferred`+사유 중 하나에 정확히 사상, 미사상 1건이라도 있으면 종결 금지 — plan.md 를 만들지 않는 대신 이 한 줄이 장부다. `state.json.tasks[]` 로 우회하지 않는다) · **code-reviewer verdict(또는 미실행 사유)** · **독립성** — 코드를 직접 수정한 주체는 그 수정에 대한 PASS 판정을 스스로 내리지 않는다(직접 수정이 있었다면 `code-reviewer` 또는 `qa` 중 최소 1인을 그 diff 에 붙인다).

## 4. Report (Korean)
What changed (file paths), test + positive-control evidence (actual values/exit codes), reviewer verdict if dispatched, wiki insights added. Append a final result entry to today's log.

State discipline: quick tasks leave a log trail only — do NOT add rows to plan.md, do NOT touch state.json `phase` or `tasks[]` (the goal-closure step in 3.4 is the one exception, and it belongs to the command, not the dev agent). If the "quick" task turns out bigger mid-flight, stop, log it, redirect to the full loop.
