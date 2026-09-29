#!/usr/bin/env python3
"""
OpenCode -> Hermes A2A Bridge CLI Helper.
Allows OpenCode agents to query Hermes for persistent memory, architectural decisions, and user clarification.
Adheres to A2A v1.0 JSON-RPC specification.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid

HERMES_A2A_URL = os.environ.get("HERMES_A2A_URL", "http://127.0.0.1:9900/").rstrip("/")
HERMES_A2A_TOKEN = os.environ.get("HERMES_A2A_TOKEN", "")
DEFAULT_TIMEOUT = int(os.environ.get("HERMES_A2A_TIMEOUT", "300"))

_SECRET_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}", re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Scrub tokens and keys from output."""
    if not text:
        return ""
    sanitized = text
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized


def ask_hermes(query: str, context_id: str | None = None, timeout: int = DEFAULT_TIMEOUT) -> str:
    """
    Send query to Hermes A2A endpoint via A2A v1.0 JSON-RPC.
    Returns response string on success, raises RuntimeError on failure.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "ROLE_USER",
                "messageId": f"msg-ask-{uuid.uuid4().hex[:8]}",
                "parts": [{"text": query}],
            }
        },
        "id": f"opencode-req-{uuid.uuid4().hex[:8]}",
    }
    if context_id:
        payload["params"]["message"]["contextId"] = context_id

    headers = {
        "Content-Type": "application/json",
        "A2A-Version": "1.0",
    }
    if HERMES_A2A_TOKEN:
        headers["Authorization"] = f"Bearer {HERMES_A2A_TOKEN}"

    req = urllib.request.Request(
        HERMES_A2A_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                err_info = data["error"]
                raise RuntimeError(f"Hermes A2A returned error: {json.dumps(err_info, ensure_ascii=False)}")

            result = data.get("result", {})
            status = result.get("status", {})
            state = status.get("state", "UNKNOWN")

            # Check status message
            status_msg = status.get("message", {})
            parts = status_msg.get("parts", [])
            if parts and "text" in parts[0] and parts[0]["text"].strip():
                return redact_secrets(parts[0]["text"].strip())

            # Fallback to artifacts
            artifacts = result.get("artifacts", [])
            if artifacts:
                texts = [
                    p.get("text", "")
                    for a in artifacts
                    for p in a.get("parts", [])
                    if "text" in p and p.get("text")
                ]
                if texts:
                    return redact_secrets("\n".join(texts).strip())

            if state == "TASK_STATE_COMPLETED":
                return "Completed without output."

            raise RuntimeError(f"Unexpected A2A response structure: {json.dumps(result, ensure_ascii=False)}")

    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            pass
        raise RuntimeError(f"HTTP Error {e.code} contacting Hermes at {HERMES_A2A_URL}: {redact_secrets(err_body or str(e))}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error contacting Hermes A2A at {HERMES_A2A_URL}: {redact_secrets(str(e.reason))}")
    except TimeoutError:
        raise RuntimeError(f"Request to Hermes A2A timed out after {timeout} seconds. If waiting for user response, consider raising timeout.")
    except Exception as e:
        raise RuntimeError(f"Error executing Hermes A2A query: {redact_secrets(str(e))}")


def main():
    parser = argparse.ArgumentParser(description="Query Hermes Agent via A2A protocol.")
    parser.add_argument("query", help="Query, clarification prompt, or memory request for Hermes")
    parser.add_argument("--context-id", "-c", default=None, help="Context/Session ID")
    parser.add_argument("--timeout", "-t", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})")
    args = parser.parse_args()

    try:
        output = ask_hermes(args.query, context_id=args.context_id, timeout=args.timeout)
        print(output)
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"[ERROR ask-hermes]: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
