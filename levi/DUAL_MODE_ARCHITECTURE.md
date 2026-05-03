# LEVI Dual-Mode Architecture Visualization

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          LEVI User Interface                        │
│                        (PyQt6 GUI - gui/app.py)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐  Mode Buttons  ┌──────────────────┐           │
│  │  💬 Pure LLM     │◄─── Click ────►│ 🔧 Agent + Tools │           │
│  │  (Green = ACTIVE)│                │  (Gray = Inactive)│           │
│  └──────────────────┘                └──────────────────┘           │
│           │                                    │                     │
│           │ switch_mode("pure_llm")           │                     │
│           │ Updates AGENT_CONFIG              │ switch_mode("agent_with_tools")
│           │                                    │                     │
└───────────┼────────────────────────────────────┼─────────────────────┘
            │                                    │
            ▼                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│              Configuration Layer (utils/config.py)                    │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  AGENT_CONFIG = {                                                   │
│      "agent_mode": "pure_llm" | "agent_with_tools"  ◄── Routes here
│      ...                                                             │
│  }                                                                   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────┐
│              Agent Router (core/agent.py - run() method)              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  def run(user_input):                                               │
│      if AGENT_CONFIG["agent_mode"] == "pure_llm":                  │
│          return _pure_llm_response(user_input)                      │
│      else:                                                           │
│          return _agent_response(user_input)                         │
│                                                                       │
│         ┌─────────────────────────┬──────────────────────────┐      │
│         │                         │                          │      │
└─────────┼─────────────────────────┼──────────────────────────┼──────┘
          │                         │                          │
          ▼                         ▼                          ▼
    ┌──────────────┐          ┌─────────────────┐      ┌──────────────┐
    │ Pure LLM     │          │ Agent + Tools    │      │  Memory      │
    │ Response     │          │ Response         │      │  (Shared)    │
    └──────────────┘          └─────────────────┘      └──────────────┘
          │                         │                          │
          ▼                         ▼                          ▼
    ┌──────────────────────────────────────────────────────────────┐
    │        Direct ChatOllama         LangChain Agent             │
    │        No tools access          Full tool access            │
    │        Simple prompt            Complex prompt              │
    │        Fast response            Smart reasoning             │
    └──────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Pure LLM Mode Flow
```
USER INPUT
    │
    ▼
┌─────────────────────────────────────┐
│ gui/app.py                          │
│ - Capture user text                 │
│ - Display in chat window            │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ core/agent.py run()                 │
│ Check AGENT_CONFIG["agent_mode"]    │
└─────────────────────────────────────┘
    │
    ├─► Is "pure_llm"? ──► YES ──┐
    │                             │
    │                             ▼
    │                    ┌──────────────────────┐
    │                    │ _pure_llm_response() │
    │                    │                      │
    │                    │ 1. Load chat history │
    │                    │    from memory       │
    │                    │ 2. Add system prompt:│
    │                    │    "Be helpful"      │
    │                    │ 3. Call ChatOllama   │
    │                    │    (DIRECT)          │
    │                    │ 4. Save to memory    │
    │                    │ 5. Return response   │
    │                    └──────────────────────┘
    │                             │
    │                             ▼
    │                    ┌──────────────────────┐
    │                    │  OLLAMA LLM          │
    │                    │ (http://localhost)   │
    │                    │ Answers directly     │
    │                    │ NO tool reasoning    │
    │                    └──────────────────────┘
    │                             │
    │                             ▼
    │                    Response Text (no JSON)
    │                             │
    └─────────────────────────────┼─────────────┐
                                  │             │
                                  ▼             ▼
                        ┌────────────────────────────┐
                        │ gui/app.py                  │
                        │ Display response in chat    │
                        │ Update button styles        │
                        │ Log mode and response       │
                        └────────────────────────────┘
```

### Agent with Tools Mode Flow
```
USER INPUT
    │
    ▼
┌─────────────────────────────────────┐
│ gui/app.py                          │
│ - Capture user text                 │
│ - Display in chat window            │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ core/agent.py run()                 │
│ Check AGENT_CONFIG["agent_mode"]    │
└─────────────────────────────────────┘
    │
    ├─► Is "agent_with_tools"? ──► YES ──┐
    │                                     │
    │                                     ▼
    │                            ┌──────────────────────┐
    │                            │ _agent_response()    │
    │                            │                      │
    │                            │ 1. Load chat history │
    │                            │ 2. Call LangChain    │
    │                            │    agent executor    │
    │                            │ 3. Agent evaluates   │
    │                            │    available tools   │
    │                            └──────────────────────┘
    │                                     │
    │                    ┌────────────────┼────────────────┐
    │                    │                │                │
    │                    ▼                ▼                ▼
    │            ┌────────────────┐  ┌──────────┐  ┌──────────────┐
    │            │ OLLAMA LLM     │  │ web_     │  │ Media/YouTube│
    │            │ (reasoning)    │  │ search   │  │ Tools        │
    │            │                │  │ Tool     │  │              │
    │            │ Decides:       │  │          │  │              │
    │            │ - Use tools?   │  │ Opens    │  │ Opens YouTube│
    │            │ - Which tool?  │  │ Google   │  │ or media     │
    │            │ - Answer?      │  │ Chrome   │  │              │
    │            └────────────────┘  └──────────┘  └──────────────┘
    │                    │                │                │
    │                    └────────────────┼────────────────┘
    │                                     │
    │                                     ▼
    │                            ┌──────────────────────┐
    │                            │ _clean_response()    │
    │                            │                      │
    │                            │ Remove:              │
    │                            │ - JSON artifacts     │
    │                            │ - Function calls     │
    │                            │ - Tool mentions      │
    │                            └──────────────────────┘
    │                                     │
    └─────────────────────────────────────┼─────────────┐
                                          │             │
                                          ▼             ▼
                                ┌────────────────────────────┐
                                │ gui/app.py                  │
                                │ Display response in chat    │
                                │ Update button styles        │
                                │ Log mode and response       │
                                └────────────────────────────┘
```

