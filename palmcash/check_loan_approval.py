#!/usr/bin/env python
"""
Diagnostic script to check loan approval status and permissions
Run with: python manage.py shell < check_loan_approval.py
"""

from loans.models import Loan
from accounts.models import User

print("=" * 80)
print("LOAN APPROVAL DIAGNOSTIC")
print("=" * 80)

# Check loan 1
try:
    loan = Loan.objects.get(id=1)
    print(f"\nLoan #1 Details:")
    print(f"  ID: {loan.id}")
    print(f"  Application Number: {loan.application_number}")
    print(f"  Borrower: {loan.borrower.username} ({loan.borrower.get_full_name})")
    print(f"  Status: {loan.status}")
    print(f"  Principal Amount: K{loan.principal_amount}")
    print(f"  Loan Officer: {loan.loan_officer}")
    print(f"  Approval Date: {loan.approval_date}")
    print(f"  Approval Notes: {loan.approval_notes}")
except Loan.DoesNotExist:
    print("\n❌ Loan #1 does not exist")
    print("\nAvailable loans:")
    for loan in Loan.objects.all()[:5]:
        print(f"  - Loan #{loan.id}: {loan.application_number} (Status: {loan.status})")
    exit()

# Check users and their permissions
print("\n" + "=" * 80)
print("USER PERMISSIONS")
print("=" * 80)

admins = User.objects.filter(role='admin')
print(f"\nAdmins ({admins.count()}):")
for user in admins:
    print(f"  - {user.username} ({user.get_full_name})")

managers = User.objects.filter(role='manager')
print(f"\nManagers ({managers.count()}):")
for user in managers:
    print(f"  - {user.username} ({user.get_full_name})")

loan_officers = User.objects.filter(role='loan_officer')
print(f"\nLoan Officers ({loan_officers.count()}):")
for user in loan_officers:
    active_groups = user.get_active_groups_count()
    can_approve = user.can_approve_loans()
    status = "✅ Can Approve" if can_approve else "❌ Cannot Approve"
    print(f"  - {user.username} ({user.get_full_name})")
    print(f"    Active Groups: {active_groups}/15 {status}")

# Check if loan can be approved
print("\n" + "=" * 80)
print("APPROVAL ELIGIBILITY")
print("=" * 80)

print(f"\nLoan Status: {loan.status}")
if loan.status != 'pending':
    print(f"❌ Loan cannot be approved - status is '{loan.status}', not 'pending'")
else:
    print(f"✅ Loan status is 'pending' - can be approved")

# Check who can approve
print(f"\nWho can approve this loan:")
for user in User.objects.filter(role__in=['admin', 'manager']):
    print(f"  ✅ {user.username} ({user.get_full_name}) - {user.role}")

for user in User.objects.filter(role='loan_officer'):
    if user.can_approve_loans():
        print(f"  ✅ {user.username} ({user.get_full_name}) - loan_officer (has {user.get_active_groups_count()} groups)")
    else:
        print(f"  ❌ {user.username} ({user.get_full_name}) - loan_officer (only has {user.get_active_groups_count()}/15 groups)")

print("\n" + "=" * 80)
print("HOW TO APPROVE")
print("=" * 80)
print(f"""
1. Log in as an admin or manager
2. Go to: https://stan13.pythonanywhere.com/loans/{loan.id}/
3. Scroll to the "Actions" section
4. Click the "Approve Loan" button
5. Confirm the approval

OR if you're a loan officer:
1. Make sure you manage at least 15 active groups
2. Follow steps 2-5 above
""")

print("\n" + "=" * 80)
