"""
LEVI GUI Application
Modern PyQt6-based interface with real-time transcription and responses
"""

import sys
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon

from core.loop import AssistantLoop
from utils.logger import logger


class AssistantSignals(threading.Thread):
    """
    Signal bridge: captures assistant loop events and emits PyQt signals
    Runs in background to monitor AssistantLoop state and text queue
    """
    # PyQt signals (emitted to main thread)
    started = pyqtSignal()
    stopped = pyqtSignal()
    text_received = pyqtSignal(str, str)  # (event_type, text) where event_type is "recognized" or "response"
    error_occurred = pyqtSignal(str)

    def __init__(self, assistant_loop):
        super().__init__(daemon=True)
        self.assistant = assistant_loop
        self._running = True

    def run(self):
        """Monitor assistant loop and emit signals"""
        try:
            self.started.emit()

            # Monitor loop while it's running
            while self._running and self.assistant.running:
                try:
                    # Poll for recognized text
                    text = self.assistant.speech_recognizer.get_text(timeout=0.5)
                    if text:
                        self.text_received.emit("recognized", text)

                except Exception as e:
                    self.error_occurred.emit(str(e))

        except Exception as e:
            self.error_occurred.emit(f"Signal monitor error: {e}")
        finally:
            self.stopped.emit()

    def stop(self):
        """Stop monitoring"""
        self._running = False


class LEVIMainWindow(QMainWindow):
    """Main LEVI GUI window"""

    def __init__(self):
        super().__init__()
        self.logger = logger
        self.assistant = None
        self.signal_thread = None

        self.setWindowTitle("LEVI - Voice Assistant")
        self.setGeometry(100, 100, 900, 700)

        # Create UI
        self._create_ui()
        self._apply_dark_theme()

    def _create_ui(self):
        """Create the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header = QLabel("🤖 LEVI Assistant")
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

        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.clear_button.clicked.connect(self.text_display.clear)
        self.clear_button.setMinimumHeight(50)
        button_layout.addWidget(self.clear_button)

        main_layout.addLayout(button_layout)

        # Footer
        footer = QLabel("© 2026 LEVI Virtual Assistant")
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
        if self.assistant is not None:
            self.logger.warning("Assistant already running")
            return

        try:
            # Create assistant loop
            self.assistant = AssistantLoop()

            # Start assistant in a background thread
            self.assistant_thread = threading.Thread(target=self.assistant.start, daemon=False)
            self.assistant_thread.start()

            # Start signal monitoring thread
            self.signal_thread = AssistantSignals(self.assistant)
            self.signal_thread.started.connect(self._on_assistant_started)
            self.signal_thread.stopped.connect(self._on_assistant_stopped)
            self.signal_thread.text_received.connect(self._on_text_received)
            self.signal_thread.error_occurred.connect(self._on_error)
            self.signal_thread.start()

            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("🟢 Listening...")
            self.status_label.setStyleSheet("color: #00ff41;")
            self.text_display.append("[System] LEVI started. Listening for your voice...\n")

        except Exception as e:
            self.logger.error(f"Error starting assistant: {e}")
            self._show_error(f"Failed to start LEVI: {e}")

    def stop_assistant(self):
        """Stop the assistant"""
        if self.assistant is None:
            return

        try:
            # Stop assistant
            self.assistant.stop()

            # Wait for threads to finish
            if self.assistant_thread and self.assistant_thread.is_alive():
                self.assistant_thread.join(timeout=5)

            if self.signal_thread:
                self.signal_thread.stop()
                self.signal_thread.join(timeout=2)

            # Reset state
            self.assistant = None
            self.assistant_thread = None
            self.signal_thread = None

            # Update UI
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("🔴 Stopped")
            self.status_label.setStyleSheet("color: #ff4444;")
            self.text_display.append("[System] LEVI stopped.\n")

        except Exception as e:
            self.logger.error(f"Error stopping assistant: {e}")
            self._show_error(f"Error stopping LEVI: {e}")

    def _on_assistant_started(self):
        """Called when assistant thread starts"""
        self.logger.info("Assistant started successfully")

    def _on_assistant_stopped(self):
        """Called when assistant thread stops"""
        self.logger.info("Assistant stopped")
        if self.assistant and self.assistant.running:
            # If still marked as running, something went wrong
            self._show_error("Assistant thread stopped unexpectedly")

    def _on_text_received(self, event_type, text):
        """Called when recognized text arrives"""
        if event_type == "recognized":
            self.text_display.append(f"<b style='color: #00ff41;'>🎤 You:</b> {text}")
            # Also get and display the response
            self._process_input(text)
        elif event_type == "response":
            self.text_display.append(f"<b style='color: #ffaa00;'>💬 LEVI:</b> {text}")

    def _process_input(self, user_input):
        """Process user input and display response"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")
            response = f"You said: {user_input}. Processed at {timestamp}."
            self.text_display.append(f"<b style='color: #ffaa00;'>💬 LEVI:</b> {response}\n")
        except Exception as e:
            self.logger.error(f"Error processing input: {e}")

    def _on_error(self, error_msg):
        """Called when an error occurs"""
        self.logger.error(f"Assistant error: {error_msg}")
        self.text_display.append(f"<b style='color: #ff4444;'>⚠️ Error:</b> {error_msg}")

    def _show_error(self, message):
        """Display error message in UI"""
        self.text_display.append(f"<b style='color: #ff4444;'>❌ Error:</b> {message}\n")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.assistant and self.assistant.running:
            self.stop_assistant()
        event.accept()


def launch_gui():
    """Launch the LEVI GUI application"""
    app = QApplication(sys.argv)
    window = LEVIMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui()
