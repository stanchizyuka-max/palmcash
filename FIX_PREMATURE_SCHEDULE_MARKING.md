# Fix Premature Schedule Marking Issue

## Problem
Payment schedules were being marked as "Paid" immediately when payments were recorded, even though the payments had status "Pending" and were awaiting manager confirmation.

**Example:**
- Payment PAY-000138: Status = "Pending" (awaiting manager approval)
- Related Schedule (Installment 3): Status = "Paid" ✗ (WRONG!)

This created a serious inconsistency where:
1. Officer records payment → schedule marked as paid
2. Manager rejects payment → schedule still shows as paid
3. System thinks payment is complete when it's not

## Root Cause

### The Bug Chain:
1. **Payment Creation** (lines 238 & 955 in `payments/views.py`):
   - Payment created with `status='pending'` ✓
   - PaymentCollection immediately marked as `status='completed'` ✗

2. **Signal Trigger** (line 36 in `payments/signals.py`):
   - Signal detects `PaymentCollection.status == 'completed'`
   - Automatically marks payment schedule as paid ✗

3. **Result**:
   - Schedule marked as paid BEFORE manager confirms payment
   - If manager rejects, schedule stays paid (inconsistent state)

## The Fix

### Changed Workflow:

**Before:**
```
Officer records payment
  ↓
Payment: status='pending'
PaymentCollection: status='completed' ✗
  ↓
Signal fires → Schedule marked as PAID ✗
  ↓
Manager confirms/rejects
```

**After:**
```
Officer records payment
  ↓
Payment: status='pending'
PaymentCollection: status='scheduled' ✓
  ↓
No signal fires → Schedule stays UNPAID ✓
  ↓
Manager confirms payment
  ↓
PaymentCollection: status='completed'
  ↓
Signal fires → Schedule marked as PAID ✓
```

### Code Changes:

1. **Regular Payment Creation** (`payments/views.py` line ~238):
   - Removed: `collection.status = 'completed'`
   - Added comment: "Keep status as 'scheduled' until payment is confirmed by manager"

2. **Bulk Collection** (`payments/views.py` line ~955):
   - Removed: `collection.status = 'completed'`
   - Added comment: "Keep status as 'scheduled' until payment is confirmed by manager"

3. **Payment Confirmation** (`payments/views.py` line ~301):
   - Added logic to mark PaymentCollection as 'completed' when manager confirms
   - This triggers the signal to mark schedule as paid

## Deployment Steps

### 1. Deploy the Fix
```bash
cd ~/www/palmcashloans.site
git pull origin main
find . -name "*.pyc" -delete
sudo systemctl restart gunicorn
```

### 2. Fix Existing Payment PAY-000138
```bash
cd ~/www/palmcashloans.site
python fix_payment_138.py
```

Expected output:
```
======================================================================
FIXING PAYMENT PAY-000138
======================================================================

✓ Found payment: PAY-000138
  Status: pending
  Amount: K140
  Loan: LV-000018
  Borrower: Gladys Banda

✓ Found linked schedule:
  Installment: 3
  Due Date: 2026-05-27
  Total Amount: K138
  Amount Paid: K140
  Is Paid: True
  Paid Date: 2026-05-20

⚠ ISSUE DETECTED: Payment is PENDING but schedule is marked as PAID

Fixing...

✓ Schedule fixed:
  Is Paid: False
  Paid Date: None
  Amount Paid: K0

✓ PaymentCollection reverted:
  Status: scheduled

======================================================================
✓ SUCCESS! Payment schedule reverted to unpaid
======================================================================

The schedule will be marked as paid when the manager confirms the payment.
```

## What This Fixes

### For New Payments (After Deployment):
1. ✅ Officer records payment → Payment status = "Pending", Schedule status = "Unpaid"
2. ✅ Manager confirms payment → Payment status = "Completed", Schedule status = "Paid"
3. ✅ Manager rejects payment → Payment status = "Failed", Schedule status = "Unpaid"

### For Existing Payment PAY-000138:
1. ✅ Schedule reverted to "Unpaid"
2. ✅ PaymentCollection reverted to "Scheduled"
3. ✅ When manager confirms PAY-000138, schedule will be marked as paid
4. ✅ If manager rejects PAY-000138, schedule stays unpaid

## Impact

**Affected Areas:**
- Regular payment creation (`/payments/make/<loan_id>/`)
- Bulk collection (`/payments/bulk-collection/group/<group_id>/`)

**Not Affected:**
- Default collection (already had correct logic)
- Multi-schedule payments (different workflow)

## Testing

After deployment, test the workflow:

1. **Record a payment** as loan officer
   - ✓ Payment should show status "Pending"
   - ✓ Schedule should show status "Unpaid"

2. **Confirm the payment** as manager
   - ✓ Payment should change to "Completed"
   - ✓ Schedule should change to "Paid"

3. **Record another payment** as loan officer
   - ✓ Payment should show status "Pending"
   - ✓ Schedule should show status "Unpaid"

4. **Reject the payment** as manager
   - ✓ Payment should change to "Failed"
   - ✓ Schedule should stay "Unpaid"

## Related Fixes
This is part of the payment workflow improvements:
1. ✅ Payment rejection reverts schedules and loan balance
2. ✅ Failed payments excluded from totals
3. ✅ Schedules only marked as paid after manager confirmation (this fix)
