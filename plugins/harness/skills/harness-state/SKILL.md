---
name: harness-state
description: 모든 에이전트가 매 디스패치에 여는 공용 계약 — 디렉터리 맵·공용 프로토콜·위키 형식·로그 형식·읽기 예산.
---

# harness-state: the .harness/ directory contract

`.harness/` is the harness's file-system-as-memory; agents are stateless between runs. Four universal rules:

1. Every agent reads `.harness/GOAL.md` and `.harness/wiki/INDEX.md` BEFORE any task, then opens ONLY the wiki nodes matching its own scope plus `global`/`workflow` — never bulk-reads `wiki/`.
2. Results go to files, not just chat — not in `.harness/` (or the codebase) = did not happen.
3. **Destructive git commands are forbidden for every agent**: `git reset` · `git checkout -- <path>` · `git stash` · `git clean` · `git restore`. Undo an experimental edit by REVERSE-EDITING; read past versions via `git show <sha>:<path>`; reproduce old states in an isolated `git worktree add` (remove it after). Agents share one working tree — one agent's reset destroys every sibling's uncommitted work, and untracked files are unrecoverable (로그 참조).

4. **공용 디스패치 프로토콜** — every role agent, every invocation: ①시작 전 `GOAL.md` + `wiki/INDEX.md` 를 읽고 **자기 scope + `global`/`workflow`** 노드만 연다 ②배정된 것만 한다 — 결과·결함은 디스패처에게 **RETURN**, `plan.md`·`state.json` 은 건드리지 않는다(코디네이터 제외) ③**측정 전 원장을 조회하고**(`grep -F '"key":"<명령>@<sha7>"' .harness/measurements.jsonl` — 히트하면 재실행 금지, 값 인용), 새로 측정했으면 원장에 한 줄 append ④끝나면 공용 일간 로그에 result 항목 1건(원장 id + `읽음`) + 얻은 통찰을 wiki 노드로 create/reinforce/promote 하고 그 사실을 같은 항목에 1줄로 적는다. 에이전트 파일은 이 네 가지를 **다시 쓰지 않고** 자기 역할의 델타만 적는다.

All `.harness/` content is Korean; code identifiers, file paths, technical terms as-is. This skill is the SINGLE schema authority for `.harness/` — its section lists and formats override any other file. Scaffolding creates files directly from the section lists below.

## Directory map

| Path | Purpose | Primary writer | Written when |
|------|---------|----------------|--------------|
| `GOAL.md` | Goal, success criteria, constraints, out-of-scope | /harness:goal (with user) | Goal phase; frozen after user confirm (changes = logged human decision) |
| `analysis.md` | Current state, risks, unknowns | analyst | Analyze |
| `prd.md` | Requirements, stories, priorities | planner | Plan |
| `design.md` | Architecture, API/data contracts, UX spec | architect + product-designer | Design; build gated on user approval |
| `plan.md` | Task table: id, owner, deps, acceptance, status | 코디네이터 ONLY | End of plan; status updated through build |
| `state.json` | Machine-readable phase + task state | 코디네이터 (`tasks[]`); commands: `phase`/`approvals`/`verify` | Every phase/task transition |
| `wiki/` | Self-evolving knowledge layer — ONE node (엔티티) per file | any agent (create/reinforce/promote); harness-improver (merge/retire) | Continuously, evidence in hand |
| `wiki/INDEX.md` | One line per living node — the ONLY hot knowledge read | whoever changes a node, same turn | Every node change |
| `logs/YYYY-MM-DD.md` | ONE shared append-only daily log, ALL agents | every agent (append) | Continuously |
| `measurements.jsonl` | 측정·디스패치 원장 (기계 판독, 승계·지표 계수의 유일 출처) | every agent (append 1줄) | 측정할 때마다 · 디스패치 종료 시 |
| `retro/YYYY-MM-DD.md` | Retro report + edit proposals | harness-improver | Retro |
| `logs/archive/` · `measurements.archive.jsonl` · `retro/archive/` | Cold storage: mined logs · rotated ledger rows · past retro reports (legacy playbook/inbox archives 포함) | harness-improver | Retro; never read in normal work |

