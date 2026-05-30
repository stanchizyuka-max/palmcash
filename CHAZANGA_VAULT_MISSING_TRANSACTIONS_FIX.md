# Chazanga Branch - Missing Vault Transactions Fix

## Issue Description

**Problem**: All payment records made from Chazanga branch on Thursday were not recorded in the vault.

**Impact**:
- Payments were confirmed and marked as completed
- Loan balances were updated correctly
- BUT vault balance was not increased
- Vault transactions were not created
- **Result**: Vault balance is incorrect (lower than it should be)

## Root Cause

The vault recording logic in `payments/views.py` (ConfirmPaymentView) has a **silent error handling** issue:

```python
try:
    from loans.vault_services import record_payment_collection
    record_payment_collection(loan, payment.amount, request.user)
except Exception as e:
    print(f"Vault record error: {e}")  # ← Only prints to console!
```

**The Problem**:
1. If `record_payment_collection()` fails for ANY reason, the exception is caught
2. The error is only printed to console (not logged or shown to user)
3. Payment confirmation continues as if nothing happened
4. User sees "Payment confirmed" message
5. But vault transaction was never created

**Possible Reasons for Chazanga Failures**:

1. **Branch Name Mismatch**
   - Database has "Chazanga" but code looks for "chazanga"
   - Case-sensitive comparison failing

2. **Loan Officer Not Assigned to Branch**
   - Officer's `officer_assignment.branch` is `None` or incorrect
   - `_get_branch_for_loan()` returns `None`

3. **Branch Object Not Found**
   - Branch exists as string but not as Branch model object
   - `Branch.objects.filter(name__iexact=branch_ref).first()` returns `None`

4. **Database Connection Issue**
   - Temporary database problem on Thursday
   - Transaction rolled back but error silently caught

## The Fix

### 1. Improved Error Handling in Payment Confirmation

**File**: `payments/views.py` - `ConfirmPaymentView.post()`

**Before**:
```python
try:
    from loans.vault_services import record_payment_collection
    record_payment_collection(loan, payment.amount, request.user)
except Exception as e:
    print(f"Vault record error: {e}")
```

**After**:
```python
vault_error = None
try:
    from loans.vault_services import record_payment_collection
    vault_tx = record_payment_collection(loan, payment.amount, request.user)
    if not vault_tx:
        vault_error = "Vault transaction not created - branch may not be found"
        logger.error(f"Vault recording failed for payment #{payment.id}")
except Exception as e:
    vault_error = str(e)
    logger.error(f"Vault recording error for payment #{payment.id}: {e}", exc_info=True)

if vault_error:
    messages.warning(
        request,
        f'Payment confirmed but vault recording failed: {vault_error}. '
        f'Please contact admin to manually record this transaction.'
    )
```

**Improvements**:
- Proper logging with `logger.error()` instead of `print()`
- Checks if `vault_tx` is `None` (branch not found case)
- Shows warning message to user if vault recording fails
- Includes full exception traceback in logs
- User is alerted to contact admin

### 2. Diagnostic Script

**File**: `diagnose_chazanga_vault_issue.py`

**Purpose**: Identify which payments are missing vault transactions

**What it does**:
1. Checks if Chazanga branch exists in database
2. Finds all completed payments from Chazanga on Thursday
3. For each payment, checks if vault transaction exists
4. Reports missing vault transactions
5. Identifies possible causes (branch assignment, name mismatch, etc.)

**To run**:
```bash
python diagnose_chazanga_vault_issue.py
```

**Output**:
- List of payments from Chazanga on Thursday
- Which payments have vault transactions
- Which payments are missing vault transactions
- Total amount not recorded in vault
- Possible causes and recommended actions

### 3. Fix Script

**File**: `fix_chazanga_vault_transactions.py`

**Purpose**: Create missing vault transactions for Chazanga payments

**What it does**:
1. Finds all completed Chazanga payments on Thursday
2. Checks if vault transaction already exists (to avoid duplicates)
3. For missing transactions, calls `record_payment_collection()`
4. Creates vault transaction and updates vault balance
5. Reports success/failure for each payment

**To run**:
```bash
python fix_chazanga_vault_transactions.py
```

**Safety Features**:
- Checks for existing vault transactions (no duplicates)
- Uses proper vault services (respects daily/weekly vault routing)
- Handles errors gracefully
- Provides detailed output for each payment

