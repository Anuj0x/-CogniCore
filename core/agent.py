"""
Core AutoGPT agent with modern async architecture.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import AutoGPTConfig
from .logger import logger
from ..think.modern_memory import MemoryManager
from ..think.modern_reasoning import ReasoningEngine
from ..action.modern_executor import ActionExecutor
from ..integrations.telegram import TelegramIntegration


@dataclass
class AgentState:
    """Current state of the AI agent."""

    is_active: bool = True
    last_action: Optional[str] = None
    current_goal: Optional[str] = None
    action_count: int = 0
    error_count: int = 0
    start_time: datetime = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()


class AutoGPTAgent:
    """Modern AutoGPT agent with async architecture."""

    def __init__(self, config: AutoGPTConfig):
        self.config = config
        self.state = AgentState()

        # Core components
        self.memory = MemoryManager(config.memory)
        self.reasoning = ReasoningEngine(config)
        self.executor = ActionExecutor(config)

        # Integrations
        self.telegram: Optional[TelegramIntegration] = None

        logger.info("🤖 AutoGPT Agent initialized")

    async def initialize(self) -> None:
        """Initialize all agent components."""
        logger.info("Initializing agent components...")

        await self.memory.initialize()
        await self.reasoning.initialize()
        await self.executor.initialize()

        # Load saved state if exists
        await self._load_state()

        logger.info("✅ Agent components initialized")

    async def shutdown(self) -> None:
        """Cleanup agent resources."""
        logger.info("Shutting down agent...")

        await self._save_state()
        await self.memory.shutdown()
        await self.executor.shutdown()

        logger.info("👋 Agent shutdown complete")

    async def think_and_act(self) -> None:
        """Main agent thinking and action loop."""
        try:
            # Get current context from memory
            context = await self.memory.get_context()

            # Determine what to do next
            decision = await self.reasoning.decide_next_action(context)

            # Execute the decided action
            result = await self.executor.execute_action(decision)

            # Learn from the result
            await self.memory.store_experience(decision, result)

            # Update state
            self.state.last_action = decision.action
            self.state.action_count += 1

            # Notify user if configured
            if self.telegram and self.config.telegram.enable_notifications:
                await self.telegram.send_notification(
                    f"Action completed: {decision.action}",
                    result.success
                )

        except Exception as e:
            logger.error(f"Error in think_and_act: {e}", exc_info=True)
            self.state.error_count += 1

            # Don't fail the entire loop on errors
            await asyncio.sleep(1)

    async def process_user_input(self, user_input: str) -> str:
        """Process direct user input and respond."""
        logger.info(f"Processing user input: {user_input[:100]}...")

        # Store user input in memory
        await self.memory.store_message("user", user_input)

        # Generate response using reasoning engine
        response = await self.reasoning.generate_response(user_input)

        # Store response in memory
        await self.memory.store_message("assistant", response)

        return response

    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        uptime = datetime.now() - self.state.start_time

        return {
            "active": self.state.is_active,
            "uptime_seconds": uptime.total_seconds(),
            "action_count": self.state.action_count,
            "error_count": self.state.error_count,
            "current_goal": self.state.current_goal,
            "last_action": self.state.last_action,
            "memory_stats": await self.memory.get_stats(),
        }

    async def set_goal(self, goal: str) -> None:
        """Set a new goal for the agent."""
        logger.info(f"Setting new goal: {goal}")
        self.state.current_goal = goal

        # Store goal in memory
        await self.memory.store_goal(goal)

        # Notify reasoning engine
        await self.reasoning.update_goal(goal)

    async def _load_state(self) -> None:
        """Load agent state from persistence."""
        state_file = Path("agent_state.json")
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                # Convert datetime string back
                if "start_time" in data:
                    data["start_time"] = datetime.fromisoformat(data["start_time"])

                self.state = AgentState(**data)
                logger.info("Agent state loaded from persistence")
            except Exception as e:
                logger.warning(f"Failed to load agent state: {e}")

    async def _save_state(self) -> None:
        """Save agent state to persistence."""
        try:
            state_file = Path("agent_state.json")
            data = asdict(self.state)
            # Convert datetime to ISO format
            data["start_time"] = data["start_time"].isoformat()

            state_file.write_text(json.dumps(data, indent=2))
            logger.debug("Agent state saved to persistence")
        except Exception as e:
            logger.error(f"Failed to save agent state: {e}")
