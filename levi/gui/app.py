"""
Iris GUI Application
Modern PyQt6-based interface with real-time transcription and responses
"""

import sys
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QFont

from audio.speech import SpeechRecognizer
from audio.tts import VoiceOutput
from core.agent import IrisAgent
from utils.config import SYSTEM_CONFIG
from utils.logger import logger


class SignalEmitter(QObject):
    """
    Signal emitter for assistant events
    Inherits from QObject to use PyQt signals
    """
    # PyQt signals (thread-safe, emitted to main thread)
    started = pyqtSignal()
    stopped = pyqtSignal()
    text_received = pyqtSignal(str, str)  # (event_type, text)
    response_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)


class AssistantWorkerThread(threading.Thread):
    """
    Background worker thread that manages speech recognition, AI decisions, and tool execution
    Emits signals via SignalEmitter for UI updates
    """

    def __init__(self, signal_emitter, agent, voice_output):
        super().__init__(daemon=True)
        self.emitter = signal_emitter
        self._running = True
        self.speech_recognizer = SpeechRecognizer()
        self.voice_output = voice_output
        self.agent = agent

    def run(self):
        """Main assistant loop for GUI"""
        try:
            self.emitter.started.emit()
            
            # Start listening
            self.speech_recognizer.start_listening()
            
            # Play greeting
            greeting = "Hello! I'm Iris, your voice assistant. I'm ready to listen."
            if SYSTEM_CONFIG["voice_enabled"]:
                self.voice_output.speak_async(greeting)

            # Main loop: poll for recognized text and process
            while self._running:
                try:
                    # Poll for recognized text (non-blocking)
                    text = self.speech_recognizer.get_text(timeout=0.5)
                    if text:
                        # Emit recognized text to UI
                        self.emitter.text_received.emit("recognized", text)

                        # Process input through the LangChain agent
                        response = self.agent.run(text)
                        self.emitter.response_generated.emit(response)

                        # Speak the final assistant message (non-blocking)
                        if SYSTEM_CONFIG["voice_enabled"]:
                            self.voice_output.speak_async(response)

                except Exception as e:
                    self.emitter.error_occurred.emit(str(e))

        except Exception as e:
            self.emitter.error_occurred.emit(f"Worker error: {e}")
        finally:
            # Clean up
            try:
                self.speech_recognizer.stop_listening()
                self.voice_output.wait_until_done(timeout=5)
            except Exception:
                pass
            self.emitter.stopped.emit()

    def stop(self):
        """Stop the worker thread"""
        self._running = False

    def reset_session(self):
        """Stop speech, clear buffers, and prepare for fresh listening"""
        try:
            # 1. Request interrupt of any ongoing speech
            from audio.state import request_interrupt, set_audio_state, AudioState
            
            request_interrupt()  # Signal to stop TTS
            self.voice_output.wait_until_done(timeout=1)  # Wait for speech to finish
            
            # 2. Clear audio buffer (discard any half-heard speech)
            self.speech_recognizer._clear_audio_buffer()
            
            # 3. Clear any pending transcription text
            self.speech_recognizer.clear_queue()
            
            # 4. Reset to LISTENING state
            set_audio_state(AudioState.LISTENING)
            
            # 5. Play confirmation message
            self.voice_output.speak_async("Listening session reset. Ready to listen.")
            
        except Exception as e:
            self.logger.error(f"Error during session reset: {e}")


