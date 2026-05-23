"""
Perception layer for EAGV3 Session 6 agent.

Responsibilities:
- Parse user input into structured intent
- Classify intent type
- Extract entities and parameters
- Determine which tools are needed
"""

import json
import sys
from pathlib import Path

# Add llm_gatewayV3 to path for client import
gateway_path = str(Path(__file__).parent / "llm_gatewayV3")
if gateway_path not in sys.path:
    sys.path.append(gateway_path)

from client import LLM
from schemas import Intent, IntentType, PerceptionInput, PerceptionOutput


PERCEPTION_PROMPT = """You are a perception layer that classifies user intents and extracts structured information.

Analyze the user message and classify it into one of these intent types:
- factual_query: Simple factual questions (What is X? When did Y happen?)
- memory_store: User wants to remember something (Remember that..., Store this fact...)
- memory_recall: User wants to retrieve stored information (What did I tell you about...?, Recall...)
- search_and_summarize: Needs web search and summarization
- time_query: Asking about current time
- currency_conversion: Converting between currencies
- file_operation: Reading, writing, or editing files
- multi_step_task: Complex task requiring multiple steps

Extract:
1. intent_type: The classified intent
2. query: Clean normalized version of the query
3. entities: Relevant entities (names, dates, amounts, etc.)
4. requires_tools: List of tools needed (web_search, fetch_url, get_time, currency_convert, read_file, etc.)
5. confidence: Your confidence in this classification (0.0-1.0)

User message: {user_message}

Respond with valid JSON matching this structure:
{{
  "intent_type": "<intent_type>",
  "query": "<normalized_query>",
  "entities": {{}},
  "requires_tools": [],
  "confidence": 0.95
}}"""


async def process_perception(
    perception_input: PerceptionInput,
    llm: LLM
) -> PerceptionOutput:
    """
    Process perception layer input using LLM Gateway V3.

    Classifies user intent and extracts structured information.
    """
    prompt = PERCEPTION_PROMPT.format(user_message=perception_input.user_message)

    # Use auto_route for perception layer
    response = llm.chat(
        prompt,
        auto_route="perception",
        temperature=0.3,
        max_tokens=500
    )

    # Parse the LLM response
    text = response.get("text", "").strip()

    # Try to extract JSON from the response
    try:
        # Look for JSON in the response
        json_start = text.find("{")
        json_end = text.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")

        json_text = text[json_start:json_end]
        intent_data = json.loads(json_text)

        # Validate and create Intent object
        intent = Intent(
            intent_type=IntentType(intent_data["intent_type"]),
            query=intent_data["query"],
            entities=intent_data.get("entities", {}),
            requires_tools=intent_data.get("requires_tools", []),
            confidence=intent_data.get("confidence", 0.8)
        )

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # Fallback: create a basic intent from the raw message
        print(f"Warning: Failed to parse LLM response: {e}")
        print(f"Response was: {text}")

        # Determine intent type based on keywords
        msg_lower = perception_input.user_message.lower()

        if "remember" in msg_lower or "store" in msg_lower or "save" in msg_lower:
            intent_type = IntentType.MEMORY_STORE
        elif "recall" in msg_lower or "what did i" in msg_lower or "told you" in msg_lower:
            intent_type = IntentType.MEMORY_RECALL
        elif "time" in msg_lower or "what time" in msg_lower or "when is" in msg_lower:
            intent_type = IntentType.TIME_QUERY
        elif "convert" in msg_lower and any(curr in msg_lower for curr in ["usd", "eur", "gbp", "inr", "dollar", "euro", "currency"]):
            intent_type = IntentType.CURRENCY_CONVERSION
        elif "search" in msg_lower or "find" in msg_lower or "look up" in msg_lower:
            intent_type = IntentType.SEARCH_AND_SUMMARIZE
        elif "file" in msg_lower or "read" in msg_lower or "write" in msg_lower:
            intent_type = IntentType.FILE_OPERATION
        else:
            intent_type = IntentType.FACTUAL_QUERY

        intent = Intent(
            intent_type=intent_type,
            query=perception_input.user_message,
            entities={},
            requires_tools=[],
            confidence=0.5
        )

    return PerceptionOutput(intent=intent)
