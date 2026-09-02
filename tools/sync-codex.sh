#!/usr/bin/env bash
#
# tools/sync-codex.sh — regenerate every Codex-facing artifact from the single
# source of truth: plugins/harness/ (the Claude Code plugin).
#
# Generated outputs (never edit these by hand — edit plugins/harness/ and re-run):
#   .agents/skills/<skill>       relative symlink -> ../../plugins/harness/skills/<skill>
#   .agents/skills/cmd-<cmd>/    wrapper skill mirroring plugins/harness/commands/<cmd>.md
#   .codex/agents/<name>.toml    Codex subagent from plugins/harness/agents/<name>.md
#
# Idempotent: safe to run repeatedly. Intended to be run from the repo root,
# but it resolves the repo root from its own location, so any cwd works.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SRC_SKILLS="plugins/harness/skills"
SRC_COMMANDS="plugins/harness/commands"
SRC_AGENTS="plugins/harness/agents"
DEST_SKILLS=".agents/skills"
DEST_AGENTS=".codex/agents"

for d in "$SRC_SKILLS" "$SRC_COMMANDS" "$SRC_AGENTS"; do
  [ -d "$d" ] || { echo "ERROR: $d not found — is this the harness repo root?" >&2; exit 1; }
done
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required." >&2; exit 1; }

# ------------------------------------------------------------------ 1. skills
# .agents/skills is 100% generated: wipe it first so stale links/dirs never survive.
rm -rf "$DEST_SKILLS"
mkdir -p "$DEST_SKILLS"

linked=0
copied=0
for src in "$SRC_SKILLS"/*/; do
  name="$(basename "$src")"
  if ln -s "../../$SRC_SKILLS/$name" "$DEST_SKILLS/$name" 2>/dev/null && [ -e "$DEST_SKILLS/$name" ]; then
    linked=$((linked + 1))
  else
    rm -f "$DEST_SKILLS/$name" 2>/dev/null || true
    cp -R "${src%/}" "$DEST_SKILLS/$name"
    copied=$((copied + 1))
    echo "notice: could not symlink '$name' (platform limitation?) — copied the directory instead." >&2
    echo "        edits to $SRC_SKILLS/$name will NOT propagate until you re-run this script." >&2
  fi
done

# ---------------------------------------- 2+3. command wrappers & agent TOMLs
rm -f "$DEST_AGENTS"/*.toml
mkdir -p "$DEST_AGENTS"

python3 - "$REPO_ROOT" "$linked" "$copied" <<'PYEOF'
import os
import re
import sys

repo_root, linked, copied = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
SRC_COMMANDS = os.path.join(repo_root, "plugins", "harness", "commands")
SRC_AGENTS = os.path.join(repo_root, "plugins", "harness", "agents")
DEST_SKILLS = os.path.join(repo_root, ".agents", "skills")
DEST_AGENTS = os.path.join(repo_root, ".codex", "agents")


def split_frontmatter(text):
    """Return (frontmatter_dict, body).

    Tolerates the simple YAML used in this repo: `key: value` lines, optional
    surrounding quotes, and indented continuation lines (folded values).
    """
    m = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)\Z", text, re.DOTALL)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    fm, key = {}, None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if not line[0].isspace() and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val in (">", "|", ">-", "|-", ">+", "|+"):
                val = ""
            fm[key] = val
        elif key is not None:
            fm[key] = (fm[key] + " " + line.strip()).strip()
    for k, v in list(fm.items()):
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            fm[k] = v[1:-1]
    return fm, body


def yaml_dquote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_multiline(s):
    s = s.strip("\n") + "\n"
    if "'''" not in s:
        # Literal multi-line string: body preserved verbatim, no escaping.
        # Trailing newline guarantees the closing delimiter sits on its own
        # line, so quote characters at the body edges can never merge with it.
        return "'''\n" + s + "'''"
    # Fallback for bodies containing ''': basic multi-line string with escaping.
    esc = s.replace("\\", "\\\\").replace('"', '\\"')
    return '"""\n' + esc + '"""'


# --- 2. command wrapper skills (real directories, not symlinks) --------------
WRAPPER_BODY = (
    "This skill mirrors the Claude Code command `/harness:{cmd}`. Read the full workflow "
    "definition at `plugins/harness/commands/{cmd}.md` (repo root relative) and execute it "
    "exactly as written. Where the workflow says to delegate to a named agent, spawn the "
    "Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state "
    "conventions are defined in the `harness-state` skill.\n"
)

n_wrappers = 0
for fn in sorted(os.listdir(SRC_COMMANDS)):
    if not fn.endswith(".md"):
        continue
    cmd = fn[:-3]
    with open(os.path.join(SRC_COMMANDS, fn), encoding="utf-8") as f:
        fm, _ = split_frontmatter(f.read())
    desc = fm.get("description") or ("Harness workflow command /harness:%s" % cmd)
    desc = "%s (mirrors /harness:%s)" % (desc, cmd)
    wdir = os.path.join(DEST_SKILLS, "cmd-" + cmd)
    os.makedirs(wdir, exist_ok=True)
    skill_md = (
        "---\n"
        "name: cmd-%s\n"
        "description: %s\n"
        "---\n\n" % (cmd, yaml_dquote(desc))
    ) + WRAPPER_BODY.format(cmd=cmd)
    with open(os.path.join(wdir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md)
    n_wrappers += 1

# --- 3. Codex subagent TOMLs --------------------------------------------------
READ_ONLY_AGENTS = {"code-reviewer"}  # the reviewer reads and reports; it must not edit

# frontmatter `model:` 은 **Claude Code 별칭**(opus·fable)이고 Codex 모델명 공간과 다르다.
# 사용자 결정(2026-09-02): **Codex 경로는 모델을 고정한다** — 별칭 티어링은 Claude 경로 전용이다.
# 그래서 소스의 `model:` 값과 무관하게 아래 하나를 방출한다.
#
# 검증(codex-cli 0.151.0, 격리 대조 실험):
#   - agent TOML 의 `model` 은 유효 키다 — 통제군 `zzz_not_a_real_key` 는 "unknown field" 로
#     거부되는데 `model` 은 통과했다.
#   - `reasoning_effort` 는 agent TOML 의 유효 키가 **아니다** — 통제군과 똑같이 거부된다.
#     그래서 추론 강도는 여기가 아니라 `.codex/config.toml` 의 `model_reasoning_effort` 가 정한다.
CODEX_MODEL = "gpt-5.6-luna"

n_agents = 0
for fn in sorted(os.listdir(SRC_AGENTS)):
    if not fn.endswith(".md"):
        continue
    with open(os.path.join(SRC_AGENTS, fn), encoding="utf-8") as f:
        fm, body = split_frontmatter(f.read())
    name = fm.get("name") or fn[:-3]
    desc = fm.get("description", "")
    lines = [
        "# GENERATED by tools/sync-codex.sh from plugins/harness/agents/%s — do not edit by hand." % fn,
        "name = %s" % toml_string(name),
        "description = %s" % toml_string(desc),
    ]
    lines.append("model = %s" % toml_string(CODEX_MODEL))
    if name in READ_ONLY_AGENTS:
        lines.append('sandbox_mode = "read-only"  # reviewer must not modify the workspace')
    lines.append("developer_instructions = %s" % toml_multiline(body))
    with open(os.path.join(DEST_AGENTS, name + ".toml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    n_agents += 1

print(
    "sync-codex: %d skill symlinks (%d copied as fallback), %d command wrapper skills, %d agent TOMLs."
    % (linked, copied, n_wrappers, n_agents)
)
PYEOF
