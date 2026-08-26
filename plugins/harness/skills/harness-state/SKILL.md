---
name: harness-state
description: 모든 에이전트가 매 디스패치에 여는 공용 계약 — 디렉터리 맵·공용 프로토콜·위키 형식·로그 형식·읽기 예산.
---

# harness-state: the .harness/ directory contract

`.harness/` is the harness's file-system-as-memory; agents are stateless between runs. Four universal rules:

1. Every agent reads `.harness/GOAL.md` and `.harness/wiki/INDEX.md` BEFORE any task, then opens ONLY the wiki nodes matching its own scope plus `global`/`workflow` — never bulk-reads `wiki/`.
2. Results go to files, not just chat — not in `.harness/` (or the codebase) = did not happen.
3. **Destructive git commands are forbidden for every agent**: `git reset` · `git checkout -- <path>` · `git stash` · `git clean` · `git restore`. Undo an experimental edit by REVERSE-EDITING; read past versions via `git show <sha>:<path>`; reproduce old states in an isolated `git worktree add` (remove it after). Agents share one working tree — one agent's reset destroys every sibling's uncommitted work, and untracked files are unrecoverable (로그 참조).

4. **공용 디스패치 프로토콜** — every role agent, every invocation: ①시작 전 `GOAL.md` + `wiki/INDEX.md` 를 읽고 **자기 scope + `global`/`workflow`** 노드만 연다 ②배정된 것만 한다 — 결과·결함은 디스패처에게 **RETURN**, `plan.md`·`state.json` 은 건드리지 않는다(코디네이터 제외) ③**측정 전 원장을 조회하고**(§측정 원장 §승계 규칙 — 히트하면 재실행 금지, 값 인용), 새로 측정했으면 원장에 한 줄 append ④끝나면 공용 일간 로그에 result 항목 1건(원장 id + `읽음`) + 얻은 통찰을 wiki 노드로 create/reinforce/promote 하고 그 사실을 같은 항목에 1줄로 적는다. 에이전트 파일은 이 네 가지를 **다시 쓰지 않고** 자기 역할의 델타만 적는다.

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
| `logs/archive/` · `measurements.archive.jsonl` · `retro/archive/` | Cold storage: mined logs · rotated ledger rows · past retro reports | harness-improver | Retro; never read in normal work |

## 장부·문서 계약은 별도 스킬

`state.json` 스키마·owner enum·문서별 정본 섹션·페이즈 수명주기는 **`harness-ledger`** 스킬이 소유한다. 그 셋을 쓰는 주체(코디네이터·improver)만 읽으면 되고, dev·qa·review 에이전트의 읽기 세트에서는 빠진다.

## wiki/ — the self-evolving knowledge layer

One node = one file = one operational insight (엔티티).

File name IS the node's identity: `<scope>--<kebab-slug>.md`, scope from the ONE scope enum: analysis / planning / design / backend / frontend / ai-agent / qa / review / infra / cost / workflow / global. Never reuse a slug. Node format:

```
---
scope: qa                          # exactly one scope from the enum
status: active                     # candidate | active | retired
evidence: 2026-08-03, 2026-08-04   # dates the pattern was observed — append-only
links: [qa--other-node]            # related nodes; a link to a not-yet-written node marks future work, not an error
source: T-014                      # optional: provenance (task ID, retro date)
---
운영 규칙 1–3줄 (when Y, do X — 한국어, 코드 식별자는 원문).
근거 1–2줄: 날짜 + 사건 한 줄. 반례·미탐 형태가 있으면 함께 적는다.
```

