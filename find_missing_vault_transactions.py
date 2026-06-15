#!/usr/bin/env python
"""
Find missing vault transactions - payments that were collected but not recorded in vault
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from payments.models import Payment
from expenses.models import VaultTransaction
from clients.models import Branch
from loans.models import Loan
from datetime import datetime
from django.utils import timezone
from django.db.models import Q

print("=" * 80)
print("FINDING MISSING VAULT TRANSACTIONS")
print("=" * 80)

# Date range to check
june_13 = timezone.make_aware(datetime(2026, 6, 13, 0, 0, 0))
today = timezone.now()

print(f"\nChecking for missing transactions from June 13 to {today.strftime('%b %d, %Y')}")

branches = Branch.objects.filter(is_active=True).order_by('name')

for branch in branches:
    print(f"\n{'='*80}")
    print(f"🏢 BRANCH: {branch.name}")
    print(f"{'='*80}")
    
    # Get all approved/confirmed payments in June for this branch's loans
    from accounts.models import User
    
    # Get officers assigned to this branch
    officers = User.objects.filter(
        role='loan_officer',
        officer_assignment__branch__iexact=branch.name,
        is_active=True
    ).distinct()
    
    # Get loans for these officers
    loans_query = Q(loan_officer__in=officers) | Q(borrower__group_memberships__group__assigned_officer__in=officers)
    branch_loans = Loan.objects.filter(loans_query).distinct()
    
    # Get payments made between June 13 and today
    payments_in_june = Payment.objects.filter(
        loan__in=branch_loans,
        payment_date__gte=june_13,
        payment_date__lte=today,
        status='confirmed'  # Only confirmed payments should be in vault
    ).select_related('loan', 'loan__borrower').order_by('payment_date')
    
    print(f"\n📋 Confirmed Payments (June 13 onwards): {payments_in_june.count()}")
    
    if payments_in_june.count() == 0:
        print("   ✅ No payments recorded for this period")
        continue
    
    # Check which payments have corresponding vault transactions
    missing_payments = []
    
    for payment in payments_in_june:
        # Look for vault transaction for this payment
        # Vault transactions for payments are typically "payment_collection" type
        vault_tx = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type='payment_collection',
            amount=payment.amount,
            transaction_date__date=payment.payment_date.date()
        ).first()
        
        if not vault_tx:
            missing_payments.append(payment)
    
    if missing_payments:
        print(f"\n❌ MISSING VAULT TRANSACTIONS: {len(missing_payments)}")
        print(f"\n   Details:")
        
        total_missing = 0
        for payment in missing_payments[:10]:  # Show first 10
            print(f"      {payment.payment_date.strftime('%b %d, %Y')} - "
                  f"Loan {payment.loan.application_number} - "
                  f"{payment.loan.borrower.get_full_name()} - "
                  f"K{payment.amount:,.2f} - "
                  f"Status: {payment.status}")
            total_missing += payment.amount
        
        if len(missing_payments) > 10:
            print(f"      ... and {len(missing_payments) - 10} more")
        
        print(f"\n   💰 Total Missing Amount: K{total_missing:,.2f}")
    else:
        print(f"   ✅ All payments have vault transactions")
    
    # Also check vault transactions
    vault_txs_in_june = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        transaction_date__gte=june_13,
        transaction_date__lte=today
    ).exclude(transaction_type='month_close').count()
    
    print(f"\n📊 Vault Transactions (June 13 onwards): {vault_txs_in_june}")

print("\n" + "=" * 80)
print("\nSUMMARY")
print("=" * 80)
print("\nIf payments exist but vault transactions don't, this means:")
print("1. Payments were confirmed but vault wasn't updated")
print("2. There may be a bug in the payment confirmation process")
print("3. Manual vault transactions may need to be created")
print("\nCheck the payment confirmation code to ensure it creates vault transactions.")
