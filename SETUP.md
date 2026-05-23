# Quick Setup Guide

## Prerequisites

1. Python 3.14+
2. uv installed (`pip install uv`)

## Step 1: Install Dependencies

```bash
# Install core agent dependencies
uv sync

# Install MCP server dependencies (separate)
cd llm_gatewayV3
pip install -r requirements.txt
cd ..
```

## Step 2: Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit .env and add at least one API key:
# - GEMINI_API_KEY (easiest to get)
# - GROQ_API_KEY
# - NVIDIA_API_KEY
# - Or any other supported provider
```

Minimum `.env` example:
```bash
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

## Step 3: Start LLM Gateway V3

The agent requires the gateway to be running:

```bash
cd llm_gatewayV3
./run.sh
```

In a new terminal, verify:
```bash
curl http://localhost:8101/v1/providers
```

## Step 4: Run the Agent

```bash
# Basic test
uv run python agent6.py 'What is 2+2?'

# Memory test
uv run python agent6.py 'Remember that my name is Alice'
uv run python agent6.py 'What is my name?'

# Web search test
uv run python agent6.py 'What is the capital of France?'
```

## Troubleshooting

### Gateway not running
```bash
cd llm_gatewayV3
./run.sh

# Or manually:
./.venv/bin/python main.py
```

### Missing API keys
- Add at least one provider key to `.env`
- Restart gateway after editing `.env`

### MCP server fails
```bash
# Install MCP dependencies
pip install crawl4ai duckduckgo-search tavily-python

# Test MCP server
uv run python mcp_server.py
# Should show: "MCP server initialized"
```

### State directory issues
```bash
mkdir -p state
chmod 755 state
```

## Architecture Verification

Check that all modules exist:
```bash
ls -1 *.py
# Should show:
# - agent6.py
# - schemas.py
# - perception.py
# - memory.py
# - decision.py
# - action.py
# - mcp_server.py
```

Check state directory:
```bash
ls -ld state/
# Should exist and be writable
```

## Next Steps

See README.md for full documentation and example queries.
