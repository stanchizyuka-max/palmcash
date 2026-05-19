"""
Fix Payment PAY-000107 - Revert failed payment's schedule back to unpaid
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
from decimal import Decimal

print("=" * 70)
print("FIXING PAYMENT PAY-000107")
print("=" * 70)

# Get the payment
try:
    payment = Payment.objects.get(payment_number='PAY-000107')
    print(f"\n✓ Found payment: {payment.payment_number}")
    print(f"  Status: {payment.status}")
    print(f"  Amount: K{payment.amount}")
    print(f"  Loan: {payment.loan.application_number}")
    print(f"  Borrower: {payment.loan.borrower.get_full_name()}")
except Payment.DoesNotExist:
    print("\n✗ Payment PAY-000107 not found!")
    sys.exit(1)

# Get the payment schedule
if payment.payment_schedule:
    schedule = payment.payment_schedule
    print(f"\n✓ Found linked schedule:")
    print(f"  Installment: {schedule.installment_number}")
    print(f"  Due Date: {schedule.due_date}")
    print(f"  Total Amount: K{schedule.total_amount}")
    print(f"  Amount Paid: K{schedule.amount_paid}")
    print(f"  Is Paid: {schedule.is_paid}")
    print(f"  Paid Date: {schedule.paid_date}")
else:
    print("\n✗ No payment schedule linked to this payment")
    sys.exit(1)

# Check if schedule needs fixing
if payment.status == 'failed' and schedule.is_paid:
    print("\n⚠ ISSUE DETECTED: Payment is FAILED but schedule is marked as PAID")
    print("\nFixing...")
    
    # Revert the schedule
    schedule.is_paid = False
    schedule.paid_date = None
    schedule.amount_paid = max(Decimal('0'), schedule.amount_paid - payment.amount)
    schedule.save()
    
    print(f"\n✓ Schedule fixed:")
    print(f"  Is Paid: {schedule.is_paid}")
    print(f"  Paid Date: {schedule.paid_date}")
    print(f"  Amount Paid: K{schedule.amount_paid}")
    
    # Update loan balance if needed
    loan = payment.loan
    if loan.amount_paid >= payment.amount:
        loan.amount_paid -= payment.amount
        loan.balance_remaining += payment.amount
        loan.save()
        print(f"\n✓ Loan balance updated:")
        print(f"  Amount Paid: K{loan.amount_paid}")
        print(f"  Balance Remaining: K{loan.balance_remaining}")
    
    print("\n" + "=" * 70)
    print("✓ SUCCESS! Payment schedule reverted to unpaid")
    print("=" * 70)
else:
    print("\n✓ No fix needed - schedule status is correct")
    print("=" * 70)
