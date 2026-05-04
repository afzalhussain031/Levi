"""
Iris LangChain Tools
Wraps existing browser/system actions as LangChain-compatible tools.
"""

import os
import shutil
import subprocess
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.media import MediaController
from tools.vision_tools import get_vision_langchain_tools
from utils.config import PROJECT_ROOT
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
class ToolState:
	"""Runtime state for action tools."""
	pending_shutdown: bool = False
	pending_confirmation: Dict[str, str] = field(default_factory=dict)
	last_action: str = ""
	metadata: Dict[str, Any] = field(default_factory=dict)


class IrisActionToolkit:
	"""Actual executable actions used by LangChain tools."""

	def __init__(self):
		self.logger = logger
		self.state = ToolState()

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
		"""
		Open YouTube or search for and play a specific video/music.
		
		Use when:
		- User says: "Play [song/video]", "Search YouTube for..."
		- User wants to listen to or watch something specific
		
		Example: "Play jazz music" → Search YouTube, open first result
		Example: "Search YouTube for how to cook" → Search and open results
		"""
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

	def web_search(self, tool_input: str = "") -> str:
		"""
		Search Google for current information ONLY when user explicitly requests it.
		
		Use ONLY for:
		- User says: "search for", "look up", "find information about", "google", "check online"
		- Current information: weather, news, live data
		
		DO NOT use for:
		- General knowledge questions (I have that knowledge already)
		- Facts about people, history, places
		
		Example usage: User says "Search for Python tutorials" → Use this tool
		Example non-usage: User says "Tell me about Python" → Answer directly, DON'T use this
		"""
		query = tool_input.strip()
		
		if not query:
			url = "https://www.google.com"
		else:
			url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
		
		self.state.last_action = "web_search"
		self.state.metadata = {"query": query}
		return self.open_chrome(url)

	def _is_safe_path(self, target_path: str) -> Optional[Path]:
		"""Return sanitized safe path if under allowed folders."""
		try:
			path = Path(target_path).expanduser().resolve()
		except Exception:
			return None

		allowed_roots = [Path.home().resolve(), PROJECT_ROOT.resolve()]
		for root in allowed_roots:
			if root in path.parents or path == root:
				return path
		return None

	def open_folder(self, tool_input: str = "") -> str:
		"""Open a folder in Windows Explorer."""
		path = tool_input.strip()
		if not path:
			return "Please specify a folder path to open."

		safe_path = self._is_safe_path(path)
		if safe_path is None:
			return "Access denied: I can only open folders within your home or project directories."

		try:
			subprocess.Popen(["explorer", str(safe_path)])
			self.state.last_action = "open_folder"
			self.state.metadata = {"folder": str(safe_path)}
			return f"Opened folder: {safe_path}"
		except Exception as e:
			self.logger.error(f"Failed to open folder: {e}")
			return f"Failed to open folder: {e}"

	def _find_start_menu_shortcut(self, app_name: str) -> Optional[str]:
		"""Look for a Start Menu shortcut matching the friendly app name."""
		roots = [
			Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
			Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
		]
		lower_name = app_name.lower().replace(" ", "")

		for root in roots:
			if not root.exists():
				continue
			for shortcut in root.rglob("*.lnk"):
				name = shortcut.stem.lower().replace(" ", "")
				if lower_name == name or lower_name in name or name in lower_name:
					return str(shortcut)
		return None

	def _resolve_application(self, app_input: str) -> Optional[str]:
		"""Resolve friendly app names, install paths, or executable names."""
		app_name = app_input.strip().strip('"').lower()
		if not app_name:
			return None

		app_map = {
			"notepad": [r"C:\Windows\System32\notepad.exe"],
			"calculator": [r"C:\Windows\System32\calc.exe"],
			"calc": [r"C:\Windows\System32\calc.exe"],
			"wordpad": [r"C:\Program Files\Windows NT\Accessories\wordpad.exe"],
			"paint": [r"C:\Windows\System32\mspaint.exe"],
			"powershell": [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"],
			"cmd": [r"C:\Windows\System32\cmd.exe"],
			"chrome": [
				Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
				Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
				Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
			],
			"chrome browser": [
				Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
				Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
				Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
			],
			"firefox": [r"C:\Program Files\Mozilla Firefox\firefox.exe"],
			"edge": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
			"chatgpt": [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/ChatGPT/ChatGPT.exe"],
			"whatsapp": [Path(os.environ.get("LOCALAPPDATA", "")) / "WhatsApp/WhatsApp.exe"],
			"adobe premiere pro": [
				Path(os.environ.get("PROGRAMFILES", "")) / "Adobe/Adobe Premiere Pro 2025/Adobe Premiere Pro.exe",
				Path(os.environ.get("PROGRAMFILES", "")) / "Adobe/Adobe Premiere Pro 2024/Adobe Premiere Pro.exe",
				Path(os.environ.get("PROGRAMFILES", "")) / "Adobe/Adobe Premiere Pro 2023/Adobe Premiere Pro.exe",
			],
			"premiere pro": [
				Path(os.environ.get("PROGRAMFILES", "")) / "Adobe/Adobe Premiere Pro 2025/Adobe Premiere Pro.exe",
				Path(os.environ.get("PROGRAMFILES", "")) / "Adobe/Adobe Premiere Pro 2024/Adobe Premiere Pro.exe",
				Path(os.environ.get("PROGRAMFILES", "")) / "Adobe/Adobe Premiere Pro 2023/Adobe Premiere Pro.exe",
			],
			"premiere": [
				Path(os.environ.get("PROGRAMFILES", "")) / "Adobe/Adobe Premiere Pro 2025/Adobe Premiere Pro.exe",
				Path(os.environ.get("PROGRAMFILES", "")) / "Adobe/Adobe Premiere Pro 2024/Adobe Premiere Pro.exe",
				Path(os.environ.get("PROGRAMFILES", "")) / "Adobe/Adobe Premiere Pro 2023/Adobe Premiere Pro.exe",
			],
			"visual studio code": [
				Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Microsoft VS Code/Code.exe",
				Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft VS Code/Code.exe",
			],
			"vs code": [
				Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Microsoft VS Code/Code.exe",
				Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft VS Code/Code.exe",
			],
			"teams": [Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Teams/current/Teams.exe"],
			"slack": [Path(os.environ.get("LOCALAPPDATA", "")) / "slack" / "slack.exe"],
			"discord": [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Discord" / "Discord.exe"],
		}

		def resolve_candidate(candidate: Any) -> Optional[str]:
			if not candidate:
				return None
			candidate_path = Path(candidate)
			if candidate_path.exists():
				return str(candidate_path)
			return None

		if app_name in app_map:
			entry = app_map[app_name]
			if isinstance(entry, (list, tuple)):
				for candidate in entry:
					resolved = resolve_candidate(candidate)
					if resolved:
						return resolved
			else:
				resolved = resolve_candidate(entry)
				if resolved:
					return resolved

		candidate = Path(app_input.strip().strip('"'))
		if candidate.exists():
			return str(candidate)

		found = shutil.which(app_name)
		if found:
			return found

		shortcut = self._find_start_menu_shortcut(app_name)
		if shortcut:
			return shortcut

		return None

	def open_application(self, tool_input: str = "") -> str:
		"""Open a Windows application by friendly name or executable path."""
		app_input = tool_input.strip()
		if not app_input:
			return "Please provide the name or path to the application to open."

		resolved_path = self._resolve_application(app_input)
		if resolved_path is None:
			return f"Unknown application or path: {app_input}. Try a full path or a common app name like notepad or calculator."

		try:
			if os.name == "nt":
				os.startfile(resolved_path)
			else:
				subprocess.Popen([resolved_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			self.state.last_action = "open_application"
			self.state.metadata = {"application": resolved_path}
			return f"Opened application: {resolved_path}"
		except Exception as e:
			self.logger.error(f"Failed to open application: {e}")
			return f"Failed to open application: {e}"

	def open_file(self, tool_input: str = "") -> str:
		"""Open a file with its default application."""
		path = tool_input.strip()
		if not path:
			return "Please specify a file path to open."

		safe_path = self._is_safe_path(path)
		if safe_path is None:
			return "Access denied: I can only open files within your home or project directories."

		try:
			os.startfile(str(safe_path))
			self.state.last_action = "open_file"
			self.state.metadata = {"file": str(safe_path)}
			return f"Opened file: {safe_path}"
		except Exception as e:
			self.logger.error(f"Failed to open file: {e}")
			return f"Failed to open file: {e}"

	def list_files(self, tool_input: str = "") -> str:
		"""List files in a folder."""
		path = tool_input.strip() or str(Path.home())
		if not path:
			return "Please specify a folder path to list."

		safe_path = self._is_safe_path(path)
		if safe_path is None:
			return "Access denied: I can only list files in your home or project directories."

		if not safe_path.exists() or not safe_path.is_dir():
			return f"Path is not a valid folder: {safe_path}"

		entries = [p.name for p in safe_path.iterdir()]
		self.state.last_action = "list_files"
		self.state.metadata = {"folder": str(safe_path), "entries": len(entries)}
		return "\n".join(entries) if entries else f"No files found in {safe_path}."

	def read_file(self, tool_input: str = "") -> str:
		"""Read the contents of a text file."""
		path = tool_input.strip()
		if not path:
			return "Please specify a file path to read."

		safe_path = self._is_safe_path(path)
		if safe_path is None:
			return "Access denied: I can only read files within your home or project directories."

		if not safe_path.exists() or not safe_path.is_file():
			return f"File not found: {safe_path}"

		try:
			with safe_path.open("r", encoding="utf-8", errors="replace") as f:
				content = f.read(4096)
			self.state.last_action = "read_file"
			self.state.metadata = {"file": str(safe_path), "bytes_read": len(content)}
			return content or f"File is empty: {safe_path}"
		except Exception as e:
			self.logger.error(f"Failed to read file: {e}")
			return f"Failed to read file: {e}"

	def create_file(self, tool_input: str = "") -> str:
		"""Create or overwrite a text file with content.

		Expected format: path | content
		"""
		payload = tool_input.split("|", 1)
		if len(payload) != 2:
			return "Please use the format: file_path | content"

		path, content = payload[0].strip(), payload[1].strip()
		safe_path = self._is_safe_path(path)
		if safe_path is None:
			return "Access denied: I can only create files within your home or project directories."

		try:
			with safe_path.open("w", encoding="utf-8") as f:
				f.write(content)
			self.state.last_action = "create_file"
			self.state.metadata = {"file": str(safe_path), "content_length": len(content)}
			return f"Created file: {safe_path}"
		except Exception as e:
			self.logger.error(f"Failed to create file: {e}")
			return f"Failed to create file: {e}"

	def append_to_file(self, tool_input: str = "") -> str:
		"""Append text to an existing file.

		Expected format: file_path | content
		"""
		payload = tool_input.split("|", 1)
		if len(payload) != 2:
			return "Please use the format: file_path | content"

		path, content = payload[0].strip(), payload[1].strip()
		safe_path = self._is_safe_path(path)
		if safe_path is None:
			return "Access denied: I can only append files within your home or project directories."

		if not safe_path.exists() or not safe_path.is_file():
			return f"File not found: {safe_path}"

		try:
			with safe_path.open("a", encoding="utf-8") as f:
				f.write(content)
			self.state.last_action = "append_to_file"
			self.state.metadata = {"file": str(safe_path), "content_length": len(content)}
			return f"Appended text to {safe_path}"
		except Exception as e:
			self.logger.error(f"Failed to append file: {e}")
			return f"Failed to append file: {e}"

	def move_file(self, tool_input: str = "") -> str:
		"""Move or rename a file or folder.

		Expected format: source_path | destination_path
		"""
		payload = tool_input.split("|", 1)
		if len(payload) != 2:
			return "Please use the format: source_path | destination_path"

		source, destination = payload[0].strip(), payload[1].strip()
		safe_source = self._is_safe_path(source)
		safe_destination = self._is_safe_path(destination)
		if safe_source is None or safe_destination is None:
			return "Access denied: I can only move files/folders within your home or project directories."

		try:
			shutil.move(str(safe_source), str(safe_destination))
			self.state.last_action = "move_file"
			self.state.metadata = {"source": str(safe_source), "destination": str(safe_destination)}
			return f"Moved {safe_source} to {safe_destination}"
		except Exception as e:
			self.logger.error(f"Failed to move: {e}")
			return f"Failed to move: {e}"

	def copy_file(self, tool_input: str = "") -> str:
		"""Copy a file from source to destination.

		Expected format: source_path | destination_path
		"""
		payload = tool_input.split("|", 1)
		if len(payload) != 2:
			return "Please use the format: source_path | destination_path"

		source, destination = payload[0].strip(), payload[1].strip()
		safe_source = self._is_safe_path(source)
		safe_destination = self._is_safe_path(destination)
		if safe_source is None or safe_destination is None:
			return "Access denied: I can only copy files within your home or project directories."

		try:
			shutil.copy2(str(safe_source), str(safe_destination))
			self.state.last_action = "copy_file"
			self.state.metadata = {"source": str(safe_source), "destination": str(safe_destination)}
			return f"Copied {safe_source} to {safe_destination}"
		except Exception as e:
			self.logger.error(f"Failed to copy: {e}")
			return f"Failed to copy: {e}"

	def create_folder(self, tool_input: str = "") -> str:
		"""Create a new folder."""
		path = tool_input.strip()
		if not path:
			return "Please specify a folder path to create."

		safe_path = self._is_safe_path(path)
		if safe_path is None:
			return "Access denied: I can only create folders within your home or project directories."

		try:
			safe_path.mkdir(parents=True, exist_ok=True)
			self.state.last_action = "create_folder"
			self.state.metadata = {"folder": str(safe_path)}
			return f"Created folder: {safe_path}"
		except Exception as e:
			self.logger.error(f"Failed to create folder: {e}")
			return f"Failed to create folder: {e}"

	def delete_file(self, tool_input: str = "") -> str:
		"""Delete a file with confirmation."""
		path = tool_input.strip()
		if not path:
			return "Please specify a file path to delete."

		safe_path = self._is_safe_path(path)
		if safe_path is None:
			return "Access denied: I can only delete files within your home or project directories."

		if not safe_path.exists() or not safe_path.is_file():
			return f"File not found: {safe_path}"

		pending_path = self.state.pending_confirmation.get("delete_file")
		if pending_path is None:
			self.state.pending_confirmation["delete_file"] = str(safe_path)
			return f"Are you sure you want to delete {safe_path}? Say 'confirm delete file' to proceed or 'cancel' to abort."

		if pending_path == str(safe_path) and any(word in tool_input.lower() for word in ["confirm", "yes"]):
			try:
				safe_path.unlink()
				self.state.pending_confirmation.pop("delete_file", None)
				self.state.last_action = "delete_file"
				return f"Deleted file: {safe_path}"
			except Exception as e:
				self.logger.error(f"Failed to delete file: {e}")
				return f"Failed to delete file: {e}"

		return f"Are you sure you want to delete {safe_path}? Say 'confirm delete file' to proceed or 'cancel' to abort."

	def delete_folder(self, tool_input: str = "") -> str:
		"""Delete a folder with confirmation."""
		path = tool_input.strip()
		if not path:
			return "Please specify a folder path to delete."

		safe_path = self._is_safe_path(path)
		if safe_path is None:
			return "Access denied: I can only delete folders within your home or project directories."

		if not safe_path.exists() or not safe_path.is_dir():
			return f"Folder not found: {safe_path}"

		pending_path = self.state.pending_confirmation.get("delete_folder")
		if pending_path is None:
			self.state.pending_confirmation["delete_folder"] = str(safe_path)
			return f"Are you sure you want to delete the folder {safe_path}? Say 'confirm delete folder' to proceed or 'cancel' to abort."

		if pending_path == str(safe_path) and any(word in tool_input.lower() for word in ["confirm", "yes"]):
			try:
				shutil.rmtree(str(safe_path))
				self.state.pending_confirmation.pop("delete_folder", None)
				self.state.last_action = "delete_folder"
				return f"Deleted folder: {safe_path}"
			except Exception as e:
				self.logger.error(f"Failed to delete folder: {e}")
				return f"Failed to delete folder: {e}"

		return f"Are you sure you want to delete the folder {safe_path}? Say 'confirm delete folder' to proceed or 'cancel' to abort."
	def cancel_pending_action(self, tool_input: str = "") -> str:
		"""Cancel any pending confirmation action."""
		self.state.pending_confirmation.clear()
		return "Cancelled any pending action."

	def _press_key(self, key: str) -> str:
		"""Press a key via pyautogui if available."""
		if not PYAUTOGUI_AVAILABLE:
			return "Media controls unavailable: pyautogui is not installed."
		try:
			pyautogui.press(key)
			return "ok"
		except Exception as e:
			self.logger.error(f"Failed to press key '{key}': {e}")
			return "Failed to control media. Make sure player window is focused."

	def play_media(self, tool_input: str = "") -> str:
		"""Play media or search YouTube for a query."""
		query = tool_input.strip()
		if query:
			self.state.last_action = "play_media"
			self.state.metadata["is_playing"] = True
			return self.open_youtube(query)
		
		result = self._press_key("space")
		if result == "ok":
			self.state.last_action = "play_media"
			self.state.metadata["is_playing"] = True
			return "Resumed playback."
		return result

	def pause_media(self, tool_input: str = "") -> str:
		"""Pause currently playing media."""
		result = self._press_key("space")
		if result == "ok":
			self.state.last_action = "pause_media"
			self.state.metadata["is_playing"] = False
			return "Paused playback."
		return result

	def resume_media(self, tool_input: str = "") -> str:
		"""Resume media playback (same as play_media with no query)."""
		result = self._press_key("space")
		if result == "ok":
			self.state.last_action = "resume_media"
			self.state.metadata["is_playing"] = True
			return "Resumed playback."
		return result

	def play_pause_media(self, tool_input: str = "") -> str:
		"""Toggle play/pause."""
		result = self._press_key("space")
		if result == "ok":
			self.state.last_action = "play_pause_media"
			return "Toggled play/pause."
		return result

	def next_track(self, tool_input: str = "") -> str:
		"""Skip to next track."""
		result = self._press_key("n")
		if result == "ok":
			self.state.last_action = "next_track"
			return "Skipped to next track."
		return result

	def previous_track(self, tool_input: str = "") -> str:
		"""Go to previous track."""
		result = self._press_key("p")
		if result == "ok":
			self.state.last_action = "previous_track"
			return "Went to previous track."
		return result

	def volume_up(self, tool_input: str = "") -> str:
		"""Increase volume."""
		steps_raw = tool_input.strip() or "1"
		try:
			steps = max(1, min(10, int(steps_raw)))
		except ValueError:
			steps = 1
		
		for _ in range(steps):
			result = self._press_key("up")
			if result != "ok":
				return result
		
		self.state.last_action = "volume_up"
		return f"Volume increased by {steps}."

	def volume_down(self, tool_input: str = "") -> str:
		"""Decrease volume."""
		steps_raw = tool_input.strip() or "1"
		try:
			steps = max(1, min(10, int(steps_raw)))
		except ValueError:
			steps = 1
		
		for _ in range(steps):
			result = self._press_key("down")
			if result != "ok":
				return result
		
		self.state.last_action = "volume_down"
		return f"Volume decreased by {steps}."

	def mute_media(self, tool_input: str = "") -> str:
		"""Mute/unmute media."""
		result = self._press_key("m")
		if result == "ok":
			self.state.last_action = "mute_media"
			return "Toggled mute."
		return result

	def fullscreen_media(self, tool_input: str = "") -> str:
		"""Toggle fullscreen."""
		result = self._press_key("f")
		if result == "ok":
			self.state.last_action = "fullscreen_media"
			return "Toggled fullscreen."
		return result

	def media_status(self, tool_input: str = "") -> str:
		"""Get current media playback status."""
		status = f"Last action: {self.state.last_action}"
		if self.state.metadata:
			status += f" | Metadata: {self.state.metadata}"
		return status

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


_toolkit: IrisActionToolkit | None = None


def get_action_toolkit() -> IrisActionToolkit:
	"""Get or create the singleton toolkit."""
	global _toolkit
	if _toolkit is None:
		_toolkit = IrisActionToolkit()
	return _toolkit


def get_langchain_tools() -> List[Callable[..., str]]:
	"""Build LangChain tools around the Iris action toolkit."""
	toolkit = get_action_toolkit()
	vision_tools = get_vision_langchain_tools()
	return [
		toolkit.open_chrome,
		toolkit.open_youtube,
		toolkit.web_search,
		toolkit.open_application,
		toolkit.open_folder,
		toolkit.open_file,
		toolkit.list_files,
		toolkit.read_file,
		toolkit.create_file,
		toolkit.append_to_file,
		toolkit.move_file,
		toolkit.copy_file,
		toolkit.create_folder,
		toolkit.delete_file,
		toolkit.delete_folder,
		toolkit.cancel_pending_action,
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
		toolkit.shutdown_pc,
	] + vision_tools
