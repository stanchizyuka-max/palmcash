# Fix Overdue Payment Status

## Problem
When a borrower makes a payment and it's confirmed by staff, the payment status is updated to 'completed', but the associated PaymentSchedule's `is_paid` field may not be updated. This causes the dashboard to still show the payment as overdue even though it has been paid.

## Solution
A management command has been created to fix this issue: `fix_overdue_payments`

## How to Run on PythonAnywhere

### Step 1: Pull the latest code
```bash
cd /home/stan13/palmcash/palmcash
git pull origin main
```

### Step 2: Run the fix command

**Option A: Fix for a specific borrower**
```bash
python manage.py fix_overdue_payments --borrower "jane"
```

**Option B: Fix for a specific loan**
```bash
python manage.py fix_overdue_payments --loan "LA-08E07951"
```

**Option C: Fix all overdue payments**
```bash
python manage.py fix_overdue_payments
```

### Step 3: Reload the web app
After running the command, reload your web app from the PythonAnywhere dashboard to see the changes reflected.

## What the Command Does
1. Finds all completed payments that have an associated PaymentSchedule
2. Marks the PaymentSchedule as `is_paid = True` if it hasn't been marked yet
3. Sets the `paid_date` to the payment date
4. Checks for overdue payments that have completed payments and marks them as paid

## Example Output
```
Filtering for borrower: jane phiri
✓ Fixed: Payment PAY-000002 for LA-08E07951 (Schedule #1)
✓ Successfully fixed 1 payment schedule(s)
```

## Verification
After running the command:
1. Log in as the borrower (jane phiri)
2. Go to the dashboard
3. The "Overdue Payments" alert should no longer appear
4. The payment schedule should show as paid

## Notes
- This command is safe to run multiple times - it only updates schedules that are marked as unpaid
- It only affects payments with status 'completed'
- It preserves all other payment data
