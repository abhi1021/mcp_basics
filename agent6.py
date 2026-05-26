"""
EAGV3 Session 6: Four-layer cognitive agent.

Architecture:
    Perception → Memory → Decision → Action
    └─────────────────┬─────────────────┘
                      Loop

All layers backed by typed Pydantic contracts.
All LLM calls via LLM Gateway V3.
All tool calls via MCP server.
Memory persists across runs in state/.
"""

import asyncio
import sys
import uuid
from datetime import datetime, UTC
from pathlib import Path

# Add llm_gatewayV3 to path for client import
gateway_path = str(Path(__file__).parent / "llm_gatewayV3")
if gateway_path not in sys.path:
    sys.path.append(gateway_path)

from llm_gatewayV3.client import LLM

from action import ActionExecutor, process_action
from decision import process_decision
from memory import MemoryManager, process_memory
from perception import process_perception
from schemas import (
    ActionInput,
    ActionType,
    AgentConfig,
    AgentState,
    DecisionInput,
    IntentType,
    MemoryInput,
    PerceptionInput,
)


class Agent:
    """Four-layer cognitive agent."""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self.llm = LLM(base_url=self.config.llm_gateway_url)
        self.memory_manager = MemoryManager(state_dir=self.config.state_dir)
        self.executor = ActionExecutor(mcp_command=self.config.mcp_server_command)

    async def run(self, user_message: str) -> str:
        """
        Run the agent loop.

        Returns the final response to the user.
        """
        session_id = str(uuid.uuid4())

        state = AgentState(
            session_id=session_id,
            user_message=user_message,
            max_iterations=self.config.max_iterations
        )

        print(f"\n{'='*60}")
        print(f"Agent Session: {session_id}")
        print(f"User: {user_message}")
        print(f"{'='*60}\n")

        try:
            # Connect to MCP server
            await self.executor.connect()

            # Main loop
            while state.iteration < state.max_iterations and not state.is_complete:
                state.iteration += 1
                print(f"\n--- Iteration {state.iteration} ---")

                # 1. PERCEPTION: Parse user input (only on first iteration)
                if state.perception is None:
                    print("→ Perception: Analyzing user intent...")
                    perception_input = PerceptionInput(
                        user_message=user_message,
                        session_id=session_id
                    )
                    state.perception = await process_perception(perception_input, self.llm)

                    print(f"  Intent: {state.perception.intent.intent_type.value}")
                    print(f"  Query: {state.perception.intent.query}")
                    print(f"  Confidence: {state.perception.intent.confidence:.2f}")

                # 2. MEMORY: Retrieve or store memories
                print("\n→ Memory: Processing memory operations...")

                # Determine memory operation
                if state.perception.intent.intent_type == IntentType.MEMORY_STORE:
                    operation = "store"
                    # Extract what to store from the query
                    content = state.perception.intent.query
                else:
                    operation = "retrieve"
                    content = None

                memory_input = MemoryInput(
                    intent=state.perception.intent,
                    session_id=session_id,
                    operation=operation,
                    content=content
                )

                state.memory = await process_memory(memory_input, self.memory_manager)
                print(f"  {state.memory.summary}")

                # 3. DECISION: Plan next actions
                print("\n→ Decision: Planning actions...")

                # Prepare previous actions summary
                previous_actions = []
                for action_output in state.actions:
                    action_dict = {
                        "action_type": action_output.action_type.value,
                        "success": action_output.success,
                        "summary": ""
                    }

                    if action_output.tool_result:
                        if action_output.tool_result.success:
                            action_dict["result"] = action_output.tool_result.result
                            action_dict["summary"] = f"{action_output.tool_result.tool_name} succeeded"
                        else:
                            action_dict["summary"] = f"{action_output.tool_result.tool_name} failed: {action_output.tool_result.error}"
                    elif action_output.response_text:
                        action_dict["summary"] = action_output.response_text

                    previous_actions.append(action_dict)

                decision_input = DecisionInput(
                    intent=state.perception.intent,
                    memory_context=state.memory,
                    session_id=session_id,
                    previous_actions=previous_actions
                )

                state.decision = await process_decision(decision_input, self.llm)

                print(f"  Planned {len(state.decision.planned_actions)} action(s)")
                print(f"  Reasoning: {state.decision.reasoning}")
                print(f"  Complete: {state.decision.is_complete}")

                # 4. ACTION: Execute planned actions
                for i, planned_action in enumerate(state.decision.planned_actions):
                    print(f"\n→ Action {i+1}/{len(state.decision.planned_actions)}: {planned_action.action_type.value}")
                    print(f"  Reasoning: {planned_action.reasoning}")

                    # Handle RESPOND action specially
                    if planned_action.action_type == ActionType.RESPOND:
                        state.final_response = await self._generate_final_response(state)
                        state.is_complete = True
                        print(f"  Generated final response")
                        break

                    # Handle STORE_MEMORY action
                    if planned_action.action_type == ActionType.STORE_MEMORY:
                        # Already handled in memory layer, just mark success
                        action_output = await process_action(
                            ActionInput(
                                planned_action=planned_action,
                                session_id=session_id
                            ),
                            self.executor
                        )
                        state.actions.append(action_output)
                        print(f"  Memory stored")
                        continue

                    # Execute tool action
                    action_output = await process_action(
                        ActionInput(
                            planned_action=planned_action,
                            session_id=session_id
                        ),
                        self.executor
                    )

                    state.actions.append(action_output)

                    if action_output.success and action_output.tool_result:
                        print(f"  Success: {action_output.tool_result.tool_name}")
                        if self.config.enable_debug:
                            print(f"  Result: {action_output.tool_result.result}")
                    elif not action_output.success:
                        error_msg = action_output.tool_result.error if action_output.tool_result else "Unknown error"
                        print(f"  Failed: {error_msg}")

                # Check if decision says we're complete
                if state.decision.is_complete:
                    if not state.final_response:
                        state.final_response = await self._generate_final_response(state)
                    state.is_complete = True

            # End of loop
            if not state.is_complete:
                state.final_response = f"Maximum iterations ({state.max_iterations}) reached."

            state.end_time = datetime.now(UTC)

        finally:
            # Cleanup
            await self.executor.disconnect()

        # Print summary
        print(f"\n{'='*60}")
        print(f"Agent completed in {state.iteration} iteration(s)")
        print(f"Final response:\n{state.final_response}")
        print(f"{'='*60}\n")

        return state.final_response

    async def _generate_final_response(self, state: AgentState) -> str:
        """Generate final response to user based on state."""
        intent_type = state.perception.intent.intent_type

        # Handle memory storage
        if intent_type == IntentType.MEMORY_STORE and state.memory.stored_memory:
            return f"I've stored that information: {state.memory.stored_memory.content}"

        # Handle memory recall
        if intent_type == IntentType.MEMORY_RECALL:
            if state.memory.retrieved_memories:
                memories = [m.content for m in state.memory.retrieved_memories]
                if len(memories) == 1:
                    return f"I recall: {memories[0]}"
                else:
                    # Return the most recent memory
                    return f"I recall: {memories[0]}"
            else:
                return "I don't have any memory of that."

        # Handle time queries
        if intent_type == IntentType.TIME_QUERY and state.actions:
            for action in state.actions:
                if action.action_type == ActionType.GET_TIME and action.tool_result and action.tool_result.success:
                    result = action.tool_result.result
                    if isinstance(result, dict):
                        return f"The current time is: {result.get('human', result.get('iso', 'unknown'))}"
                    return f"The current time is: {result}"

        # For factual queries with memory results, use them directly
        if intent_type == IntentType.FACTUAL_QUERY and state.memory.retrieved_memories:
            memories = [m.content for m in state.memory.retrieved_memories]
            if len(memories) == 1:
                return memories[0]
            else:
                return memories[0]  # Return most recent

        # Use LLM to synthesize final response from all gathered information
        context_parts = [
            f"User asked: {state.user_message}",
            f"Intent: {state.perception.intent.intent_type.value}",
        ]

        if state.memory.retrieved_memories:
            context_parts.append(f"Retrieved memories: {state.memory.summary}")

        if state.actions:
            context_parts.append("\nActions taken:")
            for i, action in enumerate(state.actions, 1):
                if action.tool_result and action.tool_result.success:
                    result_str = str(action.tool_result.result)
                    if len(result_str) > 10000:
                        result_str = result_str[:10000] + "..."
                    context_parts.append(f"{i}. {action.action_type.value}: {result_str}")

        context = "\n".join(context_parts)

        prompt = f"""{context}

Based on the above context, provide a clear and concise final answer to the user's question.
Do not mention internal processes, tools, or iterations. Just answer the question naturally."""

        try:
            response = self.llm.chat(
                prompt,
                auto_route="decision",
                temperature=0.7,
                max_tokens=1000
            )
            return response.get("text", "").strip()
        except Exception as e:
            # Fallback: return basic summary if LLM fails
            print(f"Warning: Final response LLM failed ({e}), using fallback")
            if state.actions:
                last_action = state.actions[-1]
                if last_action.tool_result and last_action.tool_result.success:
                    result = str(last_action.tool_result.result)
                    return result[:500]  # Truncate if too long
            return "I encountered an issue generating the final response."


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run python agent6.py '<query>'")
        print("\nExample queries:")
        print("  uv run python agent6.py 'What is the capital of France?'")
        print("  uv run python agent6.py 'Remember that my favorite color is blue'")
        print("  uv run python agent6.py 'What is my favorite color?'")
        print("  uv run python agent6.py 'Search for Python asyncio tutorials and summarize'")
        sys.exit(1)

    query = sys.argv[1]

    config = AgentConfig(
        max_iterations=10,
        enable_debug=False
    )

    agent = Agent(config)
    result = await agent.run(query)

    print(f"\nFINAL ANSWER: {result}")


if __name__ == "__main__":
    asyncio.run(main())
