"""
Memory layer for EAGV3 Session 6 agent.

Responsibilities:
- Store facts and conversation history persistently
- Retrieve relevant memories based on queries
- Manage memory lifecycle (create, read, update)
- Persist to disk under state/ directory
"""

import json
import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from schemas import (
    Intent,
    MemoryEntry,
    MemoryInput,
    MemoryOutput,
    MemoryQuery,
    MemoryType,
)


class MemoryManager:
    """Manages persistent memory storage and retrieval."""

    def __init__(self, state_dir: str = "state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.memory_file = self.state_dir / "memories.jsonl"
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Ensure the memory file exists."""
        if not self.memory_file.exists():
            self.memory_file.touch()

    def _load_all_memories(self) -> list[MemoryEntry]:
        """Load all memories from disk."""
        memories = []
        if not self.memory_file.exists():
            return memories

        with open(self.memory_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        entry = MemoryEntry.model_validate(data)
                        if entry.timestamp.tzinfo is None:
                            entry.timestamp = entry.timestamp.replace(tzinfo=UTC)
                        memories.append(entry)
                    except (json.JSONDecodeError, Exception) as e:
                        print(f"Warning: Failed to parse memory line: {e}")

        return memories

    def _append_memory(self, memory: MemoryEntry) -> None:
        """Append a memory to the persistent store."""
        with open(self.memory_file, "a", encoding="utf-8") as f:
            f.write(memory.model_dump_json() + "\n")

    def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        session_id: str,
        metadata: dict[str, Any] | None = None
    ) -> MemoryEntry:
        """Store a new memory entry."""
        memory = MemoryEntry(
            memory_id=str(uuid.uuid4()),
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
            session_id=session_id,
            timestamp=datetime.now(UTC)
        )
        self._append_memory(memory)
        return memory

    def retrieve_memories(self, query: MemoryQuery) -> list[MemoryEntry]:
        """Retrieve memories matching the query."""
        all_memories = self._load_all_memories()

        # Filter by memory types if specified
        if query.memory_types:
            all_memories = [
                m for m in all_memories
                if m.memory_type in query.memory_types
            ]

        # Filter by session if specified
        if query.session_id:
            all_memories = [
                m for m in all_memories
                if m.session_id == query.session_id
            ]

        # Simple keyword-based relevance scoring
        query_lower = query.query.lower()
        query_words = set(query_lower.split())

        scored_memories = []
        for memory in all_memories:
            content_lower = memory.content.lower()
            content_words = set(content_lower.split())

            # Calculate overlap score
            overlap = len(query_words & content_words)
            if overlap > 0 or query_lower in content_lower:
                score = overlap + (2 if query_lower in content_lower else 0)
                scored_memories.append((score, memory))

        # Sort by score (descending) and timestamp (most recent first)
        scored_memories.sort(key=lambda x: (x[0], x[1].timestamp), reverse=True)

        # Return top results
        return [mem for _, mem in scored_memories[:query.limit]]

    def summarize_memories(self, memories: list[MemoryEntry], query: str) -> str:
        """Generate a summary of retrieved memories."""
        if not memories:
            return "No relevant memories found."

        if len(memories) == 1:
            return f"Found 1 relevant memory: {memories[0].content}"

        summary_parts = [f"Found {len(memories)} relevant memories:"]
        for i, mem in enumerate(memories, 1):
            summary_parts.append(f"{i}. [{mem.memory_type.value}] {mem.content}")

        return "\n".join(summary_parts)


async def process_memory(
    memory_input: MemoryInput,
    memory_manager: MemoryManager
) -> MemoryOutput:
    """
    Process memory layer input.

    Either stores a new memory or retrieves relevant memories.
    """
    if memory_input.operation == "store":
        # Store a new memory
        if not memory_input.content:
            raise ValueError("Content required for store operation")

        stored = memory_manager.store_memory(
            content=memory_input.content,
            memory_type=MemoryType.FACT,
            session_id=memory_input.session_id,
            metadata={"intent": memory_input.intent.intent_type.value}
        )

        return MemoryOutput(
            stored_memory=stored,
            summary=f"Stored: {stored.content}"
        )

    elif memory_input.operation == "retrieve":
        # Retrieve relevant memories
        # For memory_recall, search ALL sessions (session_id=None)
        # For other queries, can optionally filter by current session
        query = MemoryQuery(
            query=memory_input.intent.query,
            session_id=None,  # Search all sessions
            limit=5
        )

        memories = memory_manager.retrieve_memories(query)
        summary = memory_manager.summarize_memories(memories, query.query)

        return MemoryOutput(
            retrieved_memories=memories,
            summary=summary
        )

    else:
        raise ValueError(f"Unknown operation: {memory_input.operation}")
