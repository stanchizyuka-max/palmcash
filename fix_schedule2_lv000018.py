"""
Fix Schedule #2 for Loan LV-000018
Based on investigation: Schedule #2 is marked as paid but has no payment linked
"""
import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from payments.models import Payment, PaymentSchedule
from loans.models import Loan
from decimal import Decimal

print("=" * 70)
print("FIXING SCHEDULE #2 FOR LOAN LV-000018")
print("=" * 70)

# Get the loan
loan = Loan.objects.get(application_number='LV-000018')
schedule2 = PaymentSchedule.objects.get(loan=loan, installment_number=2)

print(f"\n📋 Current State:")
print(f"  Schedule #2: Due {schedule2.due_date}, Paid: {schedule2.is_paid}, Paid Date: {schedule2.paid_date}")

# Get PAY-000046
pay_046 = Payment.objects.get(payment_number='PAY-000046')
print(f"\n  PAY-000046: K{pay_046.amount} on {pay_046.payment_date.date()}")
print(f"    Status: {pay_046.status}")
print(f"    Currently linked to: Schedule #{pay_046.payment_schedule.installment_number if pay_046.payment_schedule else 'None'}")

# Analysis
print(f"\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)
print(f"\nSchedule #2 is marked as PAID on {schedule2.paid_date}")
print(f"PAY-000046 was made on {pay_046.payment_date.date()} (same date)")
print(f"PAY-000046 is currently linked to Schedule #1")
print(f"\nPossible scenarios:")
print(f"  A) PAY-000046 should be linked to Schedule #2 instead of #1")
print(f"  B) Schedule #2 was marked as paid by mistake and should be reverted")
print(f"  C) There's a missing payment for Schedule #2")

# Check Schedule #1
schedule1 = PaymentSchedule.objects.get(loan=loan, installment_number=1)
print(f"\n📋 Schedule #1 Status:")
print(f"  Due: {schedule1.due_date}, Paid: {schedule1.is_paid}, Paid Date: {schedule1.paid_date}")

# Decision: Since Schedule #2 has no payment but is marked as paid,
# and there's no other evidence of a payment, we should revert it to unpaid
print(f"\n" + "=" * 70)
print("DECISION: Revert Schedule #2 to UNPAID")
print("=" * 70)
print(f"\nReason: Schedule #2 has no payment linked to it.")
print(f"The schedule was likely marked as paid by the premature marking bug.")
print(f"PAY-000046 is correctly linked to Schedule #1.")

# Fix
print(f"\n🔧 Reverting Schedule #2 to unpaid...")
schedule2.is_paid = False
schedule2.paid_date = None
schedule2.amount_paid = Decimal('0')
schedule2.save()

print(f"\n✓ Schedule #2 reverted to unpaid")
print(f"  Is Paid: {schedule2.is_paid}")
print(f"  Paid Date: {schedule2.paid_date}")
print(f"  Amount Paid: K{schedule2.amount_paid}")

print(f"\n" + "=" * 70)
print("✓ SUCCESS! Schedule #2 fixed")
print("=" * 70)
print(f"\nNext steps:")
print(f"  1. Officer should record a new payment for Schedule #2")
print(f"  2. Manager should confirm the payment")
print(f"  3. Schedule #2 will then be properly marked as paid")
