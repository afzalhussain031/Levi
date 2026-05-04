"""
Iris LangChain Agent
Uses LangChain's create_agent API with ChatOllama, callable tools, and conversation memory.
"""

from dataclasses import dataclass
from typing import Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_classic.memory import ConversationBufferMemory
from langchain_ollama import ChatOllama

from core.tools import get_langchain_tools, get_action_toolkit
from utils.config import LLM_CONFIG, SYSTEM_CONFIG, AGENT_CONFIG
from utils.logger import logger


@dataclass
class AgentOutcome:
	"""Backward-compatible response container."""
	kind: str
	message: str


class IrisAgent:
	"""LangChain-powered Iris agent."""

	def __init__(self):
		self.logger = logger
		self.ai_enabled = SYSTEM_CONFIG.get("use_ai", True)
		self.toolkit = get_action_toolkit()
		self.tools = get_langchain_tools()
		self.memory = ConversationBufferMemory(
			memory_key="chat_history",
			return_messages=True,
		)
		self.llm: Optional[ChatOllama] = None
		self.agent_executor = None
		self.current_mode = AGENT_CONFIG.get("agent_mode", "pure_llm")

		if self.ai_enabled:
			self._build_agent()

	def _build_agent(self):
		"""Initialize the ChatOllama LLM and LangChain agent graph."""
		try:
			self.llm = ChatOllama(
				model=LLM_CONFIG.get("model", "llama3.1"),
				base_url=LLM_CONFIG.get("base_url", "http://localhost:11434"),
				temperature=LLM_CONFIG.get("temperature", 0.7),
				max_tokens=LLM_CONFIG.get("max_tokens", 500),
			)
			self.agent_executor = create_agent(
				model=self.llm,
				tools=self.tools,
				system_prompt=(
				"You are Iris, a concise, helpful local voice assistant with vision capabilities.\n\n"
				"Be concise. Answer in 1-2 sentences.\n\n"
				"ABSOLUTE RULE: Answer questions directly. NEVER use web_search for general knowledge.\n\n"
				"ALWAYS ANSWER DIRECTLY FOR:\n"
				"- Facts about people (Einstein, Michael Jackson, etc.)\n"
				"- History and events\n"
				"- Geography and cities\n"
				"- Science concepts\n"
				"- Anything from your training\n\n"
				"DO NOT EVER:\n"
				"- Use web_search for general knowledge\n"
				"- Mention function calls or tool names\n"
				"- Include JSON or code in responses\n"
				"- Show thinking about what tool to use\n\n"
				"Just answer naturally and conversationally.\n"
				"Use tools ONLY if the user explicitly asks to search, open applications, open folders, open files, manage files, or analyze screen content.\n"
				"Available tools include open_application, open_folder, open_file, list_files, read_file, create_file, append_to_file, move_file, copy_file, create_folder, delete_file, delete_folder, analyze_screen, read_screen_text.\n"
				"Always confirm before deleting anything.\n"
				"For vision requests like 'What's on my screen?' or 'Describe what you see', use analyze_screen.\n"
				"For text extraction like 'What text is visible?' or 'Read the screen', use read_screen_text."
				),
				debug=False,
				name="Iris",
			)
			self.logger.info(f"✓ LangChain agent initialized with model {LLM_CONFIG.get('model', 'llama3.1')}")
		except Exception as e:
			self.logger.error(f"Failed to initialize LangChain agent: {e}")
			self.logger.warning("Iris will fall back to a simple local response mode.")
			self.ai_enabled = False
			self.agent_executor = None

	def run(self, user_input: str) -> str:
		"""
		Run Iris in the current mode (pure_llm or agent_with_tools).
		Routes based on AGENT_CONFIG["agent_mode"].
		"""
		if not self.ai_enabled:
			return f"I heard you say: {user_input}"

		# Check current mode from config
		current_mode = AGENT_CONFIG.get("agent_mode", "pure_llm")
		self.current_mode = current_mode
		
		if current_mode == "pure_llm":
			return self._pure_llm_response(user_input)
		else:  # agent_with_tools
			return self._agent_response(user_input)

	def _pure_llm_response(self, user_input: str) -> str:
		"""
		Pure conversation mode: Direct LLM call without tools.
		No tool temptation, just helpful conversation.
		"""
		if not self.ai_enabled or self.llm is None:
			return f"I heard you say: {user_input}"

		try:
			memory_vars = self.memory.load_memory_variables({})
			chat_history = memory_vars.get("chat_history", [])
			messages = []
			
			# Add system prompt for pure conversation mode
			messages.append(SystemMessage(content=(
				"You are Iris, a helpful voice assistant. "
				"Be concise. Answer in 1-2 sentences. "
				"Answer all questions directly and conversationally. "
				"You are knowledgeable about many topics and can have natural conversations. "
				"Be concise but thorough in your answers."
			)))
			
			if chat_history:
				messages.extend(chat_history)
			messages.append(HumanMessage(content=user_input))

			# Direct LLM call without LangChain agent
			result = self.llm.invoke(messages)
			assistant_text = result.content.strip() if hasattr(result, "content") else str(result).strip()
			assistant_text = assistant_text or "Sorry, I had trouble generating a response."
			
			self.memory.save_context({"input": user_input}, {"output": assistant_text})
			return assistant_text
		except Exception as e:
			self.logger.error(f"Pure LLM mode failed: {e}")
			return "Sorry, I had trouble generating a response."

	def _agent_response(self, user_input: str) -> str:
		"""
		Agent with tools mode: LangChain agent with full tool access.
		Answers with tools when appropriate, direct answers otherwise.
		"""
		if not self.ai_enabled or self.agent_executor is None:
			return f"I heard you say: {user_input}"

		try:
			memory_vars = self.memory.load_memory_variables({})
			chat_history = memory_vars.get("chat_history", [])
			messages = []
			if chat_history:
				messages.extend(chat_history)
			messages.append(HumanMessage(content=user_input))

			result = self.agent_executor.invoke({"messages": messages})
			assistant_text = ""
			if isinstance(result, dict):
				if "messages" in result and result["messages"]:
					assistant_text = result["messages"][-1].content or ""
				elif "output" in result:
					assistant_text = str(result["output"])
			else:
				assistant_text = str(result)

			assistant_text = assistant_text.strip() or "Sorry, I had trouble generating a response."
			
			# Clean up response: remove function calls, JSON, and tool mentions
			assistant_text = self._clean_response(assistant_text)
			
			self.memory.save_context({"input": user_input}, {"output": assistant_text})
			return assistant_text
		except Exception as e:
			self.logger.error(f"Agent mode failed: {e}")
			return "Sorry, I had trouble generating a response."
	
	def _clean_response(self, text: str) -> str:
		"""Remove function calls, JSON, and tool names from response."""
		import re
		
		# Remove JSON function calls like {"name": "web_search", ...}
		text = re.sub(r'\{["\']name["\']:\s*["\'][^"\']+["\'].*?\}', '', text, flags=re.DOTALL)
		
		# Remove any remaining JSON-like structures
		text = re.sub(r'\{[^}]*\}', '', text)
		
		# Remove phrases mentioning function calls or tools
		phrases_to_remove = [
			r'However, if I had to choose a function call.*?(?=\n|$)',
			r'function call.*?(?=\n|$)',
			r'tool call.*?(?=\n|$)',
			r'would choose.*?(?=\n|$)',
			r'best answers your prompt.*?(?=\n|$)',
		]
		
		for pattern in phrases_to_remove:
			text = re.sub(pattern, '', text, flags=re.IGNORECASE)
		
		# Clean up multiple spaces and extra newlines
		text = re.sub(r'\s+', ' ', text).strip()
		
		return text

	def process_user_input(self, user_input: str, confirm_callback=None) -> AgentOutcome:
		"""Compatibility wrapper for older callers."""
		return AgentOutcome(kind="response", message=self.run(user_input))

	def set_mode(self, mode: str) -> bool:
		"""
		Set the agent mode at runtime.
		Returns True if mode change was successful.
		"""
		valid_modes = ["pure_llm", "agent_with_tools"]
		if mode not in valid_modes:
			self.logger.warning(f"Invalid mode '{mode}'. Valid modes: {valid_modes}")
			return False
		
		AGENT_CONFIG["agent_mode"] = mode
		self.current_mode = mode
		self.logger.info(f"Mode switched to: {mode}")
		return True

	def get_mode(self) -> str:
		"""Get the current agent mode."""
		return self.current_mode

	def clear_memory(self):
		"""Reset conversation history and tool state."""
		try:
			self.memory.clear()
		except Exception:
			pass
		self.toolkit.state.pending_shutdown = False
		self.toolkit.state.last_action = ""