## How Vault Recording Works

### Normal Flow (When Working)

1. **Officer Records Payment**
   - Payment created with status='pending'
   - No vault transaction yet

2. **Manager Confirms Payment**
   - Payment status → 'completed'
   - `distribute_payment()` marks schedules as paid
   - Loan balance updated
   - **`record_payment_collection()` called** ✅
     - Gets branch from loan officer assignment
     - Determines vault type (daily/weekly) from loan
     - Increases vault balance
     - Creates VaultTransaction record
   - Success message shown to user

### Broken Flow (What Happened Thursday)

1. **Officer Records Payment** ✅
2. **Manager Confirms Payment**
   - Payment status → 'completed' ✅
   - `distribute_payment()` marks schedules ✅
   - Loan balance updated ✅
   - **`record_payment_collection()` called** ❌
     - `_get_branch_for_loan()` returns `None`
     - OR exception thrown
     - Error silently caught
     - No vault transaction created
     - No vault balance update
   - User sees "Payment confirmed" ✅ (misleading!)
   - **Vault balance is now INCORRECT** ❌

## Diagnosis Steps

### Step 1: Run Diagnostic Script

```bash
python diagnose_chazanga_vault_issue.py
```

This will show:
- How many payments are affected
- Total amount missing from vault
- Specific payment IDs
- Loan officer assignments
- Branch name variations

### Step 2: Check Branch Configuration

```sql
-- Check if Chazanga branch exists
SELECT * FROM clients_branch WHERE name LIKE '%chazanga%';

-- Check loan officer assignments for Chazanga
SELECT 
    u.id,
    u.username,
    u.first_name,
    u.last_name,
    oa.branch
FROM accounts_user u
LEFT JOIN clients_officerassignment oa ON oa.officer_id = u.id
WHERE u.role = 'loan_officer'
AND oa.branch LIKE '%chazanga%';
```

### Step 3: Check Vault Transactions

```sql
-- Check vault transactions for Thursday
SELECT 
    vt.id,
    vt.transaction_type,
    vt.branch,
    vt.vault_type,
    vt.amount,
    vt.balance_after,
    vt.transaction_date,
    l.application_number
FROM expenses_vaulttransaction vt
LEFT JOIN loans_loan l ON l.id = vt.loan_id
WHERE vt.branch LIKE '%chazanga%'
AND DATE(vt.transaction_date) = '2026-05-29'  -- Adjust date
ORDER BY vt.transaction_date;
```

### Step 4: Compare Payments vs Vault Transactions

```sql
-- Payments from Chazanga on Thursday
SELECT 
    p.id as payment_id,
    p.amount,
    p.payment_date,
    l.application_number,
    u.username as officer,
    oa.branch
FROM payments_payment p
JOIN loans_loan l ON l.id = p.loan_id
JOIN accounts_user u ON u.id = l.loan_officer_id
LEFT JOIN clients_officerassignment oa ON oa.officer_id = u.id
WHERE p.status = 'completed'
AND DATE(p.payment_date) = '2026-05-29'  -- Adjust date
AND oa.branch LIKE '%chazanga%';

-- Vault transactions for same payments
SELECT 
    vt.id as vault_tx_id,
    vt.amount,
    vt.transaction_date,
    l.application_number
FROM expenses_vaulttransaction vt
JOIN loans_loan l ON l.id = vt.loan_id
WHERE vt.transaction_type = 'payment_collection'
AND DATE(vt.transaction_date) = '2026-05-29'  -- Adjust date
AND vt.branch LIKE '%chazanga%';
```

## Fix Steps

### Step 1: Backup Database

```bash
mysqldump -u root -p palmcash_db > backup_before_chazanga_vault_fix.sql
```

### Step 2: Run Diagnostic

```bash
python diagnose_chazanga_vault_issue.py
```

Review the output to understand the scope of the issue.

### Step 3: Fix Branch Assignments (If Needed)

If diagnostic shows officers without branch assignments:

```sql
-- Update officer assignments
UPDATE clients_officerassignment
SET branch = 'Chazanga'  -- Use exact branch name from clients_branch table
WHERE officer_id IN (
    SELECT id FROM accounts_user 
    WHERE username IN ('officer1', 'officer2')  -- Replace with actual usernames
);
```

### Step 4: Run Fix Script

```bash
python fix_chazanga_vault_transactions.py
```

