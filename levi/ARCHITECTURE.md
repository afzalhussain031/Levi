# LEVI Architecture & Design

## 🎯 Design Philosophy

LEVI is built on three core principles:

1. **Modularity**: Each component is independent and testable
2. **Non-blocking**: All I/O operations run in background threads
3. **Scalability**: Easy to add new tools, actions, and capabilities

---

## 📊 SYSTEM ARCHITECTURE

### High-Level Flow

```
┌─────────────────────────────────────────────────────────┐
│                   MAIN EVENT LOOP                       │
│                  (core/loop.py)                         │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌───────┐ ┌────────┐ ┌────────┐
    │LISTEN │ │PROCESS │ │RESPOND │
    │(async)│ │(think) │ │(speak) │
    └───────┘ └────────┘ └────────┘
        │          │          │
        ▼          ▼          ▼
    ┌──────────────────────────────────┐
    │    THREADING & QUEUES            │
    │  (Non-blocking architecture)      │
    └──────────────────────────────────┘
```

---

## 🎤 AUDIO PIPELINE (PHASE 1)

### Speech Recognition (STT)

```
Microphone Input
      │
      ▼
┌──────────────────────┐
│ Audio Buffer Thread  │  (sounddevice)
│ - Capture at 16kHz   │
│ - 30s buffer         │
└──────────────────────┘
      │
      ▼
┌──────────────────────┐
│ Processing Thread    │
│ - Silence detection  │
│ - Voice Activity     │
└──────────────────────┘
      │
      ▼
┌──────────────────────┐
│ Transcription        │  (faster-whisper)
│ - STT conversion     │
│ - Queue result       │
└──────────────────────┘
      │
      ▼
┌──────────────────────┐
│ Text Queue           │
│ (Non-blocking)       │
└──────────────────────┘
      │
      ▼
┌──────────────────────┐
│ Main Loop Reads      │
│ (get_text)           │
└──────────────────────┘
```

### Text-to-Speech (TTS)

```
Response Text
      │
      ▼
┌──────────────────────┐
│ TTS Thread           │  (edge-tts)
│ - Convert to MP3     │
│ - Generate with voice│
└──────────────────────┘
      │
      ▼
┌──────────────────────┐
│ FFmpeg Playback      │
│ - Audio playback     │
└──────────────────────┘
```

---

## 📁 MODULE BREAKDOWN

### `audio/speech.py` - SpeechRecognizer
**Responsibility**: Continuous speech input  
**Key Features**:
- Background microphone capture
- Voice Activity Detection (VAD)
- Silence-based segmentation
- Queue-based text output

**Key Methods**:
```python
recognizer = SpeechRecognizer()
recognizer.start_listening()          # Start background thread
text = recognizer.get_text(timeout=1) # Non-blocking read
recognizer.stop_listening()           # Stop gracefully
```

---

### `audio/tts.py` - VoiceOutput
**Responsibility**: Non-blocking voice output  
**Key Features**:
- Async TTS conversion
- Background speech thread
- FFmpeg integration
- Voice customization (rate, pitch, voice)

**Key Methods**:
```python
voice = VoiceOutput()
voice.speak_async("Hello world")      # Async speech (returns immediately)
is_speaking = voice.is_speaking()     # Check status
voice.wait_until_done(timeout=30)     # Wait for completion
```

---

### `core/loop.py` - AssistantLoop
**Responsibility**: Main event loop  
**Key Features**:
- Continuous listening
- Input processing
- Response generation
- Lifecycle management

**Key Methods**:
```python
assistant = AssistantLoop()
assistant.start()   # Start main loop (blocking)
assistant.stop()    # Stop gracefully
```

---

### `utils/logger.py` - LeviLogger
**Responsibility**: Centralized logging  
**Key Features**:
- Console + file logging
- Singleton pattern
- Automatic timestamp
- DEBUG level file, INFO level console

**Usage**:
```python
from utils.logger import logger
logger.info("Starting...")
logger.error("Something failed")
logger.debug("Detailed info")
```

---

### `utils/config.py` - Configuration
**Responsibility**: Centralized settings  
**Key Features**:
- Audio settings
- Model configuration
- Voice settings
- Paths management

**Usage**:
```python
from utils.config import AUDIO_CONFIG, STT_CONFIG
sample_rate = AUDIO_CONFIG["sample_rate"]
model = STT_CONFIG["model_size"]
```