## Mode Switching Flow

```
┌─────────────────────────────────────┐
│ User clicks mode button in GUI       │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│ gui/app.py switch_mode(mode)         │
│ - Validate mode parameter           │
│ - Update AGENT_CONFIG               │
│ - Change button styles:             │
│   Active → green (#00cc44)          │
│   Inactive → gray (#555)            │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│ Update AGENT_CONFIG dict            │
│ AGENT_CONFIG["agent_mode"] = mode   │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│ Next user question...               │
│                                     │
│ agent.run(user_input)               │
│ ├─► Check AGENT_CONFIG              │
│ └─► Route to correct handler        │
└─────────────────────────────────────┘
```

## Component Interactions

```
┌────────────────────────────────────────────────────────────────┐
│                      LEVI System Components                    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  GUI Layer (gui/app.py)                                       │
│  ├─ Mode buttons (Pure LLM, Agent+Tools)                      │
│  ├─ Chat display                                              │
│  └─ switch_mode() method                                      │
│           │                                                    │
│           ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Config Layer (utils/config.py)                       │    │
│  │ ├─ AGENT_CONFIG["agent_mode"]                        │    │
│  │ ├─ LLM_CONFIG (Ollama connection)                    │    │
│  │ ├─ STT_CONFIG (Speech-to-text)                       │    │
│  │ └─ TTS_CONFIG (Text-to-speech)                       │    │
│  └──────────────────────────────────────────────────────┘    │
│           │                                                    │
│           ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Agent Layer (core/agent.py)                          │    │
│  │ ├─ run() - Routes to correct mode                    │    │
│  │ ├─ _pure_llm_response() - Direct LLM                 │    │
│  │ ├─ _agent_response() - LangChain agent               │    │
│  │ ├─ set_mode() / get_mode() - Mode management         │    │
│  │ ├─ memory - ConversationBufferMemory (shared)        │    │
│  │ └─ _clean_response() - Response sanitization        │    │
│  └──────────────────────────────────────────────────────┘    │
│           │                ▲                                   │
│           │                │                                   │
│      ┌────▼────┐      ┌────┴────┐                             │
│      ▼         ▼      ▼         │                             │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │ Pure LLM Path    │  │ Agent Path       │                  │
│  │                  │  │                  │                  │
│  │ ChatOllama       │  │ LangChain Agent  │                  │
│  │ (Direct call)    │  │ with Tools       │                  │
│  │                  │  │                  │                  │
│  │ No tools         │  │ web_search       │                  │
│  │ No reasoning     │  │ open_youtube     │                  │
│  │ Fast response    │  │ media_controls   │                  │
│  └──────────────────┘  │ play_music       │                  │
│                        │ shutdown_pc      │                  │
│                        └──────────────────┘                  │
│           │                    ▲                              │
│           └────────┬───────────┘                              │
│                    │                                          │
│           ┌────────▼────────┐                                 │
│           │ Ollama LLM      │                                │
│           │ (localhost:     │                                │
│           │  11434)         │                                │
│           └─────────────────┘                                │
│                                                               │
│  Audio Layer (audio/)                                        │
│  ├─ speech.py (STT with Whisper)                            │
│  └─ tts.py (Edge TTS for responses)                         │
│                                                               │
│  Action Layer (actions/)                                     │
│  └─ actions.py (OS control)                                  │
│                                                               │
└────────────────────────────────────────────────────────────┘
```

## State Machine Diagram

```
                    ┌─────────────────┐
                    │    STARTUP      │
                    │ (Pure LLM mode) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
        ┌──────────►│  PURE_LLM_MODE  │◄──────────┐
        │           │                 │           │
        │           │ • No tools      │           │
        │           │ • Direct answer │           │
        │           │ • Fast response │           │
        │           └────────┬────────┘           │
        │                    │                    │
        │     User clicks    │     User clicks    │
        │   "Agent+Tools"    │    "Pure LLM"      │
        │     button         │     button         │
        │                    │                    │
        │           ┌────────▼────────┐           │
        └───────────│ AGENT_WITH_TOOLS│───────────┘
                    │                 │
                    │ • Full tools    │
                    │ • Smart logic   │
                    │ • May be slower │
                    └─────────────────┘

                    On Each State:
                    • Button styling changes
                    • Config updated
                    • Next user input routed correctly
                    • Conversation history preserved
```

## Configuration Update Path

```
User clicks button
    │
    ▼
switch_mode(mode) called
    │
    ├─ Validate mode
    │
    ├─ Update AGENT_CONFIG in memory
    │  │
    │  └─ AGENT_CONFIG["agent_mode"] = mode
    │
    ├─ Update button styles
    │  │
    │  └─ Active button: #00cc44 (bright green)
    │  └─ Inactive button: #555 (gray)
    │
    ├─ Display confirmation in chat
    │  │
    │  └─ "Mode switched to: ..." message
    │
    └─ Log in system
       │
       └─ [INFO] Mode switched to: {mode}
```

---

**Note:** All diagrams show the production architecture after dual-mode implementation.
