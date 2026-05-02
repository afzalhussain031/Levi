"""
Main event loop for LEVI Assistant
Handles continuous listening, processing, and speaking
Non-blocking architecture for responsive interactions
"""

import time
from audio.speech import SpeechRecognizer
from audio.tts import VoiceOutput
from core.agent import LeviAgent
from utils.logger import logger
from utils.config import SYSTEM_CONFIG


class AssistantLoop:
    """
    Main event loop for LEVI
    Manages: Listen → Process → Respond cycle
    """

    def __init__(self):
        """Initialize the assistant loop"""
        self.logger = logger
        self.logger.info("=" * 60)
        self.logger.info("🤖 LEVI ASSISTANT - Initializing Core Loop")
        self.logger.info("=" * 60)

        # Initialize components
        self.speech_recognizer = SpeechRecognizer()
        self.voice_output = VoiceOutput()
        self.agent = LeviAgent()

        # State
        self.running = False
        self.processing_input = False

        self.logger.info("✓ Core Loop initialized successfully")

    def start(self):
        """Start the main event loop"""
        if self.running:
            self.logger.warning("Loop already running!")
            return

        self.running = True
        self.speech_recognizer.start_listening()
        self.logger.info("🎙️  LEVI is now listening...")

        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.logger.info("\n⏸️  Received stop signal")
            self.stop()

    def _main_loop(self):
        """
        Main continuous loop
        1. Check for speech input
        2. Process if available
        3. Generate response
        """
        self.voice_output.speak_async("Hello! I'm LEVI, your virtual assistant. I'm ready to listen.")

        while self.running:
            try:
                # Step 1: Check for recognized text (non-blocking)
                recognized_text = self.speech_recognizer.get_text(timeout=0.5)

                if recognized_text:
                    self.logger.debug(f"Input received: {recognized_text}")
                    self._process_input(recognized_text)

                # Non-blocking loop iteration
                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(1)

    def _process_input(self, user_input):
        """Process user input through the LangChain agent."""
        self.processing_input = True

        try:
            self.logger.info(f"📝 Processing: {user_input}")

            response = self.agent.run(user_input)

            self.logger.info(f"💬 Response: {response}")

            # Speak response (non-blocking)
            if SYSTEM_CONFIG["voice_enabled"]:
                self.voice_output.speak_async(response)

        except Exception as e:
            self.logger.error(f"Error processing input: {e}")
            error_response = "Sorry, I encountered an error processing your request."
            if SYSTEM_CONFIG["voice_enabled"]:
                self.voice_output.speak_async(error_response)

        finally:
            self.processing_input = False

    def stop(self):
        """Stop the assistant gracefully"""
        self.logger.info("⏹️  Stopping LEVI...")
        self.running = False
        self.speech_recognizer.stop_listening()
        self.voice_output.wait_until_done(timeout=5)
        self.logger.info("✓ LEVI stopped")
