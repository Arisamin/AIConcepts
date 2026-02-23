# Code Quality & Development Guidelines

## Critical Rules

### 🚫 NEVER Make Code Changes Without Testing First

**Before ANY code change is delivered to the user:**
1. Run validation: `python validate_before_use.py`
2. All tests MUST pass
3. Only then respond to user

### 🔒 Protection Against Login Lockouts

**The Problem:**
- Multiple agent restarts = multiple login attempts
- Too many attempts = account lockout
- Lost development time

**The Solution:**
- All code changes MUST pass tests before delivery
- No "try it and see" approach
- Regressions caught before they reach production

## Development Workflow

### For Every Code Change:

```
1. Make code changes
2. Run: python validate_before_use.py
3. If tests fail:
   - Fix the code
   - Go back to step 2
4. If tests pass:
   - Deliver to user with confidence
   - No login attempts wasted
```

### Test Suite Structure

1. **Unit Tests** (`test_agent_simple.py`)
   - Command hashing logic
   - File watching mechanism
   - Hash update timing
   - Error retry logic
   - Fast feedback (~5 seconds)

2. **Workflow Tests** (`test_workflow_integration.py`)
   - Login workflow sequence
   - Search doctor workflow
   - End-to-end flow
   - Button sequences
   - Comprehensive coverage (~10 seconds)

3. **Syntax Check**
   - Python compilation test
   - Catches syntax errors
   - Instant feedback (~1 second)

## What Tests Prevent

✅ **Regressions Caught:**
- Hash updated on error (would prevent retry)
- Login flow skipped (missing state check)
- Button selector changes breaking workflow
- Logic inversions

✅ **Production Issues Prevented:**
- Account lockouts from failed attempts
- Infinite loops from bad logic
- Workflow steps skipped
- Session state confusion

## Quality Metrics

### Test Coverage:
- ✅ Command hashing: 100%
- ✅ File watching: 100%
- ✅ Login logic: 100%
- ✅ Error retry: 100%
- ✅ Workflow sequences: 100%

### Code Quality Indicators:
- Zero tolerance for test failures
- All tests must pass before delivery
- Regressions caught before user testing

## When Tests Fail

### ❌ DO NOT:
- Deliver code anyway
- Ask user to test it
- "Try it and see"
- Skip validation

### ✅ DO:
- Fix the code
- Re-run tests
- Understand why it failed
- Add tests for new scenarios

## Continuous Improvement

### Adding New Features:
1. Write test FIRST (TDD)
2. Implement feature
3. Run full test suite
4. Only deliver when green

### Fixing Bugs:
1. Write test that reproduces bug
2. Verify test fails
3. Fix the bug
4. Verify test passes
5. Run full suite
6. Deliver fix

## Emergency Procedures

### If User Gets Locked Out:
- **Root Cause:** Code delivered without testing
- **Prevention:** ALWAYS run validate_before_use.py
- **Recovery:** Wait for lockout to expire, fix code, test thoroughly

### If Tests Start Failing:
- **DO NOT PANIC:** This is the safety net working
- **Investigate:** Why did it fail?
- **Fix:** Address the root cause
- **Verify:** All tests green before proceeding

## Success Metrics

### Before This System:
- Multiple login lockouts
- Regressions deployed
- Wasted time debugging live

### After This System:
- Zero lockouts from code issues
- Regressions caught in tests
- Confidence in every delivery

## Quick Reference

### Single Command Validation:
```bash
python validate_before_use.py
```

### Expected Output (Success):
```
======================================================================
Running: Unit Tests
======================================================================
[... all tests pass ...]

======================================================================
Running: Workflow Integration Tests
======================================================================
[... all tests pass ...]

======================================================================
Running: Python Syntax Check
======================================================================
[... syntax OK ...]

======================================================================
✅ ALL VALIDATION CHECKS PASSED
======================================================================

Code is ready to use
```

### On Failure:
```
======================================================================
❌ VALIDATION FAILED
======================================================================

Failed checks:
  ✗ Unit Tests

⚠️  DO NOT USE THIS CODE - FIX TESTS FIRST
```

## Commitment

**Every code change will be validated before delivery.**

This prevents:
- Login lockouts
- Wasted time
- User frustration
- Development rework

**Tests are not optional. They are the foundation of quality.**
