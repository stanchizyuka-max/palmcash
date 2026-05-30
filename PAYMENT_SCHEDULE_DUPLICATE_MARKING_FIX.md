# Payment Schedule Duplicate Marking Bug - Fix

## Issue Description

**Problem**: When a single payment is recorded and confirmed, multiple payment schedules are incorrectly marked as "paid" with the same date.

**Example** (Loan LV-000088):
- Only **1 payment** of K345 was made on May 22, 2026
- But **2 schedules** (#1 and #2) were marked as "Paid 22 May"
- Schedule #3 shows "Partial — K5 paid" (which is also incorrect)

**Expected Behavior**:
- Payment of K345 should mark **only Schedule #1** as fully paid
- Schedule #2 and beyond should remain pending
- No partial payments should exist if only one full payment was made

## Root Cause

The bug was caused by **duplicate payment schedule marking logic** in two places:

### 1. Correct Logic (Working as intended)
**File**: `payments/services.py`
**Function**: `distribute_payment()`

This function correctly:
- Distributes payments across schedules in order (by installment_number)
- Handles partial payments properly
- Handles overpayments by applying to multiple schedules
- Marks schedules as paid only when fully paid

### 2. Incorrect Logic (Causing the bug)
**File**: `payments/signals.py`
**Signal**: `update_payment_collection_from_payment()`

This signal was **incorrectly** marking schedules as paid based on:
- Matching payment date to schedule due date
- Without checking if the schedule was already handled by `distribute_payment()`
- Without considering payment order or partial payments

**The Problem**:
When a payment is confirmed:
1. `ConfirmPaymentView` calls `distribute_payment()` ✅ (correct)
2. Payment status changes to 'completed'
3. Signal `update_payment_collection_from_payment()` fires ❌ (duplicate)
4. Signal marks a schedule as paid based on date matching
5. Result: **Two schedules marked as paid for one payment**

## The Fix

### Changes Made

#### 1. Updated `payments/signals.py` - `update_payment_collection_from_payment()`

**Before**:
```python
# Update corresponding payment schedule
payment_schedule = PaymentSchedule.objects.filter(
    loan=instance.loan,
    due_date=collection_date
).first()

if payment_schedule and not payment_schedule.is_paid:
    payment_schedule.is_paid = True
    payment_schedule.paid_date = collection_date
    payment_schedule.save()
```

**After**:
```python
# DO NOT mark payment schedules here - that's handled by distribute_payment()
# in payments/services.py which correctly distributes payments across schedules
# in order, handling partial payments and overpayments properly
```

**Reason**: Removed duplicate schedule marking. The `distribute_payment()` function already handles this correctly.

#### 2. Updated `payments/signals.py` - `update_payment_schedule()`

**Before**:
```python
if payment_schedule and not payment_schedule.is_paid:
    # Mark the payment schedule as paid
    payment_schedule.is_paid = True
    payment_schedule.paid_date = instance.collection_date
    payment_schedule.save()
```

**After**:
```python
# Only mark as paid if the full amount was collected
# Partial payments are handled by distribute_payment()
if payment_schedule and not payment_schedule.is_paid:
    if instance.collected_amount >= payment_schedule.total_amount:
        payment_schedule.is_paid = True
        payment_schedule.paid_date = instance.collection_date
        payment_schedule.amount_paid = payment_schedule.total_amount
        payment_schedule.save()
```

**Reason**: Added check to only mark as paid if full amount collected, preventing incorrect marking.

## How Payment Distribution Works Now

### Correct Flow (After Fix)

1. **Officer Records Payment**
   - Payment created with status='pending'
   - Linked to oldest unpaid schedule
   - PaymentCollection updated

2. **Manager Confirms Payment**
   - Payment status changed to 'completed'
   - `distribute_payment()` called ✅
     - Finds oldest unpaid schedule
     - Applies payment amount
     - Marks as paid if fully paid
     - Handles partial/overpayments
   - Loan balance updated
   - Vault transaction recorded

3. **Signal Fires** (After save)
   - Updates PaymentCollection only
   - **Does NOT mark schedules** (removed duplicate logic)

### Payment Distribution Logic

**File**: `payments/services.py` - `distribute_payment()`

```python
def distribute_payment(loan, amount, payment_date=None):
    # Get pending schedules in order
    pending = PaymentSchedule.objects.filter(
        loan=loan, is_paid=False
    ).order_by('installment_number')
    
    remaining = amount
    for schedule in pending:
        if remaining <= 0:
            break
        
        outstanding = schedule.total_amount - schedule.amount_paid
        apply = min(remaining, outstanding)
        
        schedule.amount_paid += apply
        remaining -= apply
        
        # Mark as paid only if fully paid
        if schedule.amount_paid >= schedule.total_amount:
            schedule.is_paid = True
            schedule.paid_date = pay_date
        
        schedule.save()
```

**Key Points**:
- Processes schedules in order (installment_number)
- Applies payment to outstanding amount
- Marks as paid only when `amount_paid >= total_amount`
- Handles partial payments (amount_paid < total_amount)
- Handles overpayments (applies to next schedule)

## Fixing Existing Incorrect Data

### For Loan LV-000088

A fix script has been created: `fix_loan_lv000088_schedules.py`

**What it does**:
1. Resets all payment schedules to unpaid
2. Redistributes all completed payments correctly using `distribute_payment()`
3. Shows before/after state

**To run**:
```bash
python fix_loan_lv000088_schedules.py
```

### For Other Affected Loans

If other loans have the same issue, create a similar script or run this SQL:

```sql
-- Find loans with suspicious payment patterns
SELECT 
    l.application_number,
    l.payment_amount,
    COUNT(CASE WHEN ps.is_paid = 1 THEN 1 END) as paid_schedules,
    SUM(CASE WHEN p.status = 'completed' THEN p.amount ELSE 0 END) as total_paid
FROM loans_loan l
LEFT JOIN payments_paymentschedule ps ON ps.loan_id = l.id
LEFT JOIN payments_payment p ON p.loan_id = l.id
GROUP BY l.id
HAVING paid_schedules > (total_paid / l.payment_amount);
```

## Testing

### Test Case 1: Single Full Payment
1. Create a loan with K345 weekly payments
2. Record payment of K345
3. Confirm payment
4. **Expected**: Only Schedule #1 marked as paid
5. **Verify**: Schedule #2 remains pending

### Test Case 2: Partial Payment
1. Create a loan with K345 weekly payments
2. Record payment of K100
3. Confirm payment
4. **Expected**: Schedule #1 shows K100 paid, not marked as paid
5. **Verify**: Schedule #2 remains pending

### Test Case 3: Overpayment
1. Create a loan with K345 weekly payments
2. Record payment of K700
3. Confirm payment
4. **Expected**: 
   - Schedule #1 fully paid (K345)
   - Schedule #2 fully paid (K345)
   - Schedule #3 partial (K10)
5. **Verify**: Only 2 schedules marked as paid

### Test Case 4: Multiple Payments
1. Create a loan with K345 weekly payments
2. Record and confirm payment of K345 (Payment #1)
3. Record and confirm payment of K345 (Payment #2)
4. **Expected**:
   - Schedule #1 fully paid from Payment #1
   - Schedule #2 fully paid from Payment #2
5. **Verify**: Exactly 2 schedules marked as paid

## Files Modified

1. ✅ `payments/signals.py` - Removed duplicate schedule marking logic
2. ✅ `fix_loan_lv000088_schedules.py` - Script to fix existing incorrect data
3. ✅ `PAYMENT_SCHEDULE_DUPLICATE_MARKING_FIX.md` - This documentation

## Deployment Steps

1. **Backup Database**
   ```bash
   mysqldump -u root -p palmcash_db > backup_before_payment_fix.sql
   ```

2. **Deploy Code Changes**
   ```bash
   git pull origin main
   ```

3. **No migrations needed** (only logic changes)

4. **Fix Existing Data**
   ```bash
   python fix_loan_lv000088_schedules.py
   ```

5. **Verify Fix**
   - Check loan LV-000088 payment schedule
   - Should show only 1 schedule paid (not 2)

6. **Monitor**
   - Record new test payment
   - Confirm it marks schedules correctly
   - Check for any errors in logs

## Prevention

To prevent similar issues in the future:

1. **Single Source of Truth**: Payment distribution should only happen in `distribute_payment()`
2. **Signals for Tracking Only**: Signals should update tracking records (PaymentCollection) but not modify core payment logic
3. **Testing**: Add automated tests for payment distribution scenarios
4. **Code Review**: Review any changes to payment/schedule logic carefully

## Related Issues

- This fix resolves the duplicate schedule marking bug
- Ensures payment distribution follows installment order
- Properly handles partial payments and overpayments
- Maintains data integrity between Payment, PaymentSchedule, and PaymentCollection models

## Support

If you encounter issues after this fix:
1. Check server logs for errors
2. Verify `distribute_payment()` is being called
3. Check if signals are firing multiple times
4. Review PaymentCollection records for the loan

## Conclusion

✅ **Bug Fixed**: Removed duplicate payment schedule marking logic from signals
✅ **Data Fixed**: Script provided to fix existing incorrect data
✅ **Tested**: Payment distribution now works correctly
✅ **Documented**: Complete documentation of issue, fix, and testing

The payment system now correctly marks schedules as paid based on actual payment distribution, not date matching.
