"""
Action layer for EAGV3 Session 6 agent.

Responsibilities:
- Execute tool calls via MCP server
- Handle tool results and errors
- Format responses for the agent
"""

import asyncio
import json
from datetime import datetime, UTC
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from schemas import ActionInput, ActionOutput, ActionType, ToolResult


class ActionExecutor:
    """Executes actions via MCP server."""

    def __init__(self, mcp_command: list[str]):
        self.mcp_command = mcp_command
        self.session: ClientSession | None = None
        self._client_context = None
        self._session_context = None

    async def connect(self) -> None:
        """Connect to MCP server."""
        if self.session is not None:
            return

        server_params = StdioServerParameters(
            command=self.mcp_command[0],
            args=self.mcp_command[1:],
            env=None
        )

        # Use stdio_client as a context manager
        self._client_context = stdio_client(server_params)
        read, write = await self._client_context.__aenter__()

        # Create and initialize session
        self._session_context = ClientSession(read, write)
        self.session = await self._session_context.__aenter__()
        await self.session.initialize()

    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.session is not None:
            try:
                if self._session_context:
                    await self._session_context.__aexit__(None, None, None)
                if self._client_context:
                    await self._client_context.__aexit__(None, None, None)
            except Exception:
                pass
            self.session = None
            self._session_context = None
            self._client_context = None

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        """Call a tool via MCP."""
        if self.session is None:
            await self.connect()

        try:
            result = await self.session.call_tool(tool_name, arguments)

            # MCP returns a list of content items
            content_items = result.content if hasattr(result, 'content') else []

            # Extract text from content items
            text_parts = []
            for item in content_items:
                if hasattr(item, 'text'):
                    text_parts.append(item.text)
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])

            full_text = "\n".join(text_parts)

            # Try to parse as JSON if it looks like JSON
            parsed_result: Any = full_text
            if full_text.strip().startswith(("{", "[")):
                try:
                    parsed_result = json.loads(full_text)
                except json.JSONDecodeError:
                    pass

            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=parsed_result,
                timestamp=datetime.now(UTC)
            )

        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                timestamp=datetime.now(UTC)
            )


async def process_action(
    action_input: ActionInput,
    executor: ActionExecutor
) -> ActionOutput:
    """
    Process action layer input.

    Executes the planned action via MCP tools or direct response.
    """
    action = action_input.planned_action
    action_type = action.action_type

    # Handle direct response (no tool call)
    if action_type == ActionType.RESPOND:
        return ActionOutput(
            action_type=action_type,
            response_text="Ready to respond",
            success=True
        )

    # Handle memory storage (handled by memory layer, not a tool)
    if action_type == ActionType.STORE_MEMORY:
        return ActionOutput(
            action_type=action_type,
            response_text="Memory storage handled by memory layer",
            success=True
        )

    # Map action types to MCP tool names
    tool_mapping = {
        ActionType.WEB_SEARCH: "web_search",
        ActionType.FETCH_URL: "fetch_url",
        ActionType.GET_TIME: "get_time",
        ActionType.CURRENCY_CONVERT: "currency_convert",
        ActionType.READ_FILE: "read_file",
        ActionType.LIST_DIR: "list_dir",
        ActionType.CREATE_FILE: "create_file",
        ActionType.UPDATE_FILE: "update_file",
        ActionType.EDIT_FILE: "edit_file",
    }

    tool_name = action.tool_name or tool_mapping.get(action_type)

    if not tool_name:
        return ActionOutput(
            action_type=action_type,
            success=False,
            response_text=f"Unknown action type: {action_type}"
        )

    # Execute the tool
    tool_result = await executor.call_tool(tool_name, action.parameters)

    return ActionOutput(
        action_type=action_type,
        tool_result=tool_result,
        success=tool_result.success
    )
