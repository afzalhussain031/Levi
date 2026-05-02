# 📖 LEVI Setup Guide for Windows

Complete step-by-step instructions for setting up LEVI on Windows.

---

## 📋 PRE-REQUISITES

Before starting, ensure:
- ✓ Windows 10/11
- ✓ Internet connection
- ✓ Microphone connected
- ✓ ~5 GB free disk space (for Whisper model)
- ✓ Administrator access (for some installations)

---

## 🔧 INSTALLATION STEPS

### STEP 1: Install Python 3.11

**Option A: Windows Package Manager (Recommended)**
```powershell
winget install Python.Python.3.11
```

**Option B: Manual Download**
1. Visit https://www.python.org/downloads/
2. Download Python 3.11
3. Run installer
4. ✓ Check "Add Python to PATH"
5. Click Install

**Verify:**
```powershell
python --version
```

Should show: `Python 3.11.x`

---

### STEP 2: Install FFmpeg

FFmpeg is required for audio processing.

**Option A: Windows Package Manager (Recommended)**
```powershell
winget install FFmpeg
```

**Option B: Chocolatey**
```powershell
choco install ffmpeg
```

**Option C: Manual Installation**
1. Visit https://ffmpeg.org/download.html
2. Download Windows build
3. Extract to `C:\ffmpeg`
4. Add to PATH:
   - Right-click This PC → Properties
   - Advanced system settings
   - Environment Variables
   - Add `C:\ffmpeg\bin` to PATH

**Verify:**
```powershell
ffmpeg -version
```

Should show FFmpeg version info.

---

### STEP 3: Clone/Download LEVI

Navigate to your workspace:
```powershell
cd d:\VirtualAssistant\levi
```

The project should already be here from initialization.

---

### STEP 4: Create Virtual Environment

Virtual environment isolates dependencies for this project.

```powershell
# Navigate to LEVI directory
cd d:\VirtualAssistant\levi

# Create virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Or for Command Prompt:
# venv\Scripts\activate.bat
```

**Expected output:**
```
(venv) PS d:\VirtualAssistant\levi>
```

The `(venv)` prefix indicates virtual environment is active.

---

### STEP 5: Install Dependencies

```powershell
# Make sure virtual environment is activated
# Then:

pip install --upgrade pip

pip install -r requirements.txt
```

**Installation takes 5-10 minutes.**

What gets installed:
- `faster-whisper` - Speech recognition
- `numpy` - Numerical computing
- `sounddevice` - Microphone access
- `soundfile` - Audio file handling
- `edge-tts` - Text-to-speech

---

### STEP 6: Verify Installation

Run system check:
```powershell
python check_system.py
```

Expected output:
```
============================================================
  LEVI Assistant - System Check
============================================================

============================================================
  Python Version
============================================================
✓ Python 3.11.x

============================================================
  Project Structure
============================================================
✓ audio/
✓ brain/
... [more items] ...

============================================================
  Required Packages
============================================================
✓ faster-whisper installed
✓ numpy installed
✓ sounddevice installed
✓ soundfile installed
✓ edge-tts installed

============================================================
  FFmpeg Installation
============================================================
✓ FFmpeg installed
  ffmpeg version 6.0

============================================================
  Microphone Status
============================================================
Found 4 audio device(s):
  [0] Microphone (Name)
      Channels: 2
  ... [more devices] ...

============================================================
  Summary
============================================================
✓ Python Version
✓ Project Structure
✓ Required Packages
✓ FFmpeg
✓ Microphone

Passed: 5/5

🎉 All checks passed! Ready to run: python main.py
```

---

## 🚀 RUNNING LEVI

### First Run

The first run will download the Whisper model (~1-2 GB):

```powershell
# Make sure virtual environment is activated
# Then:

python main.py
```

**First run may take 1-2 minutes** (downloading model)

---

### Expected Startup Output

```
============================================================
🤖 LEVI ASSISTANT - Initializing Core Loop
============================================================

2024-01-15 14:30:45 | INFO     | LEVI: Initializing Speech Recognizer
2024-01-15 14:30:48 | INFO     | LEVI: Initializing Whisper model...
[downloading model file from huggingface...]
[loading model...]
2024-01-15 14:31:05 | INFO     | LEVI: Speech Recognizer initialized successfully
2024-01-15 14:31:05 | INFO     | LEVI: Initializing Voice Output
2024-01-15 14:31:05 | INFO     | LEVI: Voice Output ready
2024-01-15 14:31:05 | INFO     | LEVI: ✓ Core Loop initialized successfully
2024-01-15 14:31:05 | INFO     | LEVI: 🎙️  LEVI is now listening...
2024-01-15 14:31:06 | INFO     | LEVI: 🔊 Speaking: Hello! I'm LEVI...
```

