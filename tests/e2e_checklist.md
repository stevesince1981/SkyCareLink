# SkyCareLink End-to-End Testing Checklist

## Definition of Done
**All automated scripts pass (smoke.sh, check_routes.py), and all manual checks green.**

## Pre-Testing Setup
- [ ] Server is running on localhost:5000
- [ ] Database is accessible (PostgreSQL)
- [ ] Email service configured (or fallback logging active)
- [ ] SMS service configured (or fallback logging active)
- [ ] Admin user credentials available

## Automated Tests (Run These First)

### 1. Smoke Test Suite
```bash
bash scripts/smoke.sh
```
**Expected:** All tests pass with green ✓ PASS indicators

### 2. Route Health Check
```bash
python scripts/check_routes.py
```
**Expected:** Critical routes return success, non-critical warnings acceptable

---

## Manual Testing Checklist

### Quote Submission Flow

#### Test 1: Quote Form Validation
- [ ] **Navigate to:** `/consumer_intake`
- [ ] **Test:** Select severity level 1 → Verify equipment auto-selects basic monitoring
- [ ] **Test:** Select severity level 2 → Verify ventilator and monitoring selected  
- [ ] **Test:** Select severity level 3 → Verify ECMO and full equipment selected
- [ ] **Database Check:** Verify `severity_level` field stored correctly (1/2/3)
- [ ] **Screenshot:** Save form with each severity level

#### Test 2: Quote Submission End-to-End
- [ ] **Submit:** Complete quote form with all required fields
- [ ] **Verify:** Quote reference generated (format: REF-YYYYMMDD-XXXX)
- [ ] **Verify:** Redirected to results page showing quote reference
- [ ] **Database Check:** Quote record exists with correct timestamp
- [ ] **Screenshot:** Quote results page

### Affiliate Notification System

#### Test 3: Affiliate Email Notifications  
- [ ] **Trigger:** Submit quote from Test 2
- [ ] **Check Email:** Affiliate receives "New Quote Request" email within 2 minutes
- [ ] **Verify Email Content:** 
  - [ ] Contains quote reference number
  - [ ] Contains "Submit Quote" button/link  
  - [ ] Contains raw quote details link
  - [ ] Sender shows SkyCareLink branding
- [ ] **Test Link:** Click email button → Should redirect to affiliate quote form
- [ ] **Screenshot:** Email content and affiliate quote form

#### Test 4: Quote Response Workflow
- [ ] **Access:** `/affiliate/submit_quote/<quote_ref>` (from email link)
- [ ] **Submit:** Affiliate quote with pricing and details
- [ ] **Verify:** Caller receives "Quote Ready" notification
- [ ] **Check Email/SMS:** Caller gets notification within 2 minutes
- [ ] **Verify Content:** Contains quote details and next steps
- [ ] **Screenshot:** Quote ready notification

### Booking Confirmation Flow

#### Test 5: Booking Confirmation
- [ ] **Access:** Quote results page with submitted quotes
- [ ] **Action:** Select provider and confirm booking  
- [ ] **Verify:** Booking confirmation page displays
- [ ] **Check Notifications:** Caller receives "Booking Confirmed" email/SMS
- [ ] **Verify Content:** 
  - [ ] Booking reference number
  - [ ] Provider contact information  
  - [ ] Flight details and next steps
  - [ ] Payment/deposit information
- [ ] **Database Check:** Booking record created with correct status
- [ ] **Screenshot:** Booking confirmation and notifications

### Affiliate Management

#### Test 6: Call Center Options
- [ ] **Login:** As affiliate user
- [ ] **Navigate:** `/affiliate/call_center_settings`
- [ ] **Configure:** Set business hours, phone routing, DTMF options
- [ ] **Save:** Submit configuration form
- [ ] **Verify Persistence:** Reload page → Settings should be saved
- [ ] **Database Check:** Call center settings stored correctly
- [ ] **Screenshot:** Call center configuration page

### Admin Co-Founders System

#### Test 7: Admin Payment Tracking
- [ ] **Login:** As admin user  
- [ ] **Navigate:** `/admin/cofounders`
- [ ] **Record Partial:** Add partial buy-in payment for test co-founder
- [ ] **Verify Email:** Co-founder receives partial payment confirmation email
- [ ] **Record Full:** Complete buy-in payment for same co-founder  
- [ ] **Verify Email:** Co-founder receives full buy-in welcome email
- [ ] **Database Check:** Payment timestamps and amounts recorded
- [ ] **Verify Audit:** Check audit logs for payment entries
- [ ] **Screenshot:** Admin co-founders dashboard and email confirmations

