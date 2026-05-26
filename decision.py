"""
Decision layer for EAGV3 Session 6 agent.

Responsibilities:
- Plan next actions based on intent and memory context
- Determine tool calls needed
- Decide when task is complete
- Provide reasoning for decisions
"""

import json
import sys
from pathlib import Path

# Add llm_gatewayV3 to path for client import
gateway_path = str(Path(__file__).parent / "llm_gatewayV3")
if gateway_path not in sys.path:
    sys.path.append(gateway_path)

from client import LLM
from schemas import ActionType, DecisionInput, DecisionOutput, IntentType, PlannedAction


DECISION_PROMPT = """You are a decision-making layer for an agent. Given the current state, plan the next actions.

User Intent:
- Type: {intent_type}
- Query: {query}
- Required Tools: {requires_tools}

Memory Context:
{memory_summary}

Previous Actions Taken:
{previous_actions}

Your task is to decide what actions to take next. Consider:
1. Has the task been completed based on previous actions?
2. What tools need to be called?
3. What are the parameters for each tool?
4. Should we store any results in memory?
5. Should we respond to the user?

Available action types:
- web_search: Search the web (tool: web_search)
- fetch_url: Fetch content from URL (tool: fetch_url)
- get_time: Get current time (tool: get_time)
- currency_convert: Convert currency (tool: currency_convert)
- read_file: Read a file (tool: read_file)
- list_dir: List directory (tool: list_dir)
- create_file: Create file (tool: create_file)
- update_file: Update file (tool: update_file)
- edit_file: Edit file (tool: edit_file)
- store_memory: Store in persistent memory
- respond: Final response to user (no more actions)

Respond with valid JSON:
{{
  "planned_actions": [
    {{
      "action_type": "<action_type>",
      "tool_name": "<tool_name or null>",
      "parameters": {{}},
      "reasoning": "<why this action>"
    }}
  ],
  "is_complete": false,
  "reasoning": "<overall reasoning>"
}}

IMPORTANT:
- If previous actions have already answered the question, set is_complete=true and include a "respond" action
- For memory_store intents, use store_memory action
- For memory_recall intents, check if memory_summary has the answer, then respond
- If the user asks to create or set calendar reminders, record them by writing a file inside the sandbox (e.g. using "create_file" with a path like "reminders/mom_birthday_2026.txt" containing the birthday and the requested reminder dates).
- Always end with a "respond" action when the task is complete
- You must strictly output one of the available action types listed above. Do not invent any new action_type.
"""


async def process_decision(
    decision_input: DecisionInput,
    llm: LLM
) -> DecisionOutput:
    """
    Process decision layer input using LLM Gateway V3.

    Plans next actions based on intent, memory, and previous actions.
    """
    # For simple intents, use fallback directly to avoid LLM issues
    # But if the query contains reminder/calendar keywords, we need complex planning (e.g. creating files)!
    needs_complex_planning = any(word in decision_input.intent.query.lower() for word in ["reminder", "calendar", "remind", "schedule", "file"])
    if decision_input.intent.intent_type in (IntentType.MEMORY_STORE, IntentType.MEMORY_RECALL) and not needs_complex_planning:
        return _create_fallback_decision(decision_input)

    # Format previous actions
    prev_actions_text = "None yet"
    if decision_input.previous_actions:
        formatted = []
        for i, act in enumerate(decision_input.previous_actions):
            item = f"- {i+1}. {act.get('action_type', 'unknown')}: {act.get('summary', str(act))}"
            if "result" in act:
                item += f"\n   Result: {json.dumps(act['result'])}"
            formatted.append(item)
        prev_actions_text = "\n".join(formatted)

    prompt = DECISION_PROMPT.format(
        intent_type=decision_input.intent.intent_type.value,
        query=decision_input.intent.query,
        requires_tools=", ".join(decision_input.intent.requires_tools) if decision_input.intent.requires_tools else "None",
        memory_summary=decision_input.memory_context.summary,
        previous_actions=prev_actions_text
    )

    # Use auto_route for decision layer
    try:
        response = llm.chat(
            prompt,
            auto_route="decision",
            temperature=0.4,
            max_tokens=2048
        )
    except Exception as e:
        print(f"Warning: LLM decision failed ({e}), using fallback")
        return _create_fallback_decision(decision_input)

    text = response.get("text", "").strip()

    # Parse the decision
    try:
        json_start = text.find("{")
        json_end = text.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")

        json_text = text[json_start:json_end]
        decision_data = json.loads(json_text)

        planned_actions = []
        for action_data in decision_data.get("planned_actions", []):
            planned_actions.append(PlannedAction(
                action_type=ActionType(action_data["action_type"]),
                tool_name=action_data.get("tool_name"),
                parameters=action_data.get("parameters", {}),
                reasoning=action_data.get("reasoning", "")
            ))

        return DecisionOutput(
            planned_actions=planned_actions,
            is_complete=decision_data.get("is_complete", False),
            reasoning=decision_data.get("reasoning", "Planned actions based on current state")
        )

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Warning: Failed to parse decision response: {e}")
        print(f"Response was: {text}")

        # Fallback: create basic actions based on intent
        return _create_fallback_decision(decision_input)


