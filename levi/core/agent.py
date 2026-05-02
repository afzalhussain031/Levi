"""
LEVI LangChain Agent
Uses LangChain's create_agent API with ChatOllama, callable tools, and conversation memory.
"""

from dataclasses import dataclass
from typing import Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_classic.memory import ConversationBufferMemory
from langchain_ollama import ChatOllama

from core.tools import get_langchain_tools, get_action_toolkit
from utils.config import LLM_CONFIG, SYSTEM_CONFIG
from utils.logger import logger


@dataclass
class AgentOutcome:
	"""Backward-compatible response container."""
	kind: str
	message: str


class LeviAgent:
	"""LangChain-powered LEVI agent."""

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

		if self.ai_enabled:
			self._build_agent()

	def _build_agent(self):
		"""Initialize the ChatOllama LLM and LangChain agent graph."""
		try:
			self.llm = ChatOllama(
				model=LLM_CONFIG.get("model", "llama3.1"),
				base_url=LLM_CONFIG.get("base_url", "http://localhost:11434"),
				temperature=LLM_CONFIG.get("temperature", 0.7),
			)
			self.agent_executor = create_agent(
				model=self.llm,
				tools=self.tools,
				system_prompt=(
					"You are LEVI, a concise, helpful local voice assistant. "
					"Use tools when the user wants browser or system actions. "
					"For dangerous actions like shutdown, require explicit confirmation. "
					"Keep responses short and natural for text-to-speech."
				),
				debug=False,
				name="LEVI",
			)
			self.logger.info(f"✓ LangChain agent initialized with model {LLM_CONFIG.get('model', 'llama3.1')}")
		except Exception as e:
			self.logger.error(f"Failed to initialize LangChain agent: {e}")
			self.logger.warning("LEVI will fall back to a simple local response mode.")
			self.ai_enabled = False
			self.agent_executor = None

	def run(self, user_input: str) -> str:
		"""Run the LangChain agent and return the final response string."""
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
			self.memory.save_context({"input": user_input}, {"output": assistant_text})
			return assistant_text
		except Exception as e:
			self.logger.error(f"LangChain agent run failed: {e}")
			return "Sorry, I had trouble generating a response."

	def process_user_input(self, user_input: str, confirm_callback=None) -> AgentOutcome:
		"""Compatibility wrapper for older callers."""
		return AgentOutcome(kind="response", message=self.run(user_input))

	def clear_memory(self):
		"""Reset conversation history and tool state."""
		try:
			self.memory.clear()
		except Exception:
			pass
		self.toolkit.state.pending_shutdown = False
		self.toolkit.state.last_action = ""
