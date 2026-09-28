#!/usr/bin/env python3
"""
Example: Real-time SSE streaming task delegation to OpenCode + OMO via A2A.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from opencode_a2a_client import stream_opencode


def handle_event(event: dict):
    # Print high-level step progress without flooding terminal
    if "task" in event:
        status = event["task"].get("status", {})
        state = status.get("state")
        msg = status.get("message", {}).get("parts", [{}])[0].get("text", "")
        if state:
            print(f"[*] Task State: {state} | {msg[:80]}...")


def main():
    task_prompt = "Refactor math_helpers.py to optimize prime check with Miller-Rabin test. Run tests."
    print("Starting streaming delegation via /message:stream...")

    for event in stream_opencode(
        message=task_prompt,
        context_id="example-math-helpers",
        directory="/tmp",
        on_event=handle_event,
        timeout=600,
    ):
        pass

    print("\nStreaming finished.")


if __name__ == "__main__":
    main()
