"""
Hermes Plugin for OpenCode + Oh-My-OpenAgent (OMO) A2A Delegation.
"""

from typing import Any, Dict
from .client import call_opencode


def opencode_delegate_tool(
    goal: str,
    directory: str | None = None,
    context_id: str | None = None,
    timeout: int = 1800,
) -> Dict[str, Any]:
    """Delegate substantial coding, refactoring, or test execution to OpenCode + OMO via A2A."""
    result = call_opencode(
        message=goal,
        directory=directory,
        context_id=context_id,
        timeout=timeout,
    )
    return result


_OPENCODE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "opencode_delegate",
        "description": "Delegate complex coding, refactoring, bug fixing, test running, or codebase implementations to OpenCode + Oh-My-OpenAgent (OMO) over A2A protocol. OMO orchestrates parallel specialized agents (Sisyphus, Hephaestus, Oracle, Momus) to implement and verify code changes.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "The engineering task description, acceptance criteria, and constraints.",
                },
                "directory": {
                    "type": "string",
                    "description": "The absolute path to the target repository or workspace directory.",
                },
                "context_id": {
                    "type": "string",
                    "description": "Milestone or feature session identifier (e.g. 'feature-auth-service') to maintain session memory.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds (default: 1800).",
                },
            },
            "required": ["goal"],
        },
    },
}


def register(ctx: Any) -> None:
    """Register opencode_delegate tool into Hermes Agent runtime."""
    if hasattr(ctx, "register_tool"):
        ctx.register_tool(
            name="opencode_delegate",
            toolset="opencode",
            schema=_OPENCODE_SCHEMA["function"],
            handler=opencode_delegate_tool,
            description=_OPENCODE_SCHEMA["function"]["description"],
            emoji="🛠️",
        )
