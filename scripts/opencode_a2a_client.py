#!/usr/bin/env python3
"""
OpenCode A2A Client Helper for Hermes Agent.

Provides convenient wrapper around A2A calls to OpenCode + OMO:
- Synchronous call with configurable extended timeout (default 1800s / 30 min)
- Server-Sent Events (SSE) streaming (/message:stream) with live event yielding
- Task status inspection (/tasks/{id}) and cancellation (/tasks/{id}:cancel)
"""

import json
import os
import urllib.request
import urllib.error
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


def stream_opencode(
    message: str,
    context_id: Optional[str] = None,
    directory: Optional[str] = None,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Generator[Dict[str, Any], None, Dict[str, Any]]:
    """Stream a coding task to OpenCode + OMO via A2A SSE endpoint (/message:stream)."""
    payload = build_message_payload(message, context_id=context_id, directory=directory)

    req = urllib.request.Request(
        f"{A2A_URL}/message:stream",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {A2A_TOKEN}",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    final_result: Dict[str, Any] = {
        "success": False,
        "state": "UNKNOWN",
        "task_id": None,
        "context_id": context_id,
        "output": "",
        "events": [],
    }

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            buffer = ""
            for chunk in resp:
                text = chunk.decode("utf-8", errors="replace")
                buffer += text
                while "\n\n" in buffer:
                    raw_event, buffer = buffer.split("\n\n", 1)
                    lines = raw_event.strip().split("\n")
                    event_data = ""
                    for line in lines:
                        if line.startswith("data:"):
                            event_data += line[5:].strip()
                    if not event_data:
                        continue
                    try:
                        parsed = json.loads(event_data)
                        final_result["events"].append(parsed)
                        if on_event:
                            on_event(parsed)
                        yield parsed

                        # Track final task outcome if present
                        if "task" in parsed:
                            t = parsed["task"]
                            final_result["task_id"] = t.get("id")
                            final_result["context_id"] = t.get("contextId", final_result["context_id"])
                            state = t.get("status", {}).get("state", final_result["state"])
                            final_result["state"] = state
                            final_result["success"] = state == "TASK_STATE_COMPLETED"
                            output_text = ""
                            for artifact in t.get("artifacts", []):
                                for part in artifact.get("parts", []):
                                    if "text" in part:
                                        output_text += part["text"] + "\n"
                            if output_text:
                                final_result["output"] = output_text.strip()
                    except json.JSONDecodeError:
                        pass
        return final_result
    except Exception as e:
        final_result["error"] = str(e)
        final_result["state"] = "ERROR"
        return final_result


def get_task(task_id: str) -> Dict[str, Any]:
    """Inspect status of an existing task."""
    req = urllib.request.Request(
        f"{A2A_URL}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {A2A_TOKEN}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def cancel_task(task_id: str) -> Dict[str, Any]:
    """Cancel a running task."""
    req = urllib.request.Request(
        f"{A2A_URL}/tasks/{task_id}:cancel",
        headers={"Authorization": f"Bearer {A2A_TOKEN}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def check_health() -> Dict[str, bool]:
    """Check if opencode-serve and opencode-a2a are running."""
    results = {"opencode_serve": False, "opencode_a2a": False}
    try:
        req = urllib.request.Request("http://127.0.0.1:4096/project", method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            results["opencode_serve"] = r.status == 200
    except Exception:
        pass

    try:
        req = urllib.request.Request(f"{A2A_URL}/.well-known/agent-card.json", method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            results["opencode_a2a"] = r.status == 200
    except Exception:
        pass

    return results


if __name__ == "__main__":
    health = check_health()
    print("Health:", health)
    if all(health.values()):
        print("All services UP and ready with extended timeouts & SSE support.")
    else:
        print("Some services DOWN:", health)
