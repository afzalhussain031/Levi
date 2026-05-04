"""
Deterministic command router for LEVI.
Executes known media/system commands without using the LLM agent.
"""

import re
from typing import Optional

from core.tools import IrisActionToolkit


class DeterministicCommandRouter:
	"""Maps explicit commands directly to toolkit methods."""

	def __init__(self, toolkit: IrisActionToolkit):
		self.toolkit = toolkit

	def _normalize(self, text: str) -> str:
		return re.sub(r"\s+", " ", text.strip().lower())

	def route(self, user_input: str) -> Optional[str]:
		"""
		Return direct command output when a deterministic command matches.
		Return None when input should be handled by the agent/LLM.
		"""
		text = self._normalize(user_input)
		if not text:
			return "I didn't catch that."

		if text in {"silence", "mute"}:
			return self.toolkit.mute_media()

		if text == "pause":
			return self.toolkit.pause_media()

		if text in {"resume", "play"}:
			return self.toolkit.play_media()

		if text in {"next", "skip", "next track", "next song", "next video"}:
			return self.toolkit.next_track()

		if text in {"previous", "back", "previous track", "previous song", "previous video"}:
			return self.toolkit.previous_track()

		if text in {"fullscreen", "full screen", "expand"}:
			return self.toolkit.fullscreen_media()

		volume_match = re.fullmatch(r"volume\s+(up|down)(?:\s+(\d+))?", text)
		if volume_match:
			direction = volume_match.group(1)
			steps = volume_match.group(2) or "1"
			if direction == "up":
				return self.toolkit.volume_up(steps)
			return self.toolkit.volume_down(steps)

		# No deterministic match: allow flexible/complex command handling.
		return None