Body cap: **10 lines · 200 words · 날짜 인용 ≤2** (셋 다). 줄 수만 재면 한 줄이 200단어로 자란다. Nodes are operational ("when Y, do X"); truisms are banned — every node taxes every future agent that opens it.
**상한 초과는 회고가 값으로 잡는다**(`awk` 본문 줄 수 · 날짜 계수) — 초과 노드는 압축하거나 은퇴시키기 전까지 **강화(reinforce) 금지**다. 사건 전말이 노드 안에서 자라면 그 노드는 술어를 잃고, 열려 있어도 실패를 막지 못한다.
**단 「강화 금지」가 보류로 끝나면 그 사건의 교훈은 어디에도 남지 않는다** — 강화하려던 노드가 상한 초과면 그 자리에서 **압축이 강화의 일부**다: 넣을 절과 **같은 분량 이상**의 기존 서사(날짜 인용·사건 전말)를 지우고 전후 `wc -w` 두 값을 로그에 적는다. 압축이 그 디스패치의 범위를 넘으면 **노드를 건드리지 말고 로그 result 에 「압축 대기: <노드 slug> · <넣을 규칙 1줄>」을 남긴다** — 회고는 이 줄을 압축 대기열로 읽는다(실측 2026-08-26: 이 줄이 없어 공유 트리 사고 교훈이 회고 전까지 미기록).
개선자는 매 회고에 **상한 초과 노드 수를 보고서 실행 요약에 값으로** 적고(전·후), 그중 **`global`/`workflow` scope 를 우선 압축**한다 — 이 둘은 모든 에이전트의 읽기 세트라 초과분이 디스패치 수만큼 곱해진다.

### INDEX.md — the single hot read

One line per candidate/active node (retired nodes are dropped from INDEX):

```
- [scope] [[slug]] — 한 줄 훅 (candidate)
```

Status suffix `(candidate)` only while candidate; active lines carry no suffix. INDEX cap: 80 lines. The hook line must let an agent decide open/skip without opening the node.

### Node lifecycle — the always-on evolution loop (no human gate)

- **create (candidate)**: ANY agent, immediately after a failure, surprising success, or refuted assumption — write the node AND its INDEX line in the same turn. Check INDEX for an existing node covering the pattern FIRST; if one exists, reinforce it instead of creating a near-duplicate.
- **reinforce**: on re-observing an existing node's pattern, append the evidence date; sharpen the rule text if the new case narrows or extends it (keep the sharper wording, never append prose). **본문 단어 수 순증은 0 이다** — 새 절을 넣으려면 같은 분량의 기존 절을 지우고, 전후 `wc -w` 두 값을 로그 result 에 1줄로 적는다. 지울 것을 못 고르면 그 노드는 이미 둘이므로 분할하거나 신규 노드를 만든다. 이 규약 아래서 **상한 초과 노드의 강화는 곧 압축**이라 동결이 발생하지 않는다.
- **promote (candidate → active)**: any agent, once the node has ≥2 evidence dates from independent tasks — flip `status` in place, remove the INDEX suffix. Promotion does not wait for a retro. **단 승격으로 active 총량(40) 또는 그 scope 상한(8)을 넘기게 되면 candidate 로 유지하고 로그에 「승격 보류(상한)」 1줄만 남긴다** — 자리는 improver 가 은퇴로 만든 뒤에만 승격한다.
- **merge / split / retire**: harness-improver only (at retro, or on demand). Merge = union the evidence into the survivor, add a `links` entry, mark the absorbed node `status: retired` and drop its INDEX line. Retired files STAY in `wiki/` as tombstones — cold storage in place.
- Human approval is NOT required for any wiki edit. It remains required for agent-prompt / command / gate edit proposals (retro), and permission/safety rules stay untouchable.

### Caps (hard)

- active ≤ 40 total AND ≤ 8 per scope — over budget: the improver merges/retires BEFORE anything new is promoted.
- candidate ≤ 15 — over budget: build/verify emit the retro nudge.
- **계수는 INDEX 가 아니라 노드 파일의 `status:` 로 낸다** — `grep -l "^status: candidate" .harness/wiki/*.md | wc -l` · `grep -l "^status: active" .harness/wiki/*.md | wc -l` · scope 별은 `| cut -d- -f1 | sort | uniq -c`. INDEX 를 grep 하면 형식 주석 1행과 승격 후 미제거 접미사가 함께 세어져 **상시 과대**다(실측 2026-08-25: 실측 14 를 17 로 읽어 세 세션이 노드 생성을 보류했고, 같은 결손으로 active 41/40 승격이 통과했다).

**은퇴 순서·노드 효과 계수는 `harness-ledger` §위키 큐레이션 계수** 소관이다(집행 주체 = harness-improver). 여기서는 상한만 안다.

## Log format (logs/YYYY-MM-DD.md, append-only)

