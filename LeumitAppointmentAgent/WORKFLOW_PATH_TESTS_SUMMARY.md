# Workflow Path Tests - Complete Summary

## Overview
This document lists all comprehensive workflow path tests created to validate every possible execution route through the Leumit Appointment Agent flowchart.

## Test Framework
- **Test File**: `test_workflow_paths.py`
- **Validation Method**: Analyzes log outputs for `<step_x>` tag sequences
- **Total Paths Tested**: 12

---

## Test Paths

### PATH 1: Fresh Login → Search → Date in Range → Approval Loop → SMS
**Class**: `TestPath1_FreshLoginSuccess`  
**Test Method**: `test_fresh_login_to_sms_validation()`  
**Description**: Complete path from fresh login through SMS validation screen  
**Expected Steps**:
```
step_0  → Navigate to google
step_1  → Search לאומית
step_2  → Click first link
step_3  → Click אזור אישי
step_4  → Select specialty
step_5  → Select subcategory
step_6  → Fill doctor name
step_7  → Click login/verify
step_8  → Click appointment scheduling
step_16 → New search
step_17 → Click doctors
step_18 → Specialty dropdown
step_19 → Select appointment type button
step_20 → Subcategory dropdown
step_21 → Doctor name field
step_22 → Click search
step_A  → Check SMS screen
step_B  → Find continuation button
step_C  → Click button
step_D  → Wait 1 second
step_E  → Take screenshot
```
**Validates**: Full fresh login workflow, search, and approval loop ending in SMS validation

---

### PATH 2: Already Logged In → Search → Date in Range → Success
**Class**: `TestPath2_AlreadyLoggedIn`  
**Test Method**: `test_skip_login_when_already_authenticated()`  
**Description**: Path when user is already authenticated - skips login steps  
**Expected Steps**:
```
step_0  → Navigate
step_1  → Search
step_2  → Click link
(Steps 3-7 SKIPPED - already logged in)
step_8  → Appointment scheduling
step_16 → New search
step_19 → Appointment selection
```
**Validates**: Skip login logic when user is pre-authenticated

---

### PATH 3: Search → Date Out of Range → Fallback → Step 106 Found → Retry Later
**Class**: `TestPath3_DateOutOfRange_RetryLater`  
**Test Method**: `test_fallback_with_valid_session()`  
**Description**: Fallback workflow when date is out of range but session is still valid  
**Expected Steps**:
```
step_19  → Appointment selection (before fallback)
step_100 → Refresh page
step_101 → Screenshot post-refresh
step_102 → Wait 15 minutes
step_103 → Refresh again
step_104 → Screenshot post-wait
step_105 → Check calendar page
step_106 → Check zimon button (FOUND)
step_8   → Appointment scheduling (retry after 5s wait)
```
**Validates**: Fallback retry mechanism with valid session

---

### PATH 4: Search → Date Out of Range → Fallback → Step 105 YES → Restart at Step 19
**Class**: `TestPath4_DateOutOfRange_StillOnCalendar`  
**Test Method**: `test_fallback_calendar_detection_restart()`  
**Description**: Fallback detects still on calendar page - restarts directly at Step 19  
**Expected Steps**:
```
step_19  → Initial appointment attempt
step_100 → Fallback: refresh
step_101 → Screenshot
step_102 → Wait 15 min
step_103 → Refresh
step_104 → Screenshot
step_105 → Check calendar (YES - still on calendar)
step_19  → Direct restart at appointment selection
```
**Validates**: Step 105 YES branch routing back to Step 19

---

### PATH 5: Search → Fallback → Step 106 Not Found → Session Expired → Full Restart
**Class**: `TestPath5_SessionExpired`  
**Test Method**: `test_session_expiration_full_restart()`  
**Description**: Session expiration detected leads to full restart at Step 1  
**Expected Steps**:
```
step_22  → Last search step
step_100 → Fallback
step_105 → Calendar check
step_106 → Zimon button (NOT FOUND - session expired)
step_1   → Full restart - navigate to google
```
**Validates**: Session expiration detection and full restart logic

---

### PATH 6: Login Failure → Wait 30s → Retry at Step 1
**Class**: `TestPath6_LoginFailure_Retry`  
**Test Method**: `test_login_failure_retry_mechanism()`  
**Description**: Login failure triggers 30-second wait and retry  
**Expected Steps**:
```
step_1 → Initial navigation
step_2 → Search
step_3 → Click link
step_4 → Specialty
step_5 → Subcategory
step_6 → Doctor name
step_7 → Login attempt (FAILS)
(Wait 30s - no step tag)
step_1 → Retry navigation
```
**Validates**: Login failure recovery with 30s wait

---

### PATH 7: Approval Loop Reaches 10 Iterations Without SMS
**Class**: `TestPath7_ApprovalLoop_MaxIterations`  
**Test Method**: `test_approval_loop_max_iterations()`  
**Description**: Approval loop terminates after 10 iterations without finding SMS  
**Expected Steps**:
```
(step_A → step_B → step_C → step_D → step_E) × 10 iterations
Total: 50 step tags
```
**Validates**: Max iteration limit (10) for approval loop

---

### PATH 8: Command Failure → Auto-Retry Mechanism
**Class**: `TestPath8_MultipleCommandRetries`  
**Test Method**: `test_command_auto_retry()`  
**Description**: Failed commands are automatically retried up to 3 times  
**Expected Steps**:
```
step_8 → First attempt (fails)
step_8 → Retry 1 (fails)
step_8 → Retry 2 (fails)
(Return error if still failing)
```
**Validates**: Command retry mechanism with hash management

