# Testing Guide for Security Features

## Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:8080`
- PostgreSQL database running and initialized
- Authenticator app installed (Google Authenticator, Microsoft Authenticator, etc.)

## Test Suite

### Test 1: Complete User Registration and MFA Setup

**Objective**: Verify full registration flow with forced MFA setup and backup code generation.

**Steps:**
1. Navigate to `http://localhost:8080/register`
2. Fill in registration form:
   - Username: `testuser1`
   - Email: `test1@example.com`
   - Password: `SecurePass123!`
3. Click "Sign Up"
4. **Expected**: Auto-redirect to `/mfa-setup` page
5. Scan QR code with authenticator app
6. **Expected**: Authenticator shows "MFA POC (testuser1)"
7. Enter 6-digit code from authenticator
8. Click "Verify & Enable MFA"
9. **Expected**: Redirect to `/dashboard` (Security Dashboard)
10. **Expected**: Backup codes section visible with 8 codes
11. Click to expand backup codes
12. **Expected**: Grid display with 8 codes (format: ABCD1234)
13. Copy one code to clipboard
14. **Expected**: Toast notification "Copied!"
15. Click "Download" button
16. **Expected**: File downloaded: `mfa-backup-codes-testuser1.txt`
17. Open file and verify:
    - Contains 8 codes
    - Includes timestamp
    - Has security warnings

**✅ Pass Criteria:**
- Registration completes successfully
- MFA setup is forced (cannot skip)
- QR code displays "MFA POC"
- Backup codes are generated and displayed
- Copy and download functions work
- File contains all codes with proper formatting

---

### Test 2: Login with MFA

**Objective**: Verify MFA token is required on every login.

**Steps:**
1. If logged in, click "Sign Out"
2. Navigate to `http://localhost:8080/login`
3. Enter credentials:
   - Username: `testuser1`
   - Password: `SecurePass123!`
4. Click "Sign In"
5. **Expected**: MFA token input appears (not a new page)
6. Open authenticator app
7. **Expected**: "MFA POC (testuser1)" entry exists
8. Copy current 6-digit code
9. Enter code in MFA token field
10. Click "Sign In" again
11. **Expected**: Redirect to `/dashboard`
12. **Expected**: Backup codes section shows "Backup Codes Not Available"
13. **Expected**: Warning message explains codes only shown once

**✅ Pass Criteria:**
- Login requires password + MFA token
- MFA token field appears dynamically
- Valid token grants access
- Dashboard shows "no backup codes" warning
- Account information displays correctly

---

### Test 3: Backup Code Recovery

**Objective**: Test MFA reset using backup code when authenticator is lost.

**Preparation:**
- Use one of the backup codes saved from Test 1
- Example: `ABCD1234`

**Steps:**
1. Logout if logged in
2. Navigate to `http://localhost:8080/login`
3. Enter username and password for `testuser1`
4. Click "Sign In"
5. **Expected**: MFA token input appears
6. Click "Lost MFA device? Use backup code" link
7. **Expected**: Modal dialog opens
8. Enter username: `testuser1`
9. Enter backup code: `ABCD1234` (from Test 1)
10. Click "Verify & Reset MFA"
11. **Expected**: Success toast "Backup code verified!"
12. **Expected**: Toast "MFA Reset Complete"
13. **Expected**: Auto-redirect to `/mfa-setup`
14. Scan new QR code with authenticator app
15. **Expected**: New "MFA POC (testuser1)" entry created (old one should be deleted manually)
16. Enter code and verify
17. **Expected**: Redirect to dashboard with NEW backup codes
18. **Expected**: 8 new backup codes displayed
19. Logout
20. Try to use the same backup code again (`ABCD1234`)
21. **Expected**: Error "Invalid backup code or already used"

**✅ Pass Criteria:**
- Backup code successfully verifies
- MFA is reset (old secret deleted)
- New MFA setup is forced
- New backup codes are generated
- Old backup code cannot be reused
- Recovery workflow is seamless

---

