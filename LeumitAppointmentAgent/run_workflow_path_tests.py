"""
Workflow Path Tests Runner - Executes all workflow path tests and prints test names
"""

from test_workflow_paths import (
    TestPath1_FreshLoginSuccess,
    TestPath2_AlreadyLoggedIn,
    TestPath3_DateOutOfRange_RetryLater,
    TestPath4_DateOutOfRange_StillOnCalendar,
    TestPath5_SessionExpired,
    TestPath6_LoginFailure_Retry,
    TestPath7_ApprovalLoop_MaxIterations,
    TestPath8_MultipleCommandRetries,
    TestPath9_SkipLoginAfterModalCheck,
    TestPath10_BookAppointment_FullFlow,
    TestPath11_Fallback_15MinuteWait,
    TestPath12_SpecialtySubcategoryDoctor_Filters,
)

def run_all_tests():
    """Run all workflow path tests"""
    
    print("\n" + "="*80)
    print("RUNNING ALL WORKFLOW PATH TESTS")
    print("="*80)
    
    tests = [
        (TestPath1_FreshLoginSuccess(), "test_fresh_login_to_sms_validation"),
        (TestPath2_AlreadyLoggedIn(), "test_skip_login_when_already_authenticated"),
        (TestPath3_DateOutOfRange_RetryLater(), "test_fallback_with_valid_session"),
        (TestPath4_DateOutOfRange_StillOnCalendar(), "test_fallback_calendar_detection_restart"),
        (TestPath5_SessionExpired(), "test_session_expiration_full_restart"),
        (TestPath6_LoginFailure_Retry(), "test_login_failure_retry_mechanism"),
        (TestPath7_ApprovalLoop_MaxIterations(), "test_approval_loop_max_iterations"),
        (TestPath8_MultipleCommandRetries(), "test_command_auto_retry"),
        (TestPath9_SkipLoginAfterModalCheck(), "test_skip_login_form_if_already_logged_in"),
        (TestPath10_BookAppointment_FullFlow(), "test_book_appointment_sequence"),
        (TestPath11_Fallback_15MinuteWait(), "test_fallback_wait_progress_logging"),
        (TestPath12_SpecialtySubcategoryDoctor_Filters(), "test_filter_selection_sequence"),
    ]
    
    passed = 0
    failed = 0
    
    for test_instance, test_method_name in tests:
        try:
            test_method = getattr(test_instance, test_method_name)
            test_method()
            print(f"✓ PASS")
            passed += 1
        except AssertionError as e:
            print(f"✗ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print(f"Total:  {len(tests)}")
    print("="*80 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
