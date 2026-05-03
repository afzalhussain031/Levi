# LEVI Dual-Mode Implementation Test Guide

## Overview
LEVI now supports two operational modes that can be toggled at runtime:
1. **Pure LLM Mode** (`pure_llm`) - Direct conversation, no tools
2. **Agent with Tools Mode** (`agent_with_tools`) - Full tool access (search, browser, media, etc.)

## Architecture Changes

### Core Changes in `core/agent.py`:
- **`current_mode` field**: Tracks the active mode
- **`run()` method**: Routes to correct mode handler based on `AGENT_CONFIG["agent_mode"]`
- **`_pure_llm_response()`**: New method for direct LLM conversation
- **`_agent_response()`**: New method for agent with tools (existing logic)
- **`set_mode(mode)`**: Runtime mode switching method
- **`get_mode()`**: Query current mode method

### GUI Changes in `gui/app.py`:
- **Mode toggle buttons**: "💬 Pure LLM" and "🔧 Agent + Tools" buttons
- **`switch_mode(mode)`**: Method to switch modes with visual feedback
- **Button styling**: Active mode highlighted in green (#00cc44), inactive in gray (#555)

### Configuration in `utils/config.py`:
- **`AGENT_CONFIG`**: New field `"agent_mode": "pure_llm"` (default)

## Test Scenarios

### Scenario 1: Start in Pure LLM Mode (Default)
```bash
cd d:\VirtualAssistant\levi
python main.py
```
**Expected Behavior:**
- GUI launches with both mode buttons visible
- "💬 Pure LLM" button highlighted in green (active)
- "🔧 Agent + Tools" button highlighted in gray (inactive)

### Scenario 2: Test Pure LLM Mode Directly
Ask these questions while in Pure LLM mode:
1. **"Tell me about Albert Einstein"**
   - Expected: Direct answer from LLM about Einstein
   - ❌ Should NOT open browser
   - ❌ Should NOT call web_search tool
   - ✅ Should answer from training knowledge

2. **"What is quantum mechanics?"**
   - Expected: Detailed explanation from LLM
   - ❌ Should NOT open browser
   - ✅ Should answer directly

3. **"How was Rome founded?"**
   - Expected: Historical explanation from LLM
   - ❌ Should NOT open browser
   - ✅ Should answer directly

### Scenario 3: Switch to Agent + Tools Mode
**Action:** Click "🔧 Agent + Tools" button
**Expected Behavior:**
- "🔧 Agent + Tools" button highlights in green (active)
- "💬 Pure LLM" button changes to gray (inactive)
- System logs: "Switched to agent_with_tools mode"
- UI displays: "Mode switched to: 🔧 Agent + Tools (Search, Browser, Media)"

### Scenario 4: Test Agent Mode with Tools
Ask these questions while in Agent + Tools mode:
1. **"Search for latest AI news"**
   - Expected: Google browser opens, searches performed
   - ✅ Should use web_search tool
   - ✅ Should open Chrome

2. **"Play jazz music"**
   - Expected: YouTube opens and plays jazz
   - ✅ Should use media tools
   - ✅ Should open YouTube or media player

3. **"What is Python?" (General knowledge)**
   - Expected: LLM answers directly without search
   - ✅ Should answer directly
   - ❌ Should NOT search (unless user explicitly asks)

### Scenario 5: Switch Back to Pure LLM Mode
**Action:** Click "💬 Pure LLM" button
**Expected Behavior:**
- "💬 Pure LLM" button highlights in green (active)
- "🔧 Agent + Tools" button changes to gray (inactive)
- System logs: "Switched to pure_llm mode"
- UI displays: "Mode switched to: 💬 Pure LLM (Direct Conversation)"

### Scenario 6: Test Pure LLM Mode Again
Ask: **"Tell me about the moon"**
- Expected: Direct LLM answer
- ❌ Should NOT open browser
- ✅ Should answer directly

### Scenario 7: Mode Persistence
Ask a multi-turn conversation in Pure LLM mode:
1. "What is photosynthesis?"
2. "How does it help plants grow?"
3. "What plants photosynthsize the fastest?"
**Expected Behavior:**
- All questions answered directly
- Conversation history maintained
- No tools used
- Context from previous questions understood

### Scenario 8: Mode Persistence in Agent Mode
Ask a multi-turn conversation in Agent + Tools mode:
1. "Search for world record for fastest plant growth"
2. "Show me a video of fast-growing plants"
3. "What's the tallest plant in the world?"
**Expected Behavior:**
- First question uses web_search (browser opens)
- Second question uses media/YouTube tools
- Third question might search or answer directly
- Conversation history maintained

## Expected Code Flow

### Pure LLM Mode Flow:
```
User Input → gui/app.py → agent.py.run()
  → AGENT_CONFIG["agent_mode"] == "pure_llm"
  → agent.py._pure_llm_response()
  → Direct ChatOllama.invoke() (no LangChain agent)
  → System prompt: "Just be helpful and conversational"
  → Response → Display in GUI
```

### Agent Mode Flow:
```
User Input → gui/app.py → agent.py.run()
  → AGENT_CONFIG["agent_mode"] == "agent_with_tools"
  → agent.py._agent_response()
  → LangChain agent.executor.invoke()
  → System prompt: "Use tools when appropriate, answer directly otherwise"
  → May call tools (web_search, media, etc.)
  → Response → Clean (_clean_response) → Display in GUI
```

## Runtime Mode Switching

### Via GUI (Recommended):
1. Click "💬 Pure LLM" or "🔧 Agent + Tools" button
2. Mode changes immediately
3. Next question uses new mode
4. Conversation history preserved

### Via Code (For Testing):
```python
# In main.py or test script
from core.agent import LeviAgent

agent = LeviAgent()
print(f"Current mode: {agent.get_mode()}")  # "pure_llm"

agent.set_mode("agent_with_tools")
print(f"Current mode: {agent.get_mode()}")  # "agent_with_tools"

response = agent.run("Tell me about Python")
```

## Configuration

### Default Mode (Pure LLM):
```python
# utils/config.py
AGENT_CONFIG = {
    "agent_mode": "pure_llm",  # Start in conversation-only mode
    ...
}
```

### Change Default Mode:
Edit `utils/config.py`:
```python
AGENT_CONFIG = {
    "agent_mode": "agent_with_tools",  # Start in tools mode
    ...
}
```

## Troubleshooting

### Issue: Mode button clicks don't change mode
**Solution:**
1. Check that `AGENT_CONFIG` is imported in gui/app.py
2. Verify switch_mode() method is called
3. Check logs for mode switch confirmation

### Issue: Pure LLM mode still opens browser
**Solution:**
1. Verify you're in pure_llm mode (button should be green)
2. Check that _pure_llm_response() is being called
3. Ensure agent.py uses AGENT_CONFIG["agent_mode"] check

### Issue: Agent mode doesn't use tools
**Solution:**
1. Verify you're in agent_with_tools mode (button should be green)
2. Check that agent_executor is initialized
3. Verify tools are registered in get_langchain_tools()
4. Check system prompt includes tool usage guidelines

### Issue: Conversation history lost after mode switch
**Solution:**
- This should NOT happen. Memory is preserved across mode switches.
- Both modes use the same ConversationBufferMemory object
- Check memory.clear() is not being called

## Performance Notes

- **Pure LLM Mode**: Slightly faster (no tool reasoning overhead)
- **Agent Mode**: May be slower (evaluates whether to use tools)
- **Memory**: Both modes share same conversation history (~3-5MB for 100+ messages)

## Future Enhancements

1. **Persistent Mode Setting**: Save last used mode to disk
2. **Mode-Specific Shortcuts**: Keyboard shortcuts for mode switching
3. **Auto-Mode Detection**: Analyze user input to suggest mode
4. **Mode Profiles**: Save conversation contexts per mode
5. **Tool Whitelist**: In agent mode, restrict available tools

## Verification Checklist

- [ ] GUI buttons render correctly (green/gray)
- [ ] Clicking buttons changes active mode visually
- [ ] Pure LLM mode answers questions without tools
- [ ] Agent mode uses tools when appropriate
- [ ] Conversation history persists across mode switches
- [ ] System logs show mode switches
- [ ] No errors in console/logs
- [ ] Both modes handle multi-turn conversations
- [ ] Mode can be switched mid-conversation

## Test Automation

To run automated mode tests:
```python
# test_dual_mode.py (create this file)
import asyncio
from core.agent import LeviAgent

async def test_dual_mode():
    agent = LeviAgent()
    
    # Test 1: Pure LLM mode
    agent.set_mode("pure_llm")
    response1 = agent.run("What is gravity?")
    print(f"Pure LLM: {response1}")
    
    # Test 2: Agent mode
    agent.set_mode("agent_with_tools")
    response2 = agent.run("What is gravity?")
    print(f"Agent: {response2}")
    
    # Test 3: Mode persistence
    agent.set_mode("pure_llm")
    response3 = agent.run("Can you explain that more?")
    print(f"Follow-up in Pure LLM: {response3}")

asyncio.run(test_dual_mode())
```

---

**Ready for testing!** Follow the scenarios above to verify dual-mode functionality.
