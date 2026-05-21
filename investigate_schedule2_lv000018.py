"""
Investigate Schedule #2 for Loan LV-000018 - Find out why it's marked as paid
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
print("INVESTIGATING SCHEDULE #2 FOR LOAN LV-000018")
print("=" * 70)

# Get the loan
loan = Loan.objects.get(application_number='LV-000018')
print(f"\n✓ Loan: {loan.application_number} - {loan.borrower.get_full_name()}")

# Get schedule #2
schedule2 = PaymentSchedule.objects.filter(loan=loan, installment_number=2).first()
if not schedule2:
    print("\n✗ Schedule #2 not found!")
    sys.exit(1)

print(f"\n📋 Schedule #2 Details:")
print(f"  Due Date: {schedule2.due_date}")
print(f"  Total Amount: K{schedule2.total_amount}")
print(f"  Amount Paid: K{schedule2.amount_paid}")
print(f"  Is Paid: {schedule2.is_paid}")
print(f"  Paid Date: {schedule2.paid_date}")

# Find ALL payments for this loan
all_payments = Payment.objects.filter(loan=loan).order_by('payment_date')
print(f"\n💰 All Payments for this loan ({all_payments.count()} total):")
for payment in all_payments:
    linked_schedule = f"→ Schedule #{payment.payment_schedule.installment_number}" if payment.payment_schedule else "→ No schedule"
    print(f"  {payment.payment_number}: K{payment.amount} on {payment.payment_date.date()} - Status: {payment.status} {linked_schedule}")

# Find payments that might be for schedule #2
print(f"\n🔍 Searching for payments around schedule #2 due date ({schedule2.due_date}):")
nearby_payments = Payment.objects.filter(
    loan=loan,
    payment_date__date__lte=schedule2.paid_date if schedule2.paid_date else schedule2.due_date
).order_by('-payment_date')

for payment in nearby_payments:
    print(f"  {payment.payment_number}: K{payment.amount} on {payment.payment_date.date()} - Status: {payment.status}")
    if payment.payment_schedule:
        print(f"    → Linked to Schedule #{payment.payment_schedule.installment_number}")
    else:
        print(f"    → Not linked to any schedule")

# Check PaymentCollection
collections = PaymentCollection.objects.filter(loan=loan).order_by('collection_date')
print(f"\n📦 PaymentCollections for this loan ({collections.count()} total):")
for coll in collections:
    print(f"  {coll.collection_date}: Expected K{coll.expected_amount}, Collected K{coll.collected_amount}, Status: {coll.status}")

# Decision
print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

if schedule2.is_paid and schedule2.paid_date:
    print(f"\n⚠️ Schedule #2 is marked as PAID on {schedule2.paid_date}")
    print(f"   But there's no COMPLETED payment linked to it.")
    
    # Check if there's a completed payment on that date
    payment_on_paid_date = Payment.objects.filter(
        loan=loan,
        payment_date__date=schedule2.paid_date,
        status='completed'
    ).first()
    
    if payment_on_paid_date:
        print(f"\n✓ Found completed payment on paid date: {payment_on_paid_date.payment_number}")
        print(f"   This payment should probably be linked to Schedule #2")
        print(f"\n   FIX: Link {payment_on_paid_date.payment_number} to Schedule #2")
    else:
        print(f"\n✗ No completed payment found on {schedule2.paid_date}")
        print(f"   This schedule was likely marked as paid by mistake")
        print(f"\n   FIX: Revert Schedule #2 to UNPAID")
        
        # Offer to fix
        print(f"\n🔧 Reverting Schedule #2 to unpaid...")
        schedule2.is_paid = False
        schedule2.paid_date = None
        schedule2.amount_paid = Decimal('0')
        schedule2.save()
        print(f"   ✓ Schedule #2 reverted to unpaid")

print("\n" + "=" * 70)