class IrisMainWindow(QMainWindow):
    """Main Iris GUI window"""

    def __init__(self):
        super().__init__()
        self.logger = logger
        self.signal_emitter = SignalEmitter()
        self.worker_thread = None
        self.agent = IrisAgent()
        self.voice_output = VoiceOutput()
        self.input_mode = "voice"

        self.setWindowTitle("Iris - Voice Assistant")
        self.setGeometry(100, 100, 900, 700)

        # Create UI
        self._create_ui()
        self._apply_dark_theme()

        # Connect persistent signals for both voice and chat modes
        self.signal_emitter.started.connect(self._on_assistant_started)
        self.signal_emitter.stopped.connect(self._on_assistant_stopped)
        self.signal_emitter.text_received.connect(self._on_text_received)
        self.signal_emitter.response_generated.connect(self._on_response_generated)
        self.signal_emitter.error_occurred.connect(self._on_error)

        # Set initial mode state
        self.switch_input_mode(self.input_mode)

    def _create_ui(self):
        """Create the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header = QLabel("🤖 Iris Assistant")
        header_font = QFont()
        header_font.setPointSize(20)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Status indicator
        self.status_label = QLabel("🔴 Stopped")
        status_font = QFont()
        status_font.setPointSize(12)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Transcript display area
        display_label = QLabel("Transcript & Responses:")
        display_label.setFont(QFont("Arial", 11))
        main_layout.addWidget(display_label)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Courier", 10))
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff41;
                border: 1px solid #00ff41;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        main_layout.addWidget(self.text_display)

        # Control buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.start_button = QPushButton("▶️ Start Listening")
        self.start_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.start_button.clicked.connect(self.start_assistant)
        self.start_button.setMinimumHeight(50)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹️ Stop Listening")
        self.stop_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.stop_button.clicked.connect(self.stop_assistant)
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        self.reset_button = QPushButton("🔄 Stop & Reset")
        self.reset_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.reset_button.clicked.connect(self.reset_session)
        self.reset_button.setMinimumHeight(50)
        self.reset_button.setEnabled(False)
        button_layout.addWidget(self.reset_button)

        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.clear_button.clicked.connect(self.text_display.clear)
        self.clear_button.setMinimumHeight(50)
        button_layout.addWidget(self.clear_button)

        main_layout.addLayout(button_layout)

        # Mode toggle buttons layout
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)

        mode_label = QLabel("Mode:")
        mode_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        mode_layout.addWidget(mode_label)

        self.pure_llm_button = QPushButton("💬 Pure LLM")
        self.pure_llm_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.pure_llm_button.clicked.connect(lambda: self.switch_mode("pure_llm"))
        self.pure_llm_button.setMinimumHeight(40)
        self.pure_llm_button.setStyleSheet("""
            QPushButton {
                background-color: #00cc44;
                color: #000000;
            }
        """)
        mode_layout.addWidget(self.pure_llm_button)

        self.agent_tools_button = QPushButton("🔧 Agent + Tools")
        self.agent_tools_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.agent_tools_button.clicked.connect(lambda: self.switch_mode("agent_with_tools"))
        self.agent_tools_button.setMinimumHeight(40)
        self.agent_tools_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: #ccc;
            }
        """)
        mode_layout.addWidget(self.agent_tools_button)

        main_layout.addLayout(mode_layout)

        # Input mode selection
        input_mode_layout = QHBoxLayout()
        input_mode_layout.setSpacing(10)

        input_label = QLabel("Input:")
        input_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        input_mode_layout.addWidget(input_label)

        self.voice_mode_button = QPushButton("🎙️ Voice Mode")
        self.voice_mode_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.voice_mode_button.clicked.connect(lambda: self.switch_input_mode("voice"))
        self.voice_mode_button.setMinimumHeight(40)
        self.voice_mode_button.setStyleSheet("""
            QPushButton {
                background-color: #00cc44;
                color: #000000;
            }
        """)
        input_mode_layout.addWidget(self.voice_mode_button)

        self.chat_mode_button = QPushButton("⌨️ Chat Mode")
        self.chat_mode_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.chat_mode_button.clicked.connect(lambda: self.switch_input_mode("chat"))
        self.chat_mode_button.setMinimumHeight(40)
        self.chat_mode_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: #ccc;
            }
        """)
        input_mode_layout.addWidget(self.chat_mode_button)

        main_layout.addLayout(input_mode_layout)

        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Type your prompt here...")
        self.chat_input.setFont(QFont("Courier", 10))
        self.chat_input.setFixedHeight(120)
        self.chat_input.setStyleSheet("""
            QTextEdit {
                background-color: #111;
                color: #ffffff;
                border: 1px solid #666;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.chat_input.hide()
        main_layout.addWidget(self.chat_input)

        chat_button_layout = QHBoxLayout()
        chat_button_layout.setSpacing(10)

        self.send_button = QPushButton("📝 Send")
        self.send_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.send_button.clicked.connect(self.send_chat_text)
        self.send_button.setMinimumHeight(40)
        self.send_button.hide()
        chat_button_layout.addWidget(self.send_button)

        main_layout.addLayout(chat_button_layout)

        # Footer
        footer = QLabel("© 2026 Iris Virtual Assistant")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Arial", 9))
        footer.setStyleSheet("color: #888; margin-top: 10px;")
        main_layout.addWidget(footer)

    def _apply_dark_theme(self):
        """Apply Jarvis-style dark theme"""
        dark_stylesheet = """
            QMainWindow {
                background-color: #0d0d0d;
            }
            QWidget {
                background-color: #0d0d0d;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #00cc44;
                color: #000000;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ff41;
            }
            QPushButton:pressed {
                background-color: #00aa33;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
            QLabel {
                color: #e0e0e0;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff41;
                border: 1px solid #00ff41;
                border-radius: 5px;
            }
        """
        QApplication.instance().setStyle("Fusion")
        self.setStyleSheet(dark_stylesheet)

    def start_assistant(self):
        """Start the assistant and monitoring"""
        if self.input_mode != "voice":
            self.text_display.append("[System] Switch to Voice Mode to start listening.\n")
            return

        if self.worker_thread is not None:
            self.logger.warning("Assistant already running")
            return

        try:
            # Create and start worker thread (manages recognizer + TTS directly)
            self.worker_thread = AssistantWorkerThread(self.signal_emitter, self.agent, self.voice_output)
            self.worker_thread.start()

            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            self.status_label.setText("🟢 Listening...")
            self.status_label.setStyleSheet("color: #00ff41;")
            self.text_display.append("[System] Iris started. Listening for your voice...\n")

        except Exception as e:
            self.logger.error(f"Error starting assistant: {e}")
            self._show_error(f"Failed to start Iris: {e}")

    def stop_assistant(self):
        """Stop the assistant"""
        if self.worker_thread is None:
            return

        try:
            # Signal worker thread to stop
            self.worker_thread.stop()

            # Wait for thread to finish
            if self.worker_thread.is_alive():
                self.worker_thread.join(timeout=5)

            # Reset state
            self.worker_thread = None

            # Update UI
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.status_label.setText("🔴 Stopped")
            self.status_label.setStyleSheet("color: #ff4444;")
            self.text_display.append("[System] Iris stopped.\n")

        except Exception as e:
            self.logger.error(f"Error stopping assistant: {e}")
            self._show_error(f"Error stopping Iris: {e}")

    def reset_session(self):
        """User clicked reset button - stop everything and start fresh"""
        if self.worker_thread:
            self.worker_thread.reset_session()
            # Clear chat display/logs completely
            self.text_display.clear()
            self.text_display.append("[🔄 Session Reset - Fresh listening session started]")
            self.status_label.setText("🟢 Listening...")
            self.status_label.setStyleSheet("color: #00ff41;")

    def _on_assistant_started(self):
        """Called when assistant thread starts"""
        self.logger.info("Assistant started successfully")

    def _on_assistant_stopped(self):
        """Called when assistant thread stops"""
        self.logger.info("Assistant stopped")

    def _on_text_received(self, event_type, text):
        """Called when recognized text arrives from worker"""
        if event_type == "recognized":
            self.text_display.append(f"<b style='color: #00ff41;'>🎤 You:</b> {text}")

    def _on_response_generated(self, response):
        """Called when assistant generates a response"""
        self.text_display.append(f"<b style='color: #ffaa00;'>💬 Iris:</b> {response}\n")

    def _on_error(self, error_msg):
        """Called when an error occurs"""
        self.logger.error(f"Assistant error: {error_msg}")
        self.text_display.append(f"<b style='color: #ff4444;'>⚠️ Error:</b> {error_msg}")

    def _show_error(self, message):
        """Display error message in UI"""
        self.text_display.append(f"<b style='color: #ff4444;'>❌ Error:</b> {message}\n")

    def switch_input_mode(self, mode: str):
        """Switch between voice and chat input modes"""
        self.input_mode = mode

        if mode == "chat":
            # Stop any running voice assistant when switching to chat mode
            if self.worker_thread is not None:
                self.stop_assistant()

            self.chat_input.show()
            self.send_button.show()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.status_label.setText("🟡 Chat mode active")
            self.status_label.setStyleSheet("color: #ffdd00;")

            self.voice_mode_button.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    color: #ccc;
                    border: none;
                }
            """)
            self.chat_mode_button.setStyleSheet("""
                QPushButton {
                    background-color: #00cc44;
                    color: #000000;
                    border: 2px solid #00ff41;
                }
            """)
            self.text_display.append("[System] Input mode switched to: Chat mode. Type your prompt and send.\n")
        else:
            self.chat_input.hide()
            self.send_button.hide()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.status_label.setText("🔴 Voice mode ready")
            self.status_label.setStyleSheet("color: #00ff41;")

            self.voice_mode_button.setStyleSheet("""
                QPushButton {
                    background-color: #00cc44;
                    color: #000000;
                    border: 2px solid #00ff41;
                }
            """)
            self.chat_mode_button.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    color: #ccc;
                    border: none;
                }
            """)
            self.text_display.append("[System] Input mode switched to: Voice mode. Press Start Listening.\n")

    def send_chat_text(self):
        """Send typed chat text to the agent"""
        if self.input_mode != "chat":
            return

        user_text = self.chat_input.toPlainText().strip()
        if not user_text:
            return

        self.text_display.append(f"<b style='color: #00ff41;'>⌨️ You:</b> {user_text}")
        self.chat_input.clear()

        def worker():
            try:
                response = self.agent.run(user_text)
                self.signal_emitter.response_generated.emit(response)
                if SYSTEM_CONFIG["voice_enabled"]:
                    self.voice_output.speak_async(response)
            except Exception as e:
                self.signal_emitter.error_occurred.emit(str(e))

        threading.Thread(target=worker, daemon=True).start()

    def switch_mode(self, mode: str):
        """Switch between pure_llm and agent_with_tools modes"""
        from utils.config import AGENT_CONFIG
        
        # Update config
        AGENT_CONFIG["agent_mode"] = mode
        
        # Update button styles
        if mode == "pure_llm":
            self.pure_llm_button.setStyleSheet("""
                QPushButton {
                    background-color: #00cc44;
                    color: #000000;
                    border: 2px solid #00ff41;
                }
            """)
            self.agent_tools_button.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    color: #ccc;
                    border: none;
                }
            """)
            mode_display = "💬 Pure LLM (Direct Conversation)"
        else:
            self.agent_tools_button.setStyleSheet("""
                QPushButton {
                    background-color: #00cc44;
                    color: #000000;
                    border: 2px solid #00ff41;
                }
            """)
            self.pure_llm_button.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    color: #ccc;
                    border: none;
                }
            """)
            mode_display = "🔧 Agent + Tools (Search, Browser, Media)"
        
        # Log mode switch
        self.logger.info(f"Switched to {mode} mode")
        self.text_display.append(f"\n[System] Mode switched to: {mode_display}\n")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.worker_thread is not None:
            self.stop_assistant()
        event.accept()


def launch_gui():
    """Launch the Iris GUI application"""
    app = QApplication(sys.argv)
    window = IrisMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui()
