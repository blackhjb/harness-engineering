---
name: cmd-quick
description: "Lightweight path for S/M-size mechanical work (bugfix, config change, guard/test additions, small refactor batch) — minimal ceremony, full verification rigor; refuses anything that needs the full loop (mirrors /harness:quick)"
---

This skill mirrors the Claude Code command `/harness:quick`. Read the full workflow definition at `plugins/harness/commands/quick.md` (repo root relative) and execute it exactly as written. Where the workflow says to delegate to a named agent, spawn the Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state conventions are defined in the `harness-state` skill.
