"""
LEVI Vision Module
Handles screenshot capture and LLaVA-based image analysis via Ollama.
"""

import base64
import io
import os
import tempfile
from typing import Optional

try:
    from PIL import Image, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

import requests
from utils.config import LLM_CONFIG, VISION_CONFIG
from utils.logger import logger


class VisionProcessor:
    """Handles screenshot capture and LLaVA analysis."""

    def __init__(self):
        self.logger = logger
        self.ollama_base_url = LLM_CONFIG.get("base_url", "http://localhost:11434").rstrip("/")
        self.llava_model = VISION_CONFIG.get("llava_model", "llava")
        self.max_image_size = VISION_CONFIG.get("max_image_size", 1024)
        self.image_quality = VISION_CONFIG.get("image_quality", 85)
        self.request_timeout = VISION_CONFIG.get("request_timeout", 30)

    def capture_screenshot(self) -> Optional[Image.Image]:
        """
        Capture a screenshot of the entire screen.
        Returns PIL Image or None if capture fails.
        """
        if not PIL_AVAILABLE:
            self.logger.error("PIL/Pillow not available for screenshot capture")
            return None

        try:
            # Use PIL's ImageGrab for cross-platform screenshot
            screenshot = ImageGrab.grab()
            self.logger.info("Screenshot captured successfully")
            return screenshot
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot with PIL: {e}")

            # Fallback to pyautogui if available
            if PYAUTOGUI_AVAILABLE:
                try:
                    screenshot = pyautogui.screenshot()
                    self.logger.info("Screenshot captured with pyautogui fallback")
                    return screenshot
                except Exception as e2:
                    self.logger.error(f"Failed to capture screenshot with pyautogui: {e2}")

            return None

    def _resize_image(self, image: Image.Image, max_size: int = 1024) -> Image.Image:
        """
        Resize image to fit within max_size while maintaining aspect ratio.
        This optimizes for LLaVA processing performance.
        """
        # Use config value if no max_size provided
        if max_size == 1024:
            max_size = self.max_image_size
        width, height = image.size

        # Calculate scaling factor
        if width > height:
            if width > max_size:
                scale = max_size / width
                new_width = max_size
                new_height = int(height * scale)
            else:
                return image
        else:
            if height > max_size:
                scale = max_size / height
                new_height = max_size
                new_width = int(width * scale)
            else:
                return image

        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.logger.info(f"Image resized from {width}x{height} to {new_width}x{new_height}")
        return resized

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        # Save as JPEG for smaller size
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=self.image_quality)
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')

    def analyze_image_with_llava(self, image: Image.Image, prompt: str) -> str:
        """
        Send image to Ollama LLaVA model for analysis.

        Args:
            image: PIL Image to analyze
            prompt: Text prompt describing what to analyze

        Returns:
            Structured text response from LLaVA
        """
        # Resize image for performance
        resized_image = self._resize_image(image)

        # Convert to base64
        image_b64 = self._image_to_base64(resized_image)

        # Prepare Ollama API request
        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.llava_model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False
        }

        try:
            self.logger.info(f"Sending image to LLaVA model '{self.llava_model}' for analysis")
            response = requests.post(url, json=payload, timeout=self.request_timeout)

            if response.status_code == 200:
                result = response.json()
                analysis = result.get("response", "").strip()
                self.logger.info("LLaVA analysis completed successfully")
                return analysis
            else:
                error_msg = f"LLaVA API error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return f"Failed to analyze image: {error_msg}"

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to connect to Ollama LLaVA: {e}"
            self.logger.error(error_msg)
            return f"Failed to analyze image: {error_msg}"

    def analyze_screen(self, prompt: str = "Describe what you see on this screen in detail.") -> str:
        """
        Capture screenshot and analyze with LLaVA.

        Args:
            prompt: What to ask LLaVA about the screen

        Returns:
            Analysis result or error message
        """
        # Capture screenshot
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return "Failed to capture screenshot. Make sure PIL/Pillow is installed."

        # Analyze with LLaVA
        analysis = self.analyze_image_with_llava(screenshot, prompt)

        # Clean up - don't store images permanently
        # PIL images are in memory, so no cleanup needed

        return analysis

    def read_screen_text(self) -> str:
        """
        Specialized function to extract readable text from screen.

        Returns:
            Extracted text or error message
        """
        prompt = (
            "Extract and return all readable text you can see on this screen. "
            "Focus on text content like window titles, menu items, buttons, "
            "documents, messages, or any other text elements. "
            "Return only the text content, organized by sections if applicable."
        )

        return self.analyze_screen(prompt)


# Global vision processor instance
_vision_processor: Optional[VisionProcessor] = None


def get_vision_processor() -> VisionProcessor:
    """Get or create the singleton vision processor."""
    global _vision_processor
    if _vision_processor is None:
        _vision_processor = VisionProcessor()
    return _vision_processor