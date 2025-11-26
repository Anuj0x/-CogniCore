"""
Mini AutoGPT - A modern, efficient AI agent system.
"""
from __future__ import annotations

import asyncio
import sys
import signal
from pathlib import Path
from typing import NoReturn

from dotenv import load_dotenv

from .core.config import Config
from .core.agent import AutoGPTAgent
from .core.logger import logger
from .integrations.telegram import TelegramIntegration
from .llm.provider import LLMProvider


class MiniAutoGPT:
    """Main application class for Mini AutoGPT."""

    def __init__(self) -> None:
        self.config = Config.load()
        self.agent = AutoGPTAgent(self.config)
        self.telegram = TelegramIntegration(self.config.telegram) if self.config.telegram else None
        self.llm = LLMProvider(self.config.llm)
        self.running = False

    async def initialize(self) -> None:
        """Initialize all components asynchronously."""
        logger.info("Initializing Mini AutoGPT...")

        # Load and display logo
        await self._display_logo()

        # Verify all integrations
        await self._verify_integrations()

        # Initialize agent memory
        await self.agent.initialize()

        logger.info("✅ Initialization complete!")

    async def _display_logo(self) -> None:
        """Display the application logo."""
        logo_path = Path(__file__).parent / "assets" / "logo.txt"

        try:
            logo = logo_path.read_text(encoding="utf-8")
            print(logo)
        except FileNotFoundError:
            logger.warning("Logo file not found, skipping display")

        print("🤖 Mini AutoGPT initialized!")
        print("A modern, efficient AI agent system.\n")

    async def _verify_integrations(self) -> None:
        """Verify all external integrations are working."""
        logger.info("Verifying integrations...")

        # Test LLM connection
        if not await self.llm.test_connection():
            raise RuntimeError("LLM connection failed")

        # Test Telegram if configured
        if self.telegram and not await self.telegram.test_connection():
            raise RuntimeError("Telegram integration failed")

        logger.info("✅ All integrations verified")

    async def run(self) -> NoReturn:
        """Main application loop."""
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Starting main loop...")

        try:
            while self.running:
                try:
                    await self.agent.think_and_act()
                    await asyncio.sleep(0.1)  # Prevent busy loop
                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    await asyncio.sleep(5)  # Error backoff
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            await self.shutdown()

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    async def shutdown(self) -> None:
        """Cleanup resources."""
        logger.info("Shutting down...")

        await self.agent.shutdown()
        if self.telegram:
            await self.telegram.shutdown()

        logger.info("👋 Goodbye!")


async def main() -> NoReturn:
    """Application entry point."""
    # Load environment
    load_dotenv()

    try:
        # Create and run app
        app = MiniAutoGPT()
        await app.initialize()
        await app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run async application
    asyncio.run(main())