## 장부·문서 계약은 별도 스킬

`state.json` 스키마·owner enum·문서별 정본 섹션·페이즈 수명주기는 **`harness-ledger`** 스킬이 소유한다. 그 셋을 쓰는 주체(코디네이터·improver)만 읽으면 되고, dev·qa·review 에이전트의 읽기 세트에서는 빠진다.

## wiki/ — the self-evolving knowledge layer

One node = one file = one operational insight (엔티티). This replaces the legacy flat `playbook.md` and `retro/inbox.md` (migration at the end of this section).

File name IS the node's identity: `<scope>--<kebab-slug>.md`, scope from the ONE scope enum: analysis / planning / design / backend / frontend / ai-agent / qa / review / infra / cost / workflow / global. Never reuse a slug. Node format:

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
- **promote (candidate → active)**: any agent, once the node has ≥2 evidence dates from independent tasks — flip `status` in place, remove the INDEX suffix. Promotion does not wait for a retro. **단 승격으로 active 총량(40) 또는 그 scope 상한(8)을 넘기게 되면 candidate 로 유지하고 로그에 「승격 보류(상한)」 1줄만 남긴다** — 자리는 improver 가 은퇴로 만든 뒤에만 승격한다.
- **merge / split / retire**: harness-improver only (at retro, or on demand). Merge = union the evidence into the survivor, add a `links` entry, mark the absorbed node `status: retired` and drop its INDEX line. Retired files STAY in `wiki/` as tombstones — cold storage in place.
- Human approval is NOT required for any wiki edit. It remains required for agent-prompt / command / gate edit proposals (retro), and permission/safety rules stay untouchable.

### Caps (hard)

- active ≤ 40 total AND ≤ 8 per scope — over budget: the improver merges/retires BEFORE anything new is promoted.
- candidate ≤ 15 — over budget: build/verify emit the retro nudge.

**은퇴 순서는 추측이 아니라 측정으로 정한다** — 「저가치」는 판단이라 오래된 노드가 남고 새 학습이 막힌다(실측 2026-08-07: 근거 3건짜리 노드가 `qa` scope 8/8 포화로 승격 보류됐다). 은퇴 후보 순서:
1. **효과 반증** — 열린 상태에서 그 scope 의 `refutes` 가 발생한 노드(원장으로 계수). 노드가 있었는데 막지 못했다는 뜻이다.
2. **효과 미관측** — 5회 이상 열렸으나 그 scope 에서 `refutes` 도 예방 기록도 없는 노드.
3. 그 외 개선자 판단.
**효과가 확인된 노드(열린 goal 에서 그 부류 실패 0)는 은퇴시키지 않는다.** 자리가 없으면 1·2 를 먼저 비운다.

### 노드 효과 계수 (P5 의 유일한 입력)

디스패치 종료 시 원장 `d` 레코드에 **그 세션이 실제로 연 노드 slug 를 적는다**: `"nodes":["qa--x","global--y"]`. 개선자는 이것으로 센다 —
```
열림   = nodes 에 그 slug 를 가진 d 레코드 수
동반실패 = 그중 rework:true 인 d 레코드 수
```
「읽었다」가 아니라 **「열려 있었는데도 실패했는가」**를 센다. 노드가 조언인지 장치인지는 이 비율로만 판별된다.

**이 수치는 지목이지 판결이 아니다** — 귀속이 디스패치 단위라 한 세션에서 여러 노드가 열렸으면 실패 책임이 나뉘지 않는다. 개선자는 이 표로 **조사 순서만** 정하고, 은퇴·수정은 해당 실패의 기전을 확인한 뒤에 한다. 노드 1건에 근거 goal 이 1개뿐이면 아직 데이터가 아니다.

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
- `result` 항목: `- 원장: <id> … · 읽음: INDEX+<scope>` — 측정값 본체는 산문이 아니라 **측정 원장**(다음 절)에 쓰고 여기엔 id 만 적는다. `읽음` 이 비면 위키에 도달하지 않은 것이다. Never edit/delete past entries; corrections = new entries referencing the old one.

