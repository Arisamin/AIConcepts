"""Cookie management for persistent authentication."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

COOKIES_FILE = Path(__file__).parent.parent.parent / "cookies.json"


class CookieManager:
    """Manages saving and loading cookies for persistent authentication."""
    
    @staticmethod
    def save_cookies(page) -> bool:
        """Save cookies from current page to file.
        
        Args:
            page: Playwright page object
            
        Returns:
            bool: True if saved successfully
        """
        try:
            cookies = page.context.cookies()
            
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"Saved {len(cookies)} cookies to {COOKIES_FILE}")
            return True
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            return False
    
    @staticmethod
    def load_cookies(context) -> bool:
        """Load cookies into current context.
        
        Args:
            context: Playwright context object
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            if not COOKIES_FILE.exists():
                logger.info(f"No saved cookies found at {COOKIES_FILE}")
                return False
            
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
            
            context.add_cookies(cookies)
            logger.info(f"Loaded {len(cookies)} cookies from {COOKIES_FILE}")
            return True
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False
    
    @staticmethod
    def clear_cookies() -> bool:
        """Clear saved cookies.
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            if COOKIES_FILE.exists():
                COOKIES_FILE.unlink()
                logger.info("Cleared saved cookies")
            return True
        except Exception as e:
            logger.error(f"Error clearing cookies: {e}")
            return False
