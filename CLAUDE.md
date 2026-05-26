# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **four-layer cognitive agent** implementation (EAGV3 Session 6) built with strict architectural constraints: Pydantic v2 contracts on all boundaries, no third-party agentic frameworks, and all LLM calls via a local gateway.

## Architecture: Perception → Memory → Decision → Action

The agent processes queries through four isolated layers, each with typed Pydantic inputs/outputs:

1. **Perception** (`perception.py`) - Classifies user intent via LLM, outputs structured `Intent`
2. **Memory** (`memory.py`) - Stores/retrieves facts in `state/memories.jsonl` (JSONL format)
3. **Decision** (`decision.py`) - Plans actions as list of `PlannedAction`, determines completion
4. **Action** (`action.py`) - Executes tools via MCP stdio transport

**Main loop:** `agent6.py` wires layers together, max 10 iterations, generates final response.

**Contracts:** `schemas.py` contains all 30+ Pydantic v2 models. No dict passing between layers.

## Critical Commands

### Running the Agent
```bash
# Prerequisites: LLM Gateway V3 must be running on port 8101
cd llm_gatewayV3 && ./run.sh  # In separate terminal

# Run agent with query
uv run python agent6.py 'your query here'

# Examples
uv run python agent6.py 'Remember that my name is Alice'
uv run python agent6.py "What's my name?"
```

### Development
```bash
# Install dependencies
uv sync

# Test installation
uv run python test_installation.py

# Verify gateway is running
curl -s http://localhost:8101/v1/providers

# Clean memory state (between test runs)
rm state/memories.jsonl
```

### Gateway Management
```bash
# Start gateway (required before running agent)
cd llm_gatewayV3 && ./.venv/bin/python main.py

# Check gateway status
curl http://localhost:8101/v1/routers

# View gateway logs (if started in background)
tail -f /tmp/gateway.log
```

## Key Architectural Constraints

1. **Pydantic-on-Prompt (PoP)**: LLM prompts explicitly request JSON matching Pydantic schemas. Both `perception.py` and `decision.py` embed schema structure in prompts and validate responses with `model_validate()`.

2. **Memory is cross-session**: `memory.py:167` searches ALL sessions (`session_id=None`), not current session. Memories persist in `state/memories.jsonl` as newline-delimited JSON.

3. **MCP via stdio transport**: `action.py` uses proper `ClientSession` context managers. The MCP server (`mcp_server.py`) provides 9 tools and must be launched as a subprocess.

4. **LLM Gateway V3 auto-routing**: Perception uses `auto_route="perception"` (fast models), Decision uses `auto_route="decision"` (context-aware). Gateway is on port 8101, separate from V1/V2.

5. **Fallback logic**: Decision layer (`decision.py:88-90`) uses rule-based fallbacks for `MEMORY_STORE` and `MEMORY_RECALL` intents to avoid LLM 503 errors.

## Important File Relationships

- **`agent6.py`** imports from all four layers + `schemas.py`
- **Perception/Decision** import `client.py` from `llm_gatewayV3/` (added to sys.path)
- **Action** creates MCP client with command: `["uv", "run", "python", "mcp_server.py"]`
- **Memory** directly reads/writes `state/memories.jsonl`, no database
- **Gateway client** (`llm_gatewayV3/client.py`) is copied/reused, not installed as package

## Common Gotchas

1. **Import path conflicts**: Root `schemas.py` vs `llm_gatewayV3/schemas.py`. Fixed by appending (not prepending) gateway path to `sys.path`.

2. **MCP client initialization**: Use `async with` pattern for `stdio_client()` and `ClientSession()`. Both are context managers that must be entered with `__aenter__()`.

3. **Datetime deprecation**: Use `datetime.now(UTC)` not `datetime.utcnow()` throughout.

4. **Gateway must be running**: Agent fails with `ConnectError` if port 8101 is not responding. Always start gateway first.

5. **Memory retrieval**: If memories aren't found, check `session_id` filtering in `memory.py:165-169`. Should be `None` to search all sessions.

6. **Tool execution**: Tools defined in `mcp_server.py` use `@mcp.tool()` decorator. Action layer maps `ActionType` enums to tool names via `tool_mapping` dict.

## Testing Workflow

```bash
# 1. Start gateway
cd llm_gatewayV3 && ./run.sh &

# 2. Clean state
rm state/memories.jsonl

# 3. Test memory store
uv run python agent6.py 'Remember that my favorite color is blue'

# 4. Test memory recall (new session)
uv run python agent6.py 'What is my favorite color?'

# 5. Verify persistence
cat state/memories.jsonl  # Should show stored fact
```

## Modifying the Agent

**To add a new intent type:**
1. Add enum to `IntentType` in `schemas.py`
2. Update `PERCEPTION_PROMPT` in `perception.py`
3. Add fallback case in `decision.py:_create_fallback_decision()`

**To add a new tool:**
1. Define in `mcp_server.py` with `@mcp.tool()` decorator
2. Add `ActionType` enum in `schemas.py`
3. Add mapping in `action.py:tool_mapping` dict
4. Update `DECISION_PROMPT` available actions list

**To change LLM behavior:**
- Edit prompts: `PERCEPTION_PROMPT` (perception.py), `DECISION_PROMPT` (decision.py)
- Change routing: `auto_route` parameter in LLM calls
- Adjust iterations: `max_iterations` in `AgentConfig` (schemas.py)

## Environment Setup

Required in `.env`:
- At least one LLM provider key (GEMINI_API_KEY, GROQ_API_KEY, etc.)
- Optional: TAVILY_API_KEY (web search, falls back to DuckDuckGo)

Gateway loads `.env` from parent directory or `llm_gatewayV3/.env`.

## Dependencies

Core: `pydantic>=2.6`, `httpx>=0.27`, `mcp>=1.0.0`, `python-dotenv>=1.0`

MCP server: `duckduckgo-search>=7.0.0`, `crawl4ai>=0.4.0`, `tavily-python>=0.5.0`

Managed via `pyproject.toml`, installed with `uv sync`.