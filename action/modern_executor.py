"""
Modern action executor with async patterns and structured results.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.config import AutoGPTConfig
from ..core.logger import logger


@dataclass
class ActionResult:
    """Result of an executed action."""

    success: bool
    data: Any = None
    message: str = ""
    duration: float = 0.0
    timestamp: datetime = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ActionExecutor:
    """Modern action executor with structured execution."""

    def __init__(self, config: AutoGPTConfig):
        self.config = config
        self.action_registry: Dict[str, callable] = {}
        self.running_actions: Dict[str, asyncio.Task] = {}

        # Register built-in actions
        self._register_builtin_actions()

    async def initialize(self) -> None:
        """Initialize action executor."""
        logger.info("Initializing action executor...")

        # Test any external dependencies
        await self._test_dependencies()

        logger.info("✅ Action executor initialized")

    async def shutdown(self) -> None:
        """Shutdown action executor."""
        logger.info("Shutting down action executor...")

        # Cancel any running actions
        for task in self.running_actions.values():
            if not task.done():
                task.cancel()

        # Wait for all to finish
        if self.running_actions:
            await asyncio.gather(*self.running_actions.values(), return_exceptions=True)

        logger.info("✅ Action executor shutdown")

    async def execute_action(self, decision: Any) -> ActionResult:
        """Execute an action based on a decision."""

        action_name = getattr(decision, 'action', str(decision))
        parameters = getattr(decision, 'parameters', {}) or {}

        start_time = datetime.now()

        try:
            logger.info(f"Executing action: {action_name}")

            # Get action handler
            action_handler = self.action_registry.get(action_name)
            if not action_handler:
                return ActionResult(
                    success=False,
                    message=f"Unknown action: {action_name}",
                    error=f"No handler registered for action '{action_name}'",
                    duration=(datetime.now() - start_time).total_seconds()
                )

            # Execute action
            result_data = await action_handler(parameters)

            duration = (datetime.now() - start_time).total_seconds()

            return ActionResult(
                success=True,
                data=result_data,
                message=f"Action '{action_name}' completed successfully",
                duration=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            logger.error(f"Action '{action_name}' failed: {e}", exc_info=True)

            return ActionResult(
                success=False,
                message=f"Action '{action_name}' failed",
                error=str(e),
                duration=duration
            )

    async def register_action(self, name: str, handler: callable) -> None:
        """Register a custom action handler."""
        self.action_registry[name] = handler
        logger.debug(f"Registered action: {name}")

    def get_available_actions(self) -> List[str]:
        """Get list of available actions."""
        return list(self.action_registry.keys())

    async def _test_dependencies(self) -> None:
        """Test external dependencies."""
        # Test web search if needed
        try:
            from duckduckgo_search import DDGS
            logger.debug("Web search dependency available")
        except ImportError:
            logger.warning("Web search dependency not available")

    def _register_builtin_actions(self) -> None:
        """Register built-in action handlers."""

        # Observe action - passive monitoring
        async def observe_action(params: Dict[str, Any]) -> Dict[str, Any]:
            duration = params.get('duration', 10)
            await asyncio.sleep(min(duration, 60))  # Max 60 seconds
            return {"observation": "Monitoring completed", "duration": duration}

        # Think action - internal reflection
        async def think_action(params: Dict[str, Any]) -> Dict[str, Any]:
            topic = params.get('topic', 'general reflection')
            duration = params.get('duration', 5)
            await asyncio.sleep(min(duration, 30))  # Max 30 seconds
            return {"reflection": f"Reflected on {topic}", "duration": duration}

        # Wait action - simple pause
        async def wait_action(params: Dict[str, Any]) -> Dict[str, Any]:
            duration = params.get('duration', 5)
            await asyncio.sleep(min(duration, 300))  # Max 5 minutes
            return {"waited": duration, "duration": duration}

        # Communicate action - placeholder for communication
        async def communicate_action(params: Dict[str, Any]) -> Dict[str, Any]:
            message = params.get('message', 'Hello!')
            # Note: Actual communication handled by Telegram integration
            return {"message": message, "sent": True}

        # Search action - web search
        async def search_action(params: Dict[str, Any]) -> Dict[str, Any]:
            query = params.get('query', '')
            num_results = params.get('num_results', 3)

            if not query:
                raise ValueError("Search query is required")

            try:
                from duckduckgo_search import DDGS

                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=num_results):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", "")
                        })

                return {
                    "query": query,
                    "results": results,
                    "count": len(results)
                }

            except ImportError:
                raise RuntimeError("Web search not available - missing duckduckgo_search")
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                raise

        # Learn action - store information
        async def learn_action(params: Dict[str, Any]) -> Dict[str, Any]:
            information = params.get('information', '')
            category = params.get('category', 'general')

            if not information:
                raise ValueError("Information to learn is required")

            # Note: Actual learning handled by memory system
            return {
                "learned": information[:100] + "..." if len(information) > 100 else information,
                "category": category,
                "stored": True
            }

        # Analyze action - break down information
        async def analyze_action(params: Dict[str, Any]) -> Dict[str, Any]:
            data = params.get('data', '')
            analysis_type = params.get('type', 'general')

            if not data:
                raise ValueError("Data to analyze is required")

            # Simple analysis - count words, etc.
            word_count = len(data.split())
            char_count = len(data)

            analysis = {
                "type": analysis_type,
                "word_count": word_count,
                "character_count": char_count,
                "data_preview": data[:200] + "..." if len(data) > 200 else data
            }

            return analysis

        # Register all actions
        self.action_registry.update({
            "observe": observe_action,
            "think": think_action,
            "wait": wait_action,
            "communicate": communicate_action,
            "search": search_action,
            "learn": learn_action,
            "analyze": analyze_action,
        })

        logger.debug(f"Registered {len(self.action_registry)} built-in actions")
