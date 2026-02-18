"""AI vision agent for analyzing page screenshots."""

import logging
from pathlib import Path
from typing import Optional
import base64

from config.credentials import Credentials

logger = logging.getLogger(__name__)


class VisionAgent:
    """Uses AI vision to understand and interact with web pages."""
    
    def __init__(self):
        """Initialize vision agent."""
        self.api_key = Credentials.get_openai_api_key()
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("Vision agent initialized with OpenAI")
            except ImportError:
                logger.warning("OpenAI package not installed. Vision features disabled.")
        else:
            logger.warning("OpenAI API key not found. Vision features disabled.")
    
    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    async def analyze_page(self, screenshot_path: Path, prompt: str) -> Optional[str]:
        """Analyze a page screenshot using AI vision.
        
        Args:
            screenshot_path: Path to screenshot file
            prompt: Question or instruction for the AI
            
        Returns:
            AI's response or None if vision not available
        """
        if not self.client:
            logger.warning("Vision agent not available")
            return None
        
        try:
            # Encode image
            base64_image = self._encode_image(screenshot_path)
            
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            logger.info(f"Vision analysis complete: {result[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error in vision analysis: {e}")
            return None
    
    async def find_element_description(self, screenshot_path: Path, element_description: str) -> Optional[dict]:
        """Find an element on the page by description.
        
        Args:
            screenshot_path: Path to screenshot file
            element_description: Description of element to find (e.g., "login button")
            
        Returns:
            Dictionary with element information or None
        """
        prompt = f"""
        Look at this webpage screenshot and find the {element_description}.
        Provide:
        1. Whether the element exists (yes/no)
        2. Its approximate position (top/middle/bottom, left/center/right)
        3. Any visible text on or near it
        4. Suggested CSS selector or text to locate it
        
        Format your response as JSON.
        """
        
        response = await self.analyze_page(screenshot_path, prompt)
        
        if response:
            # Parse response (you might want to use proper JSON parsing)
            return {"analysis": response}
        
        return None
    
    async def extract_appointments(self, screenshot_path: Path) -> Optional[list]:
        """Extract appointment information from a screenshot.
        
        Args:
            screenshot_path: Path to screenshot file
            
        Returns:
            List of appointments or None
        """
        prompt = """
        Analyze this webpage screenshot and extract all visible appointment slots.
        For each appointment, identify:
        1. Date
        2. Time
        3. Doctor name (if visible)
        4. Any other relevant information
        
        Format your response as a JSON array of appointments.
        """
        
        response = await self.analyze_page(screenshot_path, prompt)
        
        if response:
            logger.info(f"Extracted appointments using vision: {response}")
            # TODO: Parse JSON response into appointment list
            return []
        
        return None