## 측정 원장 — `.harness/measurements.jsonl` (append-only, 기계 판독)

산문 로그로는 다음 사람이 「이 명령을 이 sha 에서 이미 돌렸나」를 **조회할 수 없다**. 그래서 같은 측정이 반복된다(실측: 한 goal 에서 전건 pytest 8회·골든 재생성 6회, 승계 규칙이 존재했음에도). 측정값과 디스패치 결과는 **한 줄 JSON** 으로 남긴다.

레코드 2종. 한 줄 = 한 레코드, 필드는 아래가 전부다.
```jsonl
{"t":"m","id":"m-1533-dev","agent":"ai-agent-dev","key":"pytest -q@4394fef","value":"1426 passed, 1 skipped","exit":0}
{"t":"m","id":"m-1602-rev","agent":"code-reviewer","key":"sha256 golden@609faa4","value":"338b6ea7…","exit":0,"refutes":"m-1533-dev"}
{"t":"d","id":"d-1505","agent":"ai-agent-dev","scope":"W1~W6","rework":false,"tokens":244829,"nodes":["qa--zero-baseline-lint-needs-resident-fixture","global--read-before-restructure"]}
```
- `t` — `m` 측정 · `d` 디스패치. `id` — `<t>-<HHMM>-<짧은식별>`, 충돌하면 뒤에 숫자.
- `key` — **`<명령 문자열>@<sha7>`**. 이것이 승계의 유일한 키다.
- `refutes` — 이 레코드가 뒤집은 앞선 레코드의 id(없으면 필드 자체를 생략). qa·code-reviewer 가 재측정해 다른 값이 나오거나 결함을 실증하면 **반드시** 채운다.
- `rework` — 그 디스패치가 재작업(재개·재브리프)을 유발했으면 `true`.
  **브리프 전제(사실·인과 가설·해법 지정)가 반증돼 산출 0 으로 닫힌 디스패치도 `rework:true` 다** — 「blocked 로 잘 닫았다」는 에이전트의 정확한 행동이지만, 왕복 1회는 이미 소비됐고 원인은 브리프에 있다. `scope` 끝에 `(전제반증)` 을 붙여 재작업형과 구분한다. 이 구분이 없으면 M2 가 100% 로 나오면서 회고가 매번 같은 패턴을 산문에서만 발견한다. **주의**: 이 정의 변경은 M2 기준선을 이동시키므로 적용 goal 의 결산에 「M2 정의 변경」을 병기하고, 적용 전후 값을 직접 비교하지 않는다.
- `nodes` — 그 세션이 실제로 **연** 위키 노드 slug 배열(§노드 효과 계수). 안 열었으면 `[]`.

**승계 규칙(장치)** — 측정 전에 **먼저 조회한다**:
```
grep -F '"key":"<명령>@<sha7>"' .harness/measurements.jsonl
```
히트가 있고 그 트리에 이후 커밋이 없으면 **재실행하지 않고 그 값을 인용**한다. 재실행 의무는 셋뿐 — ①히트 없음 ②이후 커밋 존재 ③red 이력 없는 회귀 pin(goal 당 표본 1건만 격리 worktree 재현).

**추가는 한 줄이다** — 부담이 커지면 아무도 안 쓴다:
```
echo '{"t":"m","id":"...","agent":"...","key":"...","value":"...","exit":0}' >> .harness/measurements.jsonl
```

**품질 지표 자동 계수**(하네스 `docs/GOAL.md` M1·M2·M5) — goal 종결 시 결산에 값으로 기재:
```
M1 자기보고 정확도 = 1 − (refutes 필드를 가진 m 레코드 수 ÷ 전체 m 레코드 수)
M2 1회 통과율      = (rework:false 인 d 레코드 수) ÷ (전체 d 레코드 수)
M5 비용 비례       = (d 레코드 tokens 합) ÷ (변경 소스 파일 수, 테스트·픽스처·문서 제외)
```
원장이 비어 있으면 그 goal 의 M1·M2·M5 는 **미측정**이지 100% 가 아니다 — 결산에 그렇게 적는다.

