#!/usr/bin/env python
"""
Check Tamara Nkuna's payment schedules for loan LV-000075
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
print("CHECKING TAMARA NKUNA'S PAYMENT SCHEDULES (LV-000075)")
print("=" * 70)
print()

# Get the loan
try:
    loan = Loan.objects.get(application_number='LV-000075')
    print(f"✓ Found loan: {loan.application_number}")
    print(f"  Borrower: {loan.borrower.get_full_name()}")
    print(f"  Principal: K{loan.principal_amount}")
    print(f"  Payment Amount: K{loan.payment_amount}")
    print()
except Loan.DoesNotExist:
    print("✗ Loan LV-000075 not found!")
    sys.exit(1)

# Get all payment schedules
schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')

print(f"Total payment schedules: {schedules.count()}")
print()

# Show first 10 schedules
print("First 10 payment schedules:")
print("-" * 70)
print(f"{'#':<4} {'Due Date':<15} {'Amount':<12} {'Paid?':<8} {'Paid Date':<15}")
print("-" * 70)

for schedule in schedules[:10]:
    paid_status = "✓ PAID" if schedule.is_paid else "✗ PENDING"
    paid_date = schedule.paid_date.strftime('%Y-%m-%d') if schedule.paid_date else "—"
    print(f"{schedule.installment_number:<4} {schedule.due_date.strftime('%Y-%m-%d'):<15} K{schedule.total_amount:<11} {paid_status:<8} {paid_date:<15}")

print("-" * 70)
print()

# Count paid vs unpaid
paid_count = schedules.filter(is_paid=True).count()
unpaid_count = schedules.filter(is_paid=False).count()
overdue_count = schedules.filter(is_paid=False, due_date__lt=date.today()).count()
due_today_count = schedules.filter(is_paid=False, due_date=date.today()).count()

print("Summary:")
print(f"  Total schedules: {schedules.count()}")
print(f"  Paid: {paid_count}")
print(f"  Unpaid: {unpaid_count}")
print(f"  Overdue (past due): {overdue_count}")
print(f"  Due today: {due_today_count}")
print()

# Show overdue schedules
if overdue_count > 0:
    print("Overdue schedules:")
    overdue = schedules.filter(is_paid=False, due_date__lt=date.today())
    for schedule in overdue:
        days_overdue = (date.today() - schedule.due_date).days
        print(f"  - #{schedule.installment_number}: {schedule.due_date} (K{schedule.total_amount}) - {days_overdue} days overdue")
    print()

# Show due today
if due_today_count > 0:
    print("Due today:")
    due_today = schedules.filter(is_paid=False, due_date=date.today())
    for schedule in due_today:
        print(f"  - #{schedule.installment_number}: {schedule.due_date} (K{schedule.total_amount})")
    print()

print("=" * 70)
print(f"Today's date: {date.today()}")
print("=" * 70)
