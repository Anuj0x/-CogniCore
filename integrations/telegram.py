"""
Modern Telegram integration with async patterns.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from telegram import Bot, Update
from telegram.error import TimedOut, NetworkError
from telegram.ext import Application, CallbackContext, MessageHandler, filters

from ..core.config import TelegramConfig
from ..core.logger import logger


class TelegramIntegration:
    """Modernized Telegram bot integration."""

    def __init__(self, config: TelegramConfig):
        self.config = config
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self.message_queue: asyncio.Queue[str] = asyncio.Queue()
        self.response_queue: asyncio.Queue[str] = asyncio.Queue()
        self.running = False

    async def initialize(self) -> None:
        """Initialize Telegram bot."""
        logger.info("Initializing Telegram integration...")

        try:
            # Create application
            self.application = Application.builder().token(self.config.api_key).build()

            # Create bot instance
            self.bot = Bot(token=self.config.api_key)

            # Setup message handlers
            self.application.add_handler(
                MessageHandler(
                    filters.TEXT & filters.Chat(chat_id=int(self.config.chat_id)),
                    self._handle_message
                )
            )

            # Set up command handlers
            self.application.add_handler(MessageHandler(filters.COMMAND, self._handle_command))

            logger.info("✅ Telegram integration initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Telegram: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown Telegram integration."""
        logger.info("Shutting down Telegram integration...")

        self.running = False

        if self.application:
            await self.application.shutdown()
            self.application = None

        logger.info("✅ Telegram integration shutdown")

    async def test_connection(self) -> bool:
        """Test Telegram connection."""
        if not self.bot:
            return False

        try:
            # Test by getting bot info
            bot_info = await self.bot.get_me()
            logger.info(f"Connected to Telegram as: @{bot_info.username}")
            return True
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False

    async def send_message(self, message: str) -> bool:
        """Send a message to the configured chat."""
        if not self.bot:
            logger.warning("Telegram bot not initialized")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.config.chat_id,
                text=message,
                parse_mode="Markdown"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_notification(self, message: str, success: bool = True) -> bool:
        """Send a notification with status indicator."""
        if not self.config.enable_notifications:
            return True

        status_icon = "✅" if success else "❌"
        formatted_message = f"{status_icon} {message}"

        return await self.send_message(formatted_message)

    async def poll_message(self, timeout: float = 30.0) -> Optional[str]:
        """Poll for new messages with timeout."""
        try:
            message = await asyncio.wait_for(
                self.message_queue.get(),
                timeout=timeout
            )
            return message
        except asyncio.TimeoutError:
            return None

    async def wait_for_response(self, timeout: float = 60.0) -> Optional[str]:
        """Wait for a user response."""
        try:
            response = await asyncio.wait_for(
                self.response_queue.get(),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            return None

    async def ask_user(self, question: str) -> Optional[str]:
        """Ask user a question and wait for response."""
        try:
            # Send question
            await self.send_message(f"🤖 {question}")

            # Wait for response
            response = await self.wait_for_response(timeout=300.0)  # 5 minutes
            return response

        except Exception as e:
            logger.error(f"Failed to ask user question: {e}")
            return None

    async def run_polling(self) -> None:
        """Run the bot with polling (blocking)."""
        if not self.application:
            raise RuntimeError("Telegram application not initialized")

        logger.info("Starting Telegram polling...")
        self.running = True

        try:
            await self.application.run_polling(
                poll_interval=1.0,
                timeout=self.config.timeout,
                drop_pending_updates=True
            )
        except Exception as e:
            logger.error(f"Telegram polling failed: {e}")
        finally:
            self.running = False

    async def _handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handle incoming messages."""
        if not update.message or not update.message.text:
            return

        message_text = update.message.text.strip()

        # Check if authorized user
        if str(update.effective_user.id) != self.config.chat_id:
            logger.warning(f"Unauthorized message from user {update.effective_user.id}")
            return

        # Put message in queue
        await self.message_queue.put(message_text)

        logger.debug(f"Received Telegram message: {message_text[:50]}...")

    async def _handle_command(self, update: Update, context: CallbackContext) -> None:
        """Handle bot commands."""
        if not update.message or not update.message.text:
            return

        command = update.message.text.strip()

        # Basic commands
        if command.startswith("/status"):
            await self._send_status(update)
        elif command.startswith("/help"):
            await self._send_help(update)
        elif command.startswith("/ping"):
            await update.message.reply_text("Pong! 🤖")

    async def _send_status(self, update: Update) -> None:
        """Send bot status."""
        status = "🟢 Online and operational" if self.running else "🔴 Offline"
        await update.message.reply_text(f"Status: {status}")

    async def _send_help(self, update: Update) -> None:
        """Send help information."""
        help_text = """
🤖 Mini AutoGPT Commands:
/status - Show bot status
/help - Show this help
/ping - Test connectivity

Just send me a message and I'll respond!
        """
        await update.message.reply_text(help_text.strip())
