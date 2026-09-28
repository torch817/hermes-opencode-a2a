#!/usr/bin/env python3
"""
OpenCode -> Hermes A2A Bridge CLI Helper.
Allows OMO agents to query Hermes for external research, memory, and user clarification.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
import uuid

HERMES_A2A_URL = "http://127.0.0.1:9900/"


def ask_hermes(query: str, context_id: str | None = None, timeout: int = 180) -> str:
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": query}],
            }
        },
        "id": f"omo-req-{uuid.uuid4().hex[:8]}",
    }
    if context_id:
        payload["params"]["message"]["contextId"] = context_id

    req = urllib.request.Request(
        HERMES_A2A_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                return f"[Hermes A2A Error]: {data['error']}"
            result = data.get("result", {})
            status_msg = result.get("status", {}).get("message", {})
            parts = status_msg.get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"]
            # Fallback to artifacts
            artifacts = result.get("artifacts", [])
            if artifacts:
                texts = [
                    p.get("text", "")
                    for a in artifacts
                    for p in a.get("parts", [])
                    if "text" in p
                ]
                return "\n".join(texts)
            return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"[Failed to reach Hermes A2A on {HERMES_A2A_URL}]: {e}"


def main():
    parser = argparse.ArgumentParser(description="Query Hermes Agent via A2A protocol.")
    parser.add_argument("query", help="Query, research prompt, or question for Hermes")
    parser.add_argument("--context-id", "-c", default=None, help="Context/Session ID")
    parser.add_argument("--timeout", "-t", type=int, default=180, help="Timeout in seconds")
    args = parser.parse_args()

    output = ask_hermes(args.query, context_id=args.context_id, timeout=args.timeout)
    print(output)


if __name__ == "__main__":
    main()
