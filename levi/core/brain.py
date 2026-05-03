"""
LEVI Brain Module
Handles conversation memory, rule-based intent detection, and Ollama-based AI decisions.
"""

import json
import re
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

from utils.config import LLM_CONFIG, SYSTEM_CONFIG
from utils.logger import logger


@dataclass
class IntentDecision:
    """Structured decision returned by the brain."""
    kind: str  # "action" or "response"
    response: str = ""
    action: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    source: str = "rule"
    raw: str = ""


class ConversationMemory:
    """Simple bounded conversation memory."""

    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self.history = deque(maxlen=max_messages)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_history(self):
        return list(self.history)

    def get_context(self):
        if not self.history:
            return ""
        return "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in self.history)

    def clear(self):
        self.history.clear()


class OllamaClient:
    """Low-level Ollama HTTP client."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or LLM_CONFIG["base_url"]
        self.model = model or LLM_CONFIG["model"]
        self.logger = logger
        self._verify_connection()

    def _verify_connection(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info(f"✓ Ollama connected at {self.base_url}")
                models = response.json().get("models", [])
                self.logger.debug(f"Available models: {[m.get('name') for m in models]}")
                return
            raise RuntimeError(f"Ollama returned {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Cannot connect to Ollama at {self.base_url}. Is it running? (ollama serve)")
            raise RuntimeError(f"Ollama not accessible at {self.base_url}") from e

    def chat(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """Send chat messages to Ollama and return assistant content."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": LLM_CONFIG.get("temperature", 0.7),
                "top_p": LLM_CONFIG.get("top_p", 0.9),
                "num_predict": LLM_CONFIG.get("max_tokens", 500),
            },
        }
        if json_mode:
            payload["format"] = "json"

        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Ollama error {response.status_code}: {response.text}")

        result = response.json()
        return result.get("message", {}).get("content", "").strip()