### Document Management System

#### Test 8: Document Upload
- [ ] **Navigate:** Document upload section (via quote or booking flow)
- [ ] **Upload:** Select 2 test files (PDF and image recommended)
- [ ] **Verify:** Both files appear in document list with metadata
- [ ] **Test Immutability:** Attempt to delete documents → Should be blocked
- [ ] **Verify Security:** HTTP DELETE requests return 405 Method Not Allowed
- [ ] **Database Check:** Document records with SHA-256 hashes stored
- [ ] **Screenshot:** Document upload interface and file list

### Security and Authentication

#### Test 9: Password Reset Flow
- [ ] **Navigate:** `/auth/password-reset`
- [ ] **Submit:** Password reset request for test email
- [ ] **Verify Email:** Password reset email sent with secure token link
- [ ] **Click Link:** Access password reset form with token
- [ ] **Reset Password:** Submit new password
- [ ] **Verify Confirmation:** Post-reset notification email sent
- [ ] **Check Audit:** Audit log entry exists for password reset (actor=null)
- [ ] **Test Login:** Confirm new password works
- [ ] **Screenshot:** Password reset form and confirmation emails

### Platform Performance

#### Test 10: Load and Response Times
- [ ] **Measure:** Home page load time < 2 seconds
- [ ] **Measure:** Quote form submission < 5 seconds  
- [ ] **Measure:** Quote results display < 3 seconds
- [ ] **Test:** Multiple concurrent quote submissions (3-5 simultaneous)
- [ ] **Verify:** No timeout errors or failed requests
- [ ] **Check Logs:** No error entries in application logs

### Data Integrity

#### Test 11: Session and Data Persistence
- [ ] **Test:** Start quote, close browser, return → Form data restored
- [ ] **Test:** Submit quote, check multiple browser sessions → Data consistent
- [ ] **Test:** Admin changes persist across page reloads
- [ ] **Verify:** No PHI stored permanently (session-only for demo data)
- [ ] **Check:** Audit logs maintain data change history

---

## Post-Testing Verification

### Final Checks
- [ ] **Run:** `curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/healthz` → Returns 200
- [ ] **Run:** `bash scripts/smoke.sh && python scripts/check_routes.py` → Both pass
- [ ] **Check:** No critical errors in application logs
- [ ] **Verify:** All test data cleaned up appropriately

### Documentation
- [ ] **Screenshots:** Stored in `/docs/qa/` (optional)
- [ ] **Log Excerpts:** Email/SMS attempts documented
- [ ] **Test Results:** All checklist items marked complete
- [ ] **Git Status:** All test-related changes committed

---

## Acceptance Criteria Self-Audit

### Verification Report Template:
```
TESTED BY: [Name]
DATE: [YYYY-MM-DD]  
ENVIRONMENT: [Local/Staging/Production]

AUTOMATED TESTS:
✓ smoke.sh: [PASS/FAIL]
✓ check_routes.py: [PASS/FAIL]

MANUAL TESTS VERIFIED:
✓ Quote submission with severity levels: [PASS/FAIL]
✓ Affiliate email notifications: [PASS/FAIL] 
✓ Booking confirmation flow: [PASS/FAIL]
✓ Call center options persistence: [PASS/FAIL]
✓ Admin payment tracking: [PASS/FAIL]
✓ Document upload security: [PASS/FAIL]
✓ Password reset with audit: [PASS/FAIL]

CRITICAL ISSUES: [None/List any blockers]
NON-CRITICAL ISSUES: [None/List any warnings]

RECOMMENDATION: [APPROVED FOR DEPLOYMENT/NEEDS FIXES]
```

### Files Changed Summary:
- List all files modified during testing
- Include any test data or configuration changes  
- Note any temporary test files created

### System Health Status:
- Application server: [UP/DOWN]
- Database connectivity: [OK/ISSUES]
- Email service: [OK/FALLBACK/ISSUES]  
- SMS service: [OK/FALLBACK/ISSUES]
- Static assets: [OK/ISSUES]

---

## Emergency Procedures

### If Critical Tests Fail:
1. **STOP** deployment immediately
2. Capture full error logs and screenshots
3. Document exact steps to reproduce failure
4. Notify development team with full context
5. Do not proceed until critical issues resolved

### If Non-Critical Tests Fail:
1. Document the failure with context
2. Assess impact on user workflows  
3. Create tickets for follow-up fixes
4. May proceed with deployment if core functionality intact
5. Monitor production closely after deployment

---

**Test Checklist Version:** 1.0  
**Last Updated:** August 17, 2025  
**Next Review:** Before next major release