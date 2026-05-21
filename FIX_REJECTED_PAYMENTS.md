# Fix Rejected Payments Issue

## Problem
When a payment is rejected (status changed to 'failed'), the payment schedule remains marked as "Paid" instead of reverting to "Unpaid". This causes inconsistency where failed payments show schedules as paid.

**Example:** Payment PAY-000107 has status "Failed" but its schedule shows as "Paid"

## Fix Applied
Modified `payments/views.py` in the `RejectPaymentView` to:
1. Revert payment schedule: `is_paid = False`, `paid_date = None`
2. Reduce `amount_paid` on the schedule
3. Revert loan balance: reduce `amount_paid`, increase `balance_remaining`

## Deployment Steps

### 1. Deploy the Fix
```bash
cd ~/www/palmcashloans.site
git pull origin main
find . -name "*.pyc" -delete
sudo systemctl restart gunicorn
```

### 2. Fix Existing Payment PAY-000107
```bash
cd ~/www/palmcashloans.site
python fix_payment_107.py
```

Expected output:
```
======================================================================
FIXING PAYMENT PAY-000107
======================================================================

✓ Found payment: PAY-000107
  Status: failed
  Amount: K50
  Loan: LV-000050
  Borrower: ruth chisi

✓ Found linked schedule:
  Installment: 1
  Due Date: 2026-05-19
  Total Amount: K207
  Amount Paid: K50
  Is Paid: True
  Paid Date: 2026-05-19

⚠ ISSUE DETECTED: Payment is FAILED but schedule is marked as PAID

Fixing...

✓ Schedule fixed:
  Is Paid: False
  Paid Date: None
  Amount Paid: K0

✓ Loan balance updated:
  Amount Paid: K[updated amount]
  Balance Remaining: K[updated amount]

======================================================================
✓ SUCCESS! Payment schedule reverted to unpaid
======================================================================
```

## What This Fixes

**Before:**
- Payment rejected → status = 'failed'
- Schedule still shows as "Paid"
- Loan balance not adjusted

**After:**
- Payment rejected → status = 'failed'
- Schedule reverted to "Unpaid"
- Loan balance corrected (amount_paid reduced, balance_remaining increased)

## Future Behavior
Going forward, when a manager/admin rejects a payment:
1. Payment status changes to 'failed'
2. Payment schedule automatically reverts to unpaid
3. Loan balance automatically adjusts
4. Borrower can make a new payment for that schedule