---

## 🔄 THREADING MODEL

LEVI uses multiple threads to ensure responsiveness:

```
Main Thread (core/loop.py)
│
├─ Audio Capture Thread (speech.py)
│  └─ Continuously reads microphone
│
├─ Audio Processing Thread (speech.py)
│  └─ Detects speech, sends for transcription
│
└─ TTS Thread (tts.py)
   └─ When speak_async() is called
```

**Why Threads?**
- **Non-blocking**: UI stays responsive
- **Parallel**: Listen while speaking
- **Real-time**: No noticeable delay

---

## 🎯 DATA FLOW

### Complete Request-Response Cycle

```
1. LISTEN (Thread)
   Microphone → Audio Buffer → Accumulate 2+ seconds
   
2. DETECT SPEECH (Thread)
   Energy check → Voice Activity Detection
   
3. SILENCE DETECTED (Thread)
   2+ seconds quiet → Trigger transcription
   
4. TRANSCRIBE (Thread)
   Audio → faster-whisper → Text
   Push to queue
   
5. MAIN LOOP (Main Thread)
   Read queue → text = "user said X"
   Process input
   
6. GENERATE RESPONSE (Main Thread - PHASE 1)
   response = "You said: X. Time: HH:MM:SS"
   
7. SPEAK (Thread)
   Text → edge-tts → MP3
   FFmpeg → Playback
   
8. REPEAT
   Go to step 1
```

---

## 🛡️ SAFETY & ERROR HANDLING

Each module has:
- **Try-except blocks** around critical operations
- **Logging** of all errors
- **Graceful degradation** (fallback to CPU if GPU fails)
- **Thread-safe queues** (thread.queue.Queue)

---

## 📈 SCALABILITY PLANNING

### Phase 2 (Tools)
Add to core/loop.py:
```python
def _process_input(self, user_input):
    # Parse intent
    # Select tool
    # Execute tool
    # Return result
```

### Phase 3 (LLM)
Add brain/agent.py:
```python
from brain.agent import Agent
agent = Agent()
response = agent.reason(user_input, context)
```

### Phase 4+ (Complex)
- Add planner (multi-step tasks)
- Add memory (conversation context)
- Add more tools (browser, system, files)

---

## ⚡ PERFORMANCE CHARACTERISTICS

### Memory Usage
- **Idle**: ~300 MB (Whisper model loaded)
- **Listening**: ~400-500 MB
- **Speaking**: ~500-600 MB

### CPU Usage
- **Idle**: ~2-5%
- **Listening**: ~10-20%
- **Transcribing**: ~30-50% (brief spikes)
- **Speaking**: ~5-10%

### Latency (Phase 1)
- **Speech → Text**: 2-5 seconds (depends on model size)
- **Text → Speech**: 1-2 seconds
- **Total response time**: 3-7 seconds

---

## 🔐 Security Model

PHASE 1 is foundational. Later phases add:

1. **Input Validation**
   - Sanitize speech input
   - Validate tool parameters

2. **Permission System**
   - Ask before risky actions
   - Whitelist safe commands

3. **Audit Logging**
   - Log all actions taken
   - Maintain audit trail

---

## 📋 DESIGN DECISIONS

### Why faster-whisper?
✓ Faster than openai/whisper  
✓ Runs locally (no API)  
✓ GPU acceleration support  
✓ Production-ready  

### Why edge-tts?
✓ Free (no API key)  
✓ Natural voices  
✓ No online dependency  
✓ Works offline  

### Why threading + queues?
✓ Non-blocking I/O  
✓ Responsive UI  
✓ Parallel operations  
✓ Clean separation  

### Why queue.Queue?
✓ Thread-safe  
✓ Built-in Python  
✓ No external dependencies  
✓ Proven pattern  

---

## 🚀 FUTURE ENHANCEMENTS

- **WebSocket API**: Remote control
- **Multi-user**: Support multiple voices
- **Database**: Persistent memory
- **Analytics**: Usage statistics
- **GUI**: PyQt HUD
- **Distributed**: Run on multiple machines

---

This architecture ensures LEVI remains:
- **Modular** (easy to extend)
- **Responsive** (non-blocking)
- **Reliable** (error handling)
- **Maintainable** (clean code)
