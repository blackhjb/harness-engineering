---
description: Set or reset the harness goal — brief interview, then scaffold .harness/ and write GOAL.md with measurable success criteria
argument-hint: "<one-line goal>"
---

The user wants to set a harness goal: $ARGUMENTS

Respond in Korean; write all .harness/ files in Korean (code identifiers, file paths, technical terms as-is). Consult the `harness-ledger` skill; scaffold files directly from its canonical section lists.

## 1. Interview (one message, short)
Ask in Korean, in ONE message. **quick 후보면 2문항만**(성공 기준 · 범위 제외); 표준 루프면 최대 4문항(+ 제약 · 기한). 이미 "$ARGUMENTS" 가 답한 것은 묻지 않는다.
1. 성공 기준 — how will we MEASURE done? 검증 가능한 값으로("p95 < 200ms"), 느낌 말고. 각 기준은 **수정 전 거짓이어야** 한다(참이면 vacuous — 인용한 로그 레벨·문자열·상수는 원문 줄을 열어 확인). 같은 값이 다른 경로로도 나올 수 있으면 경로 식별 증거를 함께 적고, 착수 시점에 확정 불가면 "수정 전 red 실측을 같은 태스크에 포함"을 명시한다.
2. 범위 제외 — explicitly OUT of scope.  3. 제약 · 4. 기한 (표준 루프만)
Wait for the answers before writing anything. If a success criterion comes back vague, restate it measurably once ("이렇게 바꾸면 측정 가능합니다: ... 맞습니까?") and proceed on confirmation.

## 2. Size triage (규모 비례 라우팅 — do not skip)
**먼저 `.harness/wiki/INDEX.md` 를 열고 `cost`/`workflow`/`global` 노드를 읽는다** — 아래 임계값은 그 노드가 이기는 기본값이라, 읽지 않으면 프로젝트가 이미 배운 값을 무시하게 된다.
Classify the goal's size BEFORE scaffolding. **The change surface MUST be grep-measured first — routing on document reasoning alone is forbidden**: locate the files that actually change (the constant, the route, the component), count them, and write that count into GOAL.md 승인 섹션 next to the route. Ceremony scales with the measured change, never with the goal's importance — and unmeasured routing is this triage's most expensive error (로그 참조).

- **quick 경로** — ALL of: **no compatibility-breaking contract change** · no architecture decision (no new module boundary, no tech choice) · measured diff localized and mechanical (guards, re-exports, test fixes, config/doc tweaks — roughly ≤8 files / ≤150 lines) · every success criterion directly checkable by a command.
  - breaking = 필드 제거·rename·타입/의미 변경·필수 요청 필드/인자 추가. **추가형**(새 응답 필드 · 기본값 있는 kwarg · 구 소비자가 무시하는 enum 값)은 quick 을 탈락시키지 않는다 — 둘 중 어느 쪽인지 **구 소비자 동작 근거와 함께 1줄**로 명시한다.
  → Still scaffold per section 4, but leave analysis.md/prd.md/design.md/plan.md as stubs marked "해당 없음 — quick 경로", record the route + one-line rationale in GOAL.md (승인 섹션) and the daily log, and hand off to `/harness:quick` (one batch, or one invocation per SC cluster) instead of `/harness:analyze`. Verification rigor is NOT reduced — quick's proportional-verify rules still apply in full.
- **표준 루프** — anything else, or any doubt that a wrong guess is expensive → `/harness:analyze` as usual.
- **판단 불가** — run `/harness:analyze` first; analysis.md's 권고 MUST then name the route (quick vs plan) explicitly, and the goal proceeds on that recommendation.

The numeric thresholds above (≤8 files / ≤150 lines) are **retro-tunable defaults, not constants**: retro mines each goal's 결산 (diff vs orchestration cost, logged by verify/quick closure) and proposes threshold adjustments through the bounded harness-edit channel; a project may also carry a sharper local rule as a `cost`-scope wiki node — when one exists, it wins over these defaults.

State the chosen route and its rationale in the confirmation message (section 5).

**문안 확정 게이트**: 산출물이 사용자 눈에 보이는 문자열(문구·라벨·에러·화면 상태)을 포함하면, 착수 전에 **리터럴 3안 이내로 1회 확정**받고 그 문안을 GOAL.md 목표치 칸(또는 design.md §8)에 **그 턴에** 적는다. 미기재 문안으로는 디스패치하지 않는다 — 문구는 취향이라 착수 후 바뀌면 배선까지 되돌아간다(실측: 문구 3회 회전으로 주입 배선 전량 삭제).

