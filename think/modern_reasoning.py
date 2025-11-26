"""
Modern reasoning engine with flexible prompt management.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..core.config import AutoGPTConfig
from ..core.logger import logger
from ..llm.provider import LLMProvider


@dataclass
class Decision:
    """A decision made by the reasoning engine."""

    action: str
    reasoning: str
    parameters: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    priority: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action,
            "reasoning": self.reasoning,
            "parameters": self.parameters,
            "confidence": self.confidence,
            "priority": self.priority,
        }


class ReasoningEngine:
    """Modern reasoning engine with structured prompts."""

    def __init__(self, config: AutoGPTConfig):
        self.config = config
        self.llm: Optional[LLMProvider] = None
        self.current_goal: Optional[str] = None
        self.personality = "helpful and intelligent AI assistant"

    async def initialize(self) -> None:
        """Initialize reasoning engine."""
        logger.info("Initializing reasoning engine...")

        # Will be set by agent
        logger.info("✅ Reasoning engine initialized")

    async def decide_next_action(self, context: Dict[str, Any]) -> Decision:
        """Decide the next action based on current context."""

        if not self.llm:
            # Fallback decision when no LLM available
            return Decision(
                action="observe",
                reasoning="No LLM available, defaulting to observation",
                parameters={"duration": 60}
            )

        # Create decision prompt
        prompt = self._build_decision_prompt(context)

        try:
            response = await self.llm.generate(prompt, max_tokens=500, temperature=0.3)

            # Parse LLM response into decision
            decision = self._parse_decision_response(response.content)

            logger.info(f"Decided on action: {decision.action}")
            return decision

        except Exception as e:
            logger.error(f"Failed to generate decision: {e}")

            # Return safe fallback decision
            return Decision(
                action="wait",
                reasoning=f"Error in decision making: {e}",
                parameters={"duration": 30}
            )

    async def generate_response(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response to user input."""

        if not self.llm:
            return "I'm sorry, but my language model is not available right now."

        # Build conversation prompt
        prompt = self._build_response_prompt(user_input, context or {})

        try:
            response = await self.llm.generate(
                prompt,
                max_tokens=1000,
                temperature=self.config.llm.temperature
            )

            return response.content.strip()

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return "I apologize, but I'm having trouble processing your message right now. Please try again."

    async def evaluate_decision(self, decision: Decision, result: Any) -> Dict[str, Any]:
        """Evaluate the outcome of a decision."""

        if not self.llm:
            return {"evaluation": "neutral", "score": 0.5}

        prompt = f"""
        Evaluate the success of this action:

        Action: {decision.action}
        Reasoning: {decision.reasoning}
        Result: {result}

        Rate the success on a scale of 0-1, where:
        0 = Complete failure
        0.5 = Partial success or neutral
        1 = Complete success

        Provide a brief justification and the numerical score.
        Respond in JSON format with keys: "evaluation", "score", "justification"
        """

        try:
            response = await self.llm.generate(prompt, max_tokens=200, temperature=0.1)

            # Try to parse JSON response
            result_data = json.loads(response.content.strip())

            return {
                "evaluation": result_data.get("evaluation", "unknown"),
                "score": float(result_data.get("score", 0.5)),
                "justification": result_data.get("justification", ""),
                "raw_response": response.content
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse evaluation response: {e}")

            # Simple fallback evaluation
            return {
                "evaluation": "neutral",
                "score": 0.5,
                "justification": "Unable to evaluate properly",
                "raw_response": response.content if 'response' in locals() else ""
            }

    async def update_goal(self, goal: str) -> None:
        """Update the current goal."""
        self.current_goal = goal
        logger.info(f"Updated goal: {goal}")

    def _build_decision_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for decision making."""

        recent_memories = context.get("recent_memories", [])
        message_history = context.get("message_history", [])
        active_goals = context.get("active_goals", [])

        memories_text = "\n".join([
            f"- {m.get('memory_type', 'unknown').upper()}: {m.get('content', '')}"
            for m in recent_memories[:10]  # Limit to 10 most recent
        ]) if recent_memories else "None"

        goals_text = "\n".join([
            f"- {g.get('content', '')}"
            for g in active_goals
        ]) if active_goals else "None"

        conversation_text = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in message_history[-5:]  # Last 5 messages
        ]) if message_history else "None"

        return f"""
        You are {self.personality}.

        Current Goal: {self.current_goal or "Observation and learning"}

        Active Goals:
        {goals_text}

        Recent Conversation:
        {conversation_text}

        Recent Memories:
        {memories_text}

        Available Actions:
        - observe: Observe the environment and gather information
        - think: Reflect on current situation and plan next steps
        - communicate: Send a message or ask for clarification
        - search: Search for information on the web
        - wait: Pause for a specified duration
        - learn: Store important information in memory
        - analyze: Break down complex information

        Instructions:
        1. Choose the most appropriate action based on current context
        2. Consider your goals and recent information
        3. Be efficient - don't take unnecessary actions
        4. If something needs clarification, use 'communicate'
        5. Response must be valid JSON with: action, reasoning, parameters (optional), confidence (0-1)

        Decide the next best action:
        """.strip()

    def _build_response_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Build prompt for generating user responses."""

        message_history = context.get("message_history", [])
        current_goal = self.current_goal or "Assist the user helpfully"

        # Build conversation history
        history_text = ""
        if message_history:
            history_lines = []
            for msg in message_history[-10:]:  # Last 10 messages for context
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                history_lines.append(f"{role.title()}: {content}")
            history_text = "\n".join(history_lines)

        return f"""
        You are {self.personality}.

        Current Goal: {current_goal}

        Conversation History:
        {history_text}

        User: {user_input}

        Respond naturally and helpfully. Keep your response concise but informative.
        If you need clarification, ask specific questions.
        Remember your goal and stay focused on helping the user.
        """.strip()

    def _parse_decision_response(self, response_text: str) -> Decision:
        """Parse LLM response into Decision object."""

        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                data = json.loads(json_text)

                return Decision(
                    action=data.get('action', 'wait'),
                    reasoning=data.get('reasoning', 'Parsed from LLM response'),
                    parameters=data.get('parameters', {}),
                    confidence=float(data.get('confidence', 1.0)),
                    priority=int(data.get('priority', 1))
                )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse decision JSON: {e}")

        # Fallback: extract action from text
        text_lower = response_text.lower()

        if 'observe' in text_lower:
            return Decision(action="observe", reasoning=response_text[:200])
        elif 'think' in text_lower or 'reflect' in text_lower:
            return Decision(action="think", reasoning=response_text[:200])
        elif 'communicate' in text_lower or 'message' in text_lower:
            return Decision(action="communicate", reasoning=response_text[:200])
        elif 'search' in text_lower:
            return Decision(action="search", reasoning=response_text[:200])
        else:
            return Decision(action="wait", reasoning=f"Default action - {response_text[:200]}")
