# 🤖 Iris - AI Voice Assistant

**Iris** is a production-level, modular AI voice assistant that runs locally on Windows. It listens to your voice, understands intent, and executes actions intelligently.

---

## 📋 PROJECT STRUCTURE

```
levi/
├── audio/              # Speech input/output
│   ├── speech.py       # Real-time STT (faster-whisper)
│   └── tts.py          # Voice output (edge-tts)
│
├── brain/              # AI decision making (coming in later phases)
│   ├── agent.py        # LLM reasoning engine
│   ├── planner.py      # Task breakdown
│   └── memory.py       # Conversation memory
│
├── actions/            # System automation (coming in later phases)
│   ├── system.py       # OS commands
│   ├── browser.py      # Web automation
│   └── automation.py    # Mouse/keyboard
│
├── core/               # Main application loop
│   └── loop.py         # Event loop (non-blocking)
│
├── utils/              # Utilities
│   ├── logger.py       # Logging system
│   └── config.py       # Configuration
│
├── ui/                 # UI components (future)
│   └── hud.py          # Optional GUI
│
├── main.py             # Entry point
└── requirements.txt    # Dependencies
```

---

## 🚀 PHASE 1: SPEECH INPUT + VOICE OUTPUT

### What's Working Now:
✅ **Real-time speech recognition** (faster-whisper)  
✅ **Non-blocking audio capture** (background thread)  
✅ **Voice responses** (edge-tts)  
✅ **Modular architecture**  
✅ **Production logging**  

### What It Does:
1. Listens continuously for speech
2. Converts speech to text (real-time)
3. Responds with voice output
4. Simple echo responses for testing

---

## 📦 INSTALLATION

### Step 1: Install Python (3.10+)
```powershell
# Download from: https://www.python.org/downloads/
# Or use Windows Package Manager:
winget install Python.Python.3.11
```

### Step 2: Install Dependencies

```powershell
# Navigate to project
cd d:\VirtualAssistant\levi

# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### Step 3: Install FFmpeg (Required for edge-tts)
Edge-tts uses FFmpeg to convert MP3 to playable audio.

**Option A: Windows Package Manager (Recommended)**
```powershell
winget install FFmpeg
```

**Option B: Manual Download**
- Download from: https://ffmpeg.org/download.html
- Add to Windows PATH

**Verify Installation:**
```powershell
ffmpeg -version
```

### Step 5: Vision Setup (Optional - For Screen Analysis)

LEVI can analyze your screen using LLaVA vision models through Ollama.

**Install Ollama:**
```powershell
# Download from: https://ollama.ai/download
# Install and start Ollama service
```

**Pull LLaVA Model:**
```powershell
# In a terminal (not PowerShell):
ollama pull llava
```

**Verify Vision Dependencies:**
```powershell
pip install Pillow pyautogui
```

**Test Vision:**
```powershell
python -c "import core.vision; v = core.vision.get_vision_processor(); print('Vision ready')"
```

---

## 🎤 RUNNING LEVI (PHASE 1)

### Start the Assistant:
```powershell
python main.py
```

### Expected Output:
```
===============================================================
🤖 LEVI ASSISTANT - Initializing Core Loop
===============================================================
2024-01-15 10:30:45 | INFO     | LEVI: Initializing Speech Recognizer
2024-01-15 10:30:48 | INFO     | LEVI: Speech Recognizer initialized successfully
2024-01-15 10:30:48 | INFO     | LEVI: Initializing Voice Output
2024-01-15 10:30:48 | INFO     | LEVI: Voice Output ready
2024-01-15 10:30:48 | INFO     | LEVI: ✓ Core Loop initialized successfully
2024-01-15 10:30:48 | INFO     | LEVI: 🎙️  LEVI is now listening...
2024-01-15 10:30:49 | INFO     | LEVI: 🔊 Speaking: Hello! I'm LEVI...
```

### Interact:
1. Speak clearly into your microphone
2. LEVI recognizes your speech
3. You'll hear a voice response
4. Continue speaking—it keeps listening

### Stop:
- Press **Ctrl+C** in the terminal

---

## 🔧 CONFIGURATION

Edit `utils/config.py` to customize:

```python
# Speech Recognition Settings
AUDIO_CONFIG = {
    "sample_rate": 16000,           # Audio sampling rate
    "silence_threshold": 0.02,      # Sensitivity to silence
    "silence_duration": 2.0,        # Time before transcribing
}

