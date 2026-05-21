"""
Revert PAY-000155 to pending status and undo its schedule distribution
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
print("REVERTING PAY-000155 TO PENDING STATUS")
print("=" * 70)

# Get the payment
try:
    payment = Payment.objects.get(payment_number='PAY-000155')
    print(f"\n✓ Found payment: {payment.payment_number}")
    print(f"  Current Status: {payment.status}")
    print(f"  Amount: K{payment.amount}")
    print(f"  Date: {payment.payment_date.date()}")
    print(f"  Loan: {payment.loan.application_number}")
    print(f"  Borrower: {payment.loan.borrower.get_full_name()}")
except Payment.DoesNotExist:
    print("\n✗ Payment PAY-000155 not found!")
    sys.exit(1)

# Get the loan
loan = payment.loan

# Show current schedule status
schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')[:5]
print(f"\n📋 Current Schedule Status:")
for sched in schedules:
    status = "PAID" if sched.is_paid else f"Partial K{sched.amount_paid}" if sched.amount_paid > 0 else "Unpaid"
    print(f"  #{sched.installment_number}: K{sched.amount_paid} paid - {status}")

# Check if payment is completed
if payment.status != 'completed':
    print(f"\n✓ Payment is already {payment.status}, no action needed")
    sys.exit(0)

print(f"\n⚠️ Payment PAY-000155 is COMPLETED but should be PENDING")
print(f"\nThis will:")
print(f"  1. Change payment status from 'completed' to 'pending'")
print(f"  2. Reset all schedules to unpaid")
print(f"  3. Re-apply only PAY-000046 (the first completed payment)")
print(f"  4. Leave PAY-000155 pending for manager approval")

# Step 1: Change payment status to pending
print(f"\n🔄 Step 1: Reverting payment status...")
payment.status = 'pending'
payment.save()
print(f"  ✓ PAY-000155 status changed to 'pending'")

# Step 2: Reset all schedules
print(f"\n🔄 Step 2: Resetting all schedules...")
for sched in schedules:
    sched.amount_paid = Decimal('0')
    sched.is_paid = False
    sched.paid_date = None
    sched.save()
print(f"  ✓ All schedules reset")

# Step 3: Re-apply only PAY-000046 (the completed payment)
print(f"\n🔄 Step 3: Re-applying PAY-000046...")
pay_046 = Payment.objects.get(payment_number='PAY-000046')
print(f"  Processing {pay_046.payment_number} (K{pay_046.amount})...")

remaining_amount = pay_046.amount

# Get unpaid schedules in order
unpaid_schedules = PaymentSchedule.objects.filter(
    loan=loan,
    is_paid=False
).order_by('installment_number')

for schedule in unpaid_schedules:
    if remaining_amount <= 0:
        break
    
    outstanding = schedule.total_amount - schedule.amount_paid
    amount_to_apply = min(remaining_amount, outstanding)
    
    schedule.amount_paid += amount_to_apply
    remaining_amount -= amount_to_apply
    
    # Mark as paid if fully covered
    if schedule.amount_paid >= schedule.total_amount:
        schedule.is_paid = True
        schedule.paid_date = pay_046.payment_date.date()
    
    schedule.save()
    
    print(f"    → Applied K{amount_to_apply} to Schedule #{schedule.installment_number}")
    if schedule.is_paid:
        print(f"       ✓ Schedule #{schedule.installment_number} marked as PAID")

# Step 4: Update loan balance
print(f"\n🔄 Step 4: Updating loan balance...")
loan.amount_paid = pay_046.amount  # Only count the completed payment
loan.balance_remaining = loan.total_amount - loan.amount_paid
loan.save()
print(f"  ✓ Loan amount_paid: K{loan.amount_paid}")
print(f"  ✓ Loan balance_remaining: K{loan.balance_remaining}")

# Show final status
print(f"\n" + "=" * 70)
print("FINAL STATUS")
print("=" * 70)

schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')[:5]
print(f"\n📋 Updated Schedule Status:")
for sched in schedules:
    status = "PAID" if sched.is_paid else f"Partial K{sched.amount_paid}" if sched.amount_paid > 0 else "Unpaid"
    print(f"  #{sched.installment_number}: K{sched.amount_paid} paid - {status}")

print(f"\n💰 Payments:")
print(f"  PAY-000046: K140 - Status: completed ✓")
print(f"  PAY-000155: K140 - Status: pending (awaiting manager approval)")
print(f"  PAY-000138: K140 - Status: pending (awaiting manager approval)")

print(f"\n✓ SUCCESS! PAY-000155 reverted to pending")
print(f"\nNext steps:")
print(f"  1. Manager should review and approve/reject PAY-000155")
print(f"  2. Manager should review and approve/reject PAY-000138")
print(f"  3. Schedules will be updated when payments are approved")

print(f"\n" + "=" * 70)