### Test 4: Incomplete MFA Setup Detection

**Objective**: Verify users with incomplete MFA setup are redirected on login.

**Preparation:**
- Register a new user but DON'T complete MFA setup

**Steps:**
1. Navigate to `http://localhost:8080/register`
2. Register new user:
   - Username: `testuser2`
   - Email: `test2@example.com`
   - Password: `SecurePass123!`
3. **Expected**: Redirect to `/mfa-setup`
4. **DO NOT SCAN OR VERIFY** - Just close the tab/window
5. Open new browser tab
6. Navigate to `http://localhost:8080/login`
7. Login with `testuser2` credentials
8. Click "Sign In"
9. **Expected**: Login succeeds (no MFA token required yet)
10. **Expected**: Toast "MFA Setup Incomplete"
11. **Expected**: Auto-redirect to `/mfa-setup`
12. Complete MFA setup this time
13. **Expected**: Redirect to dashboard after verification

**✅ Pass Criteria:**
- Incomplete MFA setup is detected on login
- User is redirected to `/mfa-setup` automatically
- Toast notification explains the situation
- Dashboard is inaccessible until MFA is complete
- Completing setup grants dashboard access

---

### Test 5: Invalid Backup Code Attempts

**Objective**: Test error handling for invalid backup codes.

**Steps:**
1. Logout if logged in
2. Navigate to login page
3. Enter valid username/password
4. Click "Sign In"
5. When MFA token appears, click "Lost MFA device?"
6. Enter username: `testuser1`
7. Enter invalid code: `INVALID1`
8. Click "Verify & Reset MFA"
9. **Expected**: Error toast "Invalid backup code or already used"
10. Try with wrong username:
    - Username: `wronguser`
    - Code: (any valid format code)
11. **Expected**: Error "User not found"

**✅ Pass Criteria:**
- Invalid codes are rejected
- Appropriate error messages shown
- No temp token is issued
- MFA is not reset
- System remains secure

---

### Test 6: Security Dashboard Features

**Objective**: Test all Security Dashboard functionality.

**Steps:**
1. Register a new user and complete MFA setup (to get backup codes)
   - Username: `testuser3`
   - Email: `test3@example.com`
2. **Expected**: Dashboard shows with backup codes visible
3. **Test Copy Function:**
   - Click copy button on first code
   - **Expected**: Check icon appears briefly
   - **Expected**: Toast "Copied!"
   - Paste in notepad
   - **Expected**: Code matches displayed code
4. **Test Download Function:**
   - Click "Download" button
   - **Expected**: File downloaded
   - Open file
   - **Expected**: Contains all 8 codes
   - **Expected**: Includes timestamp
   - **Expected**: Has security warnings
5. **Test Collapsible Section:**
   - Click to collapse backup codes
   - **Expected**: Codes hidden, ChevronDown icon
   - Click to expand
   - **Expected**: Codes shown, ChevronUp icon
6. **Test Account Information:**
   - Verify username displays correctly
   - Verify email displays correctly
   - Verify MFA status shows "Enabled"
7. Refresh the page
8. **Expected**: Backup codes section shows "Not Available" warning
9. **Expected**: Message explains codes only shown once

**✅ Pass Criteria:**
- All copy buttons work
- Download creates valid file
- Collapsible section toggles correctly
- Account info is accurate
- Codes disappear after page refresh (security feature)
- Appropriate warnings are shown

---

### Test 7: Multiple Users and Code Isolation

**Objective**: Verify backup codes are user-specific and isolated.

**Steps:**
1. Register two users with MFA:
   - User A: `usera` / `usera@test.com`
   - User B: `userb` / `userb@test.com`
2. Save backup codes for User A
3. Logout
4. Login as User B
5. Try MFA recovery with User A's backup code
6. **Expected**: Error "Invalid backup code"
7. Use User B's backup code with User A's username
8. **Expected**: Error "Invalid backup code"

**✅ Pass Criteria:**
- Backup codes are user-specific
- Cross-user code usage is prevented
- Database properly isolates codes by user_id

