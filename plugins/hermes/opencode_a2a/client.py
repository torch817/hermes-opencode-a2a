"""
Client wrapper for communicating with OpenCode A2A Gateway.
"""

import json
import os
import urllib.error
import urllib.request
import uuid
from typing import Any, Callable, Dict, Generator, Optional

A2A_URL = os.environ.get("OPENCODE_A2A_URL", "http://127.0.0.1:8000")
A2A_TOKEN = os.environ.get("OPENCODE_A2A_TOKEN", "6624bef6a7e4e68c713665cfedc2fa6459545c544c966a85")
DEFAULT_TIMEOUT = int(os.environ.get("OPENCODE_A2A_TIMEOUT", "1800"))


def build_message_payload(
    message: str,
    context_id: Optional[str] = None,
    directory: Optional[str] = None,
) -> Dict[str, Any]:
    if directory and not message.startswith(f"In {directory}"):
        message = f"In {directory}:\n\n{message}"

    payload = {
        "message": {
            "role": "ROLE_USER",
            "messageId": f"msg-{uuid.uuid4().hex[:8]}",
            "parts": [{"text": message}],
        }
    }
    if context_id:
        payload["message"]["contextId"] = context_id
    return payload


def call_opencode(
    message: str,
    context_id: Optional[str] = None,
    directory: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Send a coding task to OpenCode + OMO via A2A (synchronous)."""
    payload = build_message_payload(message, context_id=context_id, directory=directory)

    req = urllib.request.Request(
        f"{A2A_URL}/message:send",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {A2A_TOKEN}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            task = data.get("task", {})
            state = task.get("status", {}).get("state", "UNKNOWN")

            output_text = ""
            for artifact in task.get("artifacts", []):
                for part in artifact.get("parts", []):
                    if "text" in part:
                        output_text += part["text"] + "\n"

            return {
                "success": state == "TASK_STATE_COMPLETED",
                "state": state,
                "task_id": task.get("id"),
                "context_id": task.get("contextId"),
                "output": output_text.strip(),
                "raw": data,
            }
    except Exception as e:
        return {"success": False, "error": str(e), "state": "ERROR"}
