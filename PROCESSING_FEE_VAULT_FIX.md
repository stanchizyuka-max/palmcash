# Processing Fee Vault Recording - WORKFLOW FIX

## Problem Description

Processing fees were being recorded in the vault at the **wrong step** in the workflow:

**OLD (INCORRECT) WORKFLOW:**
1. Loan officer records processing fee → ❌ **Vault transaction created immediately**
2. Manager verifies processing fee → Nothing happens in vault

**NEW (CORRECT) WORKFLOW:**
1. Loan officer records processing fee → ✓ **No vault transaction yet**
2. Manager verifies processing fee → ✓ **Vault transaction created here**

## Why This Matters

The manager verification step is a control mechanism to ensure:
- The processing fee amount is correct
- The fee was actually collected from the borrower
- The transaction is legitimate

Recording the fee in the vault before manager verification bypasses this control.

## Root Causes Fixed

### Issue 1: Branch Object Type Error
**File:** `loans/views_application.py` (RecordProcessingFeeView)

**Bug:** Branch object was incorrectly converted to string, causing vault recording to fail silently.

**Fix:** Get branch object directly without string conversion.

### Issue 2: Wrong Workflow Step
**File:** `loans/views_application.py`

**Bug:** Vault transaction was created in `RecordProcessingFeeView` (officer step) instead of `VerifyProcessingFeeView` (manager step).

**Fix:** 
- Removed vault recording from `RecordProcessingFeeView`
- Added vault recording to `VerifyProcessingFeeView`

## The Fixes

### 1. RecordProcessingFeeView (Loan Officer)
**Changed:** Removed all vault recording logic. Now only saves the fee amount to the application.

```python
# Officer records the fee amount only
app.processing_fee = fee
app.processing_fee_recorded_by = request.user
app.processing_fee_verified = False
app.save()
# NO vault transaction created yet
```

### 2. VerifyProcessingFeeView (Manager)
**Changed:** Added vault recording logic. Now creates vault transaction when manager verifies.

```python
# Manager verifies and vault transaction is created
app.processing_fee_verified = True
app.processing_fee_verified_by = request.user
app.save()

# NOW create the vault transaction
vault.balance += app.processing_fee
VaultTransaction.objects.create(...)
```

## Impact

- **All NEW processing fees** will follow the correct workflow ✓
- **Existing unverified fees** that were prematurely recorded in the vault need cleanup

## How to Fix Existing Data

### Step 1: Clean up premature vault transactions
Run this script to remove vault transactions for fees that haven't been verified yet:

```bash
python cleanup_old_processing_fee_transactions.py
```

This will:
1. Find all processing fee vault transactions
2. Check if the fee has been verified by a manager
3. Remove transactions for unverified fees (they'll be re-created when manager verifies)
4. Keep transactions for verified fees

### Step 2: Manager re-verifies unverified fees
After cleanup, managers should:
1. Go to pending loan applications
2. Verify any processing fees that are marked as unverified
3. This will create the vault transactions at the correct step

## Verification

After the fix:

1. **Test the workflow:**
   - Loan officer records a processing fee
   - Check vault - fee should NOT appear yet ✓
   - Manager verifies the fee
   - Check vault - fee should NOW appear ✓

2. **Check existing data:**
   - Run `cleanup_old_processing_fee_transactions.py`
   - Verify vault balances are correct

## Example

**Scenario:** K200 processing fee for application LA-12345

**OLD Workflow:**
- Officer records K200 → Vault shows +K200 immediately ❌
- Manager verifies → Nothing changes in vault

**NEW Workflow:**
- Officer records K200 → Vault unchanged ✓
- Manager verifies → Vault shows +K200 ✓

## Files Modified

1. `loans/views_application.py` - Fixed workflow (vault recording moved to manager verification)
2. `cleanup_old_processing_fee_transactions.py` - Script to clean up premature transactions (NEW)
3. `PROCESSING_FEE_VAULT_FIX.md` - Updated documentation

## Status

✅ **WORKFLOW FIXED** - Processing fees now recorded at correct step (manager verification)
⚠️ **ACTION REQUIRED** - Run `cleanup_old_processing_fee_transactions.py` to clean up old data
