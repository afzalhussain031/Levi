"""
Audio state control for LEVI.
Provides thread-safe LISTENING / PROCESSING / SPEAKING management.
"""

import threading
from typing import Literal

AudioStateType = Literal["LISTENING", "PROCESSING", "SPEAKING"]

class AudioState:
    LISTENING: AudioStateType = "LISTENING"
    PROCESSING: AudioStateType = "PROCESSING"
    SPEAKING: AudioStateType = "SPEAKING"

_state_lock = threading.Lock()
_current_state: AudioStateType = AudioState.LISTENING
_listening_event = threading.Event()
_listening_event.set()


def set_audio_state(state: AudioStateType) -> None:
    """Set the current audio state and update the listening event."""
    global _current_state
    with _state_lock:
        _current_state = state
        if state == AudioState.LISTENING:
            _listening_event.set()
        else:
            _listening_event.clear()


def get_audio_state() -> AudioStateType:
    """Get the current audio state."""
    with _state_lock:
        return _current_state


def is_listening() -> bool:
    """Return True only when the assistant is allowed to capture microphone audio."""
    return get_audio_state() == AudioState.LISTENING


def wait_for_listening(timeout: float = 0.1) -> bool:
    """Block until the state is LISTENING or until timeout."""
    return _listening_event.wait(timeout)


_interrupt_event = threading.Event()


def clear_interrupt_request() -> None:
    """Clear any active interrupt request."""
    _interrupt_event.clear()


def request_interrupt() -> None:
    """Signal that an interrupt was requested."""
    _interrupt_event.set()


def interrupt_requested() -> bool:
    """Return True if an interrupt has been requested."""
    return _interrupt_event.is_set()
