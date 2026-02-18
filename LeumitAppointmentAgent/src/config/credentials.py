"""Secure credential management."""

import os
from dotenv import load_dotenv

load_dotenv()


class Credentials:
    """Manages secure access to credentials."""
    
    @staticmethod
    def get_leumit_id() -> str:
        """Get Leumit ID (Teudat Zehut) from environment."""
        user_id = os.getenv("LEUMIT_ID") or os.getenv("LEUMIT_USERNAME")
        if not user_id:
            raise ValueError("LEUMIT_ID not found in environment variables")
        return user_id
    
    @staticmethod
    def get_leumit_mobile() -> str:
        """Get Leumit mobile number from environment."""
        mobile = os.getenv("LEUMIT_MOBILE") or os.getenv("LEUMIT_PASSWORD")
        if not mobile:
            raise ValueError("LEUMIT_MOBILE not found in environment variables")
        return mobile
    
    @staticmethod
    def get_openai_api_key() -> str | None:
        """Get OpenAI API key from environment (optional)."""
        return os.getenv("OPENAI_API_KEY")
    
    @staticmethod
    def validate_credentials() -> bool:
        """Validate that required credentials are present."""
        try:
            Credentials.get_leumit_id()
            Credentials.get_leumit_mobile()
            return True
        except ValueError:
            return False
