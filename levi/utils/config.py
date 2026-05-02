"""
Configuration management for LEVI Assistant
Centralized settings for all modules
"""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# ==================== AUDIO CONFIGURATION ====================
AUDIO_CONFIG = {
    "sample_rate": 16000,           # Hz - faster-whisper requirement
    "chunk_duration": 0.5,          # seconds - buffer chunk size
    "silence_threshold": 0.01,      # Energy threshold for silence detection (lowered for typical mics)
    "silence_duration": 2.0,        # seconds - time of silence to trigger transcription
    "device": None,                 # None = default device, or specify 'device_name'
}

# ==================== SPEECH RECOGNITION (faster-whisper) ====================
STT_CONFIG = {
    "model_size": "base",           # tiny, base, small, medium, large
    "language": "en",               # Language code
    "temperature": 0.0,             # 0 = deterministic
    "condition_on_previous_text": False,  # Faster response
    "compute_type": "int8",         # int8 or float32
}

# ==================== TEXT-TO-SPEECH (edge-tts) ====================
TTS_CONFIG = {
    "voice": "en-US-GuyNeural",     # Default voice
    "rate": 1.0,                    # Speech rate (0.5-2.0)
    "volume": 100,                  # Volume (0-100)
    "pitch": 0,                     # Pitch (-100 to 100)
}

# ==================== LLM CONFIGURATION (Ollama) ====================
LLM_CONFIG = {
    "base_url": "http://localhost:11434",  # Ollama default endpoint
    "model": "mistral",             # Model name (mistral, neural-chat, llama2, etc.)
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 500,
}

# ==================== MEMORY CONFIGURATION ====================
MEMORY_CONFIG = {
    "max_messages": 10,             # Keep last N messages
    "save_to_json": False,          # Save conversation to JSON
}

# ==================== AGENT CONFIGURATION ====================
AGENT_CONFIG = {
    "thinking_enabled": True,       # Enable detailed thinking
    "safety_checks": True,          # Validate dangerous commands
    "confirmation_needed": True,    # Ask before risky actions
    "response_timeout": 30,         # Seconds to wait for LLM response
}

# ==================== SYSTEM CONFIGURATION ====================
SYSTEM_CONFIG = {
    "debug_mode": True,             # Verbose logging
    "voice_enabled": True,          # Enable TTS output
    "continuous_listening": True,   # Keep listening in background
}

# ==================== PATHS ====================
PATHS = {
    "logs": PROJECT_ROOT / "logs",
    "data": PROJECT_ROOT / "data",
    "conversations": PROJECT_ROOT / "data" / "conversations",
    "models": PROJECT_ROOT / "models",
}

# Create data directories if they don't exist
for path in PATHS.values():
    path.mkdir(parents=True, exist_ok=True)