ONE shared file per day for ALL agents — NO per-agent/per-task logs; "today's log" = this file. Writer = the `[agent-name]` in each entry header; commands use the command name there (e.g. `## HH:MM [goal] goal-set`).

```
## HH:MM [agent-name] event-type
- 내용: what happened, in Korean
- 증거: command run + result excerpt, or file paths (required for result/verify events)
```

Event types: `session-start`, `decision`, `dispatch`, `result`, `failure`, `gate`, `escalation`, `verify`, `goal-set`, `retro-complete`, `wiki`.

- `HH:MM` is the wall-clock time AT WRITE TIME — run `date +%H:%M` and copy its output; never reuse the dispatch prompt's time, estimate, or write placeholders (`15:__`, `13:2x`).
- Readers (gates, status, retro mining) treat APPEND ORDER as the authoritative sequence; header times are informational and may lag when an agent finishes late.

**필수 필드 2종(이것 말고 더 만들지 않는다)**
- `dispatch` 항목: `- 계기: 인수조건 N/8 · 브리프 L/20 · 계약근거 design §5 L<n>` — 셋 다 값이다. 상한 초과면 디스패치하지 말고 쪼갠다.
- `result` 항목: `- 원장: <id> @행<N> · 읽음: INDEX+<scope>` — 측정값 본체는 산문이 아니라 **측정 원장**(다음 절)에 쓰고 여기엔 id 와 행 수만 적는다. **`N` 은 append 직후의 `wc -l < .harness/measurements.jsonl` 이고 append 없이는 증가하지 않는다** — 연속한 두 result 항목의 `N` 이 같으면 결손이 그 자리에서 드러난다. 「적는 턴에 grep 하라」는 문장형 조항은 3회 연속 재발했다(로그 2026-08-20·24·25; 실측 2026-08-25: 인용 447건 중 77건 미실재). 다건이면 `원장: <id> · <id>… · @행<N>` — `@행` 은 **항목당 1회, 맨 뒤에 ` · ` 로 접합**한다(id 에 공백 접합하면 분할 소비자가 마지막 id 를 놓친다). id 대조는 `grep -c -F '<id>'`. **결손 진단의 분모는 인용 목록이 아니라 원장 전체다.** `읽음` 이 비면 위키에 도달하지 않은 것이다. Never edit/delete past entries; corrections = new entries referencing the old one.

## 측정 원장 — `.harness/measurements.jsonl` (append-only, 기계 판독)