## 2-B. 사실 명제에는 근거를 붙인다 (재작업의 최대 원인)
GOAL 배경·전제에 쓰는 **사실 명제**(도입 시점·인과 순서·"~가 없다"는 부재 주장·값의 형태·직전 iteration 의 결론)는 각각 `file:line`·커밋 sha·명령 출력 중 하나를 **같은 줄에 병기**한다. 근거를 댈 수 없으면 `[미검증]` 으로 표시하고 analyze 의 확인 대상으로 넘긴다 — 확신도를 섞어 쓰지 않는다.
직전 iteration 의 verify 로그·사용자 보고를 그대로 승격하는 것이 **가장 흔한 오염 경로**다 (로그 참조). 틀린 전제로 시작하면 그 뒤 모든 디스패치가 재작업이 된다 — 토큰을 가장 많이 태우는 지점은 작업이 아니라 **잘못된 출발**이다.

## 3. Handle an existing .harness/
- **위키 상한 위반이면 새 goal 을 열기 전에 `/harness:retro` 를 먼저 돌린다** (count it: candidate ≤15, active ≤8 per scope, INDEX ≤80 lines). Over budget, INDEX stops being triageable in one pass and every later agent recalls worse — curation is a precondition for the next goal, not a nicety deferred to "someday" (로그 2026-08-06).
- **장부가 실제와 어긋나면 먼저 맞춘다**: if code changed since the last verdict while state.json still says `done`/PASS, that follow-up work was an unregistered iteration — register it (increment `iteration`, reset `verify`) before anything else. A ledger that disagrees with the tree makes every later status read wrong.
- No `.harness/`: create the full structure below.
- `.harness/` exists: NEW GOAL ITERATION. Preserve `wiki/`, `retro/`, and `logs/` — accumulated learning. (A legacy `playbook.md`/`retro/inbox.md` is also preserved untouched; note to the user that the next `/harness:retro` migrates it into wiki nodes per the `harness-ledger` skill.) Read the old state.json, increment `iteration`, and overwrite GOAL.md / analysis.md / prd.md / design.md / plan.md with fresh scaffolds. If the previous goal's phase is not `done` or `retro`, warn the user it is unfinished and get explicit confirmation before overwriting.

## 4. Create files (from the `harness-ledger` skill's canonical section lists)
Every section present, empty ones marked "해당 없음".
- `.harness/GOAL.md` — filled from the interview.
- `analysis.md`, `prd.md`, `design.md`, `plan.md` — **표준 루프만** 생성한다(headers only). **quick 경로는 이 4개를 만들지 않는다** — 빈 스텁은 읽는 사람도 쓰는 사람도 없이 매 goal 마다 4개 파일을 갱신 대상으로 만든다. quick 의 장부는 GOAL.md + state.json + 로그다.
- `state.json` — per the skill's schema: `goal_id` = `<yyyymmdd>-<short-slug>`, `base_ref` = current commit SHA from `git rev-parse HEAD` (null if not a git repo), `phase` = "goal", `iteration` (1 or incremented), `updated_at` = now, `approvals` all false, `verify` = {"verdict": null, "date": null}, `tasks` = [].
- `wiki/INDEX.md` — create with header + format comment ONLY if missing; never overwrite an existing wiki.
- `retro/` and `logs/` — create if missing.
- Append a goal-set entry to today's daily log (who, what goal, iteration).

## 5. Confirm and hand off
Show the user in Korean: the success criteria table, 제약, 범위 제외, and the section-2 route decision with its rationale; ask them to confirm GOAL.md or request edits. Once confirmed, the next step is the routed command — `/harness:quick` for the quick 경로, `/harness:analyze` otherwise. **Routing must never add a manual step for the user**: when the user has granted standing autonomous progression (e.g., "알아서 진행"), the coordinator invokes the routed command itself in the same session — the route decides WHICH path runs, the user is never asked to type it.

## Question rules (co-creation)
All user questions in this phase follow the `co-creation` skill (key branch points only, batched options with a recommended default, decisions recorded in the owning document and never re-asked); exception — the initial interview may ask short open-ended questions for basic facts (기한, 제약 등).
