"""
Fix payment distribution for Loan LV-000018
Re-apply completed payments to schedules
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
print("FIXING PAYMENT DISTRIBUTION FOR LOAN LV-000018")
print("=" * 70)

# Get the loan
loan = Loan.objects.get(application_number='LV-000018')
print(f"\n✓ Loan: {loan.application_number} - {loan.borrower.get_full_name()}")

# Get all completed payments
completed_payments = Payment.objects.filter(
    loan=loan,
    status='completed'
).order_by('payment_date')

print(f"\n💰 Completed Payments ({completed_payments.count()} total):")
total_to_distribute = Decimal('0')
for payment in completed_payments:
    total_to_distribute += payment.amount
    linked = f"→ Schedule #{payment.payment_schedule.installment_number}" if payment.payment_schedule else "→ No schedule"
    print(f"  {payment.payment_number}: K{payment.amount} on {payment.payment_date.date()} {linked}")

print(f"\n  Total to distribute: K{total_to_distribute}")

# Get all schedules
schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
print(f"\n📋 Current Schedule Status:")
for sched in schedules[:5]:
    status = "PAID" if sched.is_paid else f"Partial K{sched.amount_paid}" if sched.amount_paid > 0 else "Unpaid"
    print(f"  #{sched.installment_number}: K{sched.amount_paid} paid - {status}")

# Reset all schedules first
print(f"\n🔄 Resetting all schedules...")
for sched in schedules:
    sched.amount_paid = Decimal('0')
    sched.is_paid = False
    sched.paid_date = None
    sched.save()
print(f"  ✓ All schedules reset")

# Re-apply each completed payment
print(f"\n💸 Re-applying completed payments...")
for payment in completed_payments:
    print(f"\n  Processing {payment.payment_number} (K{payment.amount})...")
    
    remaining_amount = payment.amount
    
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
            schedule.paid_date = payment.payment_date.date()
        
        schedule.save()
        
        print(f"    → Applied K{amount_to_apply} to Schedule #{schedule.installment_number}")
        if schedule.is_paid:
            print(f"       ✓ Schedule #{schedule.installment_number} marked as PAID")
    
    if remaining_amount > 0:
        print(f"    ⚠️ Overpayment: K{remaining_amount} remaining")

# Show final status
print(f"\n" + "=" * 70)
print("FINAL STATUS")
print("=" * 70)

schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
total_distributed = Decimal('0')

print(f"\n📋 Updated Schedule Status:")
for sched in schedules[:5]:
    total_distributed += sched.amount_paid
    status = "PAID" if sched.is_paid else f"Partial K{sched.amount_paid}" if sched.amount_paid > 0 else "Unpaid"
    print(f"  #{sched.installment_number}: K{sched.amount_paid} paid - {status}")

print(f"\n💰 Summary:")
print(f"  Total completed payments: K{total_to_distribute}")
print(f"  Total distributed: K{total_distributed}")
print(f"  Difference: K{abs(total_to_distribute - total_distributed)}")

if abs(total_to_distribute - total_distributed) < 0.01:
    print(f"\n✓ SUCCESS! All payments properly distributed")
else:
    print(f"\n⚠️ Warning: Distribution mismatch")

print(f"\n" + "=" * 70)
