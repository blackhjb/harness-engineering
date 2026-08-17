---
description: BUILD phase — the orchestrator executes plan.md, dispatching independent tasks to owner agents in parallel, updating state.json and logs until all tasks meet acceptance criteria
argument-hint: "[optional: specific task IDs to run, e.g. T-003 T-004]"
---

Run the harness BUILD phase. Optional task filter: $ARGUMENTS

Respond in Korean.

## Preconditions (hard gate)
Read `.harness/state.json`. Both `approvals.design` and `approvals.plan` must be true — if not, stop and point the user to `/harness:plan` approval. Do not offer to bypass this.

## Execution
Set state.json `phase` = "build".
**병렬/직렬의 유일한 축은 쓰기 트리 공유다.** Write tasks in the SAME working tree are serial — group them into one session that does them in order and commits per task (separate dispatches buy nothing there and each costs a round trip plus a cold context). Write groups in DIFFERENT trees, and every read-only check, run in parallel in one message. Nothing else — not phase, not repo, not "conceptually separate" — justifies serializing.
세션 기본 추론 강도가 높을수록 **호출 1건이 길어진다** — 그 설정에서 빨라지는 유일한 수단은 호출을 **적게·작게** 하는 것이다. 아래 두 값이 그 수단이다.
**브리프 상한 — 값이다**: 디스패치 1건 = 인수조건 **≤8** · 브리프 **≤20줄**. 초과하면 디스패치하지 말고 태스크를 쪼갠다. 묶기는 왕복만 줄이고 브리프를 부풀리지 않는다. (실측: 인수조건 45개 세션 50분 vs 축 적은 세션 7~15분.)
**모델 티어링 (사용자 정책 2026-08-18)**: 에이전트 frontmatter 가 기본값(설계·분석=fable, 빌드·검증=opus)이다. **`model: sonnet` 오버라이드는 코드를 편집하지 않는 실행 디스패치(골든 측정·스크립트 실행·계수)에만 허용** — 삭제·치환·이동을 포함해 **코드 편집이 1줄이라도 있으면 최소 opus** (사용자 정정 2026-08-18: "실수하면 안 된다" — 검증된 지도 위 삭제도 호출부 패치 판단이 남는다).
**메인 직접 대역**: 변경 **≤3파일 · ≤40줄 · 판정 0건 · 역편집 복구 가능**이면 코디네이터가 직접 고치고 디스패치하지 않는다 — 대신 그 diff 의 PASS 는 스스로 내지 않는다(reviewer 또는 qa 1인 필수).
**디스패치 프롬프트에 위키·스킬 내용을 재서술하지 않는다**: point the agent at `wiki/INDEX.md` + its own scope and give it the task's criteria. Pasting the rules in yourself bypasses the recall path the wiki exists for — the knowledge stops being retrievable and becomes your copy-paste (2026-08-06: recorded lessons never reached the agents that needed them for exactly this reason).
**가드·lint·측정 스크립트를 신설·수정하는 태스크의 브리프에는 qa scope 의 측정 규율 노드(양성 대조 red 선실증 · 축별 주입)를 slug 로 지정 포함한다** — 내용 재서술 금지, 지정만. 이 규율의 위반 생산자는 검증자가 아니라 빌더인데 qa 노드는 빌더의 기본 읽기 세트 밖이다 (실측 2026-08-07·08-14: 지정 태스크 무결, 미지정 태스크 3건에서 가드 무탐·red 1축 과대 보고로 rework). 판별은 인수조건에 test/lint 파일 신설·수정이 있는지로 한다.

