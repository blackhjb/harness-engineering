---
name: harness-state
description: 모든 에이전트의 공용 계약 — .harness/ 디렉터리 맵, 공용 디스패치 프로토콜, 위키 노드 형식·수명·상한, 로그 형식, 컨텍스트 예산. .harness/ 아래를 읽거나 쓰는 모든 에이전트가 읽는다. state.json 스키마·문서별 정본 섹션·페이즈 수명주기는 `harness-ledger` 가 소유한다.
---

# harness-state: the .harness/ directory contract

`.harness/` is the harness's file-system-as-memory; agents are stateless between runs. Four universal rules:

1. Every agent reads `.harness/GOAL.md` and `.harness/wiki/INDEX.md` BEFORE any task, then opens ONLY the wiki nodes matching its own scope plus `global`/`workflow` — never bulk-reads `wiki/`.
2. Results go to files, not just chat — not in `.harness/` (or the codebase) = did not happen.
3. **Destructive git commands are forbidden for every agent**: `git reset` · `git checkout -- <path>` · `git stash` · `git clean` · `git restore`. Undo an experimental edit by REVERSE-EDITING; read past versions via `git show <sha>:<path>`; reproduce old states in an isolated `git worktree add` (remove it after). Agents share one working tree — one agent's reset destroys every sibling's uncommitted work, and untracked files are unrecoverable (로그 참조).

4. **공용 디스패치 프로토콜** — every role agent, every invocation: ①시작 전 `GOAL.md` + `wiki/INDEX.md` 를 읽고 **자기 scope + `global`/`workflow`** 노드만 연다 ②배정된 것만 한다 — 결과·결함은 디스패처에게 **RETURN**, `plan.md`·`state.json` 은 건드리지 않는다(orchestrator 제외) ③끝나면 공용 일간 로그에 result 항목 1건(증거 값 포함) + 얻은 통찰을 wiki 노드로 create/reinforce/promote 하고 그 사실을 같은 항목에 1줄로 적는다. 에이전트 파일은 이 세 가지를 **다시 쓰지 않고** 자기 역할의 델타만 적는다.

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
| `wiki/` | Self-evolving knowledge layer — ONE node (엔티티) per file | any agent (create/reinforce/promote); harness-improver (merge/retire) | Continuously, evidence in hand |
| `wiki/INDEX.md` | One line per living node — the ONLY hot knowledge read | whoever changes a node, same turn | Every node change |
| `logs/YYYY-MM-DD.md` | ONE shared append-only daily log, ALL agents | every agent (append) | Continuously |
| `retro/YYYY-MM-DD.md` | Retro report + edit proposals | harness-improver | Retro |
| `logs/archive/`, `retro/*archive*` | Cold storage: mined logs, legacy playbook/inbox archives | harness-improver | Retro; never read in normal work |

## 장부·문서 계약은 별도 스킬

`state.json` 스키마·owner enum·문서별 정본 섹션·페이즈 수명주기는 **`harness-ledger`** 스킬이 소유한다. 그 셋을 쓰는 주체(orchestrator·커맨드·improver)만 읽으면 되고, dev·qa·review 에이전트의 읽기 세트에서는 빠진다.

## wiki/ — the self-evolving knowledge layer

One node = one file = one operational insight (엔티티). This replaces the legacy flat `playbook.md` and `retro/inbox.md` (migration at the end of this section).

File name IS the node's identity: `<scope>--<kebab-slug>.md`, scope from the ONE scope enum: analysis / planning / design / backend / frontend / ai-agent / qa / review / sre / cost / workflow / global. Never reuse a slug. Node format:

```
---
scope: qa                          # exactly one scope from the enum
status: active                     # candidate | active | retired
evidence: 2026-08-03, 2026-08-04   # dates the pattern was observed — append-only
links: [qa--other-node]            # related nodes; a link to a not-yet-written node marks future work, not an error
source: PB-003                     # optional: provenance (legacy bullet ID, task ID, retro date)
---
운영 규칙 1–3줄 (when Y, do X — 한국어, 코드 식별자는 원문).
근거 1–2줄: 날짜 + 사건 한 줄. 반례·미탐 형태가 있으면 함께 적는다.
```

Body cap: 10 lines. Nodes are operational ("when Y, do X"); truisms are banned — every node taxes every future agent that opens it.

### INDEX.md — the single hot read

One line per candidate/active node (retired nodes are dropped from INDEX):

```
- [scope] [[slug]] — 한 줄 훅 (candidate)
```

Status suffix `(candidate)` only while candidate; active lines carry no suffix. INDEX cap: 80 lines. The hook line must let an agent decide open/skip without opening the node.

### Node lifecycle — the always-on evolution loop (no human gate)

