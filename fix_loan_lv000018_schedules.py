"""
Fix Loan LV-000018 - Revert schedules marked as paid for pending payments
"""
import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from payments.models import Payment, PaymentSchedule, PaymentCollection
from loans.models import Loan
from decimal import Decimal

print("=" * 70)
print("FIXING LOAN LV-000018 PAYMENT SCHEDULES")
print("=" * 70)

# Get the loan
try:
    loan = Loan.objects.get(application_number='LV-000018')
    print(f"\n✓ Found loan: {loan.application_number}")
    print(f"  Borrower: {loan.borrower.get_full_name()}")
    print(f"  Status: {loan.status}")
except Loan.DoesNotExist:
    print("\n✗ Loan LV-000018 not found!")
    sys.exit(1)

# Get all pending payments for this loan
pending_payments = Payment.objects.filter(
    loan=loan,
    status='pending'
).order_by('payment_date')

print(f"\n✓ Found {pending_payments.count()} pending payment(s):")
for payment in pending_payments:
    print(f"  - {payment.payment_number}: K{payment.amount} on {payment.payment_date.date()}")

# Check each pending payment's schedule
fixed_count = 0
for payment in pending_payments:
    if payment.payment_schedule:
        schedule = payment.payment_schedule
        
        if schedule.is_paid:
            print(f"\n⚠ ISSUE: {payment.payment_number} is PENDING but schedule #{schedule.installment_number} is PAID")
            print(f"  Schedule #{schedule.installment_number}:")
            print(f"    Due Date: {schedule.due_date}")
            print(f"    Total Amount: K{schedule.total_amount}")
            print(f"    Amount Paid: K{schedule.amount_paid}")
            print(f"    Is Paid: {schedule.is_paid}")
            print(f"    Paid Date: {schedule.paid_date}")
            
            # Revert the schedule
            schedule.is_paid = False
            schedule.paid_date = None
            schedule.amount_paid = Decimal('0')
            schedule.save()
            
            print(f"  ✓ Fixed: Schedule #{schedule.installment_number} reverted to unpaid")
            fixed_count += 1
            
            # Also revert PaymentCollection
            payment_date = payment.payment_date.date()
            collection = PaymentCollection.objects.filter(
                loan=loan,
                collection_date=payment_date
            ).first()
            
            if collection and collection.status == 'completed':
                collection.status = 'scheduled'
                collection.save()
                print(f"  ✓ PaymentCollection for {payment_date} reverted to 'scheduled'")

# Check for any schedules marked as paid without a confirmed payment
print("\n" + "=" * 70)
print("CHECKING FOR ORPHANED PAID SCHEDULES")
print("=" * 70)

all_schedules = PaymentSchedule.objects.filter(loan=loan, is_paid=True).order_by('installment_number')
print(f"\n✓ Found {all_schedules.count()} schedule(s) marked as paid")

for schedule in all_schedules:
    # Find confirmed payments for this schedule
    confirmed_payments = Payment.objects.filter(
        loan=loan,
        payment_schedule=schedule,
        status='completed'
    )
    
    if confirmed_payments.count() == 0:
        print(f"\n⚠ ORPHANED: Schedule #{schedule.installment_number} is PAID but has no COMPLETED payment")
        print(f"  Due Date: {schedule.due_date}")
        print(f"  Amount Paid: K{schedule.amount_paid}")
        print(f"  Paid Date: {schedule.paid_date}")
        
        # Check if there's a pending payment
        pending_payment = Payment.objects.filter(
            loan=loan,
            payment_schedule=schedule,
            status='pending'
        ).first()
        
        if pending_payment:
            print(f"  → Has pending payment: {pending_payment.payment_number}")
            print(f"  → Reverting schedule to unpaid...")
            schedule.is_paid = False
            schedule.paid_date = None
            schedule.amount_paid = Decimal('0')
            schedule.save()
            print(f"  ✓ Fixed: Schedule #{schedule.installment_number} reverted to unpaid")
            fixed_count += 1

print("\n" + "=" * 70)
if fixed_count > 0:
    print(f"✓ SUCCESS! Fixed {fixed_count} schedule(s)")
else:
    print("✓ No issues found - all schedules are correct")
print("=" * 70)
print("\nSchedules will be marked as paid when the manager confirms the payments.")
