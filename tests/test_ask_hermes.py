"""
Unit & integration tests for ask_hermes.py
"""

import importlib.util
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

# Dynamically import ask_hermes from hyphenated directory path
_script_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "skills", "opencode", "ask-hermes", "scripts", "ask_hermes.py")
)
_spec = importlib.util.spec_from_file_location("ask_hermes_mod", _script_path)
assert _spec is not None and _spec.loader is not None
_ask_hermes_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ask_hermes_mod)

ask_hermes = _ask_hermes_mod.ask_hermes
redact_secrets = _ask_hermes_mod.redact_secrets


class TestAskHermesUnit(unittest.TestCase):
    def test_redact_secrets(self):
        text = "Authorization: Bearer secret-token and sk-123456789"
        sanitized = redact_secrets(text)
        self.assertNotIn("secret-token", sanitized)
        self.assertNotIn("sk-123456789", sanitized)
        self.assertIn("[REDACTED]", sanitized)

    @patch("urllib.request.urlopen")
    def test_ask_hermes_success_status_message(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": "req-1",
            "result": {
                "status": {
                    "state": "TASK_STATE_COMPLETED",
                    "message": {
                        "parts": [{"text": "Agreed parameters: pool_size=10"}]
                    }
                }
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        ans = ask_hermes("What is the pool size?", timeout=5)
        self.assertEqual(ans, "Agreed parameters: pool_size=10")

    @patch("urllib.request.urlopen")
    def test_ask_hermes_error_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": "req-1",
            "error": {"code": -32600, "message": "Invalid Request"}
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with self.assertRaises(RuntimeError) as ctx:
            ask_hermes("Invalid", timeout=5)
        self.assertIn("Hermes A2A returned error", str(ctx.exception))


class TestAskHermesLiveIntegration(unittest.TestCase):
    def test_live_ping_to_hermes(self):
        """Live test against running local Hermes A2A server on port 9900."""
        ans = ask_hermes("ping", timeout=10)
        self.assertEqual(ans, "pong")


if __name__ == "__main__":
    unittest.main()