- **create (candidate)**: ANY agent, immediately after a failure, surprising success, or refuted assumption — write the node AND its INDEX line in the same turn. Check INDEX for an existing node covering the pattern FIRST; if one exists, reinforce it instead of creating a near-duplicate.
- **reinforce**: on re-observing an existing node's pattern, append the evidence date; sharpen the rule text if the new case narrows or extends it (keep the sharper wording, never append prose).
- **promote (candidate → active)**: any agent, once the node has ≥2 evidence dates from independent tasks — flip `status` in place, remove the INDEX suffix. Promotion does not wait for a retro.
- **merge / split / retire**: harness-improver only (at retro, or on demand). Merge = union the evidence into the survivor, add a `links` entry, mark the absorbed node `status: retired` and drop its INDEX line. Retired files STAY in `wiki/` as tombstones — cold storage in place.
- Human approval is NOT required for any wiki edit. It remains required for agent-prompt / command / gate edit proposals (retro), and permission/safety rules stay untouchable.

### Caps (hard)

- active ≤ 40 total AND ≤ 8 per scope — over budget: the improver merges/retires lowest-value nodes BEFORE anything new is promoted.
- candidate ≤ 15 — over budget: build/verify emit the retro nudge.

## Log format (logs/YYYY-MM-DD.md, append-only)

ONE shared file per day for ALL agents — NO per-agent/per-task logs; "today's log" = this file. Writer = the `[agent-name]` in each entry header; commands use the command name there (e.g. `## HH:MM [goal] goal-set`).

```
## HH:MM [agent-name] event-type
- 내용: what happened, in Korean
- 증거: command run + result excerpt, or file paths (required for result/verify events)
```

Event types: `session-start`, `decision`, `dispatch`, `result`, `failure`, `gate`, `escalation`, `verify`, `goal-set`, `retro-complete`, `wiki`.

**필수 필드 2종(이것 말고 더 만들지 않는다)**
- `dispatch` 항목: `- 계기: 인수조건 N/8 · 브리프 L/20 · 계약근거 design §5 L<n>` — 셋 다 값이다. 상한 초과면 디스패치하지 말고 쪼갠다.
- `result` 항목: `- 측정[<명령>@<sha7>]: <값> · 읽음: INDEX+<scope>` — 측정 키가 같고 sha 가 같으면 **다음 사람은 재실행하지 않고 이 값을 인용한다**. `읽음` 이 비면 위키에 도달하지 않은 것이다. Never edit/delete past entries; corrections = new entries referencing the old one.

- `HH:MM` is the wall-clock time AT WRITE TIME — run `date +%H:%M` and copy its output; never reuse the dispatch prompt's time, estimate, or write placeholders (`15:__`, `13:2x`).
- Readers (gates, status, retro mining) treat APPEND ORDER as the authoritative sequence; header times are informational and may lag when an agent finishes late.

## Context budget (token control — hard rules)

The harness must get smarter WITHOUT per-task context growing; learning lives in the fixed-budget wiki (caps above).

0. **1회 디스패치 읽기 예산 ≤3,500단어** — 에이전트 파일 + 도메인 스킬 **1개** + 이 공용 스킬. 초과 시 절단 순서: ①사건 서사를 위키 노드·로그 날짜 참조로 강등 ②1디스패치 1스킬(둘째 스킬 금지) ③스킬을 청중 기준 분할 ④태스크 분할. **예외는 `orchestrator` 하나** — 장부 소유자라 `harness-ledger` 를 함께 읽는다.
1. **Wiki reads are INDEX-driven**: read `wiki/INDEX.md` (≤80 lines), open only own-scope + `global`/`workflow` nodes (≤10 lines each). Never bulk-read `wiki/`; never quote other scopes' nodes into outputs.
2. **Node text stays compressed**: reinforcement sharpens wording, it never appends narrative. Incident stories belong in the daily log, referenced from the node by date.
3. **Fixed read-set per task**: GOAL.md + wiki/INDEX.md + own-scope nodes + own plan.md task row + documents the role owns/consumes (e.g. dev → design.md). NEVER read `logs/`, `retro/`, or archives in normal work — past decisions live in the owning DOCUMENTS (design.md ADR / prd.md / GOAL.md), never mined from logs.
4. **Logs: write-heavy, read-rarely**: only harness-improver reads them (only newer than the last retro report), then moves them to `logs/archive/`. `/harness:status` reads only today's log.
5. **Archives = cold storage**: read only when a human asks.
6. **Every document is capped, not just the playbook**: analysis.md ≤ 80 lines · prd.md ≤ 100 · design.md ≤ 150 · GOAL.md ≤ 80. Documents carry CONCLUSIONS + file:line references; raw evidence (command output, matrices, reproduction transcripts) goes to the daily log, referenced by date. A document over budget is a defect the owner must compress before handoff (로그 참조).
7. **Task outputs never append to phase documents**: a task's findings go to the log (+ a one-line conclusion with an F-NNN update if it changes a fact). Appending task appendices to analysis.md/design.md is how documents bloat past their caps.
