#!/usr/bin/env python
"""
Diagnostic script to check why pending approvals aren't showing
Run with: python manage.py shell < check_pending_approvals.py
"""

from loans.models import Loan, SecurityDeposit
from accounts.models import User
from clients.models import OfficerAssignment, Branch

print("\n" + "="*80)
print("PENDING APPROVALS DIAGNOSTIC")
print("="*80)

# 1. Check SecurityDeposits
print("\n1. SECURITY DEPOSITS:")
print("-" * 80)
deposits = SecurityDeposit.objects.all()
print(f"Total SecurityDeposit records: {deposits.count()}")

pending_deposits = SecurityDeposit.objects.filter(is_verified=False)
print(f"Pending (is_verified=False): {pending_deposits.count()}")

verified_deposits = SecurityDeposit.objects.filter(is_verified=True)
print(f"Verified (is_verified=True): {verified_deposits.count()}")

if deposits.exists():
    print("\nDeposit Details:")
    for deposit in deposits[:5]:  # Show first 5
        print(f"  - Loan {deposit.loan.id}: paid={deposit.paid_amount}, "
              f"required={deposit.required_amount}, verified={deposit.is_verified}")

# 2. Check Loans with Upfront Payments
print("\n2. LOANS WITH UPFRONT PAYMENTS:")
print("-" * 80)
loans_with_upfront = Loan.objects.filter(upfront_payment_paid__gt=0)
print(f"Loans with upfront payment recorded: {loans_with_upfront.count()}")

if loans_with_upfront.exists():
    print("\nLoan Details:")
    for loan in loans_with_upfront[:5]:  # Show first 5
        print(f"  - Loan {loan.id}: paid={loan.upfront_payment_paid}, "
              f"verified={loan.upfront_payment_verified}, "
              f"officer={loan.loan_officer.full_name if loan.loan_officer else 'None'}")

# 3. Check Officer Assignments
print("\n3. OFFICER ASSIGNMENTS:")
print("-" * 80)
assignments = OfficerAssignment.objects.all()
print(f"Total OfficerAssignment records: {assignments.count()}")

if assignments.exists():
    print("\nAssignment Details:")
    for assignment in assignments[:5]:  # Show first 5
        print(f"  - Officer {assignment.officer.full_name}: branch={assignment.branch}")

# 4. Check Manager Branches
print("\n4. MANAGER BRANCHES:")
print("-" * 80)
managers = User.objects.filter(role='manager')
print(f"Total managers: {managers.count()}")

if managers.exists():
    print("\nManager Details:")
    for manager in managers:
        try:
            branch = manager.managed_branch
            print(f"  - {manager.full_name}: branch={branch.name if branch else 'None'}")
        except:
            print(f"  - {manager.full_name}: ERROR getting branch")

# 5. Check Query Results for Each Manager
print("\n5. PENDING DEPOSITS BY MANAGER:")
print("-" * 80)

for manager in managers:
    try:
        branch = manager.managed_branch
        if not branch:
            print(f"\n{manager.full_name}: NO BRANCH ASSIGNED")
            continue
        
        pending = SecurityDeposit.objects.filter(
            is_verified=False,
            loan__loan_officer__officer_assignment__branch=branch.name
        )
        
        print(f"\n{manager.full_name} (branch={branch.name}):")
        print(f"  Pending deposits: {pending.count()}")
        
        if pending.exists():
            for deposit in pending:
                print(f"    - Loan {deposit.loan.id}: {deposit.loan.borrower.full_name}")
    except Exception as e:
        print(f"\n{manager.full_name}: ERROR - {str(e)}")

# 6. Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Total SecurityDeposits: {deposits.count()}")
print(f"Pending (unverified): {pending_deposits.count()}")
print(f"Loans with upfront payment: {loans_with_upfront.count()}")
print(f"Officer assignments: {assignments.count()}")
print(f"Managers: {managers.count()}")
print("="*80 + "\n")
