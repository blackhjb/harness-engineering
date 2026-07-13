---
name: co-creation
description: Protocol for eliciting user decisions at key branch points — when to ask vs proceed with a default, the options+recommendation+tradeoff question format, decision recording rules, and anti-fatigue batching. Use whenever an agent or command faces a choice that user preference or business context must resolve, or before escalating any question to the human.
---

# co-creation: 핵심 분기점 질문 프로토콜

The harness builds WITH the user, but questions cost attention and stall the loop — ask only where the answer genuinely changes the outcome, and make every question effortless to answer.

## When to ask (ALL must hold — otherwise proceed with a default)

Ask only at a KEY BRANCH POINT:

1. **Real fork**: two or more defensible alternatives exist, AND
2. **Files can't answer**: the choice depends on user preference, business context, or priorities not resolvable from the codebase, `.harness/` documents, or prior decisions, AND
3. **It matters**: the choice materially changes architecture, scope, cost, or UX direction, or is hard to reverse (one-way door).

Blocking unknowns (analyze phase) that no investigation can resolve also qualify.

Below that bar: pick the sensible default, proceed, REPORT the choice ("~로 진행했습니다 — 바꾸려면 알려주세요"). Never stall on a two-way door.

## NEVER ask

- Anything answerable by reading code, docs, or running a command — investigate first.
- Anything already recorded in GOAL.md, prd.md, or design.md ADRs — check those DOCUMENTS before asking (the primary record; never mine logs for decisions). Re-asking a recorded decision is a protocol violation.
- Micro-details (naming, copy phrasing, minor layout) unless the user opted into detail-level review.
- Open-ended "어떻게 할까요?" without options — analyze first, then present the fork.

## Question format (mandatory)

- 2–4 options per question. Recommended option FIRST, labeled `(추천)`, with a one-line reason.
- Every option carries a one-line tradeoff (what you gain / what you give up).
- Always state: "잘 모르겠으면 추천안으로 진행합니다."
- BATCH: collect all pending branch points and ask once (max ~3 questions per batch), at phase start or a natural pause — never drip one at a time.

Template:

```
[결정 필요] <무엇을 정해야 하는지 한 줄>
배경: <왜 지금 갈리는지, 조사로 확인한 사실 1-2줄>

A. <선택지> (추천 — <이유 한 줄>)
   트레이드오프: <얻는 것 / 잃는 것>
B. <선택지>
   트레이드오프: <얻는 것 / 잃는 것>

잘 모르겠으면 A(추천안)로 진행합니다.
```

## Decision recording (closes the loop)

Every answered question becomes durable state in the same turn:

1. **Primary record**: the OWNING document — architecture → design.md ADR (D-NNN: 맥락/결정/결과), scope/priority → prd.md, goal-level → GOAL.md 제약/범위.
2. **Secondary record**: a `decision` entry in today's log: question, chosen option, who decided (user), date — audit trail, not the lookup source.
3. "추천안으로" answers are recorded identically; a defaulted decision is still a decision.

"Never re-ask" is enforced by checking the DOCUMENTS — agents never read logs in normal work.

## Phase-specific application

| Phase | Typical branch points |
|-------|----------------------|
| goal | 성공 기준의 수준(엄격/실용), 범위 컷 |
| analyze | 조사로 해소 불가한 unknown — 선택지화해서 질문 |
| plan (기획) | 스코프 컷, 우선순위 충돌, 릴리스 슬라이스 크기 |
| plan (설계) | 아키텍처 대안(저장소/통신 방식 등), 비용-성능 트레이드오프, UX 방향(플로우 A/B) |
| build | 계약 공백으로 차단됐고 architect도 답 못 낼 때만 — 옵션 형식으로 에스컬레이션 |
| verify/retro | 질문 없음 (증거 기반 판정 / diff 승인만) |
