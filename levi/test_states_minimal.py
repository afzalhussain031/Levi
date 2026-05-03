#!/usr/bin/env python3
"""
Minimal test for audio state control logic
Tests state transitions without heavy dependencies
"""

import sys
import time
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the heavy dependencies
class MockWhisperModel:
    def transcribe(self, audio, **kwargs):
        return [], None

class MockSoundDevice:
    @staticmethod
    def query_devices():
        return []

# Monkey patch the imports
sys.modules['faster_whisper'] = type('MockModule', (), {'WhisperModel': MockWhisperModel})()
sys.modules['sounddevice'] = MockSoundDevice

from audio.state import AudioState, get_audio_state, set_audio_state
from utils.logger import logger


def test_state_transitions():
    """Test basic state transitions"""
    logger.info("🧪 Testing audio state transitions")

    # Test initial state
    assert get_audio_state() == AudioState.LISTENING
    logger.info("✓ Initial state: LISTENING")

    # Test state changes
    set_audio_state(AudioState.PROCESSING)
    assert get_audio_state() == AudioState.PROCESSING
    logger.info("✓ State change: PROCESSING")

    set_audio_state(AudioState.SPEAKING)
    assert get_audio_state() == AudioState.SPEAKING
    logger.info("✓ State change: SPEAKING")

    set_audio_state(AudioState.LISTENING)
    assert get_audio_state() == AudioState.LISTENING
    logger.info("✓ State change: LISTENING")

    logger.info("✅ All state transitions work correctly")


def test_interrupt_mechanism():
    """Test interrupt request mechanism"""
    from audio.state import request_interrupt, interrupt_requested, clear_interrupt_request

    logger.info("🧪 Testing interrupt mechanism")

    # Test no interrupt initially
    assert not interrupt_requested()
    logger.info("✓ No interrupt initially")

    # Test interrupt request
    request_interrupt()
    assert interrupt_requested()
    logger.info("✓ Interrupt requested")

    # Test clear interrupt
    clear_interrupt_request()
    assert not interrupt_requested()
    logger.info("✓ Interrupt cleared")

    logger.info("✅ Interrupt mechanism works correctly")


def main():
    """Run all tests"""
    try:
        logger.info("🚀 Starting LEVI Audio State Control Tests")

        test_state_transitions()
        test_interrupt_mechanism()

        logger.info("🎉 All tests passed! Audio state control logic is working correctly.")
        logger.info("📝 The fixes should prevent overlapping listening during processing and speaking.")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()