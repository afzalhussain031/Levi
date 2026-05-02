# LEVI PHASE 1 - Testing & Validation

## 🧪 PHASE 1 TEST CHECKLIST

### Before Running
- [ ] Python 3.10+ installed
- [ ] FFmpeg installed and in PATH
- [ ] Microphone connected and working
- [ ] Dependencies installed: `pip install -r requirements.txt`

### Running PHASE 1

```powershell
python main.py
```

### Expected Behavior

**Test 1: Initialization**
- [ ] No errors on startup
- [ ] See "LEVI is now listening..."
- [ ] Hear voice greeting: "Hello! I'm LEVI..."

**Test 2: Speech Recognition**
- [ ] Speak clearly into microphone
- [ ] Speech is recognized and printed
- [ ] No crashes or errors

**Test 3: Voice Response**
- [ ] Hear voice response after speaking
- [ ] Response includes your text
- [ ] Response includes timestamp

**Test 4: Continuous Listening**
- [ ] Speak multiple times
- [ ] Assistant responds to each input
- [ ] No delays or hanging

**Test 5: Graceful Shutdown**
- [ ] Press Ctrl+C
- [ ] See "Stopping LEVI..." message
- [ ] No errors on exit

---

## 🔍 DEBUGGING

### Enable Debug Logging
In `utils/config.py`:
```python
SYSTEM_CONFIG = {
    "debug_mode": True,  # More verbose output
}
```

### Check Microphone
```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Monitor Audio Stream
```powershell
python -c "
import sounddevice as sd
import numpy as np

print('Recording for 5 seconds...')
duration = 5
fs = 16000
recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
sd.wait()
energy = np.sqrt(np.mean(recording ** 2))
print(f'Audio energy: {energy:.4f}')
"
```

### View Logs
```powershell
Get-Content logs\levi_*.log -Tail 100
```

---

## 🎯 SUCCESS CRITERIA

✅ PHASE 1 is complete when:
1. Can start without errors
2. Listens continuously (no listen_once)
3. Recognizes speech in background thread
4. Produces voice responses
5. Can be stopped gracefully with Ctrl+C

---

## 📈 PERFORMANCE NOTES

- **First run**: May be slow (downloading Whisper model)
- **Subsequent runs**: Much faster
- **CPU usage**: ~10-15% when listening
- **Memory usage**: ~500-800 MB with Whisper base model

To reduce memory, use smaller model:
```python
STT_CONFIG = {
    "model_size": "tiny",  # Faster, less memory
}
```

---

## ⚠️ KNOWN LIMITATIONS (PHASE 1)

- Only echoes back what you say (no AI logic yet)
- No tool execution (coming in PHASE 2)
- No LLM reasoning (coming in PHASE 3)
- No memory of past conversations
- No browser automation

These will be added in subsequent phases.

---

## 🚀 NEXT STEPS

Once PHASE 1 is working:
1. **Proceed to PHASE 2**: Add basic commands
2. **Test tool execution**: Open apps, type text
3. **Integrate Ollama**: Add LLM reasoning
4. **Build agent system**: Multi-step planning

---

Happy testing! 🎉
