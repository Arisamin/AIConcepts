"""
Test to verify that logging is correctly written to the file system.
"""
import logging
import sys
import time
from pathlib import Path
from datetime import datetime

# Setup logging exactly like persistent_agent.py
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "persistent_agent.log"


def test_log_directory_exists():
    """Verify log directory exists."""
    assert LOGS_DIR.exists(), f"Logs directory should exist at {LOGS_DIR}"
    assert LOGS_DIR.is_dir(), f"Logs path should be a directory"
    print(f"✓ Logs directory exists: {LOGS_DIR}")


def test_log_file_can_be_created():
    """Verify log file can be created and written."""
    # Create a logger with file output
    test_logger = logging.getLogger("test_logging")
    test_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    test_logger.handlers.clear()
    
    # Create file handler
    handler = logging.FileHandler(LOG_FILE, mode='a', encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    test_logger.addHandler(handler)
    
    # Write a test message
    test_msg = f"TEST_MESSAGE_{int(time.time())}"
    test_logger.info(test_msg)
    
    # Ensure written to disk
    handler.flush()
    time.sleep(0.2)
    
    # Read back and verify
    assert LOG_FILE.exists(), f"Log file should exist at {LOG_FILE}"
    content = LOG_FILE.read_text(encoding="utf-8")
    assert len(content) > 0, "Log file should not be empty"
    assert test_msg in content, f"Test message '{test_msg}' not found in log file"
    
    handler.close()
    test_logger.removeHandler(handler)
    
    print(f"✓ Log file created at: {LOG_FILE}")
    print(f"✓ Log file writable and persists to disk")
    print(f"✓ Log file size: {len(content)} bytes")


def test_hebrew_characters():
    """Verify Hebrew characters are logged correctly."""
    test_logger = logging.getLogger("test_hebrew")
    test_logger.setLevel(logging.INFO)
    test_logger.handlers.clear()
    
    handler = logging.FileHandler(LOG_FILE, mode='a', encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    test_logger.addHandler(handler)
    
    hebrew_msg = "Hebrew test: ג'ודית הלפר - פסיכיאטריה"
    test_logger.info(hebrew_msg)
    
    handler.flush()
    time.sleep(0.2)
    
    content = LOG_FILE.read_text(encoding="utf-8")
    assert hebrew_msg in content, f"Hebrew message not found in log file"
    
    handler.close()
    test_logger.removeHandler(handler)
    
    print(f"✓ Hebrew characters logged and persisted correctly")


if __name__ == "__main__":
    print("=" * 70)
    print("LOGGING FILE PERSISTENCE TEST")
    print("=" * 70)
    print()
    
    try:
        test_log_directory_exists()
        print()
        test_log_file_can_be_created()
        print()
        test_hebrew_characters()
        
        print()
        print("=" * 70)
        print("✅ ALL LOGGING TESTS PASSED")
        print("=" * 70)
        print()
        print(f"Log file location: {LOG_FILE}")
        print(f"Status: Logs are persisting to disk for examination")
        print()
        
        # Show last few lines of log
        if LOG_FILE.exists():
            content = LOG_FILE.read_text(encoding="utf-8")
            lines = content.strip().split('\n')
            print(f"Last 3 log entries:")
            for line in lines[-3:]:
                print(f"  {line}")
        
    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 70)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ ERROR: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)
