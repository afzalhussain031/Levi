"""
LEVI AI Brain Module
Integrates local Ollama LLM for intelligent responses
Maintains conversation history and context
"""

import requests
import json
from collections import deque
from utils.logger import logger
from utils.config import LLM_CONFIG


class ConversationMemory:
    """
    Simple conversation memory manager
    Stores recent user + assistant messages for context
    """

    def __init__(self, max_messages=10):
        """Initialize memory with max capacity"""
        self.max_messages = max_messages
        self.history = deque(maxlen=max_messages)

    def add_message(self, role: str, content: str):
        """Add a message to history (role: 'user' or 'assistant')"""
        self.history.append({"role": role, "content": content})

    def get_history(self):
        """Get conversation history as list"""
        return list(self.history)

    def get_context(self):
        """Get conversation context as formatted string"""
        if not self.history:
            return ""
        lines = [f"{msg['role'].upper()}: {msg['content']}" for msg in self.history]
        return "\n".join(lines)

    def clear(self):
        """Clear conversation history"""
        self.history.clear()


class OllamaClient:
    """
    Ollama LLM client
    Sends prompts to local Ollama instance and retrieves responses
    """

    def __init__(self, base_url=None, model=None):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama API endpoint (default from config)
            model: Model name (default from config)
        """
        self.base_url = base_url or LLM_CONFIG["base_url"]
        self.model = model or LLM_CONFIG["model"]
        self.logger = logger
        
        # Conversation memory
        self.memory = ConversationMemory(max_messages=LLM_CONFIG.get("max_messages", 10))
        
        # Verify connection on init
        self._verify_connection()

    def _verify_connection(self):
        """Verify Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info(f"✓ Ollama connected at {self.base_url}")
                models = response.json().get("models", [])
                self.logger.debug(f"Available models: {[m.get('name') for m in models]}")
            else:
                self.logger.warning(f"Ollama returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Cannot connect to Ollama at {self.base_url}. Is it running? (ollama serve)")
            raise RuntimeError(f"Ollama not accessible at {self.base_url}")
        except Exception as e:
            self.logger.error(f"Error verifying Ollama connection: {e}")
            raise

    def generate_response(self, user_input: str) -> str:
        """
        Generate AI response to user input
        
        Args:
            user_input: User's text input
            
        Returns:
            AI-generated response text
        """
        try:
            # Add user message to memory
            self.memory.add_message("user", user_input)
            
            # Build prompt with context
            context = self.memory.get_context()
            prompt = self._build_prompt(user_input, context)
            
            self.logger.debug(f"Sending to {self.model}: {user_input[:100]}...")
            
            # Send to Ollama
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": LLM_CONFIG.get("temperature", 0.7),
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code != 200:
                self.logger.error(f"Ollama error {response.status_code}: {response.text}")
                return "Sorry, I encountered an error processing your request."
            
            # Extract response
            result = response.json()
            ai_response = result.get("message", {}).get("content", "").strip()
            
            if not ai_response:
                self.logger.warning("Empty response from Ollama")
                return "I didn't understand that. Could you repeat?"
            
            # Add AI response to memory
            self.memory.add_message("assistant", ai_response)
            
            self.logger.debug(f"Ollama response: {ai_response[:100]}...")
            return ai_response
            
        except requests.exceptions.Timeout:
            self.logger.error("Ollama request timed out")
            return "I'm thinking too slow. Please try again."
        except requests.exceptions.ConnectionError:
            self.logger.error("Lost connection to Ollama")
            return "I lost connection to my brain. Please check if Ollama is running."
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON response from Ollama")
            return "I had trouble understanding my response. Please try again."
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return f"An error occurred: {str(e)}"

    def _build_prompt(self, user_input: str, context: str) -> str:
        """
        Build a prompt for the LLM with context and instructions
        
        Args:
            user_input: Current user input
            context: Previous conversation context
            
        Returns:
            Formatted prompt string
        """
        system_prompt = """You are LEVI, a helpful virtual voice assistant. 
Be concise, friendly, and natural in your responses. 
Keep responses brief (1-3 sentences) for TTS readability.
Avoid lengthy explanations unless specifically asked."""
        
        if context:
            return f"{system_prompt}\n\nConversation history:\n{context}\n\nUSER: {user_input}\n\nAssistant:"
        else:
            return f"{system_prompt}\n\nUSER: {user_input}\n\nAssistant:"

    def clear_memory(self):
        """Clear conversation history"""
        self.memory.clear()
        self.logger.info("Conversation memory cleared")


# Global Ollama client instance (singleton pattern)
_ollama_client = None


def get_ollama_client():
    """Get or create global Ollama client"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
