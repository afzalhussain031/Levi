# 🚀 LEVI Quick Start Guide

Get LEVI running in 5 minutes!

---

## ⚡ 5-MINUTE SETUP

### Step 1: Open PowerShell
Press `Win + X`, then select **Windows PowerShell** (or Terminal)

### Step 2: Navigate to LEVI
```powershell
cd d:\VirtualAssistant\levi
```

### Step 3: Run Setup
**Option A: Automated Setup (Recommended)**
```powershell
python setup.py
```

Or for batch file (Windows Command Prompt):
```cmd
setup.bat
```

**Option B: Manual Setup**
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Run LEVI
```powershell
python main.py
```

### Step 5: Test It
1. Wait for message: "🎙️ LEVI is now listening..."
2. Speak into your microphone
3. You'll see the recognized text
4. You'll hear a voice response

---

## ✅ SYSTEM CHECK

Before running, verify your system:

```powershell
python check_system.py
```

This checks:
- ✓ Python version
- ✓ Required packages
- ✓ FFmpeg installation
- ✓ Microphone availability
- ✓ Project structure

---

## 🎤 FIRST RUN

**Expected Output:**
```
==================================================
🤖 LEVI ASSISTANT - Initializing Core Loop
==================================================
Initializing Speech Recognizer...
[Loading Whisper model - may take 30 seconds on first run]
Initializing Voice Output...
✓ Core Loop initialized

🎙️ LEVI is now listening...
🔊 Speaking: Hello! I'm LEVI...
```

**What to do next:**
1. Speak clearly into your microphone
2. Example: "Hello LEVI" or "What time is it?"
3. LEVI will recognize and respond

---

## 🛠️ TROUBLESHOOTING

### Issue: "Python not found"
**Solution:**
```powershell
# Install Python from https://python.org
# Or use Windows Package Manager:
winget install Python.Python.3.11

# Verify:
python --version
```

### Issue: "FFmpeg not found"
**Solution:**
```powershell
winget install FFmpeg

# Verify:
ffmpeg -version
```

### Issue: "No microphone detected"
**Solution:**
1. Check Windows Settings → Sound → Volume
2. Ensure microphone is enabled
3. Test with:
```powershell
python -c "import sounddevice; sounddevice.query_devices()"
```

### Issue: "Module not found" errors
**Solution:**
```powershell
pip install -r requirements.txt --upgrade
```

### Issue: Slow transcription (first run)
**Normal!** The Whisper model downloads (~1-2 GB) on first use.
Subsequent runs are much faster.

**To speed up:**
Edit `utils/config.py`:
```python
STT_CONFIG = {
    "model_size": "tiny",  # Faster, less accurate
}
```

---

## 🎯 EXAMPLE INTERACTIONS (PHASE 1)

### Test 1: Simple Echo
```
YOU: "Hello world"
LEVI: "You said: Hello world. Processed at 10:30:45."
```

### Test 2: Multiple Inputs
```
YOU: "Open Chrome"
LEVI: "You said: Open Chrome. Processed at 10:31:12."

YOU: "What time is it?"
LEVI: "You said: What time is it?. Processed at 10:31:25."
```

### Test 3: Noisy Environment
LEVI works best in quiet environments. If noisy:
- Speak louder and slower
- Reduce background noise
- Move closer to microphone

---

## 🔧 CONFIGURATION

Want to customize LEVI? Edit `utils/config.py`:

```python
# Microphone sensitivity
AUDIO_CONFIG = {
    "silence_threshold": 0.02,   # Lower = more sensitive
    "silence_duration": 2.0,     # How long silence before transcribe
}

# Speech recognition accuracy
STT_CONFIG = {
    "model_size": "base",        # tiny, base, small, medium, large
}

# Voice settings
TTS_CONFIG = {
    "voice": "en-US-GuyNeural",  # Change voice
    "rate": 1.0,                 # Speech speed
}
```

---

## 📝 LOGS

LEVI keeps detailed logs in `logs/` directory:

```powershell
# View latest log
Get-Content logs\*.log -Tail 50

# Or in File Explorer:
# Open: d:\VirtualAssistant\levi\logs\
```

---

## 🛑 STOPPING LEVI

Press **Ctrl + C** in the terminal:
```
^C
⏸️ Received stop signal
⏹️ Stopping LEVI...
✓ LEVI stopped
```

---

## 🎓 NEXT STEPS

### After PHASE 1 works:

1. **PHASE 2**: Add basic commands
   - Open apps
   - Type text
   - Get time/date

2. **PHASE 3**: Integrate Ollama LLM
   - Smart reasoning
   - Intent understanding

3. **PHASE 4**: Agent system
   - Multi-step tasks
   - Tool selection

---

## 📚 DOCUMENTATION

- **README.md** - Full overview
- **ARCHITECTURE.md** - System design
- **TESTING_PHASE1.md** - Test checklist
- **check_system.py** - Verify setup

---

## 💡 TIPS

- **Best performance**: Run in quiet environment
- **Faster setup**: Use `"model_size": "tiny"`
- **Better accuracy**: Use `"model_size": "base"` or larger
- **Multiple commands**: Speak naturally, LEVI will respond to each
- **Debug issues**: Run `python check_system.py`

---

## 🆘 GETTING HELP

If something doesn't work:

1. Run system check:
   ```powershell
   python check_system.py
   ```

2. Check logs:
   ```powershell
   Get-Content logs\*.log -Tail 100
   ```

3. Enable debug mode in config.py:
   ```python
   SYSTEM_CONFIG = {"debug_mode": True}
   ```

4. Restart and capture full output

---

## 🎉 You're All Set!

Ready to run?

```powershell
python main.py
```

Welcome to LEVI! 🚀
