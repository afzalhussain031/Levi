"""
Logging system for LEVI Assistant
Provides consistent logging across all modules
"""

import logging
import sys
import io
from datetime import datetime
from pathlib import Path


class IrisLogger:
    """Centralized logging for the LEVI assistant"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IrisLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """Initialize logger with console and file handlers"""
        self._logger = logging.getLogger("LEVI")
        self._logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Format
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler (INFO level) - ensure UTF-8 on Windows terminals
        try:
            text_stream = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
            console_handler = logging.StreamHandler(stream=text_stream)
        except Exception:
            console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # File handler (DEBUG level)
        log_file = logs_dir / f"levi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        # File handler (DEBUG level) - write logs as UTF-8
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)
        # Avoid double logging when used as a module
        self._logger.propagate = False

    def get(self):
        """Get the logger instance"""
        return self._logger


# Singleton instance
logger = IrisLogger().get()
