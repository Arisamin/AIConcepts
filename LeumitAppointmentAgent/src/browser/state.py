"""
Browser state manager - tracks browser lifecycle and stage.
Allows detection of new vs recovery runs.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).parent / ".leumit_state.json"

# Stages of execution
STAGE_NEW = "new"              # Fresh browser, ready for login
STAGE_LOGIN_READY = "login_ready"   # Browser open at login page
STAGE_FORM_FILLED = "form_filled"   # Form has been filled with credentials
STAGE_OTP_READY = "otp_ready"       # Waiting for OTP entry
STAGE_LOGGED_IN = "logged_in"       # Successfully logged in


class BrowserState:
    """Manage browser state across script runs."""
    
    @staticmethod
    def load() -> Optional[Dict[str, Any]]:
        """Load existing state."""
        if not STATE_FILE.exists():
            return None
        
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load state file: {e}")
            return None
    
    @staticmethod
    def save(state: Dict[str, Any]) -> None:
        """Save state to file."""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug(f"State saved: {state['stage']}")
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    @staticmethod
    def create_new() -> Dict[str, Any]:
        """Create new browser state."""
        return {
            'stage': STAGE_NEW,
            'port': 9222,
            'endpoint': 'ws://127.0.0.1:9222',
            'browser_pid': None,
            'created_at': str(Path(STATE_FILE).stat().st_mtime if STATE_FILE.exists() else 0)
        }
    
    @staticmethod
    def update_stage(stage: str) -> None:
        """Update current stage."""
        state = BrowserState.load() or BrowserState.create_new()
        state['stage'] = stage
        BrowserState.save(state)
        logger.info(f"Stage updated: {stage}")
    
    @staticmethod
    def clear() -> None:
        """Clear state (on graceful exit)."""
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            logger.info("State cleared")
    
    @staticmethod
    def exists() -> bool:
        """Check if state exists."""
        return STATE_FILE.exists()