class LeviBrain:
    """High-level brain that decides between action and response."""

    def __init__(self):
        self.logger = logger
        self.ai_enabled = SYSTEM_CONFIG.get("use_ai", True)
        self.memory = ConversationMemory(max_messages=LLM_CONFIG.get("max_messages", 10))
        self.client: Optional[OllamaClient] = None

        if self.ai_enabled:
            try:
                self.client = OllamaClient()
            except Exception as e:
                self.logger.error(f"AI brain unavailable: {e}")
                self.logger.warning("LEVI will fall back to rule-based responses.")
                self.ai_enabled = False

    def remember_turn(self, user_input: str, assistant_response: str):
        self.memory.add_message("user", user_input)
        self.memory.add_message("assistant", assistant_response)

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def detect_rule_based_intent(self, user_input: str) -> Optional[IntentDecision]:
        text = self._normalize(user_input)

        if any(phrase in text for phrase in ["shutdown pc", "shut down", "power off", "turn off the computer", "turn off the pc"]):
            return IntentDecision(
                kind="action",
                action="shutdown_pc",
                requires_confirmation=True,
                response="I need confirmation before shutting down the PC.",
                source="rule",
            )

        if any(phrase in text for phrase in ["open chrome", "launch chrome", "start chrome", "open browser", "launch browser"]):
            return IntentDecision(
                kind="action",
                action="open_chrome",
                response="Opening Chrome.",
                source="rule",
            )

        # Google/web search: "search X on google", "google X", "search for X"
        if any(phrase in text for phrase in ["search", "google"]) and any(phrase in text for phrase in ["on google", "google ", "search for"]):
            # Try multiple patterns to extract the search query
            match = re.search(r"google\s+(.+?)(?:\s+on google)?$", text)
            if not match:
                match = re.search(r"search\s+for\s+(.+?)(?:\s+on google)?$", text)
            if not match:
                match = re.search(r"search\s+(.+?)\s+on google$", text)
            
            query = match.group(1).strip() if match else None
            if query:
                return IntentDecision(
                    kind="action",
                    action="web_search",
                    arguments={"query": query},
                    response="Searching Google.",
                    source="rule",
                )

        if "youtube" in text and any(phrase in text for phrase in ["open", "launch", "start", "play", "go to"]):
            query = None
            match = re.search(r"(?:search|find|play) (.+?) on youtube", text)
            if match:
                query = match.group(1).strip()
            return IntentDecision(
                kind="action",
                action="open_youtube",
                arguments={"query": query} if query else {},
                response="Opening YouTube.",
                source="rule",
            )

        return None

    def _extract_json(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                pass

        return {}

    def _parse_json_decision(self, content: str) -> IntentDecision:
        payload = self._extract_json(content)

        kind = payload.get("kind") or payload.get("type") or "response"
        action = payload.get("action")
        arguments = payload.get("arguments") or {}
        response = payload.get("response") or ""
        requires_confirmation = bool(payload.get("requires_confirmation", False))

        if kind not in {"action", "response"}:
            kind = "response"

        return IntentDecision(
            kind=kind,
            action=action,
            arguments=arguments if isinstance(arguments, dict) else {},
            response=response,
            requires_confirmation=requires_confirmation,
            source="ai",
            raw=content,
        )

    def decide_intent(self, user_input: str, available_actions: List[str]) -> IntentDecision:
        """Decide whether the user wants an action or a normal response."""
        rule_decision = self.detect_rule_based_intent(user_input)
        if rule_decision:
            return rule_decision

        if not self.ai_enabled or self.client is None:
            return IntentDecision(kind="response", response=self.generate_response(user_input), source="fallback")

        system_prompt = (
            "You are LEVI's decision engine. Return ONLY valid JSON. "
            "Choose either an action or a natural language response. "
            "If the user requests a supported tool, return kind=\"action\" and set action to one of the available actions. "
            "If the action is dangerous, set requires_confirmation=true. "
            "Otherwise return kind=\"response\". "
            "Use this JSON shape: {\"kind\":\"action|response\",\"action\":null,\"arguments\":{},\"response\":\"...\",\"requires_confirmation\":false}."
        )

        context = self.memory.get_context()
        user_message = (
            f"Available actions: {', '.join(available_actions)}\n\n"
            f"Conversation context:\n{context if context else 'None'}\n\n"
            f"User: {user_input}"
        )

        try:
            content = self.client.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                json_mode=True,
            )
            decision = self._parse_json_decision(content)

            if decision.kind == "action" and decision.action not in available_actions:
                self.logger.warning(f"AI returned unsupported action: {decision.action}")
                return IntentDecision(kind="response", response=self.generate_response(user_input), source="fallback")

            return decision

        except Exception as e:
            self.logger.error(f"AI decision failed: {e}")
            return IntentDecision(kind="response", response=self.generate_response(user_input), source="fallback")

    def generate_response(self, user_input: str) -> str:
        """Generate a normal conversational AI response."""
        if not self.ai_enabled or self.client is None:
            return f"I heard you say: {user_input}"

        system_prompt = (
            "You are LEVI, a helpful voice assistant. "
            "Be concise, friendly, and natural. Keep replies short enough for TTS."
        )

        messages = [{"role": "system", "content": system_prompt}]
        context = self.memory.get_context()
        if context:
            messages.append({"role": "system", "content": f"Conversation context:\n{context}"})
        messages.append({"role": "user", "content": user_input})

        try:
            return self.client.chat(messages)
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "Sorry, I had trouble generating a response."


class IntentRouter:
    """Simple high-level classifier for safe GUI routing."""

    GENERAL_PREFIXES = (
        "what",
        "who",
        "when",
        "where",
        "why",
        "how",
        "explain",
        "tell me",
        "describe",
        "define",
    )

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def is_general_query(self, user_input: str) -> bool:
        text = self._normalize(user_input)
        if not text:
            return True
        return text.endswith("?") or text.startswith(self.GENERAL_PREFIXES)
