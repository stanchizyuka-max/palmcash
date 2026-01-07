# Debug: Pending Approvals Not Showing

## Issue
The pending approvals page shows 0 pending security deposits even though a client sent an upfront payment.

## Possible Causes

### 1. SecurityDeposit Not Created
The SecurityDeposit record might not be created when the loan is approved.

**Check:**
```bash
python manage.py shell
from loans.models import Loan, SecurityDeposit
# Check if any loans have security deposits
loans = Loan.objects.filter(status='approved')
print(f"Approved loans: {loans.count()}")
for loan in loans:
    try:
        deposit = loan.security_deposit
        print(f"Loan {loan.id}: Has deposit - {deposit.id}, is_verified={deposit.is_verified}")
    except:
        print(f"Loan {loan.id}: NO DEPOSIT")
```

### 2. SecurityDeposit Created But is_verified=True
The deposit might be created with is_verified=True instead of False.

**Check:**
```bash
python manage.py shell
from loans.models import SecurityDeposit
deposits = SecurityDeposit.objects.all()
print(f"Total deposits: {deposits.count()}")
for deposit in deposits:
    print(f"Deposit {deposit.id}: is_verified={deposit.is_verified}, paid={deposit.paid_amount}")
```

### 3. Branch Filtering Issue
The manager's branch might not match the loan officer's branch assignment.

**Check:**
```bash
python manage.py shell
from accounts.models import User
from clients.models import OfficerAssignment
manager = User.objects.get(username='manager_username')
print(f"Manager branch: {manager.managed_branch}")

# Check officer assignments
assignments = OfficerAssignment.objects.all()
for a in assignments:
    print(f"Officer {a.officer.full_name}: branch={a.branch}")
```

### 4. Upfront Payment Not Recorded
The upfront payment might not be recorded in the Loan model.

**Check:**
```bash
python manage.py shell
from loans.models import Loan
loans = Loan.objects.filter(upfront_payment_paid__gt=0)
print(f"Loans with upfront payment: {loans.count()}")
for loan in loans:
    print(f"Loan {loan.id}: paid={loan.upfront_payment_paid}, verified={loan.upfront_payment_verified}")
```

## Solution Steps

1. **Check if SecurityDeposit exists:**
   - Run the first diagnostic query above
   - If no deposits exist, the signal might not be firing

2. **Check if is_verified is correct:**
   - Run the second diagnostic query
   - If is_verified=True, manually update to False

3. **Check branch assignments:**
   - Run the third diagnostic query
   - Ensure manager's branch matches officer's branch

4. **Check upfront payment recording:**
   - Run the fourth diagnostic query
   - Verify upfront payments are being recorded

## Manual Fix (if needed)

If SecurityDeposits exist but is_verified=True:
```bash
python manage.py shell
from loans.models import SecurityDeposit
# Update all verified deposits to pending
SecurityDeposit.objects.filter(is_verified=True).update(is_verified=False)
```

## Code Review

The pending_approvals view queries:
```python
pending_deposits = SecurityDeposit.objects.filter(
    is_verified=False,
    loan__loan_officer__officer_assignment__branch=branch.name
).order_by('-payment_date')
```

This requires:
1. SecurityDeposit.is_verified = False
2. Loan has a loan_officer
3. Loan officer has an OfficerAssignment
4. OfficerAssignment.branch matches manager's branch

If any of these are missing, the deposit won't show.
