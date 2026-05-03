"""
LEVI Vision Tools
LangChain-compatible tools for screen analysis and text extraction.
"""

from typing import Callable, List

from core.vision import get_vision_processor
from utils.logger import logger


class VisionTools:
    """Vision-related tools for LEVI."""

    def __init__(self):
        self.logger = logger
        self.vision = get_vision_processor()

    def analyze_screen(self, tool_input: str = "") -> str:
        """
        Capture and analyze the current screen content using LLaVA vision model.

        Use this tool when:
        - User asks "What's on my screen?" or "What do you see?"
        - User wants to know about current screen content
        - User asks to describe what's visible
        - User mentions screen, display, or visual content

        Args:
            tool_input: Optional specific prompt for analysis (defaults to general description)

        Returns:
            Detailed analysis of screen content
        """
        prompt = tool_input.strip() or "Describe what you see on this screen in detail, including any windows, applications, text, or visual elements."

        self.logger.info("Analyzing screen content")
        result = self.vision.analyze_screen(prompt)

        if result.startswith("Failed"):
            return result

        return f"Screen analysis: {result}"

    def read_screen_text(self, tool_input: str = "") -> str:
        """
        Extract readable text from the current screen using LLaVA vision model.

        Use this tool when:
        - User asks "What text is on my screen?" or "Read the screen"
        - User wants to extract text content from display
        - User asks about visible text, messages, or documents

        Args:
            tool_input: Optional specific instructions for text extraction

        Returns:
            Extracted text content from screen
        """
        self.logger.info("Extracting text from screen")
        result = self.vision.read_screen_text()

        if result.startswith("Failed"):
            return result

        return f"Screen text: {result}"


_vision_tools: VisionTools | None = None


def get_vision_tools_instance() -> VisionTools:
    """Get or create the singleton vision tools instance."""
    global _vision_tools
    if _vision_tools is None:
        _vision_tools = VisionTools()
    return _vision_tools


def get_vision_langchain_tools() -> List[Callable[..., str]]:
    """Get LangChain-compatible vision tools."""
    tools_instance = get_vision_tools_instance()
    return [
        tools_instance.analyze_screen,
        tools_instance.read_screen_text,
    ]