**orchestrator 기동 조건**: **묶은 뒤의 디스패치가 4건 이상이거나 병렬 트리가 3개 이상**일 때만 orchestrator 를 기동한다. 그 미만은 코디네이터가 role 에이전트를 **직접 디스패치**한다 — 왕복 게이트가 실작업보다 커지고, 장수명 인스턴스는 과부하의 단일 실패점이다 (로그 참조).
**한 트리의 디스패처는 항상 1인이다** — 시간에 민감한 계획 변경은 실행 중인 orchestrator 에 메시지로 보내지 말고(다음 툴 라운드까지 미배달) 그 웨이브의 **소유권을 가져와** 직접 디스패치하고 "이 웨이브 디스패치 금지" 정정을 보낸다(기전·실측은 wiki `workflow--liveness-by-notification-not-inference`).
**웨이브 비용 감지(웨이브 종료마다 1줄)**: log cumulative dispatch count and current diff size (`git diff --shortstat <base_ref>..HEAD`). **디스패치 수 > 변경 소스 파일 수**(테스트·픽스처·문서 제외 — 회귀 가드를 성실히 쓸수록 분모가 부풀어 초과가 가려진다) means ceremony has overtaken the change — cut the remaining ceremony (merge dispatches, drop redundant verification tasks) in that same turn and say so in the line. Waiting for verify's 결산 to notice is too late; the user should not be the detector.
**우회 시 책무 승계(필수)**: orchestrator 없이 진행하면 그 startup protocol 3종을 코디네이터가 명시적으로 승계한다 — ①`wiki/INDEX.md` + 해당 scope 노드 읽기 ②태스크↔산출물 사상 장부 유지 ③증거 없는 done 금지(값으로만 판정). 승계 사실을 dispatch 로그 항목에 한 줄로 남긴다.
**실행 형태**: 10분+ 디스패치는 orchestrator 의 「비동기 루프」 규칙 그대로 — background + 알림 전진 + 병행 작업 + 20/45분 집행. 동기 대기는 10분 미만 단건에만.

기동하는 경우 전체 build 를 `orchestrator` 에 위임한다:
- Read `.harness/GOAL.md`, `wiki/INDEX.md` (+ workflow/global nodes), `plan.md`, `design.md`, `state.json` first (your startup protocol).
- Execute plan.md wave by wave **and run ALL waves continuously — finishing one wave is not a stopping point**; stop only on your loop's four stop conditions (all done / blocked with nothing independent / escalation / context-limit handoff). Read-only tasks in parallel; commit-producing tasks strictly serial (shared working tree).
- Task IDs passed ("$ARGUMENTS") → run only those and their unmet dependencies.
- Each dispatch follows your dispatch contract (task ID, verbatim acceptance criteria, read-first paths, exact artifact paths, log + wiki-node instructions).
- `done` only when acceptance criteria are demonstrably met with evidence in today's log. Failures: your retry policy — one amended retry, then fix-task or human escalation.
- Keep plan.md statuses and state.json `tasks[]` current after every transition; logs append-only.
- Escalate mid-build per your escalation rules (ambiguity, destructive ops, tradeoffs, double failure) — pause the affected chain, keep independent work running.
- If the orchestrator instance dies TWICE to an infrastructure error (API 5xx/overload, stream abort), stop re-dispatching the same brief. Verify nothing partial landed (`git log <base_ref>..HEAD`, `git status --short`, state.json status counts), then relaunch it scoped to ONE wave or batch per instance until the window passes — short-lived instances survive overload windows that long-lived ones do not, and dispatched task agents (short-lived by construction) kept succeeding throughout.

## Report to the user (Korean)
완료/실패/차단 task counts with IDs, key artifacts (file paths), open escalations needing a decision, next step — `/harness:verify` when all tasks are done, or the specific unblock action. Do not declare the goal met here; only verify can.

## Retro nudge (always evaluate)
Count `(candidate)` lines in `.harness/wiki/INDEX.md`. If ≥5 candidate nodes, OR any `failure` event was logged during this build (including failures recovered by retry), OR a human escalation occurred, append to the report: "⚠️ 학습 루프 권장: 위키에 candidate 노드 N건 — 다음 build 전에 `/harness:retro` 실행을 권장합니다 (같은 실수 반복 방지)." One line only; do not run retro automatically.
