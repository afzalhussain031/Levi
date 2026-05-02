# LEVI + Ollama Setup Guide

## What Changed

LEVI now uses **Ollama** (a local LLM) to generate intelligent AI responses instead of just echoing user input.

### New Components

1. **`core/brain.py`** — AI brain module
   - `OllamaClient`: Connects to Ollama API and sends prompts
   - `ConversationMemory`: Stores conversation history for context
   - Thread-safe response generation with proper error handling

2. **Updated `gui/app.py`**
   - Worker thread now uses Ollama for intelligent responses
   - Fallback to echo mode if Ollama unavailable

3. **Updated `utils/config.py`**
   - New LLM settings: `base_url`, `model`, `temperature`, `max_messages`
   - New `SYSTEM_CONFIG["use_ai"]` flag to toggle AI mode

4. **Updated `requirements.txt`**
   - Added `requests` library for API calls to Ollama

## How It Works

### Flow

```
User speaks → Speech Recognition → Recognized Text
                                      ↓
                              Ollama AI Brain
                          (with conversation memory)
                                      ↓
                              AI-Generated Response
                                      ↓
                            Text-to-Speech (TTS)
                                      ↓
                            Plays audio response
```

### Conversation Memory

- Stores last 10 messages (configurable: `LLM_CONFIG["max_messages"]`)
- Provides context to AI model for coherent multi-turn conversations
- Automatically cleared when you restart the app

## Installation & Setup

### Step 1: Install Ollama

Download and install Ollama from: https://ollama.ai

### Step 2: Pull a Model

Open a terminal and run:

```bash
# Pull llama2 (recommended for local use, ~3.8 GB)
ollama pull llama2

# Or try lighter/faster models:
ollama pull mistral        # Fast, good quality (~4 GB)
ollama pull neural-chat    # Good for chat (~3 GB)
ollama pull tinyllama      # Smallest (~500 MB, slower)
```

Check installed models:
```bash
ollama list
```

### Step 3: Start Ollama Server

In a new terminal, run:
```bash
ollama serve
```

You should see:
```
listening on 127.0.0.1:11434
```

Leave this running in the background while using LEVI.

### Step 4: Install Python Dependencies

```bash
cd D:\VirtualAssistant\levi
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 5: Run LEVI GUI

```bash
python main.py
```

The GUI will:
1. Verify Ollama is running
2. Load the configured model (default: llama2)
3. Start listening for speech

## Configuration

Edit `utils/config.py` to customize:

```python
LLM_CONFIG = {
    "base_url": "http://localhost:11434",  # Ollama endpoint
    "model": "llama2",                     # Model to use
    "temperature": 0.7,                    # 0.0-1.0 (creativity)
    "max_messages": 10,                    # Conversation history size
}

SYSTEM_CONFIG = {
    "use_ai": True,                        # Enable/disable AI
    "voice_enabled": True,                 # Enable/disable TTS
}
```

## Troubleshooting

### Error: "Cannot connect to Ollama at http://localhost:11434"

**Solution:** Ollama server isn't running.
```bash
# Open a terminal and run:
ollama serve
```

### Error: "Model not found"

**Solution:** Model isn't installed.
```bash
# Pull the model:
ollama pull llama2
```

### Responses are slow

**Reasons:**
- Using a large model (7B+ parameters)
- CPU is bottleneck (CPU-only processing is slow)
- System is under load

**Solutions:**
- Use a smaller/faster model:
  ```bash
  ollama pull tinyllama    # 1.1B - very fast
  ollama pull neural-chat  # 3.8B - good balance
  ```
- Add `--gpu` flag (if you have NVIDIA/AMD GPU):
  ```bash
  # Check Ollama GPU support documentation
  ```

### Responses don't make sense

**Reasons:**
- Model quality varies by size/training
- Temperature too high (more random)
- Insufficient conversation context

**Solutions:**
- Lower temperature in config (e.g., 0.5 instead of 0.7)
- Increase `max_messages` for more context
- Try a different model

## Example Conversation

```
You: Hey LEVI, what's the weather like?
LEVI: I don't have access to real-time weather data, but I can help you check a weather website 
      or forecast. What location are you interested in?

You: Tell me a joke
LEVI: Why don't scientists trust atoms? Because they make up everything!

You: How do I make pasta?
LEVI: Boil water, add salt, drop in pasta, stir occasionally, and cook for 8-12 minutes until 
      al dente. Drain and serve with your favorite sauce!
```

## Why These Changes

1. **Smarter Responses**: AI models understand context and generate contextual replies
2. **Conversation Memory**: Multi-turn conversations feel natural and coherent
3. **Local & Private**: Ollama runs locally—no cloud, no data sent anywhere
4. **Modular Design**: `brain.py` is separate, easy to extend or replace
5. **Graceful Degradation**: Falls back to echo mode if Ollama unavailable
6. **Production-Ready**: Proper error handling, logging, threading, and timeouts

## What's Next (Future Phases)

- [ ] Intent detection (identify what user wants to do)
- [ ] Tool integration (weather, news, calculations, etc.)
- [ ] Multi-language support
- [ ] Fine-tuning on custom data
- [ ] Long-term memory (save conversations to database)
- [ ] Streaming responses (show AI thinking in real-time)
