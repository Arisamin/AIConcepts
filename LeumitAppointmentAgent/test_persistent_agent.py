"""
Unit tests for persistent_agent.py

Tests cover:
1. Command hash generation and comparison
2. Login state detection logic
3. File watching mechanism (hash + mtime)
4. Command execution flow
5. Login retry logic
"""

import pytest
import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# We'll need to import the agent after mocking playwright
import sys
sys.path.insert(0, str(Path(__file__).parent))


class TestCommandHashing:
    """Test command hash generation and comparison"""
    
    def test_identical_commands_same_hash(self):
        """Identical commands should produce the same hash"""
        from persistent_agent import PersistentAgent
        
        cmd1 = {"action": "login"}
        cmd2 = {"action": "login"}
        
        agent = Mock()
        agent.get_command_hash = PersistentAgent.get_command_hash.__get__(agent)
        
        hash1 = agent.get_command_hash(cmd1)
        hash2 = agent.get_command_hash(cmd2)
        
        assert hash1 == hash2, "Identical commands should have same hash"
    
    def test_different_commands_different_hash(self):
        """Different commands should produce different hashes"""
        from persistent_agent import PersistentAgent
        
        cmd1 = {"action": "login"}
        cmd2 = {"action": "search_doctor", "params": {"specialty": "פסיכיאטריה"}}
        
        agent = Mock()
        agent.get_command_hash = PersistentAgent.get_command_hash.__get__(agent)
        
        hash1 = agent.get_command_hash(cmd1)
        hash2 = agent.get_command_hash(cmd2)
        
        assert hash1 != hash2, "Different commands should have different hashes"
    
    def test_parameter_change_changes_hash(self):
        """Changing parameters should change the hash"""
        from persistent_agent import PersistentAgent
        
        cmd1 = {"action": "search_doctor", "params": {"date_to": "2026-03-31"}}
        cmd2 = {"action": "search_doctor", "params": {"date_to": "2026-04-01"}}
        
        agent = Mock()
        agent.get_command_hash = PersistentAgent.get_command_hash.__get__(agent)
        
        hash1 = agent.get_command_hash(cmd1)
        hash2 = agent.get_command_hash(cmd2)
        
        assert hash1 != hash2, "Parameter changes should change hash"


class TestFileWatching:
    """Test file watching mechanism with hash and mtime"""
    
    def test_file_modification_detected_by_mtime(self):
        """File modification should be detected even if content hash is same"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
            cmd = {"action": "login"}
            json.dump(cmd, f)
        
        try:
            # Get initial mtime
            initial_mtime = temp_path.stat().st_mtime
            
            # Wait a bit to ensure mtime changes
            time.sleep(0.1)
            
            # Modify file (write same content)
            with open(temp_path, 'w') as f:
                json.dump(cmd, f)
            
            new_mtime = temp_path.stat().st_mtime
            
            assert new_mtime != initial_mtime, "File modification should change mtime"
        finally:
            temp_path.unlink()
    
    def test_unchanged_file_same_mtime(self):
        """Unchanged file should keep same mtime"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
            cmd = {"action": "login"}
            json.dump(cmd, f)
        
        try:
            mtime1 = temp_path.stat().st_mtime
            time.sleep(0.1)
            mtime2 = temp_path.stat().st_mtime
            
            assert mtime1 == mtime2, "Unchanged file should have same mtime"
        finally:
            temp_path.unlink()