# Whisper Model Size
STT_CONFIG = {
    "model_size": "base",           # tiny, base, small, medium, large
    "language": "en",               # Language code
}

# Voice Settings
TTS_CONFIG = {
    "voice": "en-US-GuyNeural",     # Available voices
    "rate": 1.0,                    # Speech rate (0.5-2.0)
}
```

### Available TTS Voices:
```
# Male voices:
en-US-GuyNeural
en-US-ArthurNeural

# Female voices:
en-US-JennyNeural
en-US-AmberNeural
```

See more: https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support

---

## 🧠 TROUBLESHOOTING

### "ModuleNotFoundError: No module named 'faster_whisper'"
```powershell
pip install faster-whisper
```

### "FFmpeg not found"
```powershell
winget install FFmpeg
```

### "No audio input detected"
1. Check microphone in Windows Settings
2. Test microphone: `python -c "import sounddevice as sd; print(sd.query_devices())"`
3. Run in admin mode if still failing

### "CUDA device not found" (uses CPU instead)
This is normal. Assistant will fall back to CPU (slower but works fine).

### Speech recognition is slow
- Use smaller model: `"model_size": "tiny"` in config.py
- Trade accuracy for speed

---

## 📊 PHASE ROADMAP

### ✅ PHASE 1: Speech I/O
- Real-time listening + voice responses

### ⏳ PHASE 2: Basic Commands
- Open apps, type text, get time
- Tool-based execution

### ⏳ PHASE 3: LLM Integration
- Ollama (Llama 3 / Mistral)
- Smart reasoning

### ⏳ PHASE 4: Agent System
- Multi-step planning
- Tool selection logic
- Context awareness

### ⏳ PHASE 5: Advanced Features
- Conversation memory
- Browser automation
- System integration
- **Vision capabilities** (LLaVA screen analysis)

---

## 📝 LOGGING

Logs are saved to `logs/` directory:
```
levi/
└── logs/
    └── levi_20240115_103045.log
```

View logs:
```powershell
Get-Content logs\levi_*.log -Tail 50  # Last 50 lines
```

---

## 💡 EXAMPLE USAGE (PHASE 1)

```
LEVI: "Hello! I'm LEVI, your virtual assistant. I'm ready to listen."

YOU: "What time is it?"

LEVI: "You said: What time is it?. Processed at 10:30:45."

YOU: "Open my browser"

LEVI: "You said: Open my browser. Processed at 10:31:12."
```

*(Phase 2 will actually execute these commands)*

### Vision Examples (Phase 5):
```
YOU: "What's on my screen?"

LEVI: "Screen analysis: I can see a web browser window open with a search page, a code editor with Python files, and some system icons in the taskbar."

YOU: "Read the text on my screen"

LEVI: "Screen text: Welcome to GitHub - LEVI Virtual Assistant, def analyze_screen(self, tool_input: str) -> str:, import PIL from ImageGrab"
```

---

## 🔐 SAFETY & PRIVACY

- ✅ **Local-only**: No data sent to cloud
- ✅ **Offline LLM**: Uses Ollama (self-hosted)
- ✅ **Privacy**: Your conversations stay on your PC
- ✅ **Open source**: Full code transparency

---

## 🤝 NEXT STEPS

After PHASE 1 is working:
1. Proceed to **PHASE 2** for basic commands
2. Add **PHASE 3** for LLM reasoning
3. Build **tool system** in PHASE 4

---

## 📚 REFERENCES

- **faster-whisper**: https://github.com/guillaumekln/faster-whisper
- **edge-tts**: https://github.com/rany2/edge-tts
- **sounddevice**: https://python-sounddevice.readthedocs.io/
- **Ollama**: https://ollama.ai/

---

**Happy coding! 🚀**