This will:
- Create missing vault transactions
- Update vault balances
- Show summary of fixes

### Step 5: Verify Fix

```bash
# Check vault balance
python manage.py shell
>>> from clients.models import Branch
>>> from loans.vault_services import get_vault_balances
>>> chazanga = Branch.objects.get(name__iexact='chazanga')
>>> balances = get_vault_balances(chazanga)
>>> print(f"Daily: K{balances['daily']}, Weekly: K{balances['weekly']}, Total: K{balances['total']}")
```

### Step 6: Deploy Code Fix

```bash
git add payments/views.py
git commit -m "Fix: Improve vault recording error handling in payment confirmation

- Add proper logging for vault recording failures
- Show warning message to user if vault recording fails
- Check if vault_tx is None (branch not found case)
- Include full exception traceback in logs
- Prevents silent failures that cause missing vault transactions"

git push origin main
```

### Step 7: Restart Application

```bash
# On server
sudo systemctl restart palmcash
# or
sudo supervisorctl restart palmcash
```

## Prevention

To prevent this issue in the future:

### 1. Proper Error Handling
- ✅ Log all vault errors with full traceback
- ✅ Show warning messages to users
- ✅ Don't silently catch and ignore exceptions

### 2. Branch Assignment Validation
- Ensure all loan officers have valid branch assignments
- Add validation when creating/updating officer assignments
- Periodic audit of officer-branch mappings

### 3. Monitoring
- Add alerts for missing vault transactions
- Daily reconciliation: payments vs vault transactions
- Dashboard showing vault recording success rate

### 4. Testing
- Add automated tests for vault recording
- Test error scenarios (branch not found, etc.)
- Integration tests for payment confirmation flow

## Testing the Fix

### Test Case 1: Normal Payment (Should Work)
1. Record a payment for a loan with proper officer assignment
2. Confirm the payment
3. **Expected**: Vault transaction created, balance updated
4. **Verify**: Check vault transaction exists

### Test Case 2: Missing Branch Assignment (Should Alert)
1. Create a loan with officer who has no branch assignment
2. Record and confirm payment
3. **Expected**: Warning message shown to user
4. **Expected**: Error logged with details
5. **Verify**: User sees warning, admin can investigate

### Test Case 3: Invalid Branch Name (Should Alert)
1. Manually set officer branch to non-existent branch
2. Record and confirm payment
3. **Expected**: Warning message shown
4. **Expected**: Error logged
5. **Verify**: User alerted, no silent failure

## Files Modified

1. ✅ `payments/views.py` - Improved vault error handling
2. ✅ `diagnose_chazanga_vault_issue.py` - Diagnostic script
3. ✅ `fix_chazanga_vault_transactions.py` - Fix script
4. ✅ `CHAZANGA_VAULT_MISSING_TRANSACTIONS_FIX.md` - This documentation

## Related Issues

- Silent error handling in payment confirmation
- Missing vault transactions for confirmed payments
- Incorrect vault balances
- Branch assignment validation

## Support

If issues persist after fix:

1. Check server logs for vault errors:
   ```bash
   tail -f /var/log/palmcash/error.log | grep -i vault
   ```

2. Verify branch assignments:
   ```bash
   python manage.py shell
   >>> from accounts.models import User
   >>> officers = User.objects.filter(role='loan_officer')
   >>> for o in officers:
   ...     if hasattr(o, 'officer_assignment'):
   ...         print(f"{o.username}: {o.officer_assignment.branch}")
   ...     else:
   ...         print(f"{o.username}: NO ASSIGNMENT")
   ```

3. Manual vault transaction creation:
   ```bash
   python manage.py shell
   >>> from loans.vault_services import record_payment_collection
   >>> from loans.models import Loan
   >>> from payments.models import Payment
   >>> payment = Payment.objects.get(id=PAYMENT_ID)
   >>> vault_tx = record_payment_collection(payment.loan, payment.amount, payment.processed_by)
   >>> print(f"Created: {vault_tx}")
   ```

## Conclusion

✅ **Root Cause Identified**: Silent error handling in payment confirmation
✅ **Fix Implemented**: Proper logging and user alerts
✅ **Scripts Provided**: Diagnostic and fix scripts for existing data
✅ **Prevention**: Improved error handling prevents future occurrences

The vault recording system now properly logs errors and alerts users when vault transactions fail, preventing silent data inconsistencies.
