# Pending Approvals Not Showing - Troubleshooting Guide

## Problem
The pending approvals page shows 0 pending security deposits even though clients have sent upfront payments.

## Root Cause Analysis

The pending approvals page queries for security deposits with these conditions:
```python
pending_deposits = SecurityDeposit.objects.filter(
    is_verified=False,
    loan__loan_officer__officer_assignment__branch=branch.name
).order_by('-payment_date')
```

For deposits to show, ALL of these must be true:
1. ✓ SecurityDeposit record exists
2. ✓ SecurityDeposit.is_verified = False
3. ✓ Loan has a loan_officer assigned
4. ✓ Loan officer has an OfficerAssignment record
5. ✓ OfficerAssignment.branch matches manager's branch

If ANY of these are missing, the deposit won't appear.

## How to Diagnose

### Step 1: SSH into PythonAnywhere
```bash
ssh stan13@ssh.pythonanywhere.com
cd ~/palmcash/palmcash
```

### Step 2: Run the diagnostic script
```bash
python manage.py shell < ../check_pending_approvals.py
```

This will show:
- Total SecurityDeposit records
- How many are pending vs verified
- Loans with upfront payments
- Officer assignments
- Manager branches
- Pending deposits for each manager

### Step 3: Analyze the output

**If you see "Pending (is_verified=False): 0":**
- Either no deposits were created, or they're all marked as verified
- Check if loans are being approved
- Check if upfront payments are being recorded

**If you see "Total SecurityDeposit records: 0":**
- Deposits aren't being created when loans are approved
- The signal handler might not be firing
- Check the loans/signals.py file

**If you see "Manager has NO BRANCH ASSIGNED":**
- The manager user doesn't have a managed_branch
- Assign the manager to a branch in Django admin

**If you see "Officers show no branch assignments":**
- OfficerAssignment records don't exist
- Create them in Django admin or via management command

## Common Fixes

### Fix 1: Update verified deposits to pending
If deposits exist but are marked as verified:
```bash
python manage.py shell
from loans.models import SecurityDeposit
SecurityDeposit.objects.filter(is_verified=True).update(is_verified=False)
exit()
```

### Fix 2: Assign manager to branch
In Django admin:
1. Go to Accounts → Users
2. Find the manager user
3. Set "Managed Branch" to the appropriate branch
4. Save

### Fix 3: Create officer assignments
In Django admin:
1. Go to Clients → Officer Assignments
2. For each loan officer, create an assignment
3. Set the branch to match the manager's branch

### Fix 4: Recreate security deposits
If deposits don't exist:
```bash
python manage.py shell
from loans.models import Loan, SecurityDeposit
from decimal import Decimal

# For each approved loan without a deposit
for loan in Loan.objects.filter(status='approved'):
    if not hasattr(loan, 'security_deposit'):
        required = loan.principal_amount * Decimal('0.10')
        SecurityDeposit.objects.create(
            loan=loan,
            required_amount=required,
            paid_amount=loan.upfront_payment_paid or Decimal('0'),
            payment_date=loan.upfront_payment_date,
            is_verified=loan.upfront_payment_verified
        )
exit()
```

## After Applying Fixes

1. **Pull changes on PythonAnywhere:**
   ```bash
   cd ~/palmcash
   git pull
   ```

2. **Reload the web app:**
   - Go to https://www.pythonanywhere.com
   - Click Web tab
   - Click the green Reload button

3. **Test the page:**
   - Go to /dashboard/pending-approvals/
   - Pending deposits should now appear

## Related Code Files

- **View**: `palmcash/dashboard/views.py::pending_approvals()`
- **Template**: `palmcash/dashboard/templates/dashboard/pending_approvals.html`
- **Model**: `palmcash/loans/models.py::SecurityDeposit`
- **Signal**: `palmcash/loans/signals.py::create_security_deposit()`
- **Diagnostic**: `palmcash/check_pending_approvals.py`

## Still Not Working?

If the issue persists after trying these fixes:

1. Check the error log:
   ```bash
   tail -100 /var/log/pythonanywhere.com/stan13_pythonanywhere_com_wsgi.error.log
   ```

2. Check the database directly:
   ```bash
   python manage.py dbshell
   SELECT * FROM loans_securitydeposit;
   SELECT * FROM loans_loan WHERE upfront_payment_paid > 0;
   ```

3. Check if the signal is firing:
   - Add a print statement to `loans/signals.py`
   - Approve a new loan
   - Check the error log for the print output

4. Contact support with:
   - Output from the diagnostic script
   - Error log entries
   - Database query results
