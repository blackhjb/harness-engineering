---
name: cmd-status
description: "Read .harness/ state and render a concise Korean status report — phase, task progress, blockers, and next actions (mirrors /harness:status)"
---

This skill mirrors the Claude Code command `/harness:status`. Read the full workflow definition at `plugins/harness/commands/status.md` (repo root relative) and execute it exactly as written. Where the workflow says to delegate to a named agent, spawn the Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state conventions are defined in the `harness-state` skill.
