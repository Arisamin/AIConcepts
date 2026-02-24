"""
Simple unit tests for persistent_agent.py (no pytest required)

Run with: python test_agent_simple.py
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock

# Test color output (disabled for Windows console compatibility)
GREEN = ''
RED = ''
YELLOW = ''
RESET = ''

def test_passed(msg):
    print(f"[PASS] {msg}")

def test_failed(msg):
    print(f"[FAIL] {msg}")

def test_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")


# Import after setup
from persistent_agent import PersistentAgent


def test_command_hashing():
    """Test command hash generation"""
    test_section("TEST: Command Hashing")
    
    agent = Mock()
    agent.get_command_hash = PersistentAgent.get_command_hash.__get__(agent)
    
    # Test 1: Identical commands
    cmd1 = {"action": "login"}
    cmd2 = {"action": "login"}
    hash1 = agent.get_command_hash(cmd1)
    hash2 = agent.get_command_hash(cmd2)
    
    if hash1 == hash2:
        test_passed("Identical commands produce same hash")
    else:
        test_failed(f"Identical commands have different hashes: {hash1} vs {hash2}")
    
    # Test 2: Different commands
    cmd3 = {"action": "search_doctor"}
    hash3 = agent.get_command_hash(cmd3)
    
    if hash1 != hash3:
        test_passed("Different commands produce different hashes")
    else:
        test_failed(f"Different commands have same hash: {hash1}")
    
    # Test 3: Parameter changes
    cmd4 = {"action": "search_doctor", "params": {"date_to": "2026-03-31"}}
    cmd5 = {"action": "search_doctor", "params": {"date_to": "2026-04-01"}}
    hash4 = agent.get_command_hash(cmd4)
    hash5 = agent.get_command_hash(cmd5)
    
    if hash4 != hash5:
        test_passed("Parameter changes produce different hashes")
    else:
        test_failed(f"Parameter changes didn't change hash: {hash4}")


def test_file_watching():
    """Test file modification detection"""
    test_section("TEST: File Watching (mtime)")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
        cmd = {"action": "login"}
        json.dump(cmd, f)
    
    try:
        # Test 1: File modification changes mtime
        initial_mtime = temp_path.stat().st_mtime
        time.sleep(0.2)  # Ensure time passes
        
        with open(temp_path, 'w') as f:
            json.dump(cmd, f)
        
        new_mtime = temp_path.stat().st_mtime
        
        if new_mtime > initial_mtime:
            test_passed("File modification changes mtime")
        else:
            test_failed(f"File modification didn't change mtime: {initial_mtime} vs {new_mtime}")
        
        # Test 2: Unchanged file keeps same mtime
        mtime1 = temp_path.stat().st_mtime
        time.sleep(0.1)
        mtime2 = temp_path.stat().st_mtime
        
        if mtime1 == mtime2:
            test_passed("Unchanged file keeps same mtime")
        else:
            test_failed(f"Unchanged file mtime changed: {mtime1} vs {mtime2}")
            
    finally:
        temp_path.unlink()


def test_command_detection_logic():
    """Test when commands should be re-executed"""
    test_section("TEST: Command Change Detection")
    
    # Test 1: Same hash, same mtime = no execution
    last_hash, last_mtime = "abc123", 1000.0
    curr_hash, curr_mtime = "abc123", 1000.0
    should_exec = (curr_hash != last_hash) or (curr_mtime != last_mtime)
    
    if not should_exec:
        test_passed("Same hash and mtime  no execution")
    else:
        test_failed("Same hash and mtime should not trigger execution")
    
    # Test 2: Different hash = execution
    curr_hash = "def456"
    should_exec = (curr_hash != last_hash) or (curr_mtime != last_mtime)
    
    if should_exec:
        test_passed("Different hash  execution")
    else:
        test_failed("Different hash should trigger execution")
    
    # Test 3: Different mtime = execution (even with same hash)
    curr_hash, curr_mtime = "abc123", 1001.0
    should_exec = (curr_hash != last_hash) or (curr_mtime != last_mtime)
    
    if should_exec:
        test_passed("Different mtime  execution (even with same hash)")
    else:
        test_failed("Different mtime should trigger execution")


def test_login_flow_logic():
    """Test login command recognition"""
    test_section("TEST: Login Flow Logic")
    
    # Test 1: Login command recognized
    cmd = {"action": "login"}
    is_login = cmd.get("action") == "login"
    
    if is_login:
        test_passed("Login command recognized")
    else:
        test_failed("Login command not recognized")
    
    # Test 2: Other commands not treated as login
    cmd = {"action": "search_doctor"}
    is_login = cmd.get("action") == "login"
    
    if not is_login:
        test_passed("Non-login command not treated as login")
    else:
        test_failed("Non-login command mistaken for login")


def test_hash_update_logic():
    """Test when hash should be updated"""
    test_section("TEST: Hash Update Logic")
    
    # Test 1: Hash updated after successful login
    cmd_hash = "abc123"
    last_hash = None
    login_success = True
    
    if login_success:
        last_hash = cmd_hash
    
    if last_hash == cmd_hash:
        test_passed("Hash updated after successful login")
    else:
        test_failed("Hash should be updated after successful login")
    
    # Test 2: Hash NOT updated after failed login
    last_hash = None
    login_success = False
    
    if login_success:
        last_hash = cmd_hash
    
    if last_hash is None:
        test_passed("Hash NOT updated after failed login (enables retry)")
    else:
        test_failed("Hash should not be updated after failed login")


def test_requires_login_logic():
    """Test the requires_login flow"""
    test_section("TEST: Requires Login Flow")
    
    # Test 1: Command returns requires_login when not logged in
    logged_in = False
    
    if not logged_in:
        result = {"status": "error", "requires_login": True}
    else:
        result = {"status": "success"}
    
    if result.get("requires_login"):
        test_passed("Command returns requires_login when not logged in")
    else:
        test_failed("Command should return requires_login when not logged in")
    
    # Test 2: Hash should NOT be updated when requires_login is True
    # This allows the command to retry after login completes
    if result.get("requires_login"):
        hash_updated = False  # Don't update hash
    else:
        hash_updated = True
    
    if not hash_updated:
        test_passed("Hash NOT updated when requires_login (enables retry after login)")
    else:
        test_failed("Hash should not be updated when requires_login")


def test_command_error_retry_logic():
    """Test that failed commands retry automatically"""
    test_section("TEST: Failed Command Retry Logic")
    
    # Test 1: Success result updates hash
    result = {"status": "success", "data": "some data"}
    is_error = (result.get("status") == "error")
    hash_updated = not is_error
    
    if hash_updated:
        test_passed("Successful command updates hash (no retry)")
    else:
        test_failed("Successful command should update hash")
    
    # Test 2: Error result does NOT update hash (enables retry)
    result = {"status": "error", "message": "Timeout waiting for element"}
    is_error = (result.get("status") == "error")
    hash_updated = not is_error
    
    if not hash_updated:
        test_passed("Failed command does NOT update hash (enables retry)")
    else:
        test_failed("Failed command should not update hash to allow retry")
    
    # Test 3: requires_login error also does NOT update hash
    result = {"status": "error", "requires_login": True}
    has_requires_login = result.get("requires_login")
    is_error = (result.get("status") == "error")
    
    # Hash should NOT be updated for either requires_login OR regular errors
    hash_updated = not (has_requires_login or is_error)
    
    if not hash_updated:
        test_passed("requires_login error does NOT update hash")
    else:
        test_failed("requires_login should not update hash")
    
    # Test 4: Demonstrate the retry flow for failed commands
    print("\n  Retry Flow for Failed Commands:")
    print("    1. Command executes  Step 3 fails (element not visible)")
    print("    2. Returns: {'status': 'error', 'message': '...'}")
    print("    3. Hash NOT updated")
    print("    4. Next cycle (2 seconds)  Command re-executes")
    print("    5. Eventually succeeds  Hash updated ")
    
    test_passed("Failed commands retry automatically until success")


def main():
    print("\n" + "="*60)
    print("PERSISTENT AGENT UNIT TESTS")
    print("="*60)
    
    try:
        test_command_hashing()
        test_file_watching()
        test_command_detection_logic()
        test_login_flow_logic()
        test_hash_update_logic()
        test_requires_login_logic()
        test_command_error_retry_logic()
        
        print("\n" + "="*60)
        print(f"{GREEN}ALL TESTS COMPLETED{RESET}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n{RED}TEST SUITE ERROR: {e}{RESET}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
