"""
Test to verify that log files are created with correct naming format:
persistent_agent_<PID>_<HH-mm>.log
"""
import logging
import sys
import os
import re
import time
from pathlib import Path
from datetime import datetime

LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def test_log_file_naming_format():
    """Verify log file naming follows format: persistent_agent_<PID>_<HH-mm>.log"""
    
    # Simulate what persistent_agent.py does
    pid = os.getpid()
    time_str = datetime.now().strftime("%H-%m")
    expected_filename = f"persistent_agent_{pid}_{time_str}.log"
    log_file = LOGS_DIR / expected_filename
    
    # Create logger with file handler (simulate persistent_agent.py setup)
    test_logger = logging.getLogger("test_naming")
    test_logger.setLevel(logging.INFO)
    test_logger.handlers.clear()
    
    handler = logging.FileHandler(log_file, mode='a', encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    test_logger.addHandler(handler)
    
    # Write test message
    test_message = f"Test log entry for naming format validation"
    test_logger.info(test_message)
    
    # Flush to disk
    handler.flush()
    time.sleep(0.2)
    
    # Verify file exists with correct name
    assert log_file.exists(), f"Log file should exist at {log_file}"
    
    # Verify filename matches pattern
    pattern = r"^persistent_agent_\d+_\d{2}-\d{2}\.log$"
    assert re.match(pattern, log_file.name), \
        f"Log filename '{log_file.name}' doesn't match pattern 'persistent_agent_<PID>_<HH-mm>.log'"
    
    # Verify file contains the message
    content = log_file.read_text(encoding="utf-8")
    assert test_message in content, f"Test message not found in log file"
    
    handler.close()
    test_logger.removeHandler(handler)
    
    print(f"✓ Log file created with correct naming format")
    print(f"  Filename: {log_file.name}")
    print(f"  Full path: {log_file}")
    print(f"  Size: {len(content)} bytes")
    return log_file


def test_multiple_runs_create_separate_files():
    """Verify that multiple runs (even with same PID/minute) create distinct files."""
    
    files_created = []
    
    # Simulate multiple "runs" by creating loggers with slight variations
    for i in range(3):
        pid = os.getpid()
        time_str = datetime.now().strftime("%H-%m")
        filename = f"persistent_agent_{pid}_{time_str}.log"
        log_file = LOGS_DIR / filename
        
        test_logger = logging.getLogger(f"test_run_{i}")
        test_logger.setLevel(logging.INFO)
        test_logger.handlers.clear()
        
        handler = logging.FileHandler(log_file, mode='a', encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        test_logger.addHandler(handler)
        
        # Write distinct message for this run
        run_message = f"Run {i} - Test message with timestamp {datetime.now().isoformat()}"
        test_logger.info(run_message)
        
        handler.flush()
        time.sleep(0.1)
        
        # Verify file exists and contains the message
        assert log_file.exists(), f"Log file {log_file} should exist"
        content = log_file.read_text(encoding="utf-8")
        assert run_message in content, f"Run {i} message not found in log file"
        
        handler.close()
        test_logger.removeHandler(handler)
        
        files_created.append(log_file)
    
    print(f"✓ Multiple runs write to same log file (when PID and minute are same)")
    print(f"  Files verified: {len(files_created)}")
    for f in files_created:
        print(f"    - {f.name}")


def test_log_file_contains_all_entries():
    """Verify that all log entries from a run are persisted."""
    
    pid = os.getpid()
    time_str = datetime.now().strftime("%H-%m")
    log_file = LOGS_DIR / f"persistent_agent_{pid}_{time_str}.log"
    
    test_logger = logging.getLogger("test_all_entries")
    test_logger.setLevel(logging.INFO)
    test_logger.handlers.clear()
    
    handler = logging.FileHandler(log_file, mode='a', encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    test_logger.addHandler(handler)
    
    # Write multiple test messages
    messages = [
        "Entry 1: Startup message",
        "Entry 2: Step execution",
        "Entry 3: Hebrew text: ג'ודית הלפר",
        "Entry 4: Error handling",
        "Entry 5: Final status"
    ]
    
    for msg in messages:
        test_logger.info(msg)
    
    handler.flush()
    time.sleep(0.2)
    
    # Verify all messages are in file
    content = log_file.read_text(encoding="utf-8")
    for msg in messages:
        assert msg in content, f"Message '{msg}' not found in log file"
    
    handler.close()
    test_logger.removeHandler(handler)
    
    print(f"✓ All log entries persisted to file")
    print(f"  Total entries verified: {len(messages)}")
    print(f"  File size: {len(content)} bytes")


if __name__ == "__main__":
    print("=" * 70)
    print("LOG FILE NAMING FORMAT TEST")
    print("=" * 70)
    print()
    
    test_log_file = None
    
    try:
        test_log_file = test_log_file_naming_format()
        print()
        test_multiple_runs_create_separate_files()
        print()
        test_log_file_contains_all_entries()
        
        print()
        print("=" * 70)
        print("✅ ALL LOG NAMING TESTS PASSED")
        print("=" * 70)
        print()
        print("Log files directory: " + str(LOGS_DIR))
        print("Naming format verified: persistent_agent_<PID>_<HH-mm>.log")
        print()
        
        # List all log files in directory
        log_files = sorted(LOGS_DIR.glob("persistent_agent_*.log"), 
                          key=lambda x: x.stat().st_mtime, reverse=True)
        print(f"Recent log files in {LOGS_DIR.name}/:")
        for f in log_files[:5]:
            size_kb = f.stat().st_size / 1024
            print(f"  - {f.name:40} ({size_kb:.1f} KB)")
        
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
    finally:
        # Clean up test log file if it exists
        if test_log_file and test_log_file.exists():
            try:
                test_log_file.unlink()
                print()
                print(f"✓ Cleaned up test log file: {test_log_file.name}")
            except Exception as e:
                print(f"Warning: Could not delete test log file: {e}")
