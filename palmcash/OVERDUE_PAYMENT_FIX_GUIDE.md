# Fix Overdue Payment Status - Complete Guide

## Problem
Jane Phiri made an overdue payment but the dashboard still shows the overdue alert. This happens when:
1. Payment is submitted but not yet confirmed by staff (status = 'pending')
2. Payment is confirmed but the PaymentSchedule.is_paid field wasn't updated

## Solution Steps

### Step 1: Check Current Payment Status

SSH into PythonAnywhere and run the diagnostic command:

```bash
cd /home/stan13/palmcash/palmcash
python manage.py diagnose_payments --borrower "jane"
```

This will show:
- All payment schedules for jane phiri
- All payments made
- Which payments are linked to schedules
- Which schedules are marked as paid/unpaid

**Expected Output Example:**
```
============================================================
BORROWER: jane phiri (janephiri)
============================================================

────────────────────────────────────────────────────────────
LOAN: LA-08E07951 - Active
Amount: K4000
────────────────────────────────────────────────────────────

PAYMENT SCHEDULES (4):
  Schedule #1: K1000.00 due 2026-01-22 - ✗ UNPAID
  Schedule #2: K1000.00 due 2026-01-29 - ✗ UNPAID
  Schedule #3: K1000.00 due 2026-02-05 - ✗ UNPAID
  Schedule #4: K1000.00 due 2026-02-12 - ✗ UNPAID

PAYMENTS (1):
  PAY-000001: K1000.00 (Pending) on 2026-01-22 → NO SCHEDULE LINKED

ANALYSIS:
  Found 4 unpaid schedule(s)
  ⚠ Found 1 payment(s) not linked to any schedule
    - PAY-000001: K1000.00 (Pending)
```

### Step 2: Confirm the Payment (If Pending)

If the payment status is "Pending", a staff member needs to confirm it:

1. Log in to the admin panel as a loan officer or admin
2. Go to Payments → Pending Payments
3. Find jane phiri's payment
4. Click "Confirm Payment"
5. The system will automatically:
   - Mark the payment as 'completed'
   - Link it to the oldest unpaid schedule
   - Mark that schedule as paid
   - Update the loan balance

### Step 3: Run the Fix Command (If Payment is Confirmed but Schedule Not Updated)

If the diagnostic shows the payment is "Completed" but the schedule is still "UNPAID", run:

```bash
python manage.py fix_overdue_payments --borrower "jane"
```

**Expected Output:**
```
Filtering for borrower: jane phiri
✓ Fixed: Payment PAY-000001 for LA-08E07951 (Schedule #1)
✓ Successfully fixed 1 payment schedule(s)
```

### Step 4: Reload the Web App

After running the fix command, reload the web app from PythonAnywhere dashboard:

1. Go to https://www.pythonanywhere.com/
2. Click on your web app
3. Click "Reload" button
4. Wait for it to complete

### Step 5: Verify the Fix

Log in as jane phiri and check:
1. Dashboard should no longer show "Overdue Payments" alert
2. The payment schedule should show as "Paid"
3. Next payment due should be displayed instead

## Troubleshooting

### If diagnostic shows payment is "Pending"
→ A staff member needs to confirm the payment in the admin panel

### If diagnostic shows payment is "Completed" but schedule is "UNPAID"
→ Run the fix command: `python manage.py fix_overdue_payments --borrower "jane"`

### If diagnostic shows payment is "NO SCHEDULE LINKED"
→ The payment wasn't auto-linked. Run the fix command to link it to the oldest unpaid schedule

### If the issue persists after fix
→ Check if there are multiple loans for jane phiri. Run diagnostic for each loan:
```bash
python manage.py diagnose_payments --loan "LA-08E07951"
```

## Prevention

To prevent this issue in the future:
1. Ensure staff confirms all pending payments promptly
2. The system now auto-links payments to the oldest unpaid schedule when confirmed
3. Run the fix command periodically to catch any missed updates

## Commands Reference

```bash
# Diagnose a specific borrower
python manage.py diagnose_payments --borrower "jane"

# Diagnose a specific loan
python manage.py diagnose_payments --loan "LA-08E07951"

# Fix payments for a specific borrower
python manage.py fix_overdue_payments --borrower "jane"

# Fix payments for a specific loan
python manage.py fix_overdue_payments --loan "LA-08E07951"

# Fix all overdue payments in the system
python manage.py fix_overdue_payments
```

