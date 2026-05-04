"""
Iris Media Controller
Manages media playback, searching, and keyboard controls.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from utils.logger import logger

try:
	import yt_dlp
	YT_DLP_AVAILABLE = True
except ImportError:
	YT_DLP_AVAILABLE = False

try:
	import pyautogui
	PYAUTOGUI_AVAILABLE = True
except ImportError:
	PYAUTOGUI_AVAILABLE = False


@dataclass
class MediaState:
	"""Current media playback state."""
	is_playing: bool = False
	current_url: Optional[str] = None
	current_platform: str = ""  # "youtube", "spotify", etc.
	current_title: Optional[str] = None
	last_query: Optional[str] = None
	video_id: Optional[str] = None


class MediaController:
	"""
	Manages media playback control via keyboard input and URL opening.
	Stores media state and provides high-level media commands.
	"""

	def __init__(self):
		self.logger = logger
		self.state = MediaState()
		self._ensure_safe_pyautogui()

	def _ensure_safe_pyautogui(self):
		"""Disable pyautogui's fail-safe if available (allows programmatic control)."""
		if PYAUTOGUI_AVAILABLE:
			pyautogui.FAIL_SAFE = False

	def _send_key(self, key: str, duration: float = 0.1) -> bool:
		"""
		Send a keyboard key press using pyautogui.
		
		Args:
			key: Key name (e.g., 'space', 'right', 'up')
			duration: How long to press the key
			
		Returns:
			True if successful, False if pyautogui unavailable
		"""
		if not PYAUTOGUI_AVAILABLE:
			self.logger.warning(f"pyautogui not available. Cannot send key: {key}")
			return False

		try:
			pyautogui.press(key, interval=duration)
			time.sleep(0.1)  # Small delay after key press
			return True
		except Exception as e:
			self.logger.error(f"Failed to send key '{key}': {e}")
			return False

	def play_pause(self) -> str:
		"""Toggle play/pause using spacebar."""
		if self._send_key("space"):
			self.state.is_playing = not self.state.is_playing
			status = "Playing" if self.state.is_playing else "Paused"
			return f"{status} media."
		return "Could not toggle play/pause. Make sure media player is focused."

	def pause(self) -> str:
		"""Pause media using spacebar."""
		if self.state.is_playing:
			return self.play_pause()
		return "Media already paused."

	def resume(self) -> str:
		"""Resume media using spacebar."""
		if not self.state.is_playing:
			return self.play_pause()
		return "Media already playing."

	def next_track(self) -> str:
		"""Skip to next track using 'n' or 'right arrow'."""
		# YouTube uses 'j' for next (in some players), we'll try 'n' first then 'j'
		success = self._send_key("n")
		if not success:
			success = self._send_key("right")
		
		if success:
			return "Skipped to next track."
		return "Could not skip to next. Ensure media player is in focus."

	def previous_track(self) -> str:
		"""Go to previous track using 'p' or 'left arrow'."""
		success = self._send_key("p")
		if not success:
			success = self._send_key("left")
		
		if success:
			return "Went to previous track."
		return "Could not go to previous. Ensure media player is in focus."

	def volume_up(self, steps: int = 1) -> str:
		"""Increase volume using up arrow key."""
		for _ in range(steps):
			if not self._send_key("up", duration=0.05):
				return "Could not increase volume. Ensure player is in focus."
		return f"Volume increased by {steps} steps."

	def volume_down(self, steps: int = 1) -> str:
		"""Decrease volume using down arrow key."""
		for _ in range(steps):
			if not self._send_key("down", duration=0.05):
				return "Could not decrease volume. Ensure player is in focus."
		return f"Volume decreased by {steps} steps."

	def mute(self) -> str:
		"""Mute/unmute using 'm' key."""
		if self._send_key("m"):
			return "Toggled mute."
		return "Could not toggle mute. Ensure player is in focus."

	def fullscreen(self) -> str:
		"""Toggle fullscreen using 'f' key."""
		if self._send_key("f"):
			return "Toggled fullscreen."
		return "Could not toggle fullscreen."

	def search_and_play(self, query: str) -> str:
		"""
		Search for media on YouTube and return the URL to open.
		
		Args:
			query: Search query
			
		Returns:
			URL string to open in browser, or error message
		"""
		if not query:
			return "Please provide a search query."

		self.state.last_query = query

		# Try to use yt-dlp if available
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
						video_info = result["entries"][0]
						self.state.video_id = video_info.get("id")
						self.state.current_title = video_info.get("title", "Unknown")
						self.state.current_url = f"https://www.youtube.com/watch?v={self.state.video_id}"
						self.state.current_platform = "youtube"
						self.state.is_playing = True

						self.logger.info(f"Found video: {self.state.current_title}")
						return self.state.current_url
			except Exception as e:
				self.logger.warning(f"yt-dlp search failed: {e}. Falling back to YouTube search page.")

		# Fallback to YouTube search page
		search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
		self.state.current_url = search_url
		self.state.current_platform = "youtube"
		self.state.last_query = query
		self.logger.info(f"Falling back to YouTube search for: {query}")
		return search_url

	def get_status(self) -> str:
		"""Get current media playback status."""
		if not self.state.current_url:
			return "No media currently selected."

		status_parts = []
		if self.state.current_title:
			status_parts.append(f"Playing: {self.state.current_title}")
		if self.state.current_platform:
			status_parts.append(f"Platform: {self.state.current_platform}")
		if self.state.is_playing:
			status_parts.append("Status: Playing")
		else:
			status_parts.append("Status: Paused")

		return " | ".join(status_parts)

	def clear_state(self):
		"""Reset media state."""
		self.state = MediaState()
		self.logger.info("Media state cleared.")
