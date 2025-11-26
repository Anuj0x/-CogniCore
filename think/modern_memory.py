"""
Modern memory management with vector search and persistence.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import MemoryConfig
from ..core.logger import logger
from ..llm.provider import LLMProvider


@dataclass
class MemoryItem:
    """A single memory item with metadata."""

    id: str
    content: str
    memory_type: str  # "thought", "action", "observation", "goal", "message"
    timestamp: float
    importance: float = 1.0
    context: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    @property
    def age_seconds(self) -> float:
        """Get age of memory in seconds."""
        return time.time() - self.timestamp

    @property
    def age_hours(self) -> float:
        """Get age of memory in hours."""
        return self.age_seconds / 3600

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime if present
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryItem:
        """Create from dictionary."""
        return cls(**data)


class MemoryManager:
    """Modern memory management system."""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self.memories: List[MemoryItem] = []
        self.message_history: List[Dict[str, Any]] = []
        self.thought_history: List[MemoryItem] = []

        # Persistence
        self.persistence_path = config.persistence_path
        self.auto_save_task: Optional[asyncio.Task] = None

        # LLM for summarization
        self.llm: Optional[LLMProvider] = None

    async def initialize(self) -> None:
        """Initialize memory system."""
        logger.info("Initializing memory system...")

        # Load persisted memories
        await self._load_memories()

        # Start auto-save task
        if self.config.auto_summarize:
            self.auto_save_task = asyncio.create_task(self._auto_summarize_loop())

        logger.info(f"✅ Memory system initialized with {len(self.memories)} items")

    async def shutdown(self) -> None:
        """Shutdown memory system."""
        if self.auto_save_task:
            self.auto_save_task.cancel()
            try:
                await self.auto_save_task
            except asyncio.CancelledError:
                pass

        # Final save
        await self._save_memories()

    async def store_experience(self, decision: Any, result: Any) -> None:
        """Store action experience for learning."""
        memory = MemoryItem(
            id=f"action_{int(time.time())}_{hash(str(decision))}",
            content=f"Action: {decision.action if hasattr(decision, 'action') else str(decision)}",
            memory_type="action",
            context={
                "decision": str(decision),
                "result": str(result),
                "success": getattr(result, 'success', False)
            }
        )

        await self._store_memory(memory)

    async def store_message(self, role: str, content: str) -> None:
        """Store chat message."""
        memory = MemoryItem(
            id=f"msg_{int(time.time())}_{hash(content)}",
            content=content,
            memory_type="message",
            context={"role": role}
        )

        await self._store_memory(memory)

        # Also keep in message history for context
        self.message_history.append({
            "role": role,
            "content": content,
            "timestamp": memory.timestamp
        })

        # Trim message history if too long
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]

    async def store_goal(self, goal: str) -> None:
        """Store a goal."""
        memory = MemoryItem(
            id=f"goal_{int(time.time())}",
            content=goal,
            memory_type="goal",
            importance=2.0,  # Goals are more important
            context={"active": True}
        )

        await self._store_memory(memory)

    async def get_context(self, max_items: int = 20) -> Dict[str, Any]:
        """Get relevant context for decision making."""
        # Get recent memories, sorted by importance and recency
        relevant = sorted(
            self.memories,
            key=lambda m: m.importance * (1 / (1 + m.age_hours)),  # Importance weighted by recency
            reverse=True
        )[:max_items]

        return {
            "recent_memories": [m.to_dict() for m in relevant],
            "message_history": self.message_history[-10:],  # Last 10 messages
            "active_goals": [
                m.to_dict() for m in relevant
                if m.memory_type == "goal" and m.context.get("active", False)
            ],
            "current_thoughts": [m.to_dict() for m in self.thought_history[-5:]]
        }

    async def search_memories(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Search memories by content similarity."""
        # Simple text-based search (could be enhanced with vector search)
        query_lower = query.lower()
        matches = [
            memory for memory in self.memories
            if query_lower in memory.content.lower()
        ]

        # Sort by recency and importance
        matches.sort(key=lambda m: m.importance * (1 / (1 + m.age_hours)), reverse=True)

        return matches[:limit]

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_memories = len(self.memories)
        memory_types = {}
        for memory in self.memories:
            memory_types[memory.memory_type] = memory_types.get(memory.memory_type, 0) + 1

        avg_importance = sum(m.importance for m in self.memories) / max(total_memories, 1)

        return {
            "total_memories": total_memories,
            "memory_types": memory_types,
            "average_importance": avg_importance,
            "message_count": len(self.message_history),
        }

    async def _store_memory(self, memory: MemoryItem) -> None:
        """Store a memory item."""
        self.memories.append(memory)

        # Keep memories within limits
        if len(self.memories) > 1000:  # Configurable limit
            # Remove oldest, least important memories
            self.memories.sort(key=lambda m: m.importance * (1 / (1 + m.age_hours)))
            self.memories = self.memories[-900:]  # Keep 900 most relevant

        # Persist periodically
        await self._save_memories()

    async def _load_memories(self) -> None:
        """Load memories from persistence."""
        if not self.persistence_path.exists():
            return

        try:
            data = json.loads(self.persistence_path.read_text(encoding="utf-8"))

            self.memories = [MemoryItem.from_dict(item) for item in data.get("memories", [])]
            self.message_history = data.get("messages", [])
            self.thought_history = [
                MemoryItem.from_dict(item) for item in data.get("thoughts", [])
            ]

            logger.info(f"Loaded {len(self.memories)} memories from persistence")

        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
            # Start with empty memories
            self.memories = []

    async def _save_memories(self) -> None:
        """Save memories to persistence."""
        try:
            data = {
                "memories": [m.to_dict() for m in self.memories],
                "messages": self.message_history,
                "thoughts": [m.to_dict() for m in self.thought_history],
                "saved_at": datetime.now().isoformat()
            }

            self.persistence_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save memories: {e}")

    async def _auto_summarize_loop(self) -> None:
        """Background task to summarize old memories."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self._summarize_old_memories()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-summarize: {e}")

    async def _summarize_old_memories(self) -> None:
        """Summarize old, less important memories."""
        old_threshold_hours = 24  # 24 hours
        batch_size = 10

        # Find old memories to summarize
        old_memories = [
            m for m in self.memories
            if m.age_hours > old_threshold_hours and m.importance < 1.5
        ][:batch_size]

        if not old_memories:
            return

        if not self.llm:
            return  # Can't summarize without LLM

        try:
            # Combine old memories
            combined_content = "\n".join([
                f"- {m.memory_type.upper()}: {m.content}"
                for m in old_memories
            ])

            # Generate summary
            summary_prompt = f"""
            Summarize these old memories into a concise paragraph (max 100 words).
            Focus on key information and patterns:

            {combined_content}
            """

            summary = await self.llm.generate(summary_prompt, max_tokens=150)

            # Create summary memory
            summary_memory = MemoryItem(
                id=f"summary_{int(time.time())}",
                content=f"Summary of {len(old_memories)} old memories: {summary}",
                memory_type="summary",
                importance=1.0,
                context={"summarized_count": len(old_memories)}
            )

            # Replace old memories with summary
            for old_memory in old_memories:
                self.memories.remove(old_memory)
            self.memories.append(summary_memory)

            logger.debug(f"Summarized {len(old_memories)} old memories")

        except Exception as e:
            logger.error(f"Failed to summarize memories: {e}")