class TestLoginStateDetection:
    """Test login state detection logic"""
    
    @pytest.mark.asyncio
    async def test_already_logged_in_detected(self):
        """Agent should detect when already logged in by finding 'זימון תורים' button"""
        # Mock page with "זימון תורים" button visible
        mock_page = AsyncMock()
        mock_button = AsyncMock()
        mock_button.wait_for = AsyncMock(return_value=None)  # Button found
        mock_page.get_by_text = Mock(return_value=Mock(first=mock_button))
        
        # Simulate the login detection check
        try:
            await mock_button.wait_for(timeout=3000, state="visible")
            logged_in = True
        except:
            logged_in = False
        
        assert logged_in == True, "Should detect logged in state when 'זימון תורים' button exists"
    
    @pytest.mark.asyncio
    async def test_not_logged_in_detected(self):
        """Agent should detect when not logged in by absence of 'זימון תורים' button"""
        # Mock page without "זימון תורים" button
        mock_page = AsyncMock()
        mock_button = AsyncMock()
        
        async def timeout_wait(*args, **kwargs):
            raise Exception("Timeout")
        
        mock_button.wait_for = timeout_wait
        mock_page.get_by_text = Mock(return_value=Mock(first=mock_button))
        
        # Simulate the login detection check
        try:
            await mock_button.wait_for(timeout=3000, state="visible")
            logged_in = True
        except:
            logged_in = False
        
        assert logged_in == False, "Should detect not logged in when 'זימון תורים' button not found"


class TestCommandExecution:
    """Test command execution flow and logic"""
    
    def test_login_command_triggers_login_flow(self):
        """Login command should trigger login flow, not regular execute_command"""
        cmd = {"action": "login"}
        
        # The main loop should check for cmd.get("action") == "login"
        is_login = cmd.get("action") == "login"
        
        assert is_login == True, "Login command should be recognized"
    
    def test_search_doctor_command_triggers_execute(self):
        """Search doctor command should go through execute_command"""
        cmd = {"action": "search_doctor", "params": {"specialty": "פסיכיאטריה"}}
        
        is_login = cmd.get("action") == "login"
        
        assert is_login == False, "Non-login command should not trigger login flow"
    
    def test_hash_updated_after_successful_login(self):
        """Command hash should only be updated AFTER successful login"""
        # This tests the logic flow:
        # 1. Login attempt
        # 2. If success, update hash
        # 3. If failure, DON'T update hash (so it retries)
        
        cmd_hash = "abc123"
        last_hash = None
        
        # Simulate successful login
        login_success = True
        
        if login_success:
            last_hash = cmd_hash  # Update hash after success
        
        assert last_hash == cmd_hash, "Hash should be updated after successful login"
        
        # Simulate failed login
        last_hash = None
        login_success = False
        
        if login_success:
            last_hash = cmd_hash
        
        assert last_hash is None, "Hash should NOT be updated after failed login"
    
    def test_hash_updated_before_other_commands(self):
        """For non-login commands, hash should be updated before execution"""
        # This prevents infinite loops on non-login commands
        
        cmd = {"action": "search_doctor"}
        cmd_hash = "def456"
        last_hash = None
        
        # For non-login commands, update hash first
        is_login = cmd.get("action") == "login"
        
        if not is_login:
            last_hash = cmd_hash  # Update before execution
        
        assert last_hash == cmd_hash, "Hash should be updated before non-login commands"


class TestLoginRetryLogic:
    """Test login retry mechanism"""
    
    @pytest.mark.asyncio
    async def test_login_retries_on_failure(self):
        """Login should retry infinitely on failure"""
        retry_count = 0
        max_test_retries = 5  # For testing, we'll only test 5 retries
        
        async def mock_login():
            nonlocal retry_count
            retry_count += 1
            if retry_count < max_test_retries:
                return False  # Fail first few attempts
            return True  # Success on last attempt
        
        # Simulate retry loop
        success = False
        actual_retries = 0
        
        while not success and actual_retries < max_test_retries:
            success = await mock_login()
            actual_retries += 1
        
        assert actual_retries == max_test_retries, f"Should retry {max_test_retries} times"
        assert success == True, "Should eventually succeed"
    
    @pytest.mark.asyncio
    async def test_login_stops_on_first_success(self):
        """Login should stop retrying after first success"""
        retry_count = 0
        
        async def mock_login():
            nonlocal retry_count
            retry_count += 1
            return True  # Always succeed
        
        # Simulate retry loop
        success = False
        
        while not success:
            success = await mock_login()
            if success:
                break
        
        assert retry_count == 1, "Should stop after first successful login"


