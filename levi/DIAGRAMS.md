# LEVI System Architecture Diagram

## 🎯 High-Level System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     LEVI ASSISTANT (PHASE 1)                     │
│                     Non-Blocking Architecture                    │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────┐
                    │   MAIN EVENT LOOP    │
                    │   (core/loop.py)     │
                    │   ────────────────   │
                    │  AssistantLoop()     │
                    └──────────┬───────────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
                    ▼          ▼          ▼
              ┌──────────┐ ┌────────┐ ┌────────┐
              │ LISTEN   │ │PROCESS │ │RESPOND │
              │          │ │        │ │        │
              └──────────┘ └────────┘ └────────┘
                    │          │          │
              Async Read   Echo         Async
              Queue        Text         Speak
```

---

## 🔊 AUDIO PIPELINE (Speech Recognition)

```
MICROPHONE
    │
    │ 16 kHz, 16-bit
    ▼
┌──────────────────────────────────────┐
│   AUDIO CAPTURE THREAD               │
│   (speech.py - _audio_capture_loop)  │
│   ─────────────────────────────────  │
│   • sounddevice.InputStream           │
│   • Non-blocking read                 │
│   • Add to circular buffer (30s)      │
└──────────────────┬───────────────────┘
                   │
           Audio Buffer
         (deque, 30 seconds)
                   │
                   ▼
┌──────────────────────────────────────┐
│   PROCESSING THREAD                  │
│   (speech.py - _processing_loop)     │
│   ─────────────────────────────────  │
│   • Voice Activity Detection (VAD)    │
│   • Energy threshold check            │
│   • Silence duration counter          │
│   • Trigger transcription event       │
└──────────────────┬───────────────────┘
                   │
              Detected Speech
               (2+ seconds)
                   │
                   ▼
┌──────────────────────────────────────┐
│   TRANSCRIPTION                      │
│   (speech.py - _transcribe)          │
│   ─────────────────────────────────  │
│   • faster-whisper model              │
│   • Convert audio → text              │
│   • Push to queue                     │
└──────────────────┬───────────────────┘
                   │
            Recognized Text
                   │
                   ▼
         ┌─────────────────┐
         │   TEXT QUEUE    │
         │  (queue.Queue)  │
         │                 │
         │ Thread-safe I/O │
         └────────┬────────┘
                  │
                  │ Main loop
                  │ .get_text()
                  ▼
           Main Event Loop
```

---

## 🔊 TEXT-TO-SPEECH PIPELINE (Voice Output)

```
RESPONSE TEXT (from main loop)
         │
         ▼
┌──────────────────────────────────────┐
│   VOICE OUTPUT                       │
│   (tts.py - VoiceOutput)             │
│   ─────────────────────────────────  │
│   • speak_async(text)                │
│   • Spawn background thread          │
│   • Return immediately               │
└──────────────────┬───────────────────┘
                   │
         Async TTS Thread
                   │
                   ▼
┌──────────────────────────────────────┐
│   TEXT-TO-SPEECH CONVERSION          │
│   (tts.py - _speak_async)            │
│   ─────────────────────────────────  │
│   • edge-tts library                 │
│   • Generate MP3 audio               │
│   • Save to temp file                │
└──────────────────┬───────────────────┘
                   │
            MP3 Audio File
                   │
                   ▼
┌──────────────────────────────────────┐
│   AUDIO PLAYBACK                     │
│   ─────────────────────────────────  │
│   • FFmpeg subprocess                │
│   • Play MP3 audio                   │
│   • Clean up temp file               │
└──────────────────┬───────────────────┘
                   │
            SPEAKER OUTPUT
