# EAGV3 Session 6: Four-Layer Cognitive Agent

A production-grade agent with four cognitive layers: **Perception → Memory → Decision → Action**

## Architecture

```
User Query
    ↓
┌─────────────────────────────────────────────┐
│  PERCEPTION (perception.py)                 │
│  - Classifies intent                        │
│  - Extracts entities                        │
│  - Determines required tools                │
│  Input: PerceptionInput                     │
│  Output: PerceptionOutput                   │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  MEMORY (memory.py)                         │
│  - Retrieves relevant memories              │
│  - Stores new facts                         │
│  - Persists to state/ directory             │
│  Input: MemoryInput                         │
│  Output: MemoryOutput                       │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  DECISION (decision.py)                     │
│  - Plans next actions                       │
│  - Determines completion status             │
│  - Provides reasoning                       │
│  Input: DecisionInput                       │
│  Output: DecisionOutput                     │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  ACTION (action.py)                         │
│  - Executes tools via MCP                   │
│  - Returns results                          │
│  Input: ActionInput                         │
│  Output: ActionOutput                       │
└─────────────────┬───────────────────────────┘
                  ↓
          Loop or Respond
```

## Requirements Met

- ✅ Four code modules with clear separation: `memory.py`, `perception.py`, `decision.py`, `action.py`
- ✅ Main agent loop: `agent6.py`
- ✅ Pydantic v2 contracts: `schemas.py`
- ✅ Memory persists across runs in `state/`
- ✅ All LLM calls via LLM Gateway V3
- ✅ All tool calls via MCP server (stdio transport)
- ✅ No third-party agentic frameworks
- ✅ uv for dependency management

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Copy `.env.template` to `.env` and fill in your API keys:

```bash
cp .env.template .env
# Edit .env with your API keys
```

Minimum required keys:
- One LLM provider key (Gemini, NVIDIA, Groq, Cerebras, GitHub, or OpenRouter)
- TAVILY_API_KEY for web search (optional, falls back to DuckDuckGo)

### 3. Start LLM Gateway V3

The agent requires the LLM Gateway V3 to be running:

```bash
cd llm_gatewayV3
./run.sh
```

Verify it's running:
```bash
curl -s http://localhost:8101/v1/routers
```

## Usage

### Basic Usage

```bash
uv run python agent6.py '<your query>'
```

### Example Queries

#### Query A: Factual Lookup
```bash
uv run python agent6.py 'What is the capital of France?'
```

#### Query B: Time Query
```bash
uv run python agent6.py 'What time is it in Tokyo?'
```

#### Query C: Memory Persistence (Run 1 - Store)
```bash
uv run python agent6.py 'Remember that my favorite color is blue'
```

#### Query C: Memory Persistence (Run 2 - Recall)
```bash
uv run python agent6.py 'What is my favorite color?'
```

#### Query D: Search and Summarize
```bash
uv run python agent6.py 'Search for Python asyncio tutorials and summarize the top result'
```

## File Structure

```
session_6/
├── agent6.py              # Main agent loop
├── schemas.py             # Pydantic v2 models
├── perception.py          # Perception layer
├── memory.py              # Memory layer with persistence
├── decision.py            # Decision layer
├── action.py              # Action layer with MCP
├── mcp_server.py          # MCP server (9 tools)
├── state/                 # Persistent memory storage
│   └── memories.jsonl     # Memory entries (created on first run)
├── llm_gatewayV3/         # LLM Gateway V3
│   ├── main.py
│   ├── client.py
│   └── ...
└── pyproject.toml         # Dependencies

```

## Cognitive Layers

### Perception Layer (`perception.py`)
- **Input**: Raw user message
- **Processing**: LLM-based intent classification via Gateway V3 (`auto_route="perception"`)
- **Output**: Structured `Intent` with type, entities, confidence
- **Contract**: `PerceptionInput` → `PerceptionOutput`

### Memory Layer (`memory.py`)
- **Input**: Intent + operation (store/retrieve)
- **Processing**:
  - Store: Appends to `state/memories.jsonl`
  - Retrieve: Keyword-based search with relevance scoring
- **Output**: Retrieved memories or confirmation of storage
- **Contract**: `MemoryInput` → `MemoryOutput`
- **Persistence**: JSONL format, one memory per line

### Decision Layer (`decision.py`)
- **Input**: Intent + Memory context + Previous actions
- **Processing**: LLM-based planning via Gateway V3 (`auto_route="decision"`)
- **Output**: List of `PlannedAction` + completion status + reasoning
- **Contract**: `DecisionInput` → `DecisionOutput`
- **Fallback**: Rule-based planning when LLM parsing fails

