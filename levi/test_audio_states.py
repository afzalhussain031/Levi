#!/usr/bin/env python3
"""
Test script for LEVI audio state control
Runs the core loop without GUI for testing
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.loop import AssistantLoop
from utils.logger import logger


def main():
    """Test the audio state control"""
    try:
        logger.info("🧪 Starting LEVI Audio State Control Test")

        # Create and start the assistant loop
        loop = AssistantLoop()
        loop.start()

        logger.info("🎤 Test running - speak to test audio state transitions")
        logger.info("🔄 States: LISTENING → PROCESSING → SPEAKING → LISTENING")
        logger.info("🛑 Say 'Stop' during speaking to test interrupt")
        logger.info("Press Ctrl+C to exit")

        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Test interrupted by user")

        # Cleanup
        loop.stop()
        logger.info("✅ Test completed")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()