---
name: ask-hermes
description: "Use when OpenCode/OMO sub-agents need cross-session memory lookup, user clarification, or architectural guidance from Hermes Agent via A2A."
version: 1.0.0
author: Hermes + OpenCode Integration
license: MIT
metadata:
  tags: [hermes, a2a, multi-agent, memory, clarification, orchestration, omo]
---

# Ask Hermes (A2A Bridge for OpenCode + OMO)

When working inside OpenCode with the **Oh-My-OpenAgent (OMO)** harness (Sisyphus, Hephaestus, Oracle, Momus), use this skill to query **Hermes Agent** as an architectural peer over the A2A protocol (port 9900).

## When OMO Sub-Agents Should Call Hermes

1. **Persistent Memory & Architectural Decisions**:
   - Querying Hermes's Mem0 / vector store for user preferences, previous milestone decisions, or established system invariants.
   - Example: *"What were the agreed database connection pooling parameters for this service?"*
2. **Escalating Clarifications & Decisions to the User**:
   - When facing multiple architectural trade-offs, ambiguous requirements, or breaking changes that require human approval.
   - Example: *"We have two migration options for the users table: zero-downtime dual-write vs maintenance window. Ask the user for preference."*
3. **Cross-Service & Platform Integrations**:
   - Requesting external platform triggers or status updates (Telegram notifications, issue updates) managed by Hermes.

## How to Execute

Run the dedicated helper script via bash:

```bash
python3 ~/.config/opencode/skills/ask-hermes/scripts/ask_hermes.py "Your question or memory request here"
```

With context continuity:
```bash
python3 ~/.config/opencode/skills/ask-hermes/scripts/ask_hermes.py "Follow-up question" --context-id "feature-auth-service"
```

## Response Handling

- Hermes processes the request using its memory, reasoning, and user communication channels, returning a concise and authoritative response.
- Incorporate the returned guidance directly into your implementation plan.