### Action Layer (`action.py`)
- **Input**: Single `PlannedAction`
- **Processing**: Executes via MCP stdio transport
- **Output**: `ToolResult` with success/failure + result data
- **Contract**: `ActionInput` → `ActionOutput`
- **Tools**: 9 tools from MCP server (web_search, fetch_url, get_time, currency_convert, file ops)

## MCP Server Tools

The agent has access to 9 tools via the MCP server:

1. **web_search**: Tavily (primary) or DuckDuckGo (fallback)
2. **fetch_url**: Clean markdown via crawl4ai
3. **get_time**: Current time in any timezone
4. **currency_convert**: Live exchange rates
5. **read_file**: Read from sandbox
6. **list_dir**: List sandbox directory
7. **create_file**: Create new file
8. **update_file**: Overwrite existing file
9. **edit_file**: Find-and-replace in file

All file operations are sandboxed under `sandbox/`.

## Agent Loop

```python
while iteration < max_iterations and not is_complete:
    # 1. Perception (first iteration only)
    perception_output = await process_perception(...)

    # 2. Memory
    memory_output = await process_memory(...)

    # 3. Decision
    decision_output = await process_decision(...)

    # 4. Action(s)
    for planned_action in decision_output.planned_actions:
        action_output = await process_action(...)

        if planned_action.action_type == ActionType.RESPOND:
            final_response = generate_final_response(...)
            is_complete = True
            break
```

## Configuration

Edit `schemas.py` → `AgentConfig`:

```python
class AgentConfig(BaseModel):
    max_iterations: int = 10              # Max loop iterations
    llm_gateway_url: str = "http://localhost:8101"
    mcp_server_command: list[str] = ["uv", "run", "python", "mcp_server.py"]
    state_dir: str = "state"
    enable_debug: bool = False
```

## Cleaning State

To reset memory between test runs:

```bash
rm -rf state/
mkdir state
```

## Debugging

Enable debug logging:

```python
config = AgentConfig(enable_debug=True)
agent = Agent(config)
```

This will print:
- Full tool results
- LLM responses
- Detailed decision reasoning

## Iteration Limits

Each query has a maximum iteration count (default: 10). If exceeded, the agent returns:
```
Maximum iterations (10) reached.
```

Tune `max_iterations` in `AgentConfig` based on query complexity.

## LLM Gateway V3 Integration

All LLM calls use the gateway's auto-routing:
- **Perception**: `auto_route="perception"` → routed to TINY tier (fast models)
- **Decision**: `auto_route="decision"` → routed based on context size
- **Final Response**: `auto_route="decision"` → synthesis layer

This ensures:
- Simple intent classification uses fast/cheap models
- Complex planning uses capable models
- No hardcoded provider dependencies

## Pydantic Contracts

Every layer boundary is typed:

```python
# Perception
PerceptionInput → process_perception() → PerceptionOutput

# Memory
MemoryInput → process_memory() → MemoryOutput

# Decision
DecisionInput → process_decision() → DecisionOutput

# Action
ActionInput → process_action() → ActionOutput
```

No dict passing between layers. All validation via Pydantic v2.

## Testing

Run the agent with various query types to verify:

```bash
# Factual query
uv run python agent6.py 'What is the speed of light?'

# Memory store
uv run python agent6.py 'Remember that my birthday is January 15th'

# Memory recall
uv run python agent6.py 'When is my birthday?'

# Web search
uv run python agent6.py 'Who won the 2024 Nobel Prize in Physics?'

# Time query
uv run python agent6.py 'What time is it in Berlin?'

# Currency conversion
uv run python agent6.py 'Convert 100 USD to EUR'
```

## Troubleshooting

### "Connection refused" error
- Ensure LLM Gateway V3 is running: `cd llm_gatewayV3 && ./run.sh`
- Check: `curl http://localhost:8101/v1/providers`

### "MCP server failed"
- Verify MCP dependencies: `uv run python mcp_server.py` should not error
- Check `.env` has required keys (TAVILY_API_KEY, etc.)

### "No provider available"
- At least one LLM provider key must be set in `.env`
- Check gateway logs: `cd llm_gatewayV3 && tail -f *.log`

### Memory not persisting
- Check `state/` directory exists and is writable
- Verify `state/memories.jsonl` is created after first store operation

## License

EAGV3 Session 6 - Educational purposes
