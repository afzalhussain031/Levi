"""
LEVI - AI Voice Assistant
Entry point for the application

PHASE 1: Speech Input + Voice Output

Usage:
    python main.py

Press Ctrl+C to stop
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Ensure stdout/stderr use UTF-8 where possible (helps Windows consoles)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    # Older Python versions or unusual environments may not support reconfigure
    pass

from utils.logger import logger
from gui.app import launch_gui


def main():
    """Main entry point - launches PyQt6 GUI"""
    try:
        launch_gui()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