---

### PATH 9: Click אזור אישי → Already Logged In (Skip Steps 6-7)
**Class**: `TestPath9_SkipLoginAfterModalCheck`  
**Test Method**: `test_skip_login_form_if_already_logged_in()`  
**Description**: After clicking אזור אישי, if זימון תורים appears, skip login form  
**Expected Steps**:
```
step_3 → Click אזור אישי
step_4 → Specialty (wait/check)
(Steps 5-7 SKIPPED - already logged in)
step_8 → Appointment scheduling
```
**Validates**: Step 5 skip logic when already authenticated

---

### PATH 10: Book Appointment Steps 1-4
**Class**: `TestPath10_BookAppointment_FullFlow`  
**Test Method**: `test_book_appointment_sequence()`  
**Description**: Complete appointment booking sequence  
**Expected Steps**:
```
step_1 → Select first available slot
step_2 → Click appointment type (video/phone/clinic)
step_3 → Click המשך on popup
step_4 → Click שמור וסיים to confirm
```
**Validates**: Full booking workflow from slot selection to confirmation

---

### PATH 11: Fallback 15-Minute Wait with Progress Logging
**Class**: `TestPath11_Fallback_15MinuteWait`  
**Test Method**: `test_fallback_wait_progress_logging()`  
**Description**: 15-minute wait includes progress logging every 60 seconds  
**Expected Steps**:
```
step_100 → Refresh
step_101 → Screenshot
step_102 → Start 15-minute wait (900s)
(Progress logs every 60s: 1/15, 2/15, ..., 15/15)
step_103 → Post-wait refresh
```
**Validates**: Wait progress logging during 15-minute fallback

---

### PATH 12: Specialty/Subcategory/Doctor Filter Selection
**Class**: `TestPath12_SpecialtySubcategoryDoctor_Filters`  
**Test Method**: `test_filter_selection_sequence()`  
**Description**: Specialty/subcategory/doctor filter workflow  
**Expected Steps**:
```
step_4  → Select specialty (Select2 dropdown)
step_5  → Select subcategory (Select2 dropdown)
step_6  → Fill doctor name (optional)
step_22 → Click search
```
**Validates**: Filter selection workflow with Select2 dropdowns

---

## Test Execution

### Run All Path Tests
```powershell
pytest test_workflow_paths.py -v
```

### Run Specific Path Test
```powershell
pytest test_workflow_paths.py::TestPath1_FreshLoginSuccess::test_fresh_login_to_sms_validation -v
```

### Run Comprehensive Test Suite (includes path tests)
```powershell
python run_all_tests.py
```

---

## Helper Classes

### `WorkflowPathValidator`
Utility class for validating step sequences in logs:

- **`extract_steps(log_content)`**: Extracts all `<step_x>` tags from log content
- **`validate_sequence(actual, expected)`**: Validates exact step sequence match
- **`validate_contains_subsequence(actual, expected)`**: Validates subsequence presence

### Example Usage
```python
from test_workflow_paths import WorkflowPathValidator

# Extract steps from log
log_content = """
2024-01-01 12:00:00 - <step_1> Step 1: Navigate
2024-01-01 12:00:01 - <step_2> Step 2: Search
"""

steps = WorkflowPathValidator.extract_steps(log_content)
# Returns: ['step_1', 'step_2']

# Validate sequence
is_valid, message = WorkflowPathValidator.validate_sequence(
    steps, ['step_1', 'step_2']
)
# Returns: (True, "Valid sequence")
```

---

## Integration with Test Suite

The workflow path tests have been integrated into `run_all_tests.py` as:
```
Test Suite Position: 3/10
Description: "Workflow Path Tests (All Flowchart Routes)"
```

---

## Coverage Summary

| Category | Paths Tested |
|----------|--------------|
| **Login Workflows** | 4 (fresh login, already logged in, login failure, skip after modal) |
| **Date Range Handling** | 3 (in range, out of range with retry, out of range with calendar restart) |
| **Fallback Workflows** | 4 (valid session retry, calendar restart, session expired, 15-min wait) |
| **Approval Loop** | 2 (SMS found, max iterations) |
| **Booking** | 1 (full booking sequence) |
| **Filters** | 1 (specialty/subcategory/doctor) |
| **Error Handling** | 1 (command auto-retry) |

**Total**: 12 comprehensive workflow paths covering all flowchart routes

---

## Maintenance Notes

1. **Step Tag Format**: All workflow steps must log in `<step_x>` format for test validation
2. **Log Parsing**: Tests rely on regex pattern `<(step_[0-9A-E]+)>` to extract steps
3. **Integration Tests**: Some tests require actual browser runs - marked with "requires integration test"
4. **Continuous Validation**: Run path tests after any flowchart changes to ensure alignment

---

## Future Enhancements

- [ ] Add actual log file parsing from integration test runs
- [ ] Implement automated flowchart-to-test-path generator
- [ ] Add timing validation (e.g., Step 102 takes ~900 seconds)
- [ ] Create visual flow diagram from actual log step sequences
- [ ] Add anomaly detection for unexpected step sequences

---

*Last Updated: 2024*  
*Test Suite Version: 1.0*  
*Flowchart Version: Steps 0-106 with A-E approval loop*
