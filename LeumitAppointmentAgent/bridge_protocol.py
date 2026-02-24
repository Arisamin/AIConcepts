"""
Communication protocol between bridge and workflow processes.
"""
import json
from enum import Enum
from typing import Any, Dict, Optional


class CommandType(str, Enum):
    """Available command types."""
    PING = "ping"
    NAVIGATE = "navigate"
    FILL = "fill"
    CLICK = "click"
    CLICK_TEXT = "click_text"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    GET_URL = "get_url"
    QUERY_SELECTOR = "query_selector"
    GET_FRAMES = "get_frames"
    GET_INPUTS = "get_inputs"
    SHUTDOWN = "shutdown"


class Command:
    """Command sent from workflow to bridge."""
    
    def __init__(self, action: CommandType, **kwargs):
        self.action = action
        self.params = kwargs
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({
            "action": self.action,
            "params": self.params
        })
    
    @staticmethod
    def from_json(data: str) -> 'Command':
        """Deserialize from JSON."""
        obj = json.loads(data)
        return Command(obj["action"], **obj["params"])


class Response:
    """Response sent from bridge to workflow."""
    
    def __init__(self, status: str, data: Any = None, error: Optional[str] = None):
        self.status = status  # "success" or "error"
        self.data = data
        self.error = error
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({
            "status": self.status,
            "data": self.data,
            "error": self.error
        })
    
    @staticmethod
    def from_json(data: str) -> 'Response':
        """Deserialize from JSON."""
        obj = json.loads(data)
        return Response(obj["status"], obj.get("data"), obj.get("error"))
    
    @staticmethod
    def success(data: Any = None) -> 'Response':
        """Create success response."""
        return Response("success", data=data)
    
    @staticmethod
    def error(message: str) -> 'Response':
        """Create error response."""
        return Response("error", error=message)


# Protocol constants
BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 5555
MESSAGE_DELIMITER = b"\n"  # Messages end with newline
