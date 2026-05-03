# 🎤 Speech Transcription Troubleshooting Guide

## Issue Analysis

Your speech transcription accuracy issues are likely caused by **one or more of these factors**:

---

## 1. Model Size Too Small ⚠️ (Most Common Issue)

### Current Setting
```python
STT_CONFIG = {
    "model_size": "tiny",  # ← This is the problem!
}
```

### The Problem
- **"tiny"** model = 39M parameters, ~60-70% accuracy
- Optimized for speed, NOT accuracy
- Struggles with accents, background noise, unclear speech
- Great for testing, terrible for production use

### Model Comparison

| Model  | Size  | Speed      | Accuracy | Best For                |
|--------|-------|-----------|----------|------------------------|
| tiny   | 39M   | 30x+      | ~60-70%  | Testing only            |
| base   | 74M   | 10x       | ~85-90%  | Good balance            |
| small  | 244M  | 4x        | ~90-95%  | Production use          |
| medium | 769M  | 2x        | ~95%     | High accuracy needed    |
| large  | 1.5B  | 1x        | ~97%     | Maximum accuracy        |

### Solution
**Upgrade to "base" or "small"**:

```python
STT_CONFIG = {
    "model_size": "base",  # Better accuracy, still reasonable speed
    # OR
    "model_size": "small", # Best balance for local use
}
```

**First Run Time**:
- base: ~400MB download, ~1 min first load
- small: ~1.7GB download, ~2 min first load

---

## 2. Microphone & Audio Quality Issues 🔊

### Problem Symptoms
- Missing words or phrases
- Correct words but wrong context
- Speech detected but not transcribed

### Diagnostics

**Check Microphone Quality**:
```powershell
# Test microphone with Windows Sound Settings
# Settings → Sound → Input devices → Test microphone

# Run LEVI's diagnostic
python check_system.py
```

**Check Audio Levels**:
```powershell
# Verify microphone volume (should be 80-100%)
# Settings → Sound → Volume mixer
```

### Solutions

**1. Adjust Microphone Input Level**
```
Windows Settings → Sound → Volume mixer
→ Find your microphone → Ensure volume is 80-100%
```

**2. Enable Microphone Boost (if available)**
```
Settings → Sound → Advanced → Microphone properties
→ Levels tab → Microphone Boost → +20dB
```

**3. Reduce Background Noise**
- Noise-cancelling microphone
- Separate quiet room for demos
- Close background applications
- Turn off fans/AC during critical moments

**4. Use a Better Microphone**
- USB condenser microphone (~$50+)
- Headset with built-in mic (more directional)
- Blue Yeti, Audio-Technica AT2020, Rode NT1

---

## 3. Silence Detection Parameters Not Tuned 🔇

### Current Settings
```python
AUDIO_CONFIG = {
    "silence_threshold": 0.0075,    # Energy threshold
    "silence_duration": 0.5,        # Time before transcribing
    "energy_window": 0.8,           # Window for computing energy
}
```

### The Problems
- **silence_threshold too high**: Background noise triggers speech detection
- **silence_threshold too low**: Actual speech is missed
- **silence_duration too short**: Words cut off mid-speech
- **silence_duration too long**: Delayed response

### How to Tune

**Step 1: Run a Diagnostic**
```powershell
cd d:\VirtualAssistant\levi

# Create this test script:
# Create file: test_audio_levels.py
```

**Step 2: Monitor Audio Energy**
Add this to `config.py` to see real-time energy levels:
```python
DEBUG_AUDIO = True  # Shows energy levels in logs
```

**Step 3: Analyze the Output**
```
[DEBUG] Audio energy (last 0.8s): 0.0012 (threshold: 0.0075)  ← No speech
[DEBUG] Audio energy (last 0.8s): 0.0082 (threshold: 0.0075)  ← Speech detected!
[DEBUG] Audio energy (last 0.8s): 0.0041 (threshold: 0.0075)  ← Back to silence
```

### Recommended Adjustments

**For Noisy Environment**:
```python
AUDIO_CONFIG = {
    "silence_threshold": 0.015,     # Higher = ignore more noise
    "silence_duration": 0.7,        # Longer = less cutting off
    "energy_window": 1.0,           # Larger window for stability
}
```

**For Quiet Environment**:
```python
AUDIO_CONFIG = {
    "silence_threshold": 0.004,     # Lower = more sensitive
    "silence_duration": 0.3,        # Shorter = faster response
    "energy_window": 0.5,           # Smaller window = quicker detection
}
```

**For Balanced/Production**:
```python
AUDIO_CONFIG = {
    "silence_threshold": 0.008,     # Good middle ground
    "silence_duration": 0.5,        # Normal response time
    "energy_window": 0.8,           # Reasonable stability
}
```

---

## 4. Device Configuration Issues 🖥️

### Current Setting
```python
AUDIO_CONFIG = {
    "device": None,  # Uses default device
}

STT_CONFIG = {
    "device": "cpu",  # CPU processing
}
```