def _create_fallback_decision(decision_input: DecisionInput) -> DecisionOutput:
    """Create fallback decision when LLM parsing fails."""
    intent_type = decision_input.intent.intent_type
    planned_actions = []

    if intent_type == IntentType.FACTUAL_QUERY:
        # Check if we already have information from memory
        if decision_input.memory_context.retrieved_memories or decision_input.previous_actions:
            planned_actions.append(PlannedAction(
                action_type=ActionType.RESPOND,
                reasoning="Have information to respond"
            ))
            is_complete = True
        else:
            # Need to search
            planned_actions.append(PlannedAction(
                action_type=ActionType.WEB_SEARCH,
                tool_name="web_search",
                parameters={"query": decision_input.intent.query, "max_results": 3},
                reasoning="Search for factual information"
            ))
            is_complete = False

    elif intent_type == IntentType.MEMORY_STORE:
        planned_actions.append(PlannedAction(
            action_type=ActionType.STORE_MEMORY,
            reasoning="Store information in memory"
        ))
        planned_actions.append(PlannedAction(
            action_type=ActionType.RESPOND,
            reasoning="Confirm storage"
        ))
        is_complete = True

    elif intent_type == IntentType.MEMORY_RECALL:
        planned_actions.append(PlannedAction(
            action_type=ActionType.RESPOND,
            reasoning="Respond with retrieved memories"
        ))
        is_complete = True

    elif intent_type == IntentType.TIME_QUERY:
        if decision_input.previous_actions:
            planned_actions.append(PlannedAction(
                action_type=ActionType.RESPOND,
                reasoning="Respond with time"
            ))
            is_complete = True
        else:
            planned_actions.append(PlannedAction(
                action_type=ActionType.GET_TIME,
                tool_name="get_time",
                parameters={"timezone": "UTC"},
                reasoning="Get current time"
            ))
            is_complete = False

    elif intent_type == IntentType.SEARCH_AND_SUMMARIZE:
        if not decision_input.previous_actions:
            # First action: search
            planned_actions.append(PlannedAction(
                action_type=ActionType.WEB_SEARCH,
                tool_name="web_search",
                parameters={"query": decision_input.intent.query, "max_results": 3},
                reasoning="Search for information"
            ))
            is_complete = False
        elif len(decision_input.previous_actions) == 1:
            # Second action: fetch top result if available
            prev_result = decision_input.previous_actions[0].get("result")
            if prev_result and isinstance(prev_result, list) and len(prev_result) > 0:
                url = prev_result[0].get("url", "")
                if url:
                    planned_actions.append(PlannedAction(
                        action_type=ActionType.FETCH_URL,
                        tool_name="fetch_url",
                        parameters={"url": url},
                        reasoning="Fetch content for summarization"
                    ))
                    is_complete = False
                else:
                    planned_actions.append(PlannedAction(
                        action_type=ActionType.RESPOND,
                        reasoning="No valid URL found"
                    ))
                    is_complete = True
            else:
                planned_actions.append(PlannedAction(
                    action_type=ActionType.RESPOND,
                    reasoning="No search results"
                ))
                is_complete = True
        else:
            # Third action: respond with summary
            planned_actions.append(PlannedAction(
                action_type=ActionType.RESPOND,
                reasoning="Respond with summary"
            ))
            is_complete = True

    else:
        # Default: just respond
        planned_actions.append(PlannedAction(
            action_type=ActionType.RESPOND,
            reasoning="Handle query"
        ))
        is_complete = True

    return DecisionOutput(
        planned_actions=planned_actions,
        is_complete=is_complete,
        reasoning=f"Fallback decision for {intent_type.value}"
    )
