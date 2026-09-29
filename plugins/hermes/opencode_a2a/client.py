"""
Client wrapper for communicating with OpenCode A2A Gateway.
Implements A2A v1.0 protocol specification with async task dispatch,
polling, robust cancellation, secret redaction, and directory overrides.
"""

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

A2A_URL = os.environ.get("OPENCODE_A2A_URL", "http://127.0.0.1:8000")
A2A_TOKEN = os.environ.get("OPENCODE_A2A_TOKEN", "6624bef6a7e4e68c713665cfedc2fa6459545c544c966a85")
DEFAULT_TIMEOUT = int(os.environ.get("OPENCODE_A2A_TIMEOUT", "1800"))
SESSION_BINDING_EXTENSION = "urn:opencode-a2a:extension:session-binding:v1"

_SECRET_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}", re.IGNORECASE),
    re.compile(r"(api[_-]?key|password|secret|token)\s*[:=]\s*['\"]?[^\s'\",]+", re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Scrub sensitive credentials and tokens from text before returning or logging."""
    if not text:
        return ""
    sanitized = text
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized


def build_headers(
    token: Optional[str] = None,
    extensions: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Construct standard A2A v1.0 HTTP headers."""
    headers = {
        "Content-Type": "application/json",
        "A2A-Version": "1.0",
    }
    auth_token = token or A2A_TOKEN
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    if extensions:
        headers["A2A-Extensions"] = ", ".join(extensions)
    return headers


def build_message_payload(
    message: str,
    context_id: Optional[str] = None,
    directory: Optional[str] = None,
    return_immediately: bool = True,
) -> Dict[str, Any]:
    """Build compliant A2A v1.0 message dispatch payload."""
    payload: Dict[str, Any] = {
        "message": {
            "role": "ROLE_USER",
            "messageId": f"msg-{uuid.uuid4().hex[:12]}",
            "parts": [{"text": message}],
        }
    }
    if context_id:
        payload["message"]["contextId"] = context_id

    if directory:
        payload["metadata"] = {
            "opencode": {
                "directory": directory,
            }
        }

    if return_immediately:
        payload["configuration"] = {
            "returnImmediately": True,
        }

    return payload


def cancel_task(
    task_id: str,
    base_url: str = A2A_URL,
    token: Optional[str] = None,
    max_retries: int = 3,
) -> bool:
    """Send cancellation request with bounded retries on timeout or network drop."""
    url = f"{base_url.rstrip('/')}/tasks/{task_id}:cancel"
    headers = build_headers(token=token)
    req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 204):
                    logger.info("Successfully cancelled A2A task %s", task_id)
                    return True
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                pass
            # 400 with TASK_NOT_CANCELABLE typically means already completed/failed
            if "TASK_NOT_CANCELABLE" in err_body:
                logger.info("Task %s was not cancelable (already finished).", task_id)
                return True
            logger.warning("Cancel attempt %d failed for task %s: HTTP %d %s", attempt + 1, task_id, e.code, err_body)
        except Exception as e:
            logger.warning("Cancel attempt %d exception for task %s: %s", attempt + 1, task_id, e)
        time.sleep(0.5)

    return False