---

### Testing LEVI

Once running:

1. **Wait** for "LEVI is now listening..."
2. **Speak**: "Hello LEVI"
3. **Watch** terminal for recognized text
4. **Hear** voice response
5. **Repeat**: Speak again

Example:
```
YOU: "Hello LEVI"
[LEVI hears, recognizes, and speaks response]

LEVI: "You said: Hello LEVI. Processed at 14:31:15."
```

---

### Stopping LEVI

Press **Ctrl + C** in terminal:

```
^C
⏸️ Received stop signal
⏹️ Stopping LEVI...
✓ LEVI stopped

(venv) PS d:\VirtualAssistant\levi>
```

---

## ⚠️ TROUBLESHOOTING

### Problem: "Python not found"

**Solution 1:** Reinstall Python with PATH option
```powershell
winget install --force Python.Python.3.11
```

**Solution 2:** Add Python to PATH manually
- Find Python: `Where.exe python`
- Copy path to directory containing `python.exe`
- Add to Environment Variables

**Solution 3:** Use full path
```powershell
C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe main.py
```

---

### Problem: "FFmpeg not found"

**Quick fix:**
```powershell
winget install FFmpeg

# Restart PowerShell and try again
```

**Manual fix:**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Edit Environment Variables:
   - Windows Key → "Environment Variables"
   - User variables → New
   - Variable name: `PATH`
   - Variable value: `C:\ffmpeg\bin`
4. Restart PowerShell

---

### Problem: "ModuleNotFoundError"

**Make sure virtual environment is activated:**
```powershell
# Activate it:
.\venv\Scripts\Activate.ps1

# Should show (venv) prefix in terminal

# Then try again:
python main.py
```

---

### Problem: Microphone not detected

**Check 1: Windows Settings**
1. Settings → Sound
2. Check microphone is enabled
3. Test microphone

**Check 2: List available devices**
```powershell
python -c "import sounddevice; print(sounddevice.query_devices())"
```

**Check 3: Test audio recording**
```powershell
python -c "
import sounddevice as sd
import numpy as np

print('Recording for 3 seconds...')
recording = sd.rec(int(3 * 16000), samplerate=16000, channels=1)
sd.wait()
energy = np.sqrt(np.mean(recording ** 2))
print(f'Audio detected: {energy > 0.01}')
"
```

**Check 4: Run with default device**
In `utils/config.py`:
```python
AUDIO_CONFIG = {
    "device": "default",  # Use default microphone
}
```

---

### Problem: Very slow transcription

**Normal on first run!** The model downloads on first use.

**To speed up permanently:**
Edit `utils/config.py`:
```python
STT_CONFIG = {
    "model_size": "tiny",    # Faster (less accurate)
    # vs "base" (default)
    # vs "small"
}
```

Sizes:
- `tiny` - Fastest, least accurate (39M)
- `base` - Default (140M)
- `small` - More accurate (490M)
- `medium` - Even more accurate (1.5G)
- `large` - Most accurate (3.1G)

---

### Problem: High CPU usage

**This is normal during transcription!**
- Idle: 2-5%
- Listening: 10-20%
- Transcribing: 30-50%

If persistently high, reduce model size (see above).

---

## 📖 NEXT STEPS

Once PHASE 1 is working:

1. **Read documentation:**
   - README.md - Full overview
   - ARCHITECTURE.md - System design
   - QUICK_START.md - 5-min guide

2. **Customize LEVI:**
   - Edit `utils/config.py`
   - Change voice, model size, sensitivity

3. **Prepare for PHASE 2:**
   - Review brain/ module structure
   - Plan basic commands (open app, type text)

---

## 🆘 GETTING HELP

1. **Run system check:**
   ```powershell
   python check_system.py
   ```

2. **Check logs:**
   ```powershell
   Get-Content logs\*.log -Tail 100
   ```

3. **Enable debug:**
   In `utils/config.py`:
   ```python
   SYSTEM_CONFIG = {"debug_mode": True}
   ```

4. **Restart terminal** (fresh environment)

---

## ✅ VERIFICATION CHECKLIST

- [ ] Python 3.11 installed
- [ ] FFmpeg installed
- [ ] Virtual environment created
- [ ] Dependencies installed (pip install -r requirements.txt)
- [ ] System check passed
- [ ] Can run: `python main.py`
- [ ] Microphone detected
- [ ] Can speak and hear responses
- [ ] Can stop with Ctrl+C

---

## 🎉 Success!

If all checks pass and LEVI is listening, you've completed PHASE 1!

Next: **PHASE 2** (basic commands)

```powershell
python main.py
```

Welcome to LEVI! 🚀