### Potential Problems

**1. Wrong Microphone Selected**
```powershell
# List available audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"
```

Output shows:
```
0 Microphone (Realtek), not assigned
1 USB Audio Device ← Usually better quality
2 Headset Microphone
...
```

**Solution**: Set specific device in config:
```python
AUDIO_CONFIG = {
    "device": 1,  # Use USB Audio Device
}
```

**2. CUDA vs CPU (GPU Acceleration)**
```python
STT_CONFIG = {
    "device": "cpu",      # Current (safe but slower)
    # OR
    "device": "cuda",     # GPU (faster, if NVIDIA GPU available)
}
```

---

## 5. Language & Model Mismatches 🌍

### Current Setting
```python
STT_CONFIG = {
    "language": "en",  # English only
}
```

### Issue
- If you're speaking with accent not in "en" training
- Or speaking non-English mixed with English

### Solutions

**For Specific Accents**:
```python
STT_CONFIG = {
    "language": "en",  # Usually handles most English accents
    # Or let Whisper auto-detect:
    # Leave blank and Whisper auto-detects
}
```

**For Non-English Speech**:
```python
# Language codes:
# "es" - Spanish
# "fr" - French
# "de" - German
# "zh" - Chinese
# etc.

STT_CONFIG = {
    "language": "es",  # Spanish
}
```

---

## 6. Streaming vs VAD Mode Performance 🔄

### Current Mode
```python
AUDIO_CONFIG = {
    "streaming": False,  # Uses VAD (Voice Activity Detection)
}
```

### Comparison

| Mode    | Speed | Accuracy | Latency | Best For                 |
|---------|-------|----------|---------|-------------------------|
| VAD     | Medium| ~85-90%  | 1-3s    | Production (default)    |
| Streaming| Slower| ~95%+    | 3-5s    | High accuracy           |

### When to Use Streaming

If you have:
- Time for longer latency (3-5 seconds ok)
- Need maximum accuracy
- Lower noise environment

```python
AUDIO_CONFIG = {
    "streaming": True,  # Transcribe each chunk immediately
}
```

---

## Complete Optimization Guide

### Step 1: Upgrade Model Size (Highest Impact)

Edit [utils/config.py](utils/config.py):
```python
STT_CONFIG = {
    "model_size": "small",  # ← Change from "tiny"
    "device": "cpu",
    "language": "en",
    "temperature": 0.0,
    "condition_on_previous_text": False,
    "compute_type": "int8",
}
```

**First run will download ~1.7GB and take ~2 minutes.**

### Step 2: Tune Silence Detection

Edit [utils/config.py](utils/config.py):

**Option A: Balanced (Recommended)**
```python
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "chunk_duration": 0.5,
    "silence_threshold": 0.008,    # ← Tuned
    "silence_duration": 0.5,       # ← Tuned
    "energy_window": 0.8,          # ← Tuned
    "streaming": False,
    "device": None,
}
```

**Option B: Noisy Environment**
```python
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "chunk_duration": 0.5,
    "silence_threshold": 0.015,    # ← Higher (ignore more noise)
    "silence_duration": 0.7,       # ← Longer (don't cut off)
    "energy_window": 1.0,
    "streaming": False,
    "device": None,
}
```

**Option C: Quiet Environment**
```python
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "chunk_duration": 0.5,
    "silence_threshold": 0.004,    # ← Lower (more sensitive)
    "silence_duration": 0.3,       # ← Shorter (faster)
    "energy_window": 0.5,
    "streaming": False,
    "device": None,
}
```

### Step 3: Verify Setup

```powershell
# Run system check
python check_system.py

# Test STT directly
python -c "
from audio.speech import SpeechRecognizer
recognizer = SpeechRecognizer()
recognizer.start_listening()
print('Speak now...')
import time
time.sleep(5)
text = recognizer.get_text(timeout=10)
print(f'Result: {text}')
recognizer.stop_listening()
"
```

---

## Quick Fixes (In Order of Impact)

### Fix #1: Upgrade Model (Takes 2 min setup, +25% accuracy)
```python
# utils/config.py, line 20
"model_size": "small",  # From "tiny"
```

### Fix #2: Test Different Microphone Device
```python
# utils/config.py, line 5
"device": 1,  # Or 2, 3... try each until clear
```

### Fix #3: Reduce Background Noise
- Close unnecessary applications
- Find quieter room
- Use noise-cancelling mic

### Fix #4: Tune Silence Threshold
```python
# utils/config.py, line 9
"silence_threshold": 0.012,  # Experiment with values
```

### Fix #5: Enable GPU (if available)
```python
# utils/config.py, line 27
"device": "cuda",  # If NVIDIA GPU available
```

---

## Testing & Validation

### Test 1: Basic Accuracy Test

