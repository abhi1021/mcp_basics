"""
Pydantic v2 schemas for EAGV3 Session 6 agent.

Four cognitive layers with typed contracts:
- Perception: parse user input into structured intent
- Memory: retrieve and store relevant facts
- Decision: plan next actions based on current state
- Action: execute tools and return results
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Perception Layer Schemas
# ============================================================================

class IntentType(str, Enum):
    """Types of user intents the agent can handle."""
    FACTUAL_QUERY = "factual_query"
    MEMORY_STORE = "memory_store"
    MEMORY_RECALL = "memory_recall"
    SEARCH_AND_SUMMARIZE = "search_and_summarize"
    TIME_QUERY = "time_query"
    CURRENCY_CONVERSION = "currency_conversion"
    FILE_OPERATION = "file_operation"
    MULTI_STEP_TASK = "multi_step_task"


class PerceptionInput(BaseModel):
    """Input to the perception layer."""
    user_message: str = Field(..., description="Raw user input")
    session_id: str = Field(..., description="Session identifier")


class Intent(BaseModel):
    """Structured representation of user intent."""
    intent_type: IntentType = Field(..., description="Classified intent type")
    query: str = Field(..., description="Cleaned/normalized query")
    entities: dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    requires_tools: list[str] = Field(default_factory=list, description="Tools needed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class PerceptionOutput(BaseModel):
    """Output from the perception layer."""
    intent: Intent = Field(..., description="Parsed intent")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================================
# Memory Layer Schemas
# ============================================================================

class MemoryType(str, Enum):
    """Types of memory entries."""
    FACT = "fact"
    CONVERSATION = "conversation"
    TASK_RESULT = "task_result"


class MemoryEntry(BaseModel):
    """A single memory entry."""
    memory_id: str = Field(..., description="Unique memory identifier")
    memory_type: MemoryType = Field(..., description="Type of memory")
    content: str = Field(..., description="Memory content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    session_id: str = Field(..., description="Session that created this memory")


class MemoryQuery(BaseModel):
    """Query for retrieving memories."""
    query: str = Field(..., description="Search query")
    memory_types: list[MemoryType] | None = Field(None, description="Filter by memory types")
    session_id: str | None = Field(None, description="Filter by session")
    limit: int = Field(5, ge=1, le=20, description="Max results to return")


class MemoryInput(BaseModel):
    """Input to the memory layer."""
    intent: Intent = Field(..., description="Intent from perception")
    session_id: str = Field(..., description="Session identifier")
    operation: Literal["store", "retrieve"] = Field(..., description="Memory operation type")
    content: str | None = Field(None, description="Content to store (if operation=store)")


class MemoryOutput(BaseModel):
    """Output from the memory layer."""
    retrieved_memories: list[MemoryEntry] = Field(default_factory=list)
    stored_memory: MemoryEntry | None = Field(None, description="Newly stored memory")
    summary: str = Field("", description="Summary of retrieved memories")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================================
# Decision Layer Schemas
# ============================================================================

class ActionType(str, Enum):
    """Types of actions the agent can take."""
    WEB_SEARCH = "web_search"
    FETCH_URL = "fetch_url"
    GET_TIME = "get_time"
    CURRENCY_CONVERT = "currency_convert"
    READ_FILE = "read_file"
    LIST_DIR = "list_dir"
    CREATE_FILE = "create_file"
    UPDATE_FILE = "update_file"
    EDIT_FILE = "edit_file"
    RESPOND = "respond"
    STORE_MEMORY = "store_memory"


class PlannedAction(BaseModel):
    """A single planned action."""
    action_type: ActionType = Field(..., description="Type of action")
    tool_name: str | None = Field(None, description="MCP tool name if applicable")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    reasoning: str = Field(..., description="Why this action is needed")


class DecisionInput(BaseModel):
    """Input to the decision layer."""
    intent: Intent = Field(..., description="Intent from perception")
    memory_context: MemoryOutput = Field(..., description="Memory context")
    session_id: str = Field(..., description="Session identifier")
    previous_actions: list[dict[str, Any]] = Field(default_factory=list, description="Actions taken so far")


class DecisionOutput(BaseModel):
    """Output from the decision layer."""
    planned_actions: list[PlannedAction] = Field(..., description="Actions to execute")
    is_complete: bool = Field(False, description="Whether task is complete")
    reasoning: str = Field(..., description="Decision reasoning")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================================
# Action Layer Schemas
# ============================================================================

class ToolCall(BaseModel):
    """A tool call request."""
    tool_name: str = Field(..., description="MCP tool name")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolResult(BaseModel):
    """Result from a tool execution."""
    tool_name: str = Field(..., description="Tool that was called")
    success: bool = Field(..., description="Whether execution succeeded")
    result: Any = Field(None, description="Tool result if successful")
    error: str | None = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ActionInput(BaseModel):
    """Input to the action layer."""
    planned_action: PlannedAction = Field(..., description="Action to execute")
    session_id: str = Field(..., description="Session identifier")


class ActionOutput(BaseModel):
    """Output from the action layer."""
    action_type: ActionType = Field(..., description="Action that was executed")
    tool_result: ToolResult | None = Field(None, description="Tool result if tool was called")
    response_text: str | None = Field(None, description="Direct response if no tool needed")
    success: bool = Field(..., description="Whether action succeeded")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================================
# Agent State Schemas
# ============================================================================

class AgentState(BaseModel):
    """Overall agent state."""
    session_id: str = Field(..., description="Current session ID")
    user_message: str = Field(..., description="Original user message")
    perception: PerceptionOutput | None = None
    memory: MemoryOutput | None = None
    decision: DecisionOutput | None = None
    actions: list[ActionOutput] = Field(default_factory=list)
    iteration: int = Field(0, description="Current iteration count")
    max_iterations: int = Field(10, description="Max allowed iterations")
    is_complete: bool = Field(False, description="Whether task is complete")
    final_response: str = Field("", description="Final response to user")
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None


class AgentConfig(BaseModel):
    """Agent configuration."""
    max_iterations: int = Field(10, ge=1, le=50, description="Max iterations per query")
    llm_gateway_url: str = Field("http://localhost:8101", description="LLM Gateway V3 URL")
    mcp_server_command: list[str] = Field(
        default_factory=lambda: ["uv", "run", "python", "mcp_server.py"],
        description="Command to launch MCP server"
    )
    state_dir: str = Field("state", description="Directory for persistent state")
    enable_debug: bool = Field(False, description="Enable debug logging")
