"""
LEVI LangChain Tools
Wraps existing browser/system actions as LangChain-compatible tools.
"""

import os
import subprocess
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List

from core.media import MediaController
from utils.logger import logger

try:
	import yt_dlp
	YT_DLP_AVAILABLE = True
except ImportError:
	YT_DLP_AVAILABLE = False


@dataclass
class ToolState:
	"""Runtime state for action tools."""
	pending_shutdown: bool = False
	last_action: str = ""
	metadata: Dict[str, Any] = field(default_factory=dict)


class LeviActionToolkit:
	"""Actual executable actions used by LangChain tools."""

	def __init__(self):
		self.logger = logger
		self.state = ToolState()
		self.media_controller = MediaController()

	def open_chrome(self, tool_input: str = "") -> str:
		"""Open Chrome or the default browser. Accepts an optional URL."""
		url = tool_input.strip() or "https://www.google.com"
		if not url.startswith(("http://", "https://")):
			url = f"https://www.google.com/search?q={url.replace(' ', '+')}"

		chrome_paths = [
			Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
			Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
			Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
		]

		for chrome_path in chrome_paths:
			if chrome_path and chrome_path.exists():
				subprocess.Popen([str(chrome_path), "--new-window", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				self.state.last_action = "open_chrome"
				self.state.metadata = {"url": url, "browser": "chrome"}
				return f"Opened Chrome for {url}"

		try:
			webbrowser.open(url, new=2)
			self.state.last_action = "open_chrome"
			self.state.metadata = {"url": url, "browser": "default"}
			return f"Opened the default browser for {url}"
		except Exception as e:
			self.logger.error(f"Failed to open browser: {e}")
			return f"Failed to open browser: {e}"

	def open_youtube(self, tool_input: str = "") -> str:
		"""Open YouTube or search for a query and play first matching video."""
		query = tool_input.strip()
		
		if not query:
			url = "https://www.youtube.com"
			return self.open_chrome(url)
		
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
						video_title = result["entries"][0].get("title", "Unknown")
						self.logger.info(f"Found video: {video_title} - Opening for playback")
						self.state.metadata = {"video_title": video_title, "video_id": video_id}
						return self.open_chrome(url)
			except Exception as e:
				self.logger.warning(f"yt-dlp search failed: {e}. Falling back to search results.")
		
		# Fallback: open YouTube search results
		url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
		return self.open_chrome(url)

	def play_media(self, tool_input: str = "") -> str:
		"""Play media from a search query (uses MediaController)."""
		query = tool_input.strip()
		if not query:
			return "Please provide a search query."

		url = self.media_controller.search_and_play(query)
		self.state.last_action = "play_media"
		self.state.metadata = {
			"query": query,
			"url": url,
			"platform": self.media_controller.state.current_platform,
			"title": self.media_controller.state.current_title,
		}
		self.logger.info(f"Playing media: {query}")
		return self.open_chrome(url)

	def pause_media(self, tool_input: str = "") -> str:
		"""Pause current media playback."""
		result = self.media_controller.pause()
		self.state.last_action = "pause_media"
		return result

	def resume_media(self, tool_input: str = "") -> str:
		"""Resume current media playback."""
		result = self.media_controller.resume()
		self.state.last_action = "resume_media"
		return result

	def play_pause_media(self, tool_input: str = "") -> str:
		"""Toggle play/pause for current media."""
		result = self.media_controller.play_pause()
		self.state.last_action = "play_pause_media"
		return result

	def next_track(self, tool_input: str = "") -> str:
		"""Skip to next track."""
		result = self.media_controller.next_track()
		self.state.last_action = "next_track"
		return result

	def previous_track(self, tool_input: str = "") -> str:
		"""Go to previous track."""
		result = self.media_controller.previous_track()
		self.state.last_action = "previous_track"
		return result

	def volume_up(self, tool_input: str = "") -> str:
		"""Increase volume."""
		steps = int(tool_input.strip() or "1")
		result = self.media_controller.volume_up(steps)
		self.state.last_action = "volume_up"
		return result

	def volume_down(self, tool_input: str = "") -> str:
		"""Decrease volume."""
		steps = int(tool_input.strip() or "1")
		result = self.media_controller.volume_down(steps)
		self.state.last_action = "volume_down"
		return result

	def mute_media(self, tool_input: str = "") -> str:
		"""Mute or unmute media."""
		result = self.media_controller.mute()
		self.state.last_action = "mute_media"
		return result

	def fullscreen_media(self, tool_input: str = "") -> str:
		"""Toggle fullscreen for media player."""
		result = self.media_controller.fullscreen()
		self.state.last_action = "fullscreen_media"
		return result

	def media_status(self, tool_input: str = "") -> str:
		"""Get current media status."""
		result = self.media_controller.get_status()
		self.state.last_action = "media_status"
		return result

	def shutdown_pc(self, tool_input: str = "") -> str:
		"""Shutdown the PC with a two-step confirmation flow."""
		text = tool_input.strip().lower()

		if self.state.pending_shutdown:
			if any(word in text for word in ["confirm", "yes", "do it", "proceed", "shutdown now"]):
				self.state.pending_shutdown = False
				if os.name != "nt":
					return "Shutdown is only supported on Windows."

				try:
					subprocess.Popen(["shutdown", "/s", "/t", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
					self.state.last_action = "shutdown_pc"
					return "Shutting down the PC now."
				except Exception as e:
					self.state.pending_shutdown = False
					self.logger.error(f"Failed to shutdown PC: {e}")
					return f"Failed to shutdown PC: {e}"

			if any(word in text for word in ["cancel", "stop", "abort", "no"]):
				self.state.pending_shutdown = False
				return "Shutdown cancelled."

			return "I am waiting for confirmation to shut down the PC. Say 'confirm shutdown' or 'cancel'."

		# First shutdown request only arms the action
		self.state.pending_shutdown = True
		return "Shutdown is dangerous. Say 'confirm shutdown' to proceed or 'cancel' to stop."


_toolkit: LeviActionToolkit | None = None


def get_action_toolkit() -> LeviActionToolkit:
	"""Get or create the singleton toolkit."""
	global _toolkit
	if _toolkit is None:
		_toolkit = LeviActionToolkit()
	return _toolkit


def get_langchain_tools() -> List[Callable[..., str]]:
	"""Build LangChain tools around the LEVI action toolkit."""
	toolkit = get_action_toolkit()
	return [
		toolkit.open_chrome,
		toolkit.open_youtube,
		toolkit.shutdown_pc,
		toolkit.play_media,
		toolkit.pause_media,
		toolkit.resume_media,
		toolkit.play_pause_media,
		toolkit.next_track,
		toolkit.previous_track,
		toolkit.volume_up,
		toolkit.volume_down,
		toolkit.mute_media,
		toolkit.fullscreen_media,
		toolkit.media_status,
	]