```

---

## 🧵 THREADING MODEL

```
MAIN PROCESS
│
├─ MAIN THREAD (core/loop.py)
│  ├─ Initialize components
│  ├─ Loop iteration:
│  │  ├─ Check for text from queue
│  │  ├─ Process input (PHASE 1: echo)
│  │  ├─ Queue response for TTS
│  │  └─ Sleep 0.1s (non-blocking)
│  └─ Handle Ctrl+C shutdown
│
├─ AUDIO CAPTURE THREAD (daemon)
│  ├─ Open microphone stream
│  ├─ Read chunks continuously
│  └─ Add to buffer
│
├─ AUDIO PROCESSING THREAD (daemon)
│  ├─ Analyze buffer
│  ├─ Detect speech/silence
│  ├─ When ready, transcribe
│  └─ Push text to queue
│
└─ TTS THREAD (daemon, spawned when needed)
   ├─ Convert text to speech
   ├─ Generate MP3
   ├─ Play audio
   └─ Clean up
```

**Why threads?**
- Main loop responsive (never blocks)
- Listen while speaking
- Process multiple tasks concurrently
- Professional, scalable design

---

## 📊 DATA FLOW DIAGRAM

```
                    MAIN EVENT LOOP
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           │           ▼
    .get_text()     │    speak_async()
        │           │           │
        │           │       TTS Thread
        │           │           │
        ▼           │           ▼
    Input Queue ◄──────────► Output Queue
        │           │           │
        │           │           │
        ▼           │           ▼
    PROCESS      (Logic)      PLAY
    (PHASE 1)                 AUDIO
     ECHO
        │
        │
        ▼
    text = "You said: X. Time: Y:Z"
        │
        │ speak_async(text)
        └──────────────────────┐
                               │
                       (continues async)
                               │
                     User hears response
```

---

## 🔐 THREAD SAFETY

```
┌─────────────────────────────────────┐
│   THREAD SAFETY MODEL               │
├─────────────────────────────────────┤
│                                     │
│  Thread A          Thread B         │
│  (Audio Cap.)   (Main Loop)        │
│      │               │              │
│      ├─ Write ──┐   │              │
│      │          │   │              │
│      └─────────►│ QUEUE │◄────┐   │
│                 │       │     │   │
│                 └───────┘     │   │
│                       │       │   │
│                       └── Read ──┘
│                                     │
│  No locks, no race conditions       │
│  Queue.Queue handles synchronization│
│  FIFO ordering guaranteed           │
│                                     │
└─────────────────────────────────────┘
```

---

## 🎛️ CONFIGURATION HIERARCHY

```
┌─────────────────────────────────────┐
│   CONFIGURATION SYSTEM              │
│   (utils/config.py)                 │
├─────────────────────────────────────┤
│                                     │
│  AUDIO_CONFIG                       │
│  ├─ sample_rate: 16000 Hz           │
│  ├─ silence_threshold: 0.02         │
│  └─ silence_duration: 2.0 sec       │
│                                     │
│  STT_CONFIG                         │
│  ├─ model_size: "base"              │
│  ├─ language: "en"                  │
│  └─ compute_type: "int8"            │
│                                     │
│  TTS_CONFIG                         │
│  ├─ voice: "en-US-GuyNeural"       │
│  ├─ rate: 1.0                       │
│  └─ pitch: 0                        │
│                                     │
│  SYSTEM_CONFIG                      │
│  ├─ debug_mode: True                │
│  ├─ voice_enabled: True             │
│  └─ continuous_listening: True      │
│                                     │
│  PATHS                              │
│  ├─ logs/                           │
│  ├─ data/                           │
│  └─ conversations/                  │
│                                     │
│  ► All used by components            │
│  ► Single source of truth            │
│  ► Easy to modify                    │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔄 REQUEST-RESPONSE CYCLE (PHASE 1)

