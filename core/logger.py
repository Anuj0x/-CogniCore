"""
Modern logging configuration with structured output.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import AutoGPTConfig


def setup_logging(config: AutoGPTConfig, log_file: Optional[Path] = None) -> logging.Logger:
    """Setup structured logging configuration."""

    # Create logger
    logger = logging.getLogger("miniautogpt")
    logger.setLevel(getattr(logging, config.log_level))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )

    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if not config.debug else logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file or config.debug:
        log_path = log_file or Path("miniautogpt.log")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logging(AutoGPTConfig(
    llm={"server_type": "ollama", "api_url": "http://localhost:11434"}  # Minimal config for initial setup
))


def reinitialize_logger(config: AutoGPTConfig) -> None:
    """Reinitialize logger with new configuration."""
    global logger
    logger = setup_logging(config)


# Legacy compatibility functions
def log(message: str, level: str = "INFO") -> None:
    """Legacy log function for backward compatibility."""
    if level.upper() == "DEBUG":
        logger.debug(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    elif level.upper() == "ERROR":
        logger.error(message)
    else:
        logger.info(message)


def save_debug(data: str, response: str, request_type: str = "unknown") -> None:
    """Save debug information with context."""
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Debug [{request_type}]: {data}")
        if response:
            logger.debug(f"Response [{request_type}]: {response}")
