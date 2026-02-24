# Test Suite Documentation

## Overview

Comprehensive test suite for the Leumit Appointment Agent ensuring correct workflow execution, login logic, and command handling.

## Running Tests

### Run All Tests
```bash
python run_all_tests.py
```

### Run Individual Test Suites
```bash
# Unit tests (logic & hashing)
python test_agent_simple.py

# Workflow integration tests
python test_workflow_integration.py
```

## Test Coverage

### ✅ Unit Tests (`test_agent_simple.py`)

**Command Hashing**
- Identical commands produce same hash
- Different commands produce different hashes
- Parameter changes produce different hashes

**File Watching (mtime)**
- File modification changes mtime
- Unchanged file keeps same mtime

**Command Change Detection**
- Same hash and mtime → no execution
- Different hash → execution
- Different mtime → execution (even with same hash)

**Login Flow Logic**
- Login command recognized
- Non-login command not treated as login

**Hash Update Logic**
- Hash updated after successful login
- Hash NOT updated after failed login (enables retry)

**Requires Login Flow**
- Command returns requires_login when not logged in
- Hash NOT updated when requires_login (enables retry after login)

### ✅ Workflow Integration Tests (`test_workflow_integration.py`)

**1. Login Workflow Sequence**
Tests that login follows documented steps from `login workflow.md`:
- Navigate to Google
- Search for לאומית
- Click Leumit link
- Check for אזור אישי (not logged in) or זימון תורים (logged in)
- Click אזור אישי if present
- Fill form fields: TextBoxIdNumForOTP, TextBoxCellphone
- Wait for OTP and check for זימון תורים button

**2. Search Doctor Workflow Sequence**
Tests complete appointment search flow:
- Step 0: Check login state (look for זימון תורים)
- Step 1: Click 'זימון תורים' button
- Step 2: Click 'בצע חיפוש חדש' button
- Step 3: Click 'רופאים ומטפלים' radio
- Step 4: Select specialty from dropdown
- Step 5: Select subcategory if needed
- Step 6: Filter by doctor name
- Step 7: Click search button

**3. Full End-to-End Workflow**
Tests complete flow from fresh start to appointment search:
1. Agent starts with search_doctor command
2. Detects not logged in → returns requires_login
3. Automatically triggers login flow
4. Login completes (infinite retry until success)
5. Command retries on next cycle (hash not updated)
6. Now logged in → proceeds with search
7. Command completes → hash updated

**4. Login Always Runs on Fresh Start**
- Fresh start (no browser profile) requires login
- Existing profile still verifies login state dynamically
- Session expiration triggers automatic login

**5. Login Infinite Retry Logic**
- Failed logins don't update hash (enables retry)
- Hash updated only after successful login
- No maximum retry limit
- 10-second delay between retries

**6. Commands Auto-Trigger Login**
- search_doctor checks login state
- Returns requires_login=True if not logged in
- Agent automatically performs login
- Hash not updated during login
- Command retries after successful login
- Hash updated only after command success

**7. Button Click Sequences**
Documents exact button/element sequences for:
- Login flow (6 steps)
- Search doctor flow (6 steps)

**8. Form Field IDs**
- TextBoxIdNumForOTP (ID number)
- TextBoxCellphone (phone number)

**9. Selector Strategies**
Multiple fallback selectors for robustness:
- Priority 1: Class + onclick attribute
- Priority 2: Partial text match
- Priority 3: Button role with text

## Key Behaviors Verified

### ✅ Login Flow
1. **Always checks login state** - Never assumes cached state
2. **Follows documented workflow** - Per `login workflow.md`
3. **Infinite retry** - Continues until successful
4. **Smart hash management** - Hash updated only after success

### ✅ Command Execution
1. **Auto-login trigger** - Commands automatically trigger login when needed
2. **Hash-based change detection** - Uses both hash AND mtime
3. **Retry after login** - Commands retry after automatic login
4. **Prevents loops** - Hash updated only after success

### ✅ Search Doctor Workflow
1. **Login verification** - Checks for זימון תורים button
2. **Returns requires_login** - When not logged in
3. **Documented sequence** - All 8 steps clearly defined
4. **Multiple selectors** - Fallback strategies for robustness

## Test Statistics

- **Total Test Suites**: 2
- **Total Test Cases**: 20+
- **All Tests**: ✅ PASSING

## What's Tested vs Not Tested

### ✅ Tested (Logic & Flow)
- Command hashing and change detection
- File watching with mtime
- Login state detection logic
- Hash update timing
- Retry mechanisms
- Auto-login triggers
- Workflow sequences
- Form field IDs
- Selector strategies

### ⚠️ Not Tested (Requires Live Browser)
- Actual button clicks in browser
- Real form submissions
- OTP wait timing
- Network requests
- Page load timing
- Browser session persistence

## Adding New Tests

### For Logic/Behavior
Add to `test_agent_simple.py` or `test_workflow_integration.py`

### For New Workflows
1. Document workflow steps
2. Add test in `test_workflow_integration.py`
3. Verify button sequences
4. Document form fields/selectors

### Example Test Structure
```python
def test_new_feature():
    test_section("TEST: New Feature")
    
    # Setup
    expected_behavior = True
    
    # Test
    actual_behavior = True  # Your logic here
    
    # Assert
    if actual_behavior == expected_behavior:
        test_passed("Feature works correctly")
    else:
        test_failed("Feature doesn't work as expected")
```

## Test Maintenance

When modifying agent logic:
1. **Run tests first** - Ensure current behavior is documented
2. **Update tests** - If behavior should change
3. **Run tests again** - Verify changes work correctly
4. **Document changes** - Update workflow docs if needed

## CI/CD Integration

Add to CI/CD pipeline:
```bash
python run_all_tests.py
exit $?
```

Tests return:
- `0` = All tests passed
- `1` = Some tests failed