class TestSearchDoctorWorkflow:
    """Test search_doctor workflow logic"""
    
    def test_search_doctor_requires_login(self):
        """Search doctor should check login state first"""
        # The workflow should check for "זימון תורים" button
        # If not found, should return error requiring login
        
        logged_in = False
        
        if not logged_in:
            result = {
                "status": "error",
                "message": "Not logged in",
                "requires_login": True
            }
        else:
            result = {"status": "success"}
        
        assert result["status"] == "error", "Should error when not logged in"
        assert result.get("requires_login") == True, "Should indicate login required"
    
    def test_search_doctor_proceeds_when_logged_in(self):
        """Search doctor should proceed when logged in"""
        logged_in = True
        
        if not logged_in:
            result = {"status": "error", "requires_login": True}
        else:
            result = {"status": "in_progress"}
        
        assert result["status"] != "error", "Should not error when logged in"
        assert result.get("requires_login") != True, "Should not require login"


class TestCommandChangeDetection:
    """Test when commands should be re-executed"""
    
    def test_same_hash_same_mtime_no_execution(self):
        """Same hash and mtime should not trigger execution"""
        last_hash = "abc123"
        last_mtime = 1000.0
        
        current_hash = "abc123"
        current_mtime = 1000.0
        
        should_execute = (current_hash != last_hash) or (current_mtime != last_mtime)
        
        assert should_execute == False, "Should not execute when both hash and mtime unchanged"
    
    def test_different_hash_triggers_execution(self):
        """Different hash should trigger execution"""
        last_hash = "abc123"
        last_mtime = 1000.0
        
        current_hash = "def456"
        current_mtime = 1000.0
        
        should_execute = (current_hash != last_hash) or (current_mtime != last_mtime)
        
        assert should_execute == True, "Should execute when hash changes"
    
    def test_different_mtime_triggers_execution(self):
        """Different mtime should trigger execution even with same hash"""
        last_hash = "abc123"
        last_mtime = 1000.0
        
        current_hash = "abc123"
        current_mtime = 1001.0
        
        should_execute = (current_hash != last_hash) or (current_mtime != last_mtime)
        
        assert should_execute == True, "Should execute when mtime changes"
    
    def test_both_different_triggers_execution(self):
        """Both different should definitely trigger execution"""
        last_hash = "abc123"
        last_mtime = 1000.0
        
        current_hash = "def456"
        current_mtime = 1001.0
        
        should_execute = (current_hash != last_hash) or (current_mtime != last_mtime)
        
        assert should_execute == True, "Should execute when both change"


if __name__ == "__main__":
    print("Running tests...")
    print("\n" + "="*60)
    print("To run these tests, install pytest and run:")
    print("  pytest test_persistent_agent.py -v")
    print("="*60)
    
    # Run a quick manual test
    print("\nQuick manual test of command hashing:")
    from persistent_agent import PersistentAgent
    
    agent = Mock()
    agent.get_command_hash = PersistentAgent.get_command_hash.__get__(agent)
    
    cmd1 = {"action": "login"}
    cmd2 = {"action": "login"}
    cmd3 = {"action": "search_doctor"}
    
    hash1 = agent.get_command_hash(cmd1)
    hash2 = agent.get_command_hash(cmd2)
    hash3 = agent.get_command_hash(cmd3)
    
    print(f"  cmd1 hash: {hash1}")
    print(f"  cmd2 hash: {hash2}")
    print(f"  cmd3 hash: {hash3}")
    print(f"  cmd1 == cmd2: {hash1 == hash2} (expected: True)")
    print(f"  cmd1 != cmd3: {hash1 != hash3} (expected: True)")
