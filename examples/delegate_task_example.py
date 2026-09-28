#!/usr/bin/env python3
"""
Example: Synchronous task delegation from Hermes to OpenCode + OMO via A2A.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from opencode_a2a_client import call_opencode, check_health


def main():
    print("Checking A2A and OpenCode service health...")
    health = check_health()
    print("Service health status:", health)
    if not all(health.values()):
        print("Error: OpenCode server (:4096) or A2A adapter (:8000) is not reachable.")
        return

    task_prompt = """
    Create a Python utility module `math_helpers.py` with:
    1. `fibonacci(n: int) -> int`
    2. `is_prime(n: int) -> bool`
    3. Comprehensive pytest tests in `test_math_helpers.py`
    Run the test suite and verify all tests pass.
    """

    print("\nDelegating coding task to OpenCode (Sisyphus/Hephaestus)...")
    result = call_opencode(
        message=task_prompt,
        context_id="example-math-helpers",
        directory="/tmp",
        timeout=600,
    )

    print("\n=== Result ===")
    print("Success:", result.get("success"))
    print("Task State:", result.get("state"))
    print("Task ID:", result.get("task_id"))
    print("Output Summary:\n", result.get("output"))


if __name__ == "__main__":
    main()