```
┌──────────────────────────────────────────┐
│  REQUEST-RESPONSE CYCLE (PHASE 1)        │
├──────────────────────────────────────────┤
│                                          │
│  1. LISTEN (Async - Background Thread)   │
│     Microphone ──►  Audio Buffer         │
│     Accumulate 2+ seconds of audio       │
│                                          │
│  2. DETECT SPEECH (Async - Processing)   │
│     Energy ──► VAD ──► Silence Counter   │
│     Check if 2+ seconds of silence       │
│                                          │
│  3. TRANSCRIBE (Async - Still Background)
│     Audio ──► faster-whisper ──► Text    │
│     Convert speech to text                │
│     Push to queue                        │
│                                          │
│  4. MAIN LOOP (Sync - Main Thread)      │
│     Poll queue (non-blocking)            │
│     If text available: process           │
│                                          │
│  5. PROCESS INPUT (Sync - Main Thread)   │
│     PHASE 1: Echo                        │
│     text = "You said: X. Time: Y"        │
│     PHASE 2+: Tool execution             │
│     PHASE 3+: LLM reasoning              │
│                                          │
│  6. GENERATE RESPONSE (Sync - Main)      │
│     Create: response_text                │
│     Call: voice.speak_async(text)        │
│     Return immediately                   │
│                                          │
│  7. SPEAK (Async - TTS Thread)           │
│     Text ──► edge-tts ──► MP3            │
│     ├─ Generate speech                   │
│     ├─ Play with FFmpeg                  │
│     └─ Clean up                          │
│                                          │
│  8. REPEAT                               │
│     Go to step 1                         │
│     Listen for next command              │
│                                          │
│  LATENCY BREAKDOWN:                      │
│  - Speech capture: instant               │
│  - Transcription: 2-5 sec (async)        │
│  - Processing: <100ms                    │
│  - TTS: 1-2 sec (async)                  │
│  - TOTAL USER WAIT: 2-5 sec              │
│                                          │
└──────────────────────────────────────────┘
```

---

## 📈 PERFORMANCE PROFILE

```
┌──────────────────────────────────────┐
│  PERFORMANCE CHARACTERISTICS         │
├──────────────────────────────────────┤
│                                      │
│  CPU USAGE:                          │
│  Idle:           2-5%                │
│  Listening:      10-20%              │
│  Transcribing:   30-50% (brief)      │
│  Speaking:       5-10%               │
│                                      │
│  MEMORY USAGE:                       │
│  Whisper model:  ~300 MB             │
│  Audio buffer:   ~30 MB              │
│  Idle total:     ~300-350 MB         │
│  Peak:           ~500-600 MB         │
│                                      │
│  RESPONSE TIME:                      │
│  Listen→Recognize: 2-5 seconds       │
│  Recognize→Response: <100ms          │
│  Response→Speak: 1-2 seconds         │
│  Total user wait: 3-7 seconds        │
│                                      │
│  FIRST RUN:                          │
│  Model download: 1-2 minutes         │
│  Subsequent: Instant                 │
│                                      │
└──────────────────────────────────────┘
```

---

## 🎯 MODULE INTERACTION MAP

```
┌────────────────────────────────────────────────────────────┐
│  main.py                                                   │
│  Entry point                                               │
└────────────┬───────────────────────────────────────────────┘
             │
             ├─ from core.loop import AssistantLoop
             │
             └─► AssistantLoop()
                 └─ core/loop.py
                    ├─ from audio.speech import SpeechRecognizer
                    │  └─ SpeechRecognizer()
                    │     ├─ from faster_whisper import WhisperModel
                    │     ├─ from utils.logger import logger
                    │     └─ from utils.config import *
                    │
                    ├─ from audio.tts import VoiceOutput
                    │  └─ VoiceOutput()
                    │     ├─ from edge_tts import Communicate
                    │     ├─ from utils.logger import logger
                    │     └─ from utils.config import TTS_CONFIG
                    │
                    ├─ from utils.logger import logger
                    └─ from utils.config import SYSTEM_CONFIG
```

---

This architecture provides a solid foundation for:
- ✅ PHASE 1: Voice I/O
- ➕ PHASE 2: Tool execution
- ➕ PHASE 3: LLM integration
- ➕ PHASE 4: Advanced planning
- ➕ PHASE 5: Complex features
