# Hermes ↔ OpenCode A2A Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Protocol: A2A v1.0](https://img.shields.io/badge/Protocol-A2A%20v1.0-orange.svg)](https://github.com/a2a-protocol)

**Hermes ↔ OpenCode A2A Bridge** is a bidirectional integration layer connecting [Hermes Agent](https://github.com/NousResearch/hermes-agent) with [OpenCode](https://opencode.ai) and the [Oh-My-OpenAgent (OMO)](https://github.com/code-yeongyu/oh-my-openagent) multi-agent harness using the standard **Agent-to-Agent (A2A)** protocol.

---

## 📖 Overview

Modern AI development workflows benefit from decoupling **high-level orchestration** from **deep code execution**:

- **Hermes Agent (Orchestrator)**: User interaction across messaging platforms, project intent tracking, long-term memory (Mem0, vector stores), deep web research, and milestone verification.
- **OpenCode + OMO (Engineering Engine)**: Autonomous multi-file code editing, LSP diagnostics (Rust Analyzer, TypeScript), compiler loops (`cargo`, `pnpm`, `pytest`), test execution, and git workflows.

This bridge enables seamless, protocol-compliant collaboration between both agent environments.

---

## 🏛️ Architecture

```
User (Telegram / CLI / Web)
  │
  ▼
Hermes Agent (Port :9900)
  │
  ├── [Inbound / Delegation]
  │     │  a2a_call / opencode_delegate
  │     ▼
  │   opencode-a2a Adapter (Port :8000)
  │     │  REST / SSE Stream
  │     ▼
  │   OpenCode Server (Port :4096)
  │     │
  │     ▼
  │   Oh-My-OpenAgent (OMO Harness)
  │   (Sisyphus → Hephaestus, Oracle, Momus)
  │
  └── [Outbound / Consultation]
        ▲
        │  ask-hermes Skill (JSON-RPC A2A)
        └──────────────────────────────────┘
```

---

## ✨ Key Features

- **Bidirectional Peer Communication**:
  - **Hermes → OpenCode**: Delegate complex implementation, refactoring, and test suites.
  - **OpenCode → Hermes**: Query long-term memory, request external web research, or escalate decisions to the user.
- **Session Continuity (`context_id`)**:
  - Maintains conversation and project context across multiple turns using mapped SQLite session bindings.
- **Real-Time SSE Streaming**:
  - Streams execution events and progress in real time via Server-Sent Events (`/message:stream`).
- **Resilient Execution**:
  - Configurable extended upstream timeouts (up to 30+ minutes) to accommodate long compilation and testing cycles.
  - Process group lifecycle management to clean up background processes upon task cancellation.

---

## 📁 Repository Structure

```
hermes-opencode-a2a/
├── plugins/
│   └── hermes/
│       └── opencode_a2a/          # Native Hermes plugin (opencode_delegate tool)
├── skills/
│   └── opencode/
│       └── ask-hermes/            # OpenCode skill & CLI for querying Hermes
├── scripts/
│   └── opencode_a2a_client.py     # Standalone Python client (Sync + SSE Stream)
├── examples/
│   ├── delegate_task_example.py   # Synchronous delegation example
│   └── stream_progress_example.py # Streaming delegation example
├── docs/
│   └── deep-research-a2a.md       # Protocol analysis & implementation notes
├── LICENSE
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Node.js 20+
- OpenCode CLI (`npm install -g opencode-ai`)
- OpenCode A2A adapter (`uv tool install opencode-a2a`)

### 2. Start OpenCode Services

Start the OpenCode server and the A2A gateway adapter:

```bash
# Terminal 1: Start OpenCode server
opencode serve --hostname 127.0.0.1 --port 4096

# Terminal 2: Start A2A adapter
A2A_STATIC_AUTH_CREDENTIALS='[{"scheme":"bearer","token":"your-secure-token","principal":"hermes"}]' \
OPENCODE_BASE_URL=http://127.0.0.1:4096 \
A2A_HOST=127.0.0.1 \
A2A_PORT=8000 \
OPENCODE_TIMEOUT=1800.0 \
OPENCODE_TIMEOUT_STREAM=1800.0 \
A2A_ALLOW_DIRECTORY_OVERRIDE=true \
opencode-a2a serve
```

### 3. Install the Hermes Plugin

Copy the plugin directory into your Hermes plugins folder:

```bash
mkdir -p ~/.hermes/plugins/
cp -r plugins/hermes/opencode_a2a ~/.hermes/plugins/
```

### 4. Install the OpenCode Skill

Copy the skill directory into your OpenCode skills configuration:

```bash
mkdir -p ~/.config/opencode/skills/
cp -r skills/opencode/ask-hermes ~/.config/opencode/skills/
```

---

## 💡 Usage Examples

### 1. Delegating a Task from Hermes (Python Client)

```python
from opencode_a2a_client import call_opencode

result = call_opencode(
    message="Implement user authentication middleware and write unit tests.",
    context_id="feature-auth-service",
    directory="/path/to/your/project",
    timeout=1800
)

print(f"Status: {result['state']}")
print(f"Summary:\n{result['output']}")
```

### 2. Streaming Real-Time Progress (SSE)

```python
from opencode_a2a_client import stream_opencode

for event in stream_opencode(
    message="Run test suite and fix failing tests.",
    context_id="feature-auth-service",
    directory="/path/to/your/project",
    on_event=lambda e: print(f"Progress event: {e.get('type')}")
):
    pass
```

### 3. Consulting Hermes from OpenCode (OMO Skill)

When an OpenCode sub-agent needs documentation or user input during implementation:

```bash
python3 ~/.config/opencode/skills/ask-hermes/scripts/ask_hermes.py \
  "Research best practices for JWT rotation with refresh tokens in FastAPI"
```

---

## ⚙️ Configuration Reference

| Variable | Description | Default |
|---|---|---|
| `OPENCODE_BASE_URL` | Base URL of the upstream OpenCode server | `http://127.0.0.1:4096` |
| `A2A_PORT` | Port for the A2A adapter | `8000` |
| `OPENCODE_TIMEOUT` | Upstream synchronous request timeout (seconds) | `1800.0` |
| `OPENCODE_TIMEOUT_STREAM` | Upstream streaming request timeout (seconds) | `1800.0` |
| `A2A_STREAM_IDLE_TIMEOUT_SECONDS` | Maximum allowed idle time during streaming | `1800.0` |
| `A2A_ALLOW_DIRECTORY_OVERRIDE` | Allow caller to target specific project folders | `true` |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/torch817/hermes-opencode-a2a/issues).

---

## 📄 License

Distributed under the [MIT License](LICENSE).