산문으로는 「이 명령을 이 sha 에서 이미 돌렸나」를 조회할 수 없어 같은 측정이 반복된다 (로그 참조). 측정값과 디스패치 결과는 **한 줄 JSON** 으로 남긴다. 레코드 2종, 한 줄 = 한 레코드, 필드는 아래가 전부다.
```jsonl
{"t":"m","id":"m-1533-dev","agent":"ai-agent-dev","key":"pytest -q@4394fef","value":"1426 passed, 1 skipped","exit":0}
{"t":"m","id":"m-1602-rev","agent":"code-reviewer","key":"sha256 golden@609faa4","value":"338b6ea7…","exit":0,"refutes":"m-1533-dev"}
{"t":"d","id":"d-1505","agent":"ai-agent-dev","scope":"W1~W6","rework":false,"cause":null,"tokens":244829,"nodes":["qa--zero-baseline-lint-needs-resident-fixture","global--read-before-restructure"]}
```
- `t` — `m` 측정 · `d` 디스패치. `id` — `<t>-<HHMM>-<짧은식별>`, 충돌하면 뒤에 숫자.
- `key` — **`<복사해 실행 가능한 명령 문자열>@<sha7>@<env>`**. 이것이 승계의 유일한 키다. **`<env>` 는 그 측정을 낸 인터프리터·환경 식별자**(conda env 이름·venv 경로·`python -V` 중 하나)이며, 실행 환경에 의존하는 측정(pytest·import·모델 로드·정적 스캔) 전건에 **필수**다 — 없으면 그 행은 승계 대상이 아니고 인용도 불가다. 환경 무관 측정(`git grep`·`git diff`)은 `@<sha7>` 까지로 충분하다. **같은 명령·같은 sha 도 인터프리터가 다르면 다른 값이다** (로그 2026-08-24, wiki `global--baseline-provenance-and-interpreter`).
- `refutes` — 이 레코드가 뒤집은 앞선 레코드의 id(없으면 필드 자체를 생략). qa·code-reviewer 가 재측정해 다른 값이 나오거나 결함을 실증하면 **반드시** 채운다.
- `agent` — **에이전트 정의의 `name` 을 그대로 쓴다**(디스패처는 `코디네이터` 로 고정). 같은 역할을 두 표기로 적으면 역할별 집계가 조용히 갈라진다 (실측 2026-08-25: 한 원장에 `coordinator`/`코디네이터` 혼재).
- `tokens` — **`d` 는 왕복 1건당 1행이고 작성자는 그 왕복을 수행한 세션이다.** 디스패처가 위임 왕복의 행을 대신 쓰면 M2 분모가 부푼다(실측 2026-08-25: 코디네이터 `d` 15건 중 14건 null/0). **위임 `d` 는 null·0 금지** — 디스패처는 위임 세션의 토큰을 모르므로 그 행을 쓸 수 없다. 코디네이터가 **직접 수행한** 배치는 자신이 수행 세션이므로 자기 `d` 를 쓰고 `tokens` 는 `null` 로 둔다(자기 토큰은 세션 종료 전 알 수 없다) — M6 분모가 이 행들이다.
**토큰 수를 읽을 수 없는 세션은 `d` 행을 생략하지 말고 `"tokens":"unknown"` 으로 적는다** — 행 자체가 없으면 M2·M6 의 **분모**까지 사라져 실패한 디스패치가 성공률에서 조용히 빠진다(실측 2026-08-25: analyst 가 null 금지 조항 때문에 `d` 행을 통째로 안 씀). `"unknown"` 은 M5 분자에서만 제외되고 M2·M6 분모에는 남는다. 로그 result 에 「tokens 미확인: <사유 1줄>」을 병기한다. **`"unknown"` 이 쓰인 디스패치는 디스패처가 보정 `m` 행을 append 한다** — 서브에이전트 토큰이 보이는 주체는 완료 알림을 받는 디스패처뿐이다. 형식: `{"t":"m","id":"m-<HHMM>-coord-tokens","agent":"coordinator","key":"Task 완료 알림 subagent tokens@<sha7>","value":{"<d-id>":<정수>,...}}`. **M5 분자는 이 행 또는 `d.tokens` 정수에서만 온다 — 결산 산문에 적힌 정수는 분자가 아니다.** 보정 행이 없으면 M5 는 「미측정(위임 d <n>건 unknown)」으로 적는다 (2026-08-26: 위임 3/3 unknown, 결산의 569,582 가 원장 밖이라 재현 불가).
- `rework` — 그 디스패치가 재작업(재개·재브리프)을 유발했으면 `true`. **`true` 면 `cause` 를 함께 적는다**: `brief`(브리프 전제·처방 오류) · `design`(설계 결함) · `agent`(집행 오류) · `env`(환경·도구). 산문으로 「원인은 …」이라고 적어도 계수되지 않는다 — 값이어야 회고가 분포를 낸다. **브리프 전제가 반증돼 산출 0 으로 닫힌 디스패치도 `true`/`cause:brief` 다** — blocked 로 잘 닫는 것은 에이전트의 정확한 행동이지만 왕복 1회는 이미 소비됐고 원인은 브리프에 있다.
- `nodes` — 그 세션이 실제로 **연** 위키 노드 slug 배열. 안 열었으면 `[]` (계수는 `harness-ledger` §노드 효과 계수).

