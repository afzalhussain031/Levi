"""
Real-time Speech-to-Text (STT) module using faster-whisper
Runs in a non-blocking background thread
Continuously listens and pushes recognized text to a queue
"""

import threading
import queue
import numpy as np
from faster_whisper import WhisperModel
from collections import deque
import sounddevice as sd

from utils.logger import logger
from utils.config import AUDIO_CONFIG, STT_CONFIG


class SpeechRecognizer:
    """
    Non-blocking speech recognition using faster-whisper
    Listens continuously in background thread
    """

    def __init__(self):
        """Initialize speech recognizer"""
        self.logger = logger
        self.logger.info("Initializing Speech Recognizer (faster-whisper)")

        # Load whisper model on configured device (cpu recommended for local realtime)
        device = STT_CONFIG.get("device", "cuda")
        self.logger.info(f"Loading WhisperModel size={STT_CONFIG['model_size']} device={device} compute_type={STT_CONFIG.get('compute_type')}")
        self.model = WhisperModel(
            model_size_or_path=STT_CONFIG["model_size"],
            device=device,
            compute_type=STT_CONFIG["compute_type"]
        )

        # Audio configuration
        self.sample_rate = AUDIO_CONFIG["sample_rate"]
        self.chunk_size = int(self.sample_rate * AUDIO_CONFIG["chunk_duration"])
        self.silence_threshold = AUDIO_CONFIG["silence_threshold"]
        self.silence_duration = AUDIO_CONFIG["silence_duration"]
        self.energy_window = AUDIO_CONFIG.get("energy_window", 0.8)
        self.streaming = AUDIO_CONFIG.get("streaming", False)
        # For faster testing, use a shorter min buffer (0.5s) when processing
        self._min_buffer_seconds = 0.5

        # Audio buffer and state
        self.audio_buffer = deque(maxlen=int(self.sample_rate * 30))  # 30 second buffer
        self.recording = False
        self.is_listening = False
        self._speech_start = 0

        # Streaming queue (optional)
        self.audio_queue = queue.Queue(maxsize=32) if self.streaming else None

        # Output queue for recognized text
        self.text_queue = queue.Queue()

        # Thread management
        self.listen_thread = None
        self.process_thread = None

        self.logger.info("Speech Recognizer initialized successfully")

    def start_listening(self):
        """Start background listening thread"""
        if self.is_listening:
            self.logger.warning("Already listening!")
            return

        self.is_listening = True
        self.logger.info("Starting continuous speech recognition...")

        # Start audio capture thread
        self.listen_thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        self.listen_thread.start()

        # Start processing thread
        self.process_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.process_thread.start()

    def stop_listening(self):
        """Stop background listening"""
        self.is_listening = False
        self.logger.info("Stopping speech recognition...")

    def _audio_capture_loop(self):
        """
        Background thread: Capture audio from microphone
        Non-blocking audio input
        """
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=self.chunk_size,
                device=AUDIO_CONFIG["device"]
            ) as stream:
                self.logger.info("Microphone stream opened")

                while self.is_listening:
                    # Read audio chunk from the open stream
                    indata, overflowed = stream.read(self.chunk_size)

                    if overflowed:
                        self.logger.warning("Audio input overflowed")

                    # Convert to numpy array and add to buffer
                    if isinstance(indata, np.ndarray):
                        audio_data = indata.flatten()
                    else:
                        audio_data = np.frombuffer(indata, dtype=np.float32).flatten()

                    # Extend the circular buffer with the new samples
                    self.audio_buffer.extend(audio_data)

                    # If streaming mode is enabled, enqueue the chunk for immediate processing
                    if self.streaming:
                        try:
                            # Put latest chunk, drop oldest if queue full
                            self.audio_queue.put_nowait(audio_data)
                        except queue.Full:
                            try:
                                _ = self.audio_queue.get_nowait()
                                self.audio_queue.put_nowait(audio_data)
                            except Exception:
                                pass

                    # Debug: confirm audio capture (sample count, buffer length, queue size)
                    try:
                        qsize = self.audio_queue.qsize() if self.streaming else "-"
                        self.logger.debug(f"Captured {len(audio_data)} samples, buffer length {len(self.audio_buffer)}, queue size {qsize}")
                    except Exception:
                        pass

        except Exception as e:
            self.logger.error(f"Error in audio capture: {e}")

    def _processing_loop(self):
        """
        Background thread: Process audio buffer
        Detects speech and sends for transcription
        """
        # Two modes: streaming (transcribe each chunk) or VAD-based (short-window energy)
        silence_counter = 0

        while self.is_listening:
            try:
                if self.streaming:
                    # Consume small chunks and transcribe immediately
                    try:
                        chunk = self.audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    try:
                        segments, info = self.model.transcribe(
                            chunk,
                            language=STT_CONFIG["language"],
                            temperature=STT_CONFIG["temperature"],
                            condition_on_previous_text=False
                        )
                        text = " ".join([s.text for s in segments]).strip()
                        if text:
                            self.logger.info(f"🎤 Recognized: {text}")
                            self.text_queue.put(text)
                    except Exception as e:
                        self.logger.debug(f"Streaming chunk transcription error: {e}")

                    continue

                # VAD-based processing: compute energy over a short recent window
                min_samples = int(self.sample_rate * self._min_buffer_seconds)
                if len(self.audio_buffer) < min_samples:
                    threading.Event().wait(0.1)
                    continue

                # Compute energy on recent window only
                window_samples = int(self.sample_rate * self.energy_window)
                recent = list(self.audio_buffer)[-window_samples:]
                audio_chunk = np.array(recent, dtype=np.float32)

                try:
                    energy = float(np.sqrt(np.mean(audio_chunk ** 2)))
                except Exception:
                    energy = 0.0

                self.logger.debug(f"Audio energy (last {self.energy_window}s): {energy:.6f} (threshold: {self.silence_threshold})")

                # Simple energy VAD
                if energy > self.silence_threshold:
                    silence_counter = 0
                    if not self.recording:
                        self.logger.debug(f"Speech started (energy: {energy:.4f})")
                        # Mark approximate start position (include the recent energy window)
                        window_samples = int(self.sample_rate * self.energy_window)
                        self._speech_start = max(0, len(self.audio_buffer) - window_samples)
                    self.recording = True

                else:
                    if self.recording:
                        silence_counter += AUDIO_CONFIG["chunk_duration"]
                        if silence_counter >= self.silence_duration:
                            self.logger.debug(f"Silence detected ({silence_counter:.2f}s), transcribing...")
                            # Build a chunk to transcribe: use samples from when speech started to now
                            full_buf = list(self.audio_buffer)
                            start = int(self._speech_start) if hasattr(self, "_speech_start") else max(0, len(full_buf) - int(self.sample_rate * self.energy_window))
                            to_trans = full_buf[start:]
                            # If nothing meaningful, fallback to a small recent window
                            if len(to_trans) < 100:
                                trans_window = int(self.sample_rate * max(self.energy_window, AUDIO_CONFIG["chunk_duration"]))
                                to_trans = full_buf[-trans_window:]
                            self.logger.debug(f"Transcribing {len(to_trans)} samples (start={start}, buf_len={len(full_buf)})")
                            self._transcribe(np.array(to_trans, dtype=np.float32))
                            self.audio_buffer.clear()
                            self.recording = False
                            silence_counter = 0

                threading.Event().wait(0.05)

            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")

    def _transcribe(self, audio_data):
        """
        Transcribe audio chunk using faster-whisper
        Push result to queue
        """
        try:
            self.logger.info("Transcribing audio...")

            # Transcribe
            segments, info = self.model.transcribe(
                audio_data,
                language=STT_CONFIG["language"],
                temperature=STT_CONFIG["temperature"],
                condition_on_previous_text=STT_CONFIG["condition_on_previous_text"]
            )

            # Extract text from segments
            text = " ".join([segment.text for segment in segments])

            if text.strip():
                self.logger.info(f"🎤 Recognized: {text}")
                self.text_queue.put(text)
            else:
                self.logger.debug("No speech detected in audio chunk")

        except Exception as e:
            self.logger.error(f"Error during transcription: {e}")

    def get_text(self, timeout=None):
        """
        Get recognized text from queue (non-blocking)
        Returns None if no text available
        """
        try:
            return self.text_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_queue(self):
        """Clear any pending text in queue"""
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
            except queue.Empty:
                break
