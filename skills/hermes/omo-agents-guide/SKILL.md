---
name: omo-agents-guide
description: "Use when delegating to OMO sub-agents via OpenCode A2A."
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [omo, oh-my-openagent, opencode, a2a, agents, delegation]
    related_skills: [implement-with-opencode-a2a, omo-model-mapping]
---

# Oh-My-OpenAgent (OMO) Agents Guide

Guide to the specialized agents within Oh-My-OpenAgent (OMO) running inside OpenCode.

## OMO Agent Hierarchy & Roles

When Hermes / Builder sends an A2A task to OpenCode on port 8000, OMO orchestrates execution across specialized sub-agents:

### 1. Orchestration & Planning
- **Sisyphus**: Primary lead agent / ultrawork orchestrator. Deconstructs complex user requests into structured execution DAGs and dispatches work to specialists.
- **Sisyphus-Junior**: Fast task runner for focused, isolated sub-problems.
- **Prometheus**: Strategic planner and architect. Designs multi-phase migration plans and system boundaries in `.omo/plans/` without touching code.
- **Metis**: Pre-analysis and dependency mapping via LSP before major code edits.

### 2. Implementation & Deep Engineering
- **Hephaestus**: Autonomous deep coder. Handles multi-file implementations, AST transformations, complex algorithms, and bug fixing.
- **Oracle**: Architectural consultant. Analyzes trade-offs, design patterns, and edge cases.

### 3. Verification & Quality Gate
- **Momus**: Adversarial code reviewer and QA gate. Reviews diffs against acceptance criteria, verifies test suites, and blocks completion on regressions or broken contracts.

### 4. Codebase Navigation & Maintenance
- **Explore / Atlas**: Fast semantic search, file exploration, and dependency tree inspection.
- **Compaction**: Handles session context compaction and memory management.

## Ultrawork Mode (`ulw` / `ultrawork`)

When delegating engineering tasks, Builder MUST always trigger **Ultrawork Mode** by placing `ultrawork` (or `ulw`) at the top of the prompt:
- **IntentGate Activation**: OMO's IntentGate detects the keyword and activates all sub-agents (Sisyphus, Prometheus, Oracle, Hephaestus, Momus) in a continuous execution loop.
- **Outcome-First**: The loop does not stop, idle, or report premature completion until all acceptance criteria are met and backed by real execution evidence.
- **Evidence-Driven**: Requires running actual tests (`cargo test`, `pnpm test`), builds, and linters with captured terminal output.

## Delegation Best Practices from Builder

- Always start task briefs with `ultrawork`.
- State the **Goal** clearly without micromanaging internal AST mechanics — OMO selects the appropriate specialist (e.g. Hephaestus for deep coding, Momus for verification).
- Provide explicit **Acceptance Criteria** and **Verification Commands** so Momus and Sisyphus can validate the output before returning `TASK_STATE_COMPLETED`.
- Use consistent `context_id` across iterative tasks in the same milestone to preserve OMO's internal session context.
