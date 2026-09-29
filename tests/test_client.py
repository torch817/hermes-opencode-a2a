"""
Unit & integration tests for opencode_delegate client.py
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from plugins.hermes.opencode_a2a.client import (
    build_headers,
    build_message_payload,
    cancel_task,
    call_opencode,
    redact_secrets,
    _extract_completed_response,
    SESSION_BINDING_EXTENSION,
)


class TestClientUnit(unittest.TestCase):
    def test_redact_secrets(self):
        text = "Bearer 123456abcdef and sk-proj-1234567890abcdef and password='secret_value'"
        sanitized = redact_secrets(text)
        self.assertNotIn("123456abcdef", sanitized)
        self.assertNotIn("sk-proj-1234567890abcdef", sanitized)
        self.assertIn("[REDACTED]", sanitized)

    def test_build_headers(self):
        headers = build_headers(token="custom-token", extensions=[SESSION_BINDING_EXTENSION])
        self.assertEqual(headers["A2A-Version"], "1.0")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Authorization"], "Bearer custom-token")
        self.assertEqual(headers["A2A-Extensions"], SESSION_BINDING_EXTENSION)

    def test_build_message_payload(self):
        payload = build_message_payload(
            message="Implement feature",
            context_id="ctx-123",
            directory="/home/user/project",
            return_immediately=True,
        )
        self.assertEqual(payload["message"]["role"], "ROLE_USER")
        self.assertEqual(payload["message"]["contextId"], "ctx-123")
        self.assertEqual(payload["message"]["parts"][0]["text"], "Implement feature")
        self.assertEqual(payload["metadata"]["opencode"]["directory"], "/home/user/project")
        self.assertTrue(payload["configuration"]["returnImmediately"])

    def test_extract_completed_response_from_artifacts(self):
        task = {
            "id": "task-1",
            "contextId": "ctx-1",
            "status": {"state": "TASK_STATE_COMPLETED"},
            "artifacts": [{"parts": [{"text": "Code implemented."}]}],
        }
        resp = _extract_completed_response(task, "ctx-1")
        self.assertTrue(resp["success"])
        self.assertEqual(resp["state"], "TASK_STATE_COMPLETED")
        self.assertEqual(resp["output"], "Code implemented.")

    def test_extract_completed_response_from_status_message(self):
        task = {
            "id": "task-1",
            "status": {
                "state": "TASK_STATE_COMPLETED",
                "message": {"parts": [{"text": "Completed from status."}]},
            },
        }
        resp = _extract_completed_response(task, None)
        self.assertTrue(resp["success"])
        self.assertEqual(resp["output"], "Completed from status.")


class TestClientLiveIntegration(unittest.TestCase):
    def test_live_directory_dispatch_and_poll(self):
        """Live test against running local OpenCode A2A gateway."""
        result = call_opencode(
            message="echo A2A_TEST_SUCCESS",
            directory="/home/ayos/Work/hermes-opencode-a2a",
            context_id="test-live-ctx",
            timeout=30,
            poll_interval=1.0,
        )
        self.assertTrue(result["success"], f"Live call failed: {result}")
        self.assertEqual(result["state"], "TASK_STATE_COMPLETED")
        self.assertTrue(len(result["output"]) > 0)


if __name__ == "__main__":
    unittest.main()
