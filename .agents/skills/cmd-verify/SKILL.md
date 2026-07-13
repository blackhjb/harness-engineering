---
name: cmd-verify
description: "VERIFY phase — qa and code-reviewer run in parallel to check tests and GOAL.md success criteria; produces a PASS/FAIL verdict with evidence, FAIL spawns fix tasks via the orchestrator (mirrors /harness:verify)"
---

This skill mirrors the Claude Code command `/harness:verify`. Read the full workflow definition at `plugins/harness/commands/verify.md` (repo root relative) and execute it exactly as written. Where the workflow says to delegate to a named agent, spawn the Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state conventions are defined in the `harness-state` skill.