def call_opencode(
    message: str,
    context_id: Optional[str] = None,
    directory: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    poll_interval: float = 2.0,
    base_url: str = A2A_URL,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a coding task to OpenCode + OMO via A2A v1.0.
    Dispatches task asynchronously with returnImmediately, polls for status,
    and cleanly handles interrupts, errors, and cancellations.
    """
    extensions = [SESSION_BINDING_EXTENSION] if directory else None
    headers = build_headers(token=token, extensions=extensions)
    payload = build_message_payload(
        message=message,
        context_id=context_id,
        directory=directory,
        return_immediately=True,
    )

    dispatch_url = f"{base_url.rstrip('/')}/message:send"
    dispatch_req = urllib.request.Request(
        dispatch_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    task_id: Optional[str] = None
    try:
        with urllib.request.urlopen(dispatch_req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            task = data.get("task", {})
            task_id = task.get("id")
            context_id = task.get("contextId") or context_id

            state = task.get("status", {}).get("state", "TASK_STATE_WORKING")
            if state == "TASK_STATE_COMPLETED":
                return _extract_completed_response(task, context_id)
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            pass
        sanitized_err = redact_secrets(err_body or str(e))
        return {
            "success": False,
            "error": f"HTTP {e.code}: {sanitized_err}",
            "state": "ERROR",
            "context_id": context_id,
        }
    except Exception as e:
        return {
            "success": False,
            "error": redact_secrets(str(e)),
            "state": "ERROR",
            "context_id": context_id,
        }

    if not task_id:
        return {
            "success": False,
            "error": "Gateway returned no task ID in response",
            "state": "ERROR",
            "context_id": context_id,
        }

    # Polling loop
    poll_headers = build_headers(token=token)
    task_url = f"{base_url.rstrip('/')}/tasks/{task_id}"
    start_time = time.time()
    consecutive_404 = 0

    while time.time() - start_time < timeout:
        time.sleep(poll_interval)
        try:
            poll_req = urllib.request.Request(task_url, headers=poll_headers, method="GET")
            with urllib.request.urlopen(poll_req, timeout=10) as resp:
                consecutive_404 = 0
                task_data = json.loads(resp.read().decode("utf-8"))
                status = task_data.get("status", {})
                state = status.get("state", "UNKNOWN")
                context_id = task_data.get("contextId") or context_id

                if state == "TASK_STATE_COMPLETED":
                    return _extract_completed_response(task_data, context_id)

                if state == "TASK_STATE_FAILED":
                    error_msg = status.get("message", {}).get("parts", [{}])[0].get("text", "Task failed without error message")
                    return {
                        "success": False,
                        "state": "TASK_STATE_FAILED",
                        "task_id": task_id,
                        "context_id": context_id,
                        "error": redact_secrets(error_msg),
                    }

                if state == "TASK_STATE_INPUT_REQUIRED":
                    prompt_text = status.get("message", {}).get("parts", [{}])[0].get("text", "")
                    interrupt_meta = task_data.get("metadata", {}).get("shared", {}).get("interrupt", {})
                    return {
                        "success": False,
                        "state": "TASK_STATE_INPUT_REQUIRED",
                        "task_id": task_id,
                        "context_id": context_id,
                        "prompt": redact_secrets(prompt_text),
                        "interrupt": interrupt_meta,
                    }

        except urllib.error.HTTPError as e:
            if e.code == 404 and (time.time() - start_time) < 5.0 and consecutive_404 < 3:
                consecutive_404 += 1
                continue
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                pass
            logger.warning("Polling error on task %s: HTTP %d %s", task_id, e.code, redact_secrets(err_body))
        except Exception as e:
            logger.warning("Transient error while polling task %s: %s", task_id, redact_secrets(str(e)))

    # Timeout reached — abort the task cleanly
    logger.warning("Task %s timed out after %ds, issuing cancellation...", task_id, timeout)
    cancelled = cancel_task(task_id, base_url=base_url, token=token)
    return {
        "success": False,
        "state": "TIMEOUT",
        "task_id": task_id,
        "context_id": context_id,
        "cancelled": cancelled,
        "error": f"Execution timed out after {timeout} seconds",
    }


def _extract_completed_response(task: Dict[str, Any], context_id: Optional[str]) -> Dict[str, Any]:
    """Extract clean output text from completed task artifacts."""
    output_parts: List[str] = []
    for artifact in task.get("artifacts", []):
        for part in artifact.get("parts", []):
            if "text" in part:
                output_parts.append(part["text"])

    if not output_parts:
        msg = task.get("status", {}).get("message", {})
        for part in msg.get("parts", []):
            if "text" in part:
                output_parts.append(part["text"])

    return {
        "success": True,
        "state": "TASK_STATE_COMPLETED",
        "task_id": task.get("id"),
        "context_id": task.get("contextId") or context_id,
        "output": redact_secrets("\n".join(output_parts).strip()),
    }