---

### Test 8: Token Expiry

**Objective**: Verify temporary token expires after 10 minutes.

**Steps:**
1. Start MFA recovery process
2. Enter valid username and backup code
3. **Expected**: Success, temp token received
4. Wait 11 minutes (or modify backend to 1 minute for testing)
5. Try to use the temp token to reset MFA
6. **Expected**: Error "Token expired"

**✅ Pass Criteria:**
- Temp token expires after configured time
- Expired token cannot reset MFA
- User must restart recovery process

---

### Test 9: Edge Cases

**Objective**: Test various edge cases and error conditions.

**Test Cases:**

#### A. User without MFA trying backup code
1. Register user without completing MFA
2. Try to use backup code recovery
3. **Expected**: Error "User does not have MFA enabled"

#### B. Empty backup code
1. Start recovery
2. Leave backup code field empty
3. **Expected**: Form validation error

#### C. Wrong format backup code
1. Enter code with lowercase: `abcd1234`
2. **Expected**: Auto-converts to uppercase `ABCD1234`
3. Enter code with special chars: `AB@D12#4`
4. **Expected**: Error "Invalid backup code"

#### D. Network errors
1. Stop backend server
2. Try backup code recovery
3. **Expected**: Error message about network failure
4. Restart backend
5. Retry
6. **Expected**: Success

**✅ Pass Criteria:**
- All edge cases handled gracefully
- Error messages are informative
- No crashes or undefined behavior
- System recovers properly

---

## Test Summary Checklist

Use this checklist to track test completion:

- [ ] Test 1: Registration and MFA Setup
- [ ] Test 2: Login with MFA
- [ ] Test 3: Backup Code Recovery
- [ ] Test 4: Incomplete MFA Detection
- [ ] Test 5: Invalid Backup Code Attempts
- [ ] Test 6: Security Dashboard Features
- [ ] Test 7: Multiple Users Code Isolation
- [ ] Test 8: Token Expiry
- [ ] Test 9: Edge Cases

## Known Issues

Document any issues found during testing:

1. **Issue**: [Description]
   - **Severity**: High/Medium/Low
   - **Steps to Reproduce**: [Steps]
   - **Expected**: [Expected behavior]
   - **Actual**: [Actual behavior]

## Security Audit Points

### Backend Security
- [ ] Backup codes are hashed (never plain text)
- [ ] Single-use enforcement works
- [ ] Temp token expires correctly
- [ ] SQL injection prevention (parameterized queries)
- [ ] CORS properly configured
- [ ] Rate limiting (future enhancement)

### Frontend Security
- [ ] Backup codes not in localStorage
- [ ] Backup codes cleared on logout
- [ ] Sensitive data not in browser history
- [ ] XSS prevention (React escaping)
- [ ] CSRF token (future enhancement)

### Database Security
- [ ] Cascade delete works for backup codes
- [ ] Foreign key constraints enforced
- [ ] No orphaned records
- [ ] Indexes properly set

## Performance Testing

### Load Testing (Optional)
1. Create 100 users with MFA
2. Simulate concurrent logins
3. Monitor response times
4. Check database query performance

### Expected Performance
- Login: < 500ms
- MFA verification: < 200ms
- Backup code verification: < 300ms
- Dashboard load: < 400ms

## Troubleshooting Common Issues

### Issue: Backup codes not displayed
**Solution**: Codes only show once after MFA setup. Check AuthContext state.

### Issue: "Lost MFA?" button not visible
**Solution**: Button only appears when MFA token input is shown.

### Issue: Backup code recovery fails
**Solution**: Verify code format (uppercase, 8 chars) and ensure user has MFA enabled.

### Issue: Incomplete MFA redirect not working
**Solution**: Check backend returns `incomplete_mfa: true` in login response.

---

**Test Plan Version:** 1.0  
**Last Updated:** February 11, 2026  
**Author:** GitHub Copilot  
**Status:** Ready for Testing
