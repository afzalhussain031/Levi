"""
Iris Action Layer
Registry of executable tools for agentic behavior
"""

import os
import subprocess
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict

from utils.logger import logger
from core.media import MediaController

try:
	import yt_dlp
	YT_DLP_AVAILABLE = True
except ImportError:
	YT_DLP_AVAILABLE = False


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
			"play_media": self.play_media,
			"pause_media": self.pause_media,
			"resume_media": self.resume_media,
			"play_pause_media": self.play_pause_media,
			"next_track": self.next_track,
			"previous_track": self.previous_track,
			"volume_up": self.volume_up,
			"volume_down": self.volume_down,
			"mute_media": self.mute_media,
			"fullscreen_media": self.fullscreen_media,
			"media_status": self.media_status,
		}
		self.media_controller = MediaController()
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
		"""Open YouTube, optionally with a search query. If query provided, plays first matching video."""
		if not query:
			url = "https://www.youtube.com"
			return self.open_chrome(url=url)
		
		# If yt-dlp is available, search for the video and open the direct video URL
		if YT_DLP_AVAILABLE:
			try:
				ydl_opts = {
					"quiet": True,
					"no_warnings": True,
					"default_search": "ytsearch",
					"noplaylist": True,
				}
				with yt_dlp.YoutubeDL(ydl_opts) as ydl:
					result = ydl.extract_info(query, download=False)
					if result and "entries" in result and len(result["entries"]) > 0:
						video_id = result["entries"][0]["id"]
						url = f"https://www.youtube.com/watch?v={video_id}"
						self.logger.info(f"Found video: {result['entries'][0].get('title', 'Unknown')} - Opening for playback")
						return self.open_chrome(url=url)
			except Exception as e:
				self.logger.warning(f"yt-dlp search failed: {e}. Falling back to search results.")
		
		# Fallback: open YouTube search results
		url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
		return self.open_chrome(url=url)

	def play_media(self, query: str) -> ToolResult:
		"""Play media from a search query using MediaController."""
		if not query:
			return ToolResult(False, "Please provide a search query.", "play_media")

		url = self.media_controller.search_and_play(query)
		self.open_chrome(url=url)
		return ToolResult(
			True,
			f"Playing {query}",
			"play_media",
			{"query": query, "url": url, "platform": self.media_controller.state.current_platform}
		)

	def pause_media(self) -> ToolResult:
		"""Pause current media playback."""
		message = self.media_controller.pause()
		success = "Could not" not in message
		return ToolResult(success, message, "pause_media")

	def resume_media(self) -> ToolResult:
		"""Resume current media playback."""
		message = self.media_controller.resume()
		success = "Could not" not in message
		return ToolResult(success, message, "resume_media")

	def play_pause_media(self) -> ToolResult:
		"""Toggle play/pause for current media."""
		message = self.media_controller.play_pause()
		success = "Could not" not in message
		return ToolResult(success, message, "play_pause_media")

	def next_track(self) -> ToolResult:
		"""Skip to next track."""
		message = self.media_controller.next_track()
		success = "Could not" not in message
		return ToolResult(success, message, "next_track")

	def previous_track(self) -> ToolResult:
		"""Go to previous track."""
		message = self.media_controller.previous_track()
		success = "Could not" not in message
		return ToolResult(success, message, "previous_track")

	def volume_up(self, steps: int = 1) -> ToolResult:
		"""Increase volume."""
		message = self.media_controller.volume_up(steps)
		success = "Could not" not in message
		return ToolResult(success, message, "volume_up", {"steps": steps})

	def volume_down(self, steps: int = 1) -> ToolResult:
		"""Decrease volume."""
		message = self.media_controller.volume_down(steps)
		success = "Could not" not in message
		return ToolResult(success, message, "volume_down", {"steps": steps})

	def mute_media(self) -> ToolResult:
		"""Mute or unmute media."""
		message = self.media_controller.mute()
		success = "Could not" not in message
		return ToolResult(success, message, "mute_media")

	def fullscreen_media(self) -> ToolResult:
		"""Toggle fullscreen for media player."""
		message = self.media_controller.fullscreen()
		success = "Could not" not in message
		return ToolResult(success, message, "fullscreen_media")

	def media_status(self) -> ToolResult:
		"""Get current media status."""
		message = self.media_controller.get_status()
		return ToolResult(True, message, "media_status")

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