#!/usr/bin/env python
"""
Check today's collections for Kamwala south branch
"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from payments.models import Payment, PaymentCollection, MultiSchedulePayment
from clients.models import Branch
from django.db.models import Sum

# Get Kamwala south branch
branch = Branch.objects.get(name='Kamwala south')
today = date.today()

print("=" * 80)
print(f"TODAY'S COLLECTIONS DIAGNOSTIC - {today}")
print(f"Branch: {branch.name}")
print("=" * 80)

# Method 1: Payment model
print("\n1. PAYMENT MODEL (Payment.objects)")
print("-" * 80)
today_payments = Payment.objects.filter(
    loan__loan_officer__officer_assignment__branch=branch.name,
    payment_date__date=today,
    status='completed'
)
print(f"Count: {today_payments.count()}")
payments_total = today_payments.aggregate(total=Sum('amount'))['total'] or 0
print(f"Total: K{payments_total:,.2f}")

if today_payments.exists():
    print("\nDetails:")
    for p in today_payments:
        print(f"  - Payment ID {p.id}: K{p.amount:,.2f} | Loan: {p.loan.id} | Date: {p.payment_date}")

# Method 2: PaymentCollection model
print("\n2. PAYMENT COLLECTION MODEL (PaymentCollection.objects)")
print("-" * 80)
today_collections_all = PaymentCollection.objects.filter(
    loan__loan_officer__officer_assignment__branch=branch.name,
    collection_date=today
).distinct()
print(f"Count: {today_collections_all.count()}")
collections_total = sum(c.collected_amount for c in today_collections_all) or 0
print(f"Total: K{collections_total:,.2f}")

if today_collections_all.exists():
    print("\nDetails:")
    for c in today_collections_all:
        print(f"  - Collection ID {c.id}: Expected K{c.expected_amount:,.2f}, Collected K{c.collected_amount:,.2f}")
        print(f"    Loan: {c.loan.id} | Status: {c.loan.status} | Date: {c.collection_date}")

# Method 3: MultiSchedulePayment model
print("\n3. MULTI SCHEDULE PAYMENT MODEL (MultiSchedulePayment.objects)")
print("-" * 80)
today_multi_payments = MultiSchedulePayment.objects.filter(
    loan__loan_officer__officer_assignment__branch=branch.name,
    payment_date__date=today,
    status='approved'
)
print(f"Count: {today_multi_payments.count()}")
multi_payments_total = today_multi_payments.aggregate(total=Sum('total_amount'))['total'] or 0
print(f"Total: K{multi_payments_total:,.2f}")

if today_multi_payments.exists():
    print("\nDetails:")
    for m in today_multi_payments:
        print(f"  - Multi Payment ID {m.id}: K{m.total_amount:,.2f} | Loan: {m.loan.id} | Date: {m.payment_date}")

# Current calculation (WRONG - uses max)
print("\n" + "=" * 80)
print("CURRENT CALCULATION (WRONG)")
print("=" * 80)
current_total = max(payments_total, collections_total) + multi_payments_total
print(f"max({payments_total:,.2f}, {collections_total:,.2f}) + {multi_payments_total:,.2f} = K{current_total:,.2f}")

# Correct calculation
print("\n" + "=" * 80)
print("CORRECT CALCULATION")
print("=" * 80)

# Check for overlap - do Payment and PaymentCollection reference the same transactions?
print("\nChecking for overlap between Payment and PaymentCollection...")
payment_loan_ids = set(today_payments.values_list('loan_id', flat=True))
collection_loan_ids = set(today_collections_all.values_list('loan_id', flat=True))
overlap = payment_loan_ids & collection_loan_ids

if overlap:
    print(f"⚠️  OVERLAP DETECTED: {len(overlap)} loans appear in both Payment and PaymentCollection")
    print(f"   Overlapping loan IDs: {overlap}")
    print("\n   Need to deduplicate to avoid double-counting!")
    
    # For overlapping loans, use the higher amount
    overlap_payment_total = Payment.objects.filter(
        loan_id__in=overlap,
        payment_date__date=today,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    overlap_collection_total = sum(
        c.collected_amount for c in today_collections_all.filter(loan_id__in=overlap)
    ) or 0
    
    print(f"   Payment total for overlap: K{overlap_payment_total:,.2f}")
    print(f"   Collection total for overlap: K{overlap_collection_total:,.2f}")
    print(f"   Using max: K{max(overlap_payment_total, overlap_collection_total):,.2f}")
    
    # Non-overlapping amounts
    non_overlap_payment = Payment.objects.filter(
        loan_id__in=payment_loan_ids - overlap,
        payment_date__date=today,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    non_overlap_collection = sum(
        c.collected_amount for c in today_collections_all.filter(loan_id__in=collection_loan_ids - overlap)
    ) or 0
    
    print(f"\n   Non-overlap Payment total: K{non_overlap_payment:,.2f}")
    print(f"   Non-overlap Collection total: K{non_overlap_collection:,.2f}")
    
    correct_total = (
        max(overlap_payment_total, overlap_collection_total) +
        non_overlap_payment +
        non_overlap_collection +
        multi_payments_total
    )
    print(f"\n✅ CORRECT TOTAL: K{correct_total:,.2f}")
else:
    print("✅ No overlap - Payment and PaymentCollection are separate")
    correct_total = payments_total + collections_total + multi_payments_total
    print(f"\n✅ CORRECT TOTAL: {payments_total:,.2f} + {collections_total:,.2f} + {multi_payments_total:,.2f} = K{correct_total:,.2f}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Dashboard currently shows: K{current_total:,.2f} ❌")
print(f"Should show: K{correct_total:,.2f} ✅")
print(f"Difference: K{correct_total - current_total:,.2f}")
print("=" * 80)
