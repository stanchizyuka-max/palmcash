#!/usr/bin/env python
"""
Fix payment schedule for loan LV-000075
Mark May 19 and May 20 as unpaid (they were incorrectly marked as paid)
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from payments.models import PaymentSchedule
from loans.models import Loan
from datetime import date

print("=" * 70)
print("FIXING LOAN LV-000075 PAYMENT SCHEDULE")
print("=" * 70)
print()

# Get the loan
try:
    loan = Loan.objects.get(application_number='LV-000075')
    print(f"✓ Found loan: {loan.application_number}")
    print(f"  Borrower: {loan.borrower.get_full_name()}")
    print()
except Loan.DoesNotExist:
    print("✗ Loan LV-000075 not found!")
    sys.exit(1)

# Get the schedules that need to be fixed
schedules_to_fix = PaymentSchedule.objects.filter(
    loan=loan,
    due_date__in=[date(2026, 5, 19), date(2026, 5, 20)],
    is_paid=True
)

print(f"Found {schedules_to_fix.count()} schedules to fix:")
for schedule in schedules_to_fix:
    print(f"  - Installment #{schedule.installment_number}: {schedule.due_date} (currently marked as Paid)")

print()
print("Fixing schedules...")

fixed_count = 0
for schedule in schedules_to_fix:
    schedule.is_paid = False
    schedule.paid_date = None
    schedule.amount_paid = 0
    schedule.save()
    print(f"  ✓ Fixed installment #{schedule.installment_number} ({schedule.due_date}) - now marked as Pending")
    fixed_count += 1

print()
print("=" * 70)
print(f"✓ SUCCESS! Fixed {fixed_count} payment schedules")
print("=" * 70)
print()
print("Summary:")
print(f"  - May 19 (Tuesday): Now marked as PENDING")
print(f"  - May 20 (Wednesday): Now marked as PENDING")
print()
print("The client should now have a pending payment due today (May 19).")
print("=" * 70)
