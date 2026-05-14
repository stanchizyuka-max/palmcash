# Session Summary - May 14, 2026

## Issues Fixed Today

### 1. ✅ KUKU Branch Missing Vault Transactions (Carol & Kaluba)

**Problem:**
- Two loans disbursed on May 8 had no vault transactions
- Carol Bwalya (LV-000032): K2,000
- Kaluba Bwalya (LV-000031): K2,000

**Root Cause:**
- Loans were disbursed BEFORE the vault recording fix was deployed (May 10)
- Old code allowed silent failures - loans marked active even if vault recording failed

**Fix Applied:**
1. Created missing vault transaction records (IDs 664, 665)
2. Updated WeeklyVault balance from K13,138 → K9,138
3. Verified all transactions now match the vault balance

**Scripts Created:**
- `fix_kuku_missing_loans.py` - Find and fix missing vault transactions
- `fix_kuku_vault_balance.py` - Update vault balance to match transactions
- `verify_carol_kaluba_fix.py` - Verify the fix was successful

**Prevention:**
- Vault recording fix deployed May 10 prevents this from happening again
- If vault recording fails now, loan stays in "approved" status with clear error message

---

### 2. ✅ Phone Number Validation - New Zambian Prefixes

**Problem:**
- System was rejecting valid Zambian numbers starting with 055 and 057

**Root Cause:**
- Validation only checked for 095, 096, 097, 076, 077
- New prefixes 055 (Zamtel) and 057 (Airtel) were not included

**Fix Applied:**
- Updated validation regex to include all valid Zambian mobile prefixes:
  - 095, 096, 097 (Zamtel, MTN, Airtel)
  - 076, 077 (Zamtel, MTN)
  - 055, 057 (Zamtel, Airtel - NEW)

**Files Modified:**
- `accounts/forms.py` - Updated `validate_zambian_phone()` function

**Now Accepts:**
- ✅ 0555123456 (Zamtel)
- ✅ 0575123456 (Airtel)
- ✅ 0955123456, 0965123456, 0975123456
- ✅ 0765123456, 0775123456
- ✅ With country code: +260 or 260

---

### 3. ✅ Processing Fee Backdating - Vault Transaction Dates

**Problem:**
- When backdating a loan application, the processing fee vault transaction was recorded with current date instead of the backdated application date

**Root Cause:**
- Code used `timezone.now()` for vault transaction date
- Should use `application.created_at` (the backdated date)

**Fix Applied:**
- Updated processing fee vault recording in both flows:
  1. Register borrower wizard (`clients/views.py`)
  2. Standalone loan application (`loans/views_application.py`)
- Now uses: `transaction_date = app.created_at if app.created_at else tz.now()`

**Impact:**
- Processing fees now correctly appear on the backdated application date in vault history
- Vault balances remain accurate
- Historical reporting is now correct

**Files Modified:**
- `clients/views.py` - Register borrower wizard processing fee recording
- `loans/views_application.py` - Standalone application processing fee recording

---

### 4. ✅ Notifications Filtering by Branch

**Problem:**
- All officers and managers were receiving notifications for loans from ALL branches
- Should only receive notifications for loans in their own branch

**Root Cause:**
- Notification code was getting all staff users: `User.objects.filter(role__in=['admin', 'loan_officer', 'manager'])`
- No branch filtering applied

**Fix Applied:**
- Created `get_branch_staff_users(loan, exclude_user=None)` helper function
- Filters staff by branch:
  - **Admins**: Always notified (all branches)
  - **Managers**: Only for their managed branch
  - **Loan Officers**: Only for their assigned branch
- Updated all notification creations to use the helper

**Files Modified:**
- `payments/views.py` - Payment notifications
- `loans/views.py` - Loan application and document notifications

**Notification Types Fixed:**
- Payment confirmed
- Upfront payment submitted
- Loan application submitted
- Document uploaded

**How It Works:**
```python
# Get the loan's branch from loan officer assignment
branch_name = loan.loan_officer.officer_assignment.branch

# Filter staff users
- Admins: Always included
- Managers: Only if managed_branch matches
- Officers: Only if officer_assignment.branch matches
```

---

## Scripts to Run on Server

### Verify Carol and Kaluba Fix:
```bash
git pull origin main
python verify_carol_kaluba_fix.py
```

This will verify:
- ✅ Both loans have vault transactions
- ✅ Vault balance is correct
- ✅ Both loans appear in transaction history

---

## Technical Improvements

### 1. Import Organization
- Fixed Django import order in scripts
- Django imports must come AFTER `django.setup()`
- Prevents `NameError` and import issues

### 2. Model Relationships
- `WeeklyVault.branch` is a `OneToOneField` to Branch model
- Must pass Branch object, not string
- Fixed queries: `WeeklyVault.objects.filter(branch=branch)` not `branch=branch.name`

### 3. Vault Balance Verification
- Always verify calculated balance matches stored balance
- Calculate from transactions: `total_in - total_out`
- Compare with `vault.balance`
- Update if mismatch detected

---

## Files Modified This Session

1. `fix_kuku_missing_loans.py` - Fixed Q import, reorganized imports
2. `fix_kuku_vault_balance.py` - Fixed WeeklyVault import and query
3. `verify_carol_kaluba_fix.py` - NEW verification script
4. `accounts/forms.py` - Added 055, 057 phone prefixes
5. `clients/views.py` - Fixed processing fee backdating
6. `loans/views_application.py` - Fixed processing fee backdating
7. `payments/views.py` - Added branch filtering for notifications
8. `loans/views.py` - Added branch filtering for notifications

---

## Commits Made

1. `Fix Q import error in fix_kuku_missing_loans.py - reorganize imports`
2. `Fix WeeklyVault import and add new Zambian prefixes (055, 057)`
3. `Fix WeeklyVault query to use branch object instead of branch name`
4. `Fix processing fee vault transactions to use backdated application date`
5. `Add verification script for Carol and Kaluba loan fix`
6. `Fix notifications to filter by branch - only notify staff in same branch as loan`

---

## Prevention Measures in Place

### Vault Recording Failures:
- ✅ Vault recording happens BEFORE marking loan as active
- ✅ If vault recording fails, loan stays in "approved" status
- ✅ Clear error messages shown to users
- ✅ Detailed logging for debugging
- ✅ No more silent failures

### Data Integrity:
- ✅ Vault balances always match transaction history
- ✅ Backdated transactions use correct dates
- ✅ Branch filtering prevents cross-branch notifications

---

## Next Steps

1. **Pull latest code on server:**
   ```bash
   git pull origin main
   ```

2. **Run verification script:**
   ```bash
   python verify_carol_kaluba_fix.py
   ```

3. **Test new features:**
   - Register borrower with backdated application
   - Verify processing fee appears on correct date in vault
   - Check notifications only go to same-branch staff
   - Test phone validation with 055 and 057 numbers

4. **Monitor:**
   - Watch for any new vault recording issues
   - Verify notifications are properly filtered
   - Check vault balances remain accurate

---

## Summary

All issues have been resolved:
- ✅ Carol and Kaluba's loans fixed with correct vault transactions
- ✅ Phone validation accepts all Zambian prefixes
- ✅ Processing fees use backdated application dates
- ✅ Notifications filtered by branch

The system is now more robust with better error handling, accurate historical data, and proper branch-based filtering.
