#!/usr/bin/env python3
"""tools/check-canon.py — 지침 정합성 검사기.

설계: docs/CONSISTENCY-CHECK-2026-08-25.md

원리 셋:
  1. 낱말이 아니라 「해석 가능한 참조」를 검사한다 (은퇴 기록 서술은 오탐이 아니다).
  2. 모순을 찾지 말고 중복을 금지한다 — 정본 1곳 + 나머지는 포인터.
  3. 검사기 자신도 red 증명을 가진다 — `--against 68ff0ef`.

의존성 0 (python3 stdlib 전용). 트리를 변경하지 않는다.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# 스캔 대상 = 살아있는 지침면. 날짜 붙은 문서(`*-YYYY-MM-DD.md`)는 역사 기록이라 제외한다.
SCAN_DIRS = ["plugins/harness/agents", "plugins/harness/commands", "plugins/harness/skills"]
SCAN_FILES = ["README.md", "AGENTS.md", "docs/ARCHITECTURE.md", "docs/GOAL.md", "docs/PROCESS.md"]
DATED = re.compile(r"-\d{4}-\d{2}-\d{2}\.md$")

# §참조가 런타임 산출물(.harness/)을 가리키는 경우 — 레포에 없는 게 정상이다.
RUNTIME_DOCS = ("design", "GOAL", "prd", "analysis", "plan", "state.json", "1-B", "1-C", "9", "0")


# ───────────────────────────────────────────────────────── 최소 YAML 파서
def parse_canon(text):
    """이 스키마 전용 최소 파서: 최상위 매핑 리스트, 스칼라 + 인라인 리스트."""
    entries, cur = [], None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = raw.lstrip()
        if stripped.startswith("- "):
            cur = {}
            entries.append(cur)
            stripped = stripped[2:]
        elif cur is None:
            raise SystemExit(f"canon.yaml: 최상위 항목 밖의 줄 — {raw!r}")
        key, _, val = stripped.partition(":")
        key, val = key.strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        if val.startswith("[") and val.endswith("]"):
            val = [x.strip() for x in val[1:-1].split(",") if x.strip()]
        cur[key] = val
    return entries


# ───────────────────────────────────────────────────────── 트리 사실 수집
class Tree:
    def __init__(self, root):
        self.root = root
        self.skills = sorted(
            d for d in os.listdir(self.p("plugins/harness/skills"))
            if os.path.isdir(self.p("plugins/harness/skills", d))
        ) if os.path.isdir(self.p("plugins/harness/skills")) else []
        self.agents = sorted(
            f[:-3] for f in os.listdir(self.p("plugins/harness/agents")) if f.endswith(".md")
        ) if os.path.isdir(self.p("plugins/harness/agents")) else []
        self.commands = sorted(
            f[:-3] for f in os.listdir(self.p("plugins/harness/commands")) if f.endswith(".md")
        ) if os.path.isdir(self.p("plugins/harness/commands")) else []
        self.files = self._collect()
        self.text = {f: open(self.p(f), encoding="utf-8").read() for f in self.files}
        self.heads = {
            f: [re.sub(r"\s+", " ", h).strip() for h in re.findall(r"^#{1,4}\s+(.+)$", t, re.M)]
            for f, t in self.text.items()
        }

    def p(self, *a):
        return os.path.join(self.root, *a)

    def _collect(self):
        out = []
        for d in SCAN_DIRS:
            for dirpath, _, names in os.walk(self.p(d)):
                for n in sorted(names):
                    if n.endswith(".md"):
                        out.append(os.path.relpath(os.path.join(dirpath, n), self.root))
        for f in SCAN_FILES:
            if os.path.exists(self.p(f)) and not DATED.search(f):
                out.append(f)
        return sorted(out)

    def lines(self):
        for f in self.files:
            for i, l in enumerate(self.text[f].splitlines(), 1):
                yield f, i, l


# ───────────────────────────────────────────────────────── 검사 결과 수집
class Report:
    def __init__(self):
        self.rows = []

    def fail(self, check, where, expect, actual):
        self.rows.append(("FAIL", check, where, expect, actual))

    def warn(self, check, where, expect, actual):
        self.rows.append(("WARN", check, where, expect, actual))

    @property
    def failed(self):
        return [r for r in self.rows if r[0] == "FAIL"]


# ───────────────────────────────────────────────────────── Tier 1 파생 검사
def check_version(t, r):
    try:
        pj = json.load(open(t.p("plugins/harness/.claude-plugin/plugin.json"), encoding="utf-8"))
        mj = json.load(open(t.p(".claude-plugin/marketplace.json"), encoding="utf-8"))
    except OSError as e:
        return r.fail("VERSION", "manifest", "읽기 가능", str(e))
    for p in mj.get("plugins", []):
        if p.get("name") == pj.get("name") and p.get("version") != pj.get("version"):
            r.fail("VERSION", "marketplace.json", f"version={pj['version']}", f"version={p.get('version')}")


def check_roster(t, r):
    actual = {"role agents": len(t.agents), "workflow commands": len(t.commands), "skills": len(t.skills)}
    targets = list(t.lines())
    for name in ("plugins/harness/.claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        if os.path.exists(t.p(name)):
            for i, l in enumerate(open(t.p(name), encoding="utf-8").read().splitlines(), 1):
                targets.append((name, i, l))
    for f, i, l in targets:
        for m in re.finditer(r"(\d+)\s+(role agents|workflow commands|skills)", l):
            n, kind = int(m.group(1)), m.group(2)
            if n != actual[kind]:
                r.fail("ROSTER", f"{f}:{i}", f"{actual[kind]} {kind}", f"{n} {kind}")


def check_mirror(t, r):
    """sync-codex.sh 를 임시 트리에서 재생성해 비교한다 — 실제 트리는 건드리지 않는다."""
    script = t.p("tools/sync-codex.sh")
    if not os.path.exists(script):
        return
    with tempfile.TemporaryDirectory() as tmp:
        for d in ("tools", "plugins"):
            shutil.copytree(t.p(d), os.path.join(tmp, d), symlinks=True)
        proc = subprocess.run(["bash", os.path.join(tmp, "tools/sync-codex.sh")],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            return r.fail("MIRROR", "tools/sync-codex.sh", "exit 0", proc.stderr.strip()[:120])
        for sub in (".agents/skills", ".codex/agents"):
            gen, real = os.path.join(tmp, sub), t.p(sub)
            if not os.path.isdir(real):
                r.fail("MIRROR", sub, "존재", "없음")
                continue
            g, a = set(os.listdir(gen)), set(os.listdir(real))
            for miss in sorted(g - a):
                r.fail("MIRROR", f"{sub}/{miss}", "생성물과 일치", "레포에 없음")
            for extra in sorted(a - g):
                r.fail("MIRROR", f"{sub}/{extra}", "생성물에 없음", "레포에 잔존(stale)")
            for n in sorted(g & a):
                gp, ap = os.path.join(gen, n), os.path.join(real, n)
                if os.path.islink(gp) or os.path.islink(ap):
                    if os.path.realpath(gp).split("/plugins/")[-1] != os.path.realpath(ap).split("/plugins/")[-1]:
                        r.fail("MIRROR", f"{sub}/{n}", "동일 심볼릭 대상", "대상 불일치")
                elif os.path.isfile(gp) and os.path.isfile(ap):
                    if open(gp, encoding="utf-8").read() != open(ap, encoding="utf-8").read():
                        r.fail("MIRROR", f"{sub}/{n}", "sync-codex.sh 재생성물과 동일", "미동기 — 재실행 필요")
                elif os.path.isdir(gp) and os.path.isdir(ap):
                    for fn in sorted(set(os.listdir(gp)) | set(os.listdir(ap))):
                        x, y = os.path.join(gp, fn), os.path.join(ap, fn)
                        if not (os.path.isfile(x) and os.path.isfile(y)) or \
                           open(x, encoding="utf-8").read() != open(y, encoding="utf-8").read():
                            r.fail("MIRROR", f"{sub}/{n}/{fn}", "재생성물과 동일", "미동기")


def check_dangling(t, r):
    for f, i, l in t.lines():
        for m in re.finditer(r"`([a-z][a-z0-9-]{2,})`\s*(?:스킬|skill)\b", l):
            if m.group(1) not in t.skills:
                r.fail("DANGLING", f"{f}:{i}", "실재하는 스킬", f"`{m.group(1)}` 스킬 없음")
        for m in re.finditer(r"`((?:agents|commands)/[a-z0-9-]+\.md|skills/[a-z0-9-]+/SKILL\.md)`", l):
            if not os.path.exists(t.p("plugins/harness", m.group(1))):
                r.fail("DANGLING", f"{f}:{i}", "실재하는 경로", m.group(1))
        for m in re.finditer(r"`([a-z][a-z0-9-]{2,})`\s*(?:스킬\s*)?§\s*([^—·(,;\n]{2,40})", l):
            sk, sec = m.group(1), m.group(2).strip().rstrip(".」)의 ")
            tgt = f"plugins/harness/skills/{sk}/SKILL.md"
            if sk in t.skills and tgt in t.heads and sec and not sec[0].isdigit():
                if not any(sec.split()[0] in h for h in t.heads[tgt]):
                    r.fail("DANGLING", f"{f}:{i}", f"`{sk}` 안의 §{sec}", "그 섹션 없음")


def check_selfref(t, r):
    for f in t.files:
        m = re.match(r"plugins/harness/skills/([a-z0-9-]+)/SKILL\.md$", f)
        if not m:
            continue
        own = m.group(1)
        for i, l in enumerate(t.text[f].splitlines(), 1):
            if re.search(r"`%s`\s*(?:스킬|skill)\b" % re.escape(own), l):
                r.fail("SELFREF", f"{f}:{i}", f"자기 §섹션 지목", f"자기 자신(`{own}` 스킬)을 가리킴")


def check_portability(t, r):
    for f, i, l in t.lines():
        if not f.startswith("plugins/harness/"):
            continue
        for m in re.finditer(r"\b([a-z_][a-z0-9_]{3,})\.(py|java|ts|tsx|go):\d+", l):
            r.fail("PORTABILITY", f"{f}:{i}", "프로젝트 중립", f"{m.group(0)} (특정 프로젝트 file:line)")
        if len(l.split()) > 130:
            r.warn("PORTABILITY", f"{f}:{i}", "한 줄 ≤130단어", f"{len(l.split())}단어 — 사건 서사 비대 의심")


def check_sections(t, r):
    """정본(`harness-ledger` §Canonical required sections) ↔ 에이전트 파일 사본 대조.

    analyst·architect·planner 는 ledger 비독자다(ledger frontmatter). 비독자는 정본이
    바뀐 사실을 알 방법이 없으므로, 사본 대조가 유일한 가드다 — 2026-09-02 에
    `analyst.md` 가 `F-NNN` 조항을 잃은 채로 몇 버전을 돌았다.
    """
    canon = "plugins/harness/skills/harness-ledger/SKILL.md"
    if canon not in t.text:
        return
    lists = {}
    for l in t.text[canon].splitlines():
        m = re.match(r"-\s+\*\*([A-Za-z.]+)\*\*[^:]*:\s*(.+)$", l)
        if m:
            # 괄호 안에도 `·` 가 있다 — 항목 분리 전에 괄호 내용을 먼저 걷어낸다.
            body = m.group(2)
            for _ in range(4):
                body = re.sub(r"\([^()]*\)", "", body)
            lists[m.group(1)] = [
                re.sub(r"^\d+\s*", "", x).split("*")[0].split(".")[0].strip()
                for x in body.split("·")
            ]
    copies = {"analysis.md": "agents/analyst.md", "prd.md": "agents/planner.md",
              "design.md": "agents/architect.md"}
    for doc, rel in copies.items():
        f = "plugins/harness/" + rel
        if doc not in lists or f not in t.text:
            continue
        missing = [s for s in lists[doc] if s and s.split()[0] not in t.text[f]]
        if missing:
            r.fail("SECTIONS", rel, f"{doc} 정본 {len(lists[doc])}섹션 전건",
                   f"누락 {len(missing)}: {', '.join(missing[:3])}")
    analyst = "plugins/harness/agents/analyst.md"
    if analyst in t.text and "F-NNN" not in t.text[analyst]:
        r.fail("SECTIONS", "agents/analyst.md", "F-NNN 계약 실재",
               "0건 — 하류 문서의 F-NNN 참조 계약이 붕괴한다")


# sync-codex.sh 가 TOML 로 방출할 수 있는 frontmatter 키. 여기 없는 키를 새로 도입하면
# Codex 경로에서 조용히 소실되므로 FAIL 로 막는다 — 생성기를 먼저 고치라는 뜻이다.
MIRROR_EMITTED = {"name", "description", "model"}


def check_mirror_fields(t, r):
    """frontmatter 키가 미러까지 도달하는지 — 소실을 값으로 드러낸다.

    `model` 은 Claude 별칭이라 sync-codex.sh 의 MODEL_MAP 을 거쳐야 방출된다.
    미매핑 별칭은 키가 빠진 채 생성되므로(= Codex 세션 기본값 상속) WARN 으로 남긴다.
    """
    for a in t.agents:
        f = f"plugins/harness/agents/{a}.md"
        m = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---", t.text.get(f, ""), re.DOTALL)
        if not m:
            continue
        fm = {}
        for line in m.group(1).splitlines():
            if line and not line[0].isspace() and ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip()
        for k in sorted(set(fm) - MIRROR_EMITTED):
            r.fail("MIRROR-FIELDS", f"agents/{a}.md `{k}`", "미러 TOML 로 방출",
                   "생성기가 버린다 — sync-codex.sh 를 먼저 고쳐라")
        toml = t.p(".codex/agents", a + ".toml")
        if fm.get("model") and os.path.exists(toml):
            if not re.search(r"^model = ", open(toml, encoding="utf-8").read(), re.M):
                r.warn("MIRROR-FIELDS", f"agents/{a}.md model={fm['model']}", "MODEL_MAP 에 등가 존재",
                       "미매핑 — Codex 는 세션 기본값을 상속한다")


def check_version_cache(t, r):
    """런타임 캐시 대조 — 로컬 전용, WARN. 캐시가 없는 환경(CI)에서는 조용히 통과한다."""
    root = os.path.expanduser("~/.claude/plugins/cache/harness-engineering/harness")
    if not os.path.isdir(root):
        return
    try:
        ver = json.load(open(t.p("plugins/harness/.claude-plugin/plugin.json"), encoding="utf-8"))["version"]
    except (OSError, KeyError):
        return
    if not os.path.isdir(os.path.join(root, ver)):
        have = sorted(os.listdir(root))[-1:] or ["없음"]
        r.warn("VERSION-CACHE", f"cache/…/harness/{ver}", "소스 버전 캐시 실재",
               f"최신 캐시 {have[0]} — `claude plugin update` 미실행")


def check_budget(t, r, entry):
    cap = int(entry.get("상한", 3500))
    base = t.p("plugins/harness")
    # 측정 단위 = 공백 분할(== `LC_ALL=C wc -w`). UTF-8 로케일의 `wc -w` 는 CJK 구두점에서도
    # 쪼개서 같은 파일을 ~12% 크게 센다 — 로케일 의존 값은 기준선이 될 수 없다(원장 <env> 결박과 같은 이유).
    words = lambda p: len(open(p, encoding="utf-8").read().split()) if os.path.exists(p) else 0
    state = words(os.path.join(base, "skills/harness-state/SKILL.md"))
    for combo in entry.get("조합", []):
        agent, _, skill = combo.partition("+")
        total = words(os.path.join(base, f"agents/{agent}.md")) + state
        if skill:
            total += words(os.path.join(base, f"skills/{skill}/SKILL.md"))
        if total > cap:
            r.warn("BUDGET", combo, f"≤{cap}단어", f"{total}단어 (+{total - cap})")


# ───────────────────────────────────────────────────────── Tier 2 레지스트리
def check_canon(t, r, e):
    eid = e.get("id", "?")
    allow = set(e.get("포인터_허용", []) or [])
    canon_rel = "plugins/harness/" + e["정본"] if e.get("정본") else None

    if e.get("값") and canon_rel:
        if canon_rel not in t.text:
            r.fail(f"CANON/{eid}", canon_rel, "정본 파일 존재", "없음")
        elif e["값"] not in t.text[canon_rel]:
            r.fail(f"CANON/{eid}", canon_rel, f"값 실재: {e['값']!r}", "정본에서 증발")
        else:
            for f, i, l in t.lines():
                if f != canon_rel and f.startswith("plugins/harness/") and e["값"] in l:
                    rel = f[len("plugins/harness/"):]
                    verb = "포인터만 허용 — 값 재서술 금지" if rel in allow else "정본 밖 중복"
                    r.fail(f"CANON/{eid}", f"{f}:{i}", f"정본은 {e['정본']} 하나", verb)

    if e.get("금지"):
        pat = re.compile(e["금지"])
        scope = e.get("범위")  # "plugins" = 배포되는 프롬프트만 (레포 자체 문서 제외)
        for f, i, l in t.lines():
            if scope == "plugins" and not f.startswith("plugins/harness/"):
                continue
            if pat.search(l):
                r.fail(f"CANON/{eid}", f"{f}:{i}", f"반대형 부재: /{e['금지']}/", l.strip()[:90])


# ───────────────────────────────────────────────────────────────── 실행
def run(root, canon_path):
    t, r = Tree(root), Report()
    entries = parse_canon(open(canon_path, encoding="utf-8").read())
    for fn in (check_version, check_roster, check_mirror, check_dangling,
               check_selfref, check_portability, check_sections,
               check_mirror_fields, check_version_cache):
        fn(t, r)
    for e in entries:
        kind = e.get("종류")
        if kind == "예산":
            check_budget(t, r, e)
        elif kind in ("정본", "금지"):
            check_canon(t, r, e)
        else:
            r.fail("CANON/schema", e.get("id", "?"), "종류 ∈ {정본,금지,예산}", repr(kind))
    return t, r, entries


def render(t, r, entries, label):
    print(f"\n=== 정합성 검사 — {label} ===")
    print(f"대상 {len(t.files)}파일 · 에이전트 {len(t.agents)} · 커맨드 {len(t.commands)} · "
          f"스킬 {len(t.skills)} · 레지스트리 {len(entries)}항목")
    if not r.rows:
        print("\nPASS — 위반 0")
        return 0
    w = max(len(x[1]) for x in r.rows)
    print(f"\n{'':4} {'검사'.ljust(w)}  {'위치':<34} {'기대':<38} 실제")
    print("-" * 130)
    for lvl, check, where, expect, actual in sorted(r.rows, key=lambda x: (x[0] != "FAIL", x[1])):
        print(f"{lvl:4} {check.ljust(w)}  {where:<34} {expect:<38} {actual}")
    nf, nw = len(r.failed), len(r.rows) - len(r.failed)
    print(f"\n{'FAIL' if nf else 'PASS'} — 위반 {nf}건, 경고 {nw}건")
    return 1 if nf else 0


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    canon = os.path.join(here, "canon.yaml")
    args = sys.argv[1:]
    if args and args[0] == "--against":
        if len(args) < 2:
            raise SystemExit("usage: check-canon.py --against <sha>")
        sha = args[1]
        with tempfile.TemporaryDirectory() as tmp:
            wt = os.path.join(tmp, "wt")
            subprocess.run(["git", "-C", repo, "worktree", "add", "-q", "--detach", wt, sha], check=True)
            try:
                # 레지스트리는 현재 것을 쓴다 — 과거 트리를 오늘의 정본으로 재는 게 목적이다.
                code = render(*run(wt, canon), label=f"{sha} (자기 대조)")
            finally:
                subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt],
                               check=False, capture_output=True)
        print("\n(자기 대조 모드: 과거 트리에서 위반이 나오는 것이 정상이다 — 검사기가 살아있다는 증거)")
        return 0 if code else 1  # 과거 트리에서 위반 0 = 검사기 퇴화 = 실패
    return render(*run(repo, canon), label="HEAD")


if __name__ == "__main__":
    sys.exit(main())
