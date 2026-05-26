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

### 4 Example Queries

#### Query A. Shannon Wikipedia (artifact attach test)
```bash
> uv run python agent6.py "Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory."                                               INT py base 10:51:37

============================================================
Agent Session: 238c2084-b0bd-4ee0-9bc3-5bc0eab70e86
User: Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.
============================================================


--- Iteration 1 ---
→ Perception: Analyzing user intent...
Warning: Failed to parse LLM response: No JSON found in response
Response was: ```json
{
  "intent_type": "multi_step_task",
  Intent: factual_query
  Query: Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.
  Confidence: 0.50

→ Memory: Processing memory operations...
  No relevant memories found.

→ Decision: Planning actions...
  Planned 3 action(s)
  Reasoning: The user asked for specific biographical details and contributions. We need to fetch the Wikipedia page to get accurate data. The plan involves searching for the page, fetching it, and then responding.
  Complete: False

→ Action 1/3: web_search
  Reasoning: Search the web to locate the correct Wikipedia page URL for Claude Shannon.
[05/26/26 19:12:49] INFO     Processing request of type CallToolRequest                                                                                                                                                                                              server.py:727
[05/26/26 19:12:50] INFO     Processing request of type ListToolsRequest                                                                                                                                                                                             server.py:727
  Success: web_search

→ Action 2/3: fetch_url
  Reasoning: Retrieve the content of Claude Shannon's Wikipedia page to extract birth date, death date, and key contributions.
                    INFO     Processing request of type CallToolRequest                                                                                                                                                                                              server.py:727
[INIT].... → Crawl4AI 0.8.6 
[FETCH]... ↓ https://en.wikipedia.org/wiki/Claude_Shannon                                                         | ✓ | ⏱: 1.90s 
[SCRAPE].. ◆ https://en.wikipedia.org/wiki/Claude_Shannon                                                         | ✓ | ⏱: 0.28s 
[COMPLETE] ● https://en.wikipedia.org/wiki/Claude_Shannon                                                         | ✓ | ⏱: 2.20s 
  Success: fetch_url

→ Action 3/3: respond
  Reasoning: After obtaining the necessary information, provide the final answer to the user.
  Generated final response

============================================================
Agent completed in 1 iteration(s)
Final response:
**Claude Elwood Shannon**  
- **Birth:** April 30 1916  
- **Death:** February 24 2001  

**Three key contributions to information theory**

1. **Shannon entropy** – In his 1948 paper *“A Mathematical Theory of Communication,”* Shannon introduced the concept of entropy as a quantitative measure of information, laying the foundation for the entire field.  
2. **Channel capacity theorem** – He proved the maximum rate at which information can be transmitted over a noisy channel, establishing the theoretical limits of communication systems.  
3. **The bit as the fundamental unit** – Shannon defined the binary digit (bit) as the basic unit of information, formalizing the binary representation of data that underpins modern digital communications and computing.
============================================================


FINAL ANSWER: **Claude Elwood Shannon**  
- **Birth:** April 30 1916  
- **Death:** February 24 2001  

**Three key contributions to information theory**

1. **Shannon entropy** – In his 1948 paper *“A Mathematical Theory of Communication,”* Shannon introduced the concept of entropy as a quantitative measure of information, laying the foundation for the entire field.  
2. **Channel capacity theorem** – He proved the maximum rate at which information can be transmitted over a noisy channel, establishing the theoretical limits of communication systems.  
3. **The bit as the fundamental unit** – Shannon defined the binary digit (bit) as the basic unit of information, formalizing the binary representation of data that underpins modern digital communications and computing.
```

#### Query B: Tokyo activities with weather constraint (multi-goal plus memory carryover)
```bash
uv run python agent6.py "Find 3 family-friendly things to do in Tokyo this weekend. Check Saturday's weather forecast there and tell me which one is most appropriate."

============================================================
Agent Session: 72a4d6ca-4ac5-40ae-8ec3-a018666cb59d
User: Find 3 family-friendly things to do in Tokyo this weekend. Check Saturday's weather forecast there and tell me which one is most appropriate.
============================================================


--- Iteration 1 ---
→ Perception: Analyzing user intent...
  Intent: multi_step_task
  Query: Find 3 family-friendly activities in Tokyo for this weekend, check Saturday's weather forecast, and recommend the most suitable one.
  Confidence: 0.95

→ Memory: Processing memory operations...
  No relevant memories found.

→ Decision: Planning actions...
  Planned 4 action(s)
  Reasoning: The user needs information on activities and weather to make a recommendation. We first get the current date, then search for activities and weather, and finally respond.
  Complete: False

→ Action 1/4: get_time
  Reasoning: Determine the current date to identify the upcoming Saturday for the weather forecast.
[05/26/26 19:20:05] INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
                    INFO     Processing request of type ListToolsRequest                                                                                                                                                                        server.py:727
  Success: get_time

→ Action 2/4: web_search
  Reasoning: Find a list of suitable family-friendly activities happening in Tokyo over the weekend.
                    INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
  Success: web_search

→ Action 3/4: web_search
  Reasoning: Retrieve the weather forecast for Saturday to evaluate which activity is most suitable.
[05/26/26 19:20:07] INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
  Success: web_search

→ Action 4/4: respond
  Reasoning: After gathering activity options and weather info, provide a recommendation.
  Generated final response

============================================================
Agent completed in 1 iteration(s)
Final response:
**Family‑friendly Tokyo plans for the coming Saturday (May 30, 2026)**  

| # | Activity | Why it’s great for families | Notes |
|---|----------|-----------------------------|-------|
| **1** | **Ueno Park – Zoo & National Museum of Nature & Science** |  •  Wide open lawns for running and picnics.<br>•  Ueno Zoo has elephants, giraffes, and hippos that kids love.<br>•  The museum offers hands‑on dinosaur and space exhibits that keep children curious. |  All free admission.  Great for a sunny day. |
| **2** | **Miraikan (National Museum of Emerging Science & Innovation) – Odaiba** |  •  Interactive exhibits on robotics, space, and future tech.<br>•  Kids can try hands‑on displays and learn through play.<br>•  Indoor setting protects from any sudden showers. |  Ticket price ≈ ¥1,800.  Ideal for a rainy‑proof alternative. |
| **3** | **Family Sumo Workshop & Show at Ryogoku Kokugikan** |  •  Kids can try a short sumo match, learn the rules, and watch a live bout.<br>•  Adds a cultural twist to the day. |  Ticket + workshop ≈ ¥8,000–¥10,000.  Book in advance. |

### Which is most suitable for Saturday’s weather?
Saturday’s forecast is **mostly sunny with light clouds** (≈ 26 °C).  
**Ueno Park** is the best match—open air, plenty of shade, and plenty of space for children to run around while the family enjoys the zoo and museum.  

Enjoy your weekend in Tokyo!
============================================================


FINAL ANSWER: **Family‑friendly Tokyo plans for the coming Saturday (May 30, 2026)**  

| # | Activity | Why it’s great for families | Notes |
|---|----------|-----------------------------|-------|
| **1** | **Ueno Park – Zoo & National Museum of Nature & Science** |  •  Wide open lawns for running and picnics.<br>•  Ueno Zoo has elephants, giraffes, and hippos that kids love.<br>•  The museum offers hands‑on dinosaur and space exhibits that keep children curious. |  All free admission.  Great for a sunny day. |
| **2** | **Miraikan (National Museum of Emerging Science & Innovation) – Odaiba** |  •  Interactive exhibits on robotics, space, and future tech.<br>•  Kids can try hands‑on displays and learn through play.<br>•  Indoor setting protects from any sudden showers. |  Ticket price ≈ ¥1,800.  Ideal for a rainy‑proof alternative. |
| **3** | **Family Sumo Workshop & Show at Ryogoku Kokugikan** |  •  Kids can try a short sumo match, learn the rules, and watch a live bout.<br>•  Adds a cultural twist to the day. |  Ticket + workshop ≈ ¥8,000–¥10,000.  Book in advance. |

### Which is most suitable for Saturday’s weather?
Saturday’s forecast is **mostly sunny with light clouds** (≈ 26 °C).  
**Ueno Park** is the best match—open air, plenty of shade, and plenty of space for children to run around while the family enjoys the zoo and museum.  

Enjoy your weekend in Tokyo!
```

#### Query C. Mom's birthday (durable memory across two runs)

##### Run 1
```bash
uv run python agent6.py  "My moms birthday is 15 June 2026. Remember that and give me a calendar reminder for two weeks before and on the day."

============================================================
Agent Session: 5d439208-9411-4e5a-85dc-62d6e6633378
User: My moms birthday is 15 June 2026. Remember that and give me a calendar reminder for two weeks before and on the day.
============================================================


--- Iteration 1 ---
→ Perception: Analyzing user intent...
  Intent: memory_store
  Query: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.
  Confidence: 0.96

→ Memory: Processing memory operations...
  Stored: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.

→ Decision: Planning actions...
  Planned 3 action(s)
  Reasoning: The user's request to remember the birthday and set reminders has been fulfilled by storing the memory, creating a reminder file, and confirming back to the user.
  Complete: True

→ Action 1/3: store_memory
  Reasoning: Persist the user-provided birthday information for future recall.
  Memory stored

→ Action 2/3: create_file
  Reasoning: Create a file to represent the calendar reminders as requested.
[05/26/26 21:54:34] INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
                    INFO     Processing request of type ListToolsRequest                                                                                                                                                                        server.py:727
  Success: create_file

→ Action 3/3: respond
  Reasoning: Provide confirmation to the user that the information has been stored and reminders have been recorded.
  Generated final response

============================================================
Agent completed in 1 iteration(s)
Final response:
I've stored that information: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.
============================================================


FINAL ANSWER: I've stored that information: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.
```

##### Run 2
```bash
uv run python agent6.py  "When is mom's birthday?"

============================================================
Agent Session: be1dde22-e30c-4c74-b64c-53bd09c47833
User: When is mom's birthday?
============================================================


--- Iteration 1 ---
→ Perception: Analyzing user intent...
  Intent: memory_recall
  Query: when is mom's birthday
  Confidence: 0.96

→ Memory: Processing memory operations...
  Found 1 relevant memory: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.

→ Decision: Planning actions...
  Planned 1 action(s)
  Reasoning: Fallback decision for memory_recall
  Complete: True

→ Action 1/1: respond
  Reasoning: Respond with retrieved memories
  Generated final response

============================================================
Agent completed in 1 iteration(s)
Final response:
I recall: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.
============================================================


FINAL ANSWER: I recall: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.
```

#### Query D. Asyncio research (multi-source synthesis)
```bash
uv run python agent6.py  "Search for 'Python asyncio best practices', read the top 3 results, and give me a short numbered list of the advice they agree on."

============================================================
Agent Session: ba5c51a4-8798-4fb1-bfd2-14dde65f6dcd
User: Search for 'Python asyncio best practices', read the top 3 results, and give me a short numbered list of the advice they agree on.
============================================================


--- Iteration 1 ---
→ Perception: Analyzing user intent...
  Intent: search_and_summarize
  Query: Search for Python asyncio best practices, read the top 3 results, and provide a short numbered list of the advice they agree on.
  Confidence: 0.99

→ Memory: Processing memory operations...
  Found 1 relevant memory: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.

→ Decision: Planning actions...
  Planned 4 action(s)
  Reasoning: We need to gather the top three web pages on Python asyncio best practices, read their content, and then synthesize the overlapping recommendations into a concise numbered list. The planned actions first obtain the URLs via a search, then retrieve each page's content. After these fetches succeed, we can analyze the text and respond to the user with the agreed‑upon advice.
  Complete: False

→ Action 1/4: web_search
  Reasoning: Search the web to obtain a list of recent, authoritative articles or guides that discuss best practices for using Python's asyncio library.
[05/26/26 22:00:36] INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
[05/26/26 22:00:38] INFO     Processing request of type ListToolsRequest                                                                                                                                                                        server.py:727
  Success: web_search

→ Action 2/4: fetch_url
  Reasoning: Fetch the full content of the first search result so we can extract the advice it provides.
                    INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
  Success: fetch_url

→ Action 3/4: fetch_url
  Reasoning: Fetch the full content of the second search result to compare its recommendations with the others.
                    INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
  Success: fetch_url

→ Action 4/4: fetch_url
  Reasoning: Fetch the full content of the third search result to have three sources for cross‑checking common best‑practice advice.
                    INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
  Success: fetch_url

--- Iteration 2 ---

→ Memory: Processing memory operations...
  Found 1 relevant memory: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.

→ Decision: Planning actions...
  Planned 3 action(s)
  Reasoning: We need the full content of the top three search results before we can identify the overlapping advice and produce the requested numbered list. After fetching these URLs, we will analyze the content and respond with the summary.
  Complete: False

→ Action 1/3: fetch_url
  Reasoning: Fetch the first search result to extract its asyncio best‑practice advice.
[05/26/26 22:00:50] INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
[INIT].... → Crawl4AI 0.8.6 
[FETCH]... ↓ https://www.shanechang.com/p/python-asyncio-best-practices-pitfalls                                  | ✓ | ⏱: 4.64s 
[SCRAPE].. ◆ https://www.shanechang.com/p/python-asyncio-best-practices-pitfalls                                  | ✓ | ⏱: 0.02s 
[COMPLETE] ● https://www.shanechang.com/p/python-asyncio-best-practices-pitfalls                                  | ✓ | ⏱: 4.67s 
  Success: fetch_url

→ Action 2/3: fetch_url
  Reasoning: Fetch the second search result to extract its asyncio best‑practice advice.
[05/26/26 22:00:57] INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
[INIT].... → Crawl4AI 0.8.6 
[FETCH]... ↓ https://discuss.python.org/t/asyncio-best-practices/12576                                            | ✓ | ⏱: 4.22s 
[SCRAPE].. ◆ https://discuss.python.org/t/asyncio-best-practices/12576                                            | ✓ | ⏱: 0.03s 
[COMPLETE] ● https://discuss.python.org/t/asyncio-best-practices/12576                                            | ✓ | ⏱: 4.26s 
  Success: fetch_url

→ Action 3/3: fetch_url
  Reasoning: Fetch the third search result to extract its asyncio best‑practice advice.
[05/26/26 22:01:02] INFO     Processing request of type CallToolRequest                                                                                                                                                                         server.py:727
[INIT].... → Crawl4AI 0.8.6 
[FETCH]... ↓ https://docs.python.org/3/library/asyncio-dev.html                                                   | ✓ | ⏱: 1.96s 
[SCRAPE].. ◆ https://docs.python.org/3/library/asyncio-dev.html                                                   | ✓ | ⏱: 0.04s 
[COMPLETE] ● https://docs.python.org/3/library/asyncio-dev.html                                                   | ✓ | ⏱: 2.01s 
  Success: fetch_url

--- Iteration 3 ---

→ Memory: Processing memory operations...
  Found 1 relevant memory: Remember that my mom's birthday is June 15 2026 and set calendar reminders for two weeks before and on that day.

→ Decision: Planning actions...
  Planned 1 action(s)
  Reasoning: The required information has been extracted from the fetched pages and summarized into a concise numbered list. No further tool calls are needed.
  Complete: True

→ Action 1/1: respond
  Reasoning: All three sources (Shane's blog, the Async‑SIG discussion, and the official Python docs) emphasize these practices as fundamental to reliable asyncio programs.
  Generated final response

============================================================
Agent completed in 3 iteration(s)
Final response:
**Common advice from the top three sources**

1. **Start your program with `asyncio.run()` (or an equivalent entry‑point).**  
   It creates, configures, and cleanly shuts down the event loop for you.

2. **Never forget to `await` a coroutine.**  
   Always use `await` (or schedule the coroutine as a task) so that the coroutine actually runs and you avoid “never‑awaited” warnings.

3. **Don’t block the event loop with long‑running or synchronous code.**  
   Break up heavy loops into smaller async steps, or off‑load blocking work to a thread/process pool with `loop.run_in_executor` / `asyncio.to_thread`.

4. **Use tasks (`asyncio.create_task`, `await asyncio.gather`, etc.) for concurrency.**  
   Scheduling work as tasks lets the event loop interleave execution safely rather than manually driving the loop.
============================================================


FINAL ANSWER: **Common advice from the top three sources**

1. **Start your program with `asyncio.run()` (or an equivalent entry‑point).**  
   It creates, configures, and cleanly shuts down the event loop for you.

2. **Never forget to `await` a coroutine.**  
   Always use `await` (or schedule the coroutine as a task) so that the coroutine actually runs and you avoid “never‑awaited” warnings.

3. **Don’t block the event loop with long‑running or synchronous code.**  
   Break up heavy loops into smaller async steps, or off‑load blocking work to a thread/process pool with `loop.run_in_executor` / `asyncio.to_thread`.

4. **Use tasks (`asyncio.create_task`, `await asyncio.gather`, etc.) for concurrency.**  
   Scheduling work as tasks lets the event loop interleave execution safely rather than manually driving the loop.
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
