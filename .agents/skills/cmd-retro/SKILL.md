---
name: cmd-retro
description: "RETRO phase — delegate to harness-improver to mine failures from logs and retro inbox, update the playbook ACE-style, and propose bounded harness edits for user approval (mirrors /harness:retro)"
---

This skill mirrors the Claude Code command `/harness:retro`. Read the full workflow definition at `plugins/harness/commands/retro.md` (repo root relative) and execute it exactly as written. Where the workflow says to delegate to a named agent, spawn the Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state conventions are defined in the `harness-state` skill.
