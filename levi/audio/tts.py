"""
Text-to-Speech (TTS) module using edge-tts
Non-blocking voice output
"""

import threading
import asyncio
from pathlib import Path
import tempfile
import subprocess
import time

from utils.logger import logger
from utils.config import TTS_CONFIG, PATHS


class VoiceOutput:
    """
    Text-to-Speech using edge-tts
    Supports non-blocking async speech
    """

    def __init__(self):
        """Initialize TTS module"""
        self.logger = logger
        self.logger.info("Initializing Voice Output (edge-tts)")

        self.voice = TTS_CONFIG["voice"]
        self.rate = TTS_CONFIG["rate"]
        self.volume = TTS_CONFIG["volume"]
        self.pitch = TTS_CONFIG["pitch"]

        # Speech queue for threading
        self.speech_thread = None
        self._speaking = False

        self.logger.info(f"Voice Output ready - Voice: {self.voice}")

    def speak_async(self, text):
        """
        Speak text in background thread (non-blocking)
        """
        if not text or not text.strip():
            return

        # Start speech in daemon thread
        self.speech_thread = threading.Thread(
            target=self._speak_blocking,
            args=(text,),
            daemon=True
        )
        self.speech_thread.start()

    def _speak_blocking(self, text):
        """Internal blocking speech function (runs in thread)"""
        try:
            self._speaking = True
            self.logger.info(f"🔊 Speaking: {text[:100]}...")

            # Run async speech function
            asyncio.run(self._speak_async(text))

        except Exception as e:
            self.logger.error(f"Error in TTS: {e}")
        finally:
            self._speaking = False

    async def _speak_async(self, text):
        """Async TTS function using edge-tts"""
        try:
            from edge_tts import Communicate

            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            # Generate speech using edge-tts
            communicate = Communicate(text, self.voice, rate=self._format_rate())

            await communicate.save(tmp_path)

            # Play audio using default player
            if Path(tmp_path).exists():
                subprocess.Popen(
                    [f"{tmp_path}"],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                # Wait for speech to complete (rough estimate)
                time.sleep(len(text) / 150 + 1)

                # Clean up
                Path(tmp_path).unlink(missing_ok=True)

        except ImportError:
            self.logger.error("edge-tts not installed. Install with: pip install edge-tts")
        except Exception as e:
            self.logger.error(f"Error in async speech: {e}")

    def _format_rate(self):
        """Format rate for edge-tts (positive/negative percentage)"""
        rate_pct = (self.rate - 1.0) * 100
        # edge-tts requires a leading '+' for non-negative values
        if rate_pct >= 0:
            return f"+{rate_pct:.0f}%"
        return f"{rate_pct:.0f}%"

    def is_speaking(self):
        """Check if currently speaking"""
        return self._speaking

    def wait_until_done(self, timeout=30):
        """Wait for current speech to complete"""
        start_time = time.time()
        while self._speaking and (time.time() - start_time) < timeout:
            time.sleep(0.1)