**승계 규칙(장치)** — 측정 전에 **먼저 조회한다**. 패턴은 **키 값만** 쓴다(`"key":` 를 붙이면 `json.dumps` 의 콜론 뒤 공백 때문에 영구 미검출):
```
grep -F '<명령>@<sha7>@<env>' .harness/measurements.jsonl
```
id 대조도 `grep -c -F '<id>'`. 히트가 있고 그 트리에 이후 커밋이 없으면 **재실행하지 않고 인용**한다. 재실행 의무는 넷 — ①히트 없음 ②이후 커밋 존재 ③red 이력 없는 회귀 pin(goal 당 1건 격리 worktree) ④**키의 `<env>` 가 지금 쓰는 환경과 다름**. 이 넷이 승계의 정본이고, 커맨드·에이전트 파일은 여기를 가리킬 뿐 다시 적지 않는다. **재실행할 때는 명령을 새로 타이핑하지 말고 히트 레코드 `key` 의 `@` 앞 명령 문자열을 그대로 복사해 실행한다** — 키의 `<env>` 가 인터프리터 절대경로라 복사하면 셸 기본값(homebrew `python3`)으로 낙하하는 경로가 구조적으로 사라진다. 노드를 열어 두는 것만으로는 같은 오사용이 2회 났다(로그 2026-08-24·25).

**추가는 한 줄이다** — 부담이 커지면 아무도 안 쓴다:
```
echo '{"t":"m","id":"...","agent":"...","key":"...","value":"...","exit":0}' >> .harness/measurements.jsonl
```

## Context budget (token control — hard rules)

The harness must get smarter WITHOUT per-task context growing; learning lives in the fixed-budget wiki (caps above).

0-a. **스킬은 통째로 읽지 않는다** — `grep -n '^## ' <스킬>` 로 목차를 얻고 필요한 섹션만 offset 으로 읽는다. 스킬은 레시피북이고 한 태스크에 필요한 레시피는 1~2개다.
0. **1회 디스패치 읽기 예산 ≤3,500단어** — 에이전트 파일 + 도메인 스킬 **1개** + 이 공용 스킬. 초과 시 절단 순서: ①사건 서사를 위키 노드·로그 날짜 참조로 강등 ②1디스패치 1스킬(둘째 스킬 금지) ③스킬을 청중 기준 분할 ④태스크 분할. **예외는 코디네이터 하나** — 장부 소유자라 `harness-ledger` 를 함께 읽는다.
1–2. **Wiki reads are INDEX-driven, node text stays compressed**: read `wiki/INDEX.md` (≤80 lines), open only own-scope + `global`/`workflow` nodes (≤10 lines each); never bulk-read `wiki/`, never quote other scopes' nodes. Reinforcement sharpens wording, never appends narrative — incident stories live in the daily log, referenced by date.
3. **Fixed read-set per task**: GOAL.md + wiki/INDEX.md + own-scope nodes + own plan.md task row + documents the role owns/consumes (e.g. dev → design.md) + **`measurements.jsonl` 을 `grep -F` 키 조회로만**(통독 금지 — 승계 판정에 필요한 것은 그 키의 히트 여부뿐이다). NEVER read `logs/`, `retro/`, or archives in normal work — past decisions live in the owning DOCUMENTS (design.md ADR / prd.md / GOAL.md), never mined from logs.
4–5. **Logs write-heavy read-rarely · Archives = cold storage**: only harness-improver reads logs (newer than the last retro report), then rotates them to `logs/archive/`; `/harness:status` reads only today's log; archives are read only when a human asks.
6. **Every document is capped**: analysis.md ≤ 80 lines · prd.md ≤ 100 · design.md ≤ 150 · GOAL.md ≤ 80. Documents carry CONCLUSIONS + file:line references; raw evidence (command output, matrices, reproduction transcripts) goes to the daily log, referenced by date. A document over budget is a defect the owner must compress before handoff (로그 참조).
7. **Task outputs never append to phase documents**: a task's findings go to the log (+ a one-line conclusion with an F-NNN update if it changes a fact). Appending task appendices to analysis.md/design.md is how documents bloat past their caps.
8. **1회 디스패치 산출 예산 — 증거의 양이 아니라 서식을 조인다**: 증거 전문(표·덤프·재현 로그)은 파일로 남기고 경로·원장 id 로 인용한다. **RETURN 보고 ≤40줄 · 로그 result 항목 ≤20줄**, 문서는 §6 상한 — 브리프가 값을 지정하면 그것이 계약, 미지정이면 이것이 기본값이다. 디스패치 종료 시 `d.tokens` > **250k** 면 로그에 「산출 예산 초과: <사유 1줄>」을 남긴다 — 초과분의 지배 항은 보고·표 산문이다 (로그 2026-08-20).
