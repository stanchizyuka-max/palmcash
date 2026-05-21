"""
Check Schedule #4 for Loan LV-000018 - Investigate the K4 partial payment
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

print("=" * 70)
print("CHECKING SCHEDULE #4 FOR LOAN LV-000018")
print("=" * 70)

# Get the loan
loan = Loan.objects.get(application_number='LV-000018')
print(f"\n✓ Loan: {loan.application_number} - {loan.borrower.get_full_name()}")

# Get all schedules
schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')[:5]
print(f"\n📋 First 5 Schedules:")
for sched in schedules:
    status = "PAID" if sched.is_paid else f"Partial (K{sched.amount_paid})" if sched.amount_paid > 0 else "Unpaid"
    print(f"  #{sched.installment_number}: Due {sched.due_date}, Total K{sched.total_amount}, Paid K{sched.amount_paid} - {status}")

# Get schedule #4
schedule4 = PaymentSchedule.objects.get(loan=loan, installment_number=4)
print(f"\n📋 Schedule #4 Details:")
print(f"  Due Date: {schedule4.due_date}")
print(f"  Total Amount: K{schedule4.total_amount}")
print(f"  Amount Paid: K{schedule4.amount_paid}")
print(f"  Is Paid: {schedule4.is_paid}")
print(f"  Paid Date: {schedule4.paid_date}")

# Get all completed payments
completed_payments = Payment.objects.filter(loan=loan, status='completed').order_by('payment_date')
print(f"\n💰 Completed Payments ({completed_payments.count()} total):")
total_paid = 0
for payment in completed_payments:
    total_paid += payment.amount
    linked = f"→ Schedule #{payment.payment_schedule.installment_number}" if payment.payment_schedule else "→ No schedule"
    print(f"  {payment.payment_number}: K{payment.amount} on {payment.payment_date.date()} {linked}")

print(f"\n  Total Paid: K{total_paid}")

# Calculate expected distribution
print(f"\n" + "=" * 70)
print("PAYMENT DISTRIBUTION ANALYSIS")
print("=" * 70)

print(f"\nTotal completed payments: K{total_paid}")
print(f"Schedule amounts: K{schedule4.total_amount} each")

# Calculate how much should be paid per schedule
schedule1 = schedules[0]
schedule2 = schedules[1]
schedule3 = schedules[2]

print(f"\nExpected distribution:")
print(f"  Schedule #1: K{schedule1.total_amount} (K{schedule1.amount_paid} paid)")
print(f"  Schedule #2: K{schedule2.total_amount} (K{schedule2.amount_paid} paid)")
print(f"  Schedule #3: K{schedule3.total_amount} (K{schedule3.amount_paid} paid)")
print(f"  Schedule #4: K{schedule4.total_amount} (K{schedule4.amount_paid} paid)")

# Calculate total that should be distributed
total_should_be_paid = schedule1.amount_paid + schedule2.amount_paid + schedule3.amount_paid + schedule4.amount_paid
print(f"\nTotal distributed across schedules: K{total_should_be_paid}")

# Check if it matches
if abs(total_paid - total_should_be_paid) < 0.01:
    print(f"✓ Distribution matches total payments")
else:
    print(f"⚠️ Mismatch: Total paid K{total_paid} vs Distributed K{total_should_be_paid}")
    print(f"   Difference: K{abs(total_paid - total_should_be_paid)}")

# Analysis
print(f"\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

if schedule4.amount_paid > 0 and not schedule4.is_paid:
    print(f"\n✓ Schedule #4 has K{schedule4.amount_paid} as partial payment")
    print(f"  This is NORMAL if:")
    print(f"    - A payment was larger than the schedule amount")
    print(f"    - The overflow was applied to the next schedule")
    print(f"\n  Remaining balance on Schedule #4: K{schedule4.total_amount - schedule4.amount_paid}")
    
    if schedule4.amount_paid < 10:
        print(f"\n  ⚠️ The K{schedule4.amount_paid} seems small for an overflow")
        print(f"     This might be from a payment distribution issue")
        print(f"     But it's not critical - just means K{schedule4.amount_paid} was prepaid")
else:
    print(f"\n✓ Schedule #4 looks normal")

print(f"\n" + "=" * 70)
