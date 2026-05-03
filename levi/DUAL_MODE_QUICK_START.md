# LEVI Dual-Mode Quick Reference

## Status: ✅ FULLY IMPLEMENTED & READY TO TEST

## What Changed

LEVI now has **two distinct operational modes** that you can toggle at runtime:

### 1. 💬 Pure LLM Mode (Default)
- Direct conversation with Ollama AI
- **No tools available** (no browser, search, media)
- Answers questions directly from training knowledge
- Perfect for: Learning, asking questions, having conversations

**Example:**
- You: "Tell me about Einstein"
- LEVI: "Albert Einstein was a theoretical physicist..." ✅ (Direct answer, no browser)

### 2. 🔧 Agent + Tools Mode
- Full access to tools (web search, browser, media)
- Can search the web, open YouTube, control media
- Intelligently decides when to use tools vs answer directly
- Perfect for: Searching, playing media, browser interactions

**Example:**
- You: "Search for latest AI news"
- LEVI: *Opens Google browser and searches* ✅ (Uses tools)

## How to Use

### Starting LEVI
```bash
cd d:\VirtualAssistant\levi
python main.py
```

### Switching Modes in GUI
1. Look for two buttons at the bottom of the chat window:
   - "💬 Pure LLM" 
   - "🔧 Agent + Tools"
2. Click the button for the mode you want
3. The active mode button highlights in green
4. Your conversation history is preserved

### Via Code (For Testing)
```python
from core.agent import LeviAgent

agent = LeviAgent()

# Check current mode
print(agent.get_mode())  # "pure_llm"

# Switch mode
agent.set_mode("agent_with_tools")
print(agent.get_mode())  # "agent_with_tools"

# Use the agent
response = agent.run("Play jazz music")
```

## Default Mode

By default, LEVI starts in **Pure LLM mode** for safer, focused conversations.

To change the default, edit `utils/config.py`:
```python
AGENT_CONFIG = {
    "agent_mode": "pure_llm",  # Change to "agent_with_tools" for tools-first
    ...
}
```

## Test This Now

### Pure LLM Mode Test
1. Make sure "💬 Pure LLM" button is green (active)
2. Ask: "What is photosynthesis?"
3. Expected: Direct answer, NO browser opens ✅

### Switch to Tools Mode
1. Click "🔧 Agent + Tools" button
2. Button highlights in green

### Tools Mode Test
1. Ask: "Search for cat videos"
2. Expected: Browser opens with Google search ✅

### Back to Pure LLM
1. Click "💬 Pure LLM" button
2. Ask: "What is a cat?"
3. Expected: Direct answer, NO browser ✅

## Key Features

✅ **Runtime Switching** - Change modes while chatting
✅ **Conversation Preserved** - History maintained across mode switches
✅ **Visual Feedback** - Active mode highlighted in green
✅ **No Confusion** - Clear system prompts for each mode
✅ **Backward Compatible** - Old code still works

## Files Modified

| File | Changes |
|------|---------|
| `core/agent.py` | Added dual-mode routing, _pure_llm_response(), _agent_response(), set_mode(), get_mode() |
| `gui/app.py` | Added mode toggle buttons, switch_mode() method |
| `utils/config.py` | Added AGENT_CONFIG["agent_mode"] |

## Documentation

For detailed testing scenarios, troubleshooting, and verification, see:
**[TEST_DUAL_MODE.md](TEST_DUAL_MODE.md)**

## Architecture Diagram

```
User Input
    ↓
gui/app.py (display input)
    ↓
core/agent.py run()
    ↓
    ├─→ Is mode "pure_llm"?
    │   └─→ _pure_llm_response()
    │       └─→ ChatOllama.invoke() (direct)
    │           └─→ Response (no tools)
    │
    └─→ Is mode "agent_with_tools"?
        └─→ _agent_response()
            └─→ LangChain agent executor
                └─→ May use tools if needed
                    └─→ Response (clean format)
    ↓
gui/app.py (display response)
```

## Troubleshooting

**Q: Buttons don't appear**
- Make sure you're running the latest gui/app.py
- Check for Python errors in terminal

**Q: Mode doesn't switch**
- Click the button again
- Check that the inactive button shows gray
- Active button should be bright green (#00cc44)

**Q: Still opening browser in Pure LLM mode**
- Verify the button is showing green on "Pure LLM"
- Check the system log message confirms mode switch
- Restart LEVI

**Q: Tools not working in Agent mode**
- Make sure "Agent + Tools" button is green
- Ollama should be running: `ollama serve`
- Check yt-dlp is installed: `pip list | grep yt-dlp`

## Quick Command Reference

```bash
# Check if Ollama is running
ollama list

# Start Ollama (if not running)
ollama serve

# Run LEVI
cd d:\VirtualAssistant\levi
python main.py

# View logs
python main.py 2>&1 | more
```

## What Happens When You Switch Modes

### Pure LLM Mode
- System prompt: "You are LEVI, a helpful voice assistant..."
- No tools available
- Fast, direct responses
- Low resource usage

### Agent + Tools Mode
- System prompt: "Use tools when appropriate..."
- Full tool access
- Smart tool selection
- May use more CPU for reasoning

## Performance Notes

- **Pure LLM Mode**: ~100-500ms response time
- **Agent + Tools Mode**: ~500ms-2s (depends on tool usage)
- Both modes share conversation history (~3-5MB per 100 messages)

---

**Ready to test?** Start LEVI and click the mode buttons!