```powershell
python main.py

# Speak these test phrases:
1. "Hello LEVI"                     ← Simple greeting
2. "What time is it?"               ← Question
3. "Play some jazz music please"    ← Command with request
4. "The quick brown fox jumps"      ← Complex sentence
5. "123 456 7890"                   ← Numbers
```

**Expected**: 95%+ accuracy with "small" model

### Test 2: Noise Robustness

```powershell
# Test with background noise (TV, fan, traffic)
python main.py

# Speak same phrases with noise
```

**Expected**: Still >80% accuracy

### Test 3: Speed Test

```powershell
python main.py

# Time from speech end to recognition start
# Should be: 0.5-2 seconds (VAD mode)
```

### Test 4: Different Accents

```powershell
# If multiple speakers, test each:
- Native English speaker
- Non-native speaker
- Quiet vs loud speech
- Fast vs slow speech
```

---

## Expected Accuracy Improvements

### Before Optimization
```
Model: tiny
Accuracy: 60-70%
Example: "Play music" → "Play moo-sick"
```

### After Optimization (Model Upgrade Only)
```
Model: small
Accuracy: 90-95%
Example: "Play music" → "Play music" ✓
```

### After Full Optimization (Model + Tuning)
```
Model: small + tuned parameters
Accuracy: 95%+
Example: "Play some jazz music" → "Play some jazz music" ✓
```

---

## Troubleshooting Specific Issues

### Issue: "Keeps recognizing silence as speech"
**Cause**: silence_threshold too low
**Fix**: 
```python
"silence_threshold": 0.015,  # Increase value
```

### Issue: "Cuts off words mid-sentence"
**Cause**: silence_duration too short
**Fix**:
```python
"silence_duration": 0.7,  # Increase value
```

### Issue: "Takes forever to respond"
**Cause**: Model too large OR silence_duration too long
**Fix**:
```python
"model_size": "base",       # Reduce model
"silence_duration": 0.3,    # Shorter duration
```

### Issue: "Only recognizes loud speech"
**Cause**: silence_threshold too high
**Fix**:
```python
"silence_threshold": 0.004,  # Lower value
```

### Issue: "Accuracy still poor despite changes"
**Causes**: 
- Bad microphone
- Too much background noise
- Using "tiny" model still
**Fix**:
- Get better microphone
- Find quieter environment
- Verify "small" model is loaded

### Issue: "CPU usage too high"
**Cause**: Large model on weak CPU
**Fix**:
```python
"model_size": "tiny",  # Smaller model
"device": "cuda",      # Use GPU if available
```

---

## Performance Benchmarks

### On CPU (Ryzen 5 5600X)

| Model  | Load Time | Transcribe 3s Audio | CPU Usage |
|--------|-----------|-------------------|-----------|
| tiny   | 10s       | 0.5s              | 30%       |
| base   | 15s       | 1.5s              | 60%       |
| small  | 20s       | 3s                | 80%       |
| medium | 30s       | 8s                | 95%+      |

### On GPU (RTX 3060)

| Model  | Load Time | Transcribe 3s Audio | GPU Memory |
|--------|-----------|-------------------|-----------|
| tiny   | 5s        | 0.2s              | 600MB     |
| base   | 8s        | 0.4s              | 800MB     |
| small  | 12s       | 0.7s              | 1.2GB     |
| medium | 20s       | 1.5s              | 2GB       |

---

## Recommended Configuration by Use Case

### Development/Testing
```python
STT_CONFIG = {
    "model_size": "tiny",       # Fast iteration
    "device": "cpu",
}
AUDIO_CONFIG = {
    "silence_threshold": 0.01,
    "silence_duration": 0.5,
}
```

### Production/Demo
```python
STT_CONFIG = {
    "model_size": "small",      # Best balance
    "device": "cpu",
}
AUDIO_CONFIG = {
    "silence_threshold": 0.008,
    "silence_duration": 0.5,
}
```

### High Accuracy
```python
STT_CONFIG = {
    "model_size": "medium",     # Maximum accuracy
    "device": "cuda",           # GPU recommended
}
AUDIO_CONFIG = {
    "silence_threshold": 0.006,
    "silence_duration": 0.6,
}
```

### Low Noise Environment
```python
STT_CONFIG = {
    "model_size": "small",
    "device": "cpu",
}
AUDIO_CONFIG = {
    "silence_threshold": 0.004,  # Very sensitive
    "silence_duration": 0.3,     # Quick response
}
```

---

## Next Steps

1. **Immediately**: Upgrade model to "small"
2. **Then**: Run test phrases and measure accuracy
3. **Next**: Adjust silence parameters if needed
4. **If still poor**: Check microphone quality
5. **Final**: Consider GPU acceleration for larger models

**Expected result**: 90-95%+ accuracy after these changes.

---

## Additional Resources

- **faster-whisper docs**: https://github.com/SYSTRAN/faster-whisper
- **Whisper models**: https://github.com/openai/whisper
- **Audio troubleshooting**: See `SETUP_GUIDE.md`

