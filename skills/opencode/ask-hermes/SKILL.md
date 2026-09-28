---
name: ask-hermes
description: "Use when OpenCode/OMO needs external research, cross-session memory lookup, or clarification from Hermes Agent via A2A."
version: 1.0.0
author: Hermes + OpenCode Integration
license: MIT
metadata:
  tags: [hermes, a2a, multi-agent, research, memory, clarification]
---

# Ask Hermes (A2A Bridge for OpenCode)

When working inside OpenCode / OMO (Sisyphus, Hephaestus, Oracle), use this skill to query **Hermes Agent** as an architectural peer over the A2A protocol (port 9900).

## When to Call Hermes

1. **External Web & Documentation Research**:
   - Looking up API docs, crates/libraries, or academic papers that are not available locally.
   - Example: *"Find the latest Rapier 3D 0.18 character controller WASM bindings and example implementations."*
2. **Project Memory & Past Architecture Decisions**:
   - Querying long-term Mem0 memory for user preferences, previous milestone decisions, or system constraints.
   - Example: *"What were the agreed parameters for the slide boost formula in VHOLUME ARENA?"*
3. **Escalating Clarifications to the User**:
   - When a design trade-off has multiple viable paths and needs human input.

## How to Execute

Run the dedicated helper script via bash:

```bash
python3 ~/.config/opencode/skills/ask-hermes/scripts/ask_hermes.py "Your question or research request here"
```

With context continuity:
```bash
python3 ~/.config/opencode/skills/ask-hermes/scripts/ask_hermes.py "Follow-up question" --context-id "proj-vholume-arena"
```

## Response Handling

- Hermes processes the request with its full toolset (web search, web extract, memory, research tools) and returns a concise, structured answer.
- Incorporate the returned information directly into your implementation or architecture plan.