- `HH:MM` is the wall-clock time AT WRITE TIME — run `date +%H:%M` and copy its output; never reuse the dispatch prompt's time, estimate, or write placeholders (`15:__`, `13:2x`).
- Readers (gates, status, retro mining) treat APPEND ORDER as the authoritative sequence; header times are informational and may lag when an agent finishes late.

## Context budget (token control — hard rules)

The harness must get smarter WITHOUT per-task context growing; learning lives in the fixed-budget wiki (caps above).

0-a. **스킬은 통째로 읽지 않는다** — `grep -n '^## ' <스킬>` 로 목차를 얻고 필요한 섹션만 offset 으로 읽는다. 스킬은 레시피북이고 한 태스크에 필요한 레시피는 1~2개다.
0. **1회 디스패치 읽기 예산 ≤3,500단어** — 에이전트 파일 + 도메인 스킬 **1개** + 이 공용 스킬. 초과 시 절단 순서: ①사건 서사를 위키 노드·로그 날짜 참조로 강등 ②1디스패치 1스킬(둘째 스킬 금지) ③스킬을 청중 기준 분할 ④태스크 분할. **예외는 코디네이터 하나** — 장부 소유자라 `harness-ledger` 를 함께 읽는다.
1–2. **Wiki reads are INDEX-driven, node text stays compressed**: read `wiki/INDEX.md` (≤80 lines), open only own-scope + `global`/`workflow` nodes (≤10 lines each); never bulk-read `wiki/`, never quote other scopes' nodes. Reinforcement sharpens wording, never appends narrative — incident stories live in the daily log, referenced by date.
3. **Fixed read-set per task**: GOAL.md + wiki/INDEX.md + own-scope nodes + own plan.md task row + documents the role owns/consumes (e.g. dev → design.md) + **`measurements.jsonl` 을 `grep -F` 키 조회로만**(통독 금지 — 승계 판정에 필요한 것은 그 키의 히트 여부뿐이다). NEVER read `logs/`, `retro/`, or archives in normal work — past decisions live in the owning DOCUMENTS (design.md ADR / prd.md / GOAL.md), never mined from logs.
4–5. **Logs write-heavy read-rarely · Archives = cold storage**: only harness-improver reads logs (newer than the last retro report), then rotates them to `logs/archive/`; `/harness:status` reads only today's log; archives are read only when a human asks.
6. **Every document is capped, not just the playbook**: analysis.md ≤ 80 lines · prd.md ≤ 100 · design.md ≤ 150 · GOAL.md ≤ 80. Documents carry CONCLUSIONS + file:line references; raw evidence (command output, matrices, reproduction transcripts) goes to the daily log, referenced by date. A document over budget is a defect the owner must compress before handoff (로그 참조).
7. **Task outputs never append to phase documents**: a task's findings go to the log (+ a one-line conclusion with an F-NNN update if it changes a fact). Appending task appendices to analysis.md/design.md is how documents bloat past their caps.
8. **1회 디스패치 산출 예산 — 증거의 양이 아니라 서식을 조인다**: 증거 전문(표·덤프·재현 로그)은 파일로 남기고 경로·원장 id 로 인용한다. **RETURN 보고 ≤40줄 · 로그 result 항목 ≤20줄**, 문서는 §6 상한 — 브리프가 값을 지정하면 그것이 계약, 미지정이면 이것이 기본값이다. 디스패치 종료 시 `d.tokens` > **250k** 면 로그에 「산출 예산 초과: <사유 1줄>」을 남긴다 (실측 2026-08-20: 55건 평균 149k·최대 530k, qa 97k·architect 86k 는 이미 성립 — 초과분의 지배 항은 보고·표 산문이었다).
