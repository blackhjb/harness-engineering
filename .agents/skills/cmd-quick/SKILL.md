---
name: cmd-quick
description: "Lightweight path for S-size tasks (single-file bugfix, config change, small refactor) — one dev agent, tests, log trail; refuses anything that needs the full loop (mirrors /harness:quick)"
---

This skill mirrors the Claude Code command `/harness:quick`. Read the full workflow definition at `plugins/harness/commands/quick.md` (repo root relative) and execute it exactly as written. Where the workflow says to delegate to a named agent, spawn the Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state conventions are defined in the `harness-state` skill.
