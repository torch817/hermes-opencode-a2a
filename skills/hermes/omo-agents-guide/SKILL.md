---
name: omo-agents-guide
description: "Use when delegating to OMO sub-agents via OpenCode A2A."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [omo, oh-my-openagent, opencode, sisyphus, hephaestus, oracle, multi-agent, delegation]
    related_skills: [opencode-a2a-delegation, hermes-opencode-architecture, omo-model-mapping]
---

# Oh-My-OpenAgent (OMO) — Agent Directory & Interaction Guide

Oh-My-OpenAgent (OMO) is the specialized multi-agent engineering harness running inside OpenCode. When Hermes delegates an engineering task via A2A (`opencode_delegate`), OMO's lead orchestrator (`Sisyphus`) activates and coordinates specialized sub-agents.

---

## 👥 Directory of OMO Agents & Responsibilities

### 1. Orchestrators & Planners
- **`sisyphus` (Ultraworker / Lead Orchestrator)**:
  - *Role*: Principal engineering lead. Decomposes tasks into atomic checklists (`todowrite`), plans execution graphs, spawns sub-agents, and verifies step completions.
  - *Model*: `opencode-omniroute/auto/smart` (Gemini Pro / Claude 3.7).
- **`sisyphus-junior` (Subtask Executor)**:
  - *Role*: Executes focused, isolated subtasks spawned by Sisyphus.
  - *Model*: `opencode-omniroute/auto/coding`.
- **`prometheus` (Strategic Architect)**:
  - *Role*: Long-range architectural planner. Deconstructs large monorepos and multi-phase milestones into staged dependency graphs.
  - *Model*: `opencode-omniroute/auto/reasoning`.

### 2. Builders & Coders
- **`hephaestus` (Deep Implementer / Builder)**:
  - *Role*: Heavy code generation, multi-file refactoring, writing complex algorithms, compiler diagnostics, and test harness authoring.
  - *Model*: `opencode-omniroute/auto/coding`.
- **`build` / `plan` / `general`**:
  - *Role*: Standard OpenCode execution fallbacks.

### 3. Advisors, Critics & Reviewers
- **`oracle` (Architectural Advisor & Debugger)**:
  - *Role*: High-level technical reasoning, resolving subtle concurrency bugs, mathematical verification, and invariant analysis.
  - *Model*: `opencode-omniroute/auto/reasoning`.
- **`momus` (Adversarial Critic & Reviewer)**:
  - *Role*: Code quality gatekeeper. Reviews pull requests, diffs, edge cases, and test completeness before task finalization.
  - *Model*: `opencode-omniroute/auto/reasoning`.
- **`metis` (Pre-implementation Analyst)**:
  - *Role*: Requirements stress-testing, boundary condition analysis, and gap detection.
  - *Model*: `opencode-omniroute/auto/reasoning`.

### 4. Reconnaissance & Navigation
- **`explore` (Fast Codebase Grep)**:
  - *Role*: High-speed regex, symbol, and pattern search across large trees.
  - *Model*: `opencode-omniroute/auto/fast` (Gemini 3.7 Flash).
- **`atlas` (Structure & Call Graph Navigator)**:
  - *Role*: Maps module dependencies, import hierarchies, and codebase topology.
  - *Model*: `opencode-omniroute/auto/smart`.
- **`librarian` (Docs & Reference Researcher)**:
  - *Role*: Looks up third-party SDK signatures, API documentation, and crate specs.
  - *Model*: `opencode-omniroute/auto/fast`.
- **`multimodal-looker` (Visual Inspector)**:
  - *Role*: Inspects UI snapshots, rendering artifacts, diagrams, and visual assets.
  - *Model*: `opencode-omniroute/auto/smart`.

### 5. Utility & Session Agents
- **`compaction` / `summary` / `title`**:
  - *Role*: Context compaction, conversational summarization, and session titling.
  - *Model*: `opencode-omniroute/auto/fast`.

---

## 🔄 Interaction Flow: Hermes ↔ OMO

```
Hermes Agent (Top-Level Orchestrator)
  │
  ▼ [POST /message:send via opencode_delegate]
OpenCode A2A Gateway (:8000) → opencode serve (:4096)
  │
  ▼
Sisyphus (Ultraworker)
  ├─► Explore & Atlas (Reconnaissance)
  ├─► Oracle & Prometheus (Planning & Architecture)
  ├─► Hephaestus & Sisyphus-Junior (Implementation & Tests)
  ├─► Momus (Adversarial Code Review)
  │
  ▼ [If OMO needs memory / user decisions]
ask-hermes Skill ──(A2A :9900)──► Hermes Agent
```

---

## 🛠️ Prompting Best Practices for OMO

When delegating to OMO via `opencode_delegate`:
1. **Specify Goals & Constraints, Not Step-by-Step Code**: Let Sisyphus plan the sub-agents and tool calls.
2. **Include Concrete Acceptance Criteria**: Define exact commands to verify success (e.g. `cargo test`, `pnpm build`).
3. **Set Context ID**: Use milestone-scoped IDs (`<project>-milestone-<N>`) to maintain prompt cache affinity across related turns.
