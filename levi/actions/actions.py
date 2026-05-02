"""
LEVI Action Layer
Registry of executable tools for agentic behavior
"""

import os
import subprocess
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict

from utils.logger import logger


@dataclass
class ToolResult:
	"""Result returned by a tool execution."""
	success: bool
	message: str
	action: str
	details: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
	"""
	Registry mapping action names to executable functions.
	Keeps the tool layer centralized and easy to extend.
	"""

	def __init__(self):
		self.logger = logger
		self.tools: Dict[str, Callable[..., ToolResult]] = {
			"open_chrome": self.open_chrome,
			"open_youtube": self.open_youtube,
			"shutdown_pc": self.shutdown_pc,
		}
		self.dangerous_actions = {"shutdown_pc"}

	def list_actions(self):
		return list(self.tools.keys())

	def is_dangerous(self, action_name: str) -> bool:
		return action_name in self.dangerous_actions

	def get_confirmation_prompt(self, action_name: str) -> str:
		if action_name == "shutdown_pc":
			return "This will shut down the PC. Do you want me to continue?"
		return f"Do you want me to execute {action_name}?"

	def execute(self, action_name: str, **kwargs) -> ToolResult:
		if action_name not in self.tools:
			raise ValueError(f"Unknown action: {action_name}")

		if self.is_dangerous(action_name) and not kwargs.pop("confirmed", False):
			raise PermissionError(f"Action '{action_name}' requires confirmation")

		return self.tools[action_name](**kwargs)

	def open_chrome(self, url: str = "https://www.google.com") -> ToolResult:
		"""Open Chrome if available, otherwise fall back to the default browser."""
		chrome_paths = [
			Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
			Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
			Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
		]

		for chrome_path in chrome_paths:
			if chrome_path and chrome_path.exists():
				subprocess.Popen([str(chrome_path), "--new-window", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				return ToolResult(True, "Opened Chrome.", "open_chrome", {"url": url, "browser": "chrome"})

		try:
			webbrowser.open(url, new=2)
			return ToolResult(True, "Opened the default browser.", "open_chrome", {"url": url, "browser": "default"})
		except Exception as e:
			self.logger.error(f"Failed to open browser: {e}")
			return ToolResult(False, f"Failed to open browser: {e}", "open_chrome")

	def open_youtube(self, query: str | None = None) -> ToolResult:
		"""Open YouTube, optionally with a search query."""
		if query:
			url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
		else:
			url = "https://www.youtube.com"
		return self.open_chrome(url=url)

	def shutdown_pc(self, confirmed: bool = False) -> ToolResult:
		"""Shutdown the computer (Windows only), confirmation required."""
		if not confirmed:
			raise PermissionError("Shutdown requires confirmation")

		if os.name != "nt":
			return ToolResult(False, "Shutdown is only supported on Windows.", "shutdown_pc")

		try:
			subprocess.Popen(["shutdown", "/s", "/t", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			return ToolResult(True, "Shutting down the PC now.", "shutdown_pc")
		except Exception as e:
			self.logger.error(f"Failed to shutdown PC: {e}")
			return ToolResult(False, f"Failed to shutdown PC: {e}", "shutdown_pc")


_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
	"""Get or create the singleton tool registry."""
	global _tool_registry
	if _tool_registry is None:
		_tool_registry = ToolRegistry()
	return _tool_registry