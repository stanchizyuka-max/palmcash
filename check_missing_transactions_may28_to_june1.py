#!/usr/bin/env python
"""
Check for missing payment records and vault transactions from May 28 to June 1, 2026.
Excludes May 31st as requested.

This script checks:
1. Payment collections that were confirmed but have no vault transaction
2. Loan disbursements that were made but have no vault transaction
3. Any discrepancies between payments and vault records
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')

# Try to load .env if it exists
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / 'palmcash' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

django.setup()

from payments.models import PaymentCollection
from expenses.models import VaultTransaction
from loans.models import Loan
from clients.models import Branch
from datetime import datetime, date
from django.utils import timezone
from decimal import Decimal

print("=" * 80)
print("CHECKING FOR MISSING TRANSACTIONS: MAY 28 - JUNE 1, 2026")
print("(Excluding May 31st)")
print("=" * 80)

# Define date range (excluding May 31)
dates_to_check = [
    date(2026, 5, 28),
    date(2026, 5, 29),
    date(2026, 5, 30),
    # May 31 excluded as requested
    date(2026, 6, 1),
]

print(f"\n📅 Checking dates: {', '.join([d.strftime('%Y-%m-%d') for d in dates_to_check])}")

# Get all branches
branches = Branch.objects.filter(is_active=True).order_by('name')

total_issues = 0

for branch in branches:
    print(f"\n{'=' * 80}")
    print(f"🏢 BRANCH: {branch.name}")
    print("=" * 80)
    
    branch_has_issues = False
    
    for check_date in dates_to_check:
        print(f"\n📆 Date: {check_date.strftime('%A, %B %d, %Y')}")
        print("-" * 80)
        
        # Convert to datetime range for the full day
        start_datetime = timezone.make_aware(datetime.combine(check_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(check_date, datetime.max.time()))
        
        # 1. Check Payment Collections
        print("\n1️⃣  PAYMENT COLLECTIONS:")
        payments = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch__name__iexact=branch.name,
            payment_date__gte=start_datetime,
            payment_date__lte=end_datetime,
            status='confirmed'
        ).select_related('loan', 'confirmed_by')
        
        if payments.exists():
            print(f"   Found {payments.count()} confirmed payment(s)")
            
            for payment in payments:
                # Check if there's a corresponding vault transaction
                vault_txn = VaultTransaction.objects.filter(
                    branch=branch.name,
                    transaction_type='payment_collection',
                    amount=payment.amount,
                    transaction_date__gte=start_datetime,
                    transaction_date__lte=end_datetime,
                    loan=payment.loan
                ).first()
                
                if not vault_txn:
                    print(f"   ❌ MISSING VAULT TRANSACTION:")
                    print(f"      Payment ID: {payment.id}")
                    print(f"      Loan: {payment.loan.application_number}")
                    print(f"      Amount: K{payment.amount:,.2f}")
                    print(f"      Date: {payment.payment_date.strftime('%Y-%m-%d %H:%M')}")
                    print(f"      Confirmed by: {payment.confirmed_by.get_full_name() if payment.confirmed_by else 'N/A'}")
                    branch_has_issues = True
                    total_issues += 1
                else:
                    print(f"   ✅ Payment K{payment.amount:,.2f} for {payment.loan.application_number} - Vault transaction exists")
        else:
            print(f"   No confirmed payments on this date")
        
        # 2. Check Loan Disbursements
        print("\n2️⃣  LOAN DISBURSEMENTS:")
        disbursements = Loan.objects.filter(
            loan_officer__officer_assignment__branch__name__iexact=branch.name,
            status='disbursed',
            disbursement_date__gte=start_datetime,
            disbursement_date__lte=end_datetime
        ).select_related('loan_officer', 'borrower')
        
        if disbursements.exists():
            print(f"   Found {disbursements.count()} disbursement(s)")
            
            for loan in disbursements:
                # Check if there's a corresponding vault transaction
                vault_txn = VaultTransaction.objects.filter(
                    branch=branch.name,
                    transaction_type='loan_disbursement',
                    amount=loan.principal_amount,
                    transaction_date__gte=start_datetime,
                    transaction_date__lte=end_datetime,
                    loan=loan
                ).first()
                
                if not vault_txn:
                    print(f"   ❌ MISSING VAULT TRANSACTION:")
                    print(f"      Loan: {loan.application_number}")
                    print(f"      Borrower: {loan.borrower.get_full_name()}")
                    print(f"      Amount: K{loan.principal_amount:,.2f}")
                    print(f"      Date: {loan.disbursement_date.strftime('%Y-%m-%d %H:%M')}")
                    print(f"      Officer: {loan.loan_officer.get_full_name() if loan.loan_officer else 'N/A'}")
                    branch_has_issues = True
                    total_issues += 1
                else:
                    print(f"   ✅ Disbursement K{loan.principal_amount:,.2f} for {loan.application_number} - Vault transaction exists")
        else:
            print(f"   No disbursements on this date")
        
        # 3. Check for orphaned vault transactions (vault transactions without corresponding records)
        print("\n3️⃣  ORPHANED VAULT TRANSACTIONS:")
        vault_txns = VaultTransaction.objects.filter(
            branch=branch.name,
            transaction_date__gte=start_datetime,
            transaction_date__lte=end_datetime
        ).exclude(transaction_type__in=['month_close', 'capital_injection', 'expense', 'bank_charges', 'bank_deposit_out', 'branch_transfer_in', 'branch_transfer_out'])
        
        orphaned_count = 0
        for vault_txn in vault_txns:
            if vault_txn.transaction_type == 'payment_collection' and vault_txn.loan:
                # Check if payment exists
                payment = PaymentCollection.objects.filter(
                    loan=vault_txn.loan,
                    amount=vault_txn.amount,
                    payment_date__gte=start_datetime,
                    payment_date__lte=end_datetime,
                    status='confirmed'
                ).first()
                
                if not payment:
                    print(f"   ⚠️  Vault transaction without payment record:")
                    print(f"      Type: Payment Collection")
                    print(f"      Amount: K{vault_txn.amount:,.2f}")
                    print(f"      Loan: {vault_txn.loan.application_number if vault_txn.loan else 'N/A'}")
                    print(f"      Date: {vault_txn.transaction_date.strftime('%Y-%m-%d %H:%M')}")
                    orphaned_count += 1
            
            elif vault_txn.transaction_type == 'loan_disbursement' and vault_txn.loan:
                # Check if loan disbursement exists
                loan = Loan.objects.filter(
                    id=vault_txn.loan.id,
                    status='disbursed',
                    disbursement_date__gte=start_datetime,
                    disbursement_date__lte=end_datetime
                ).first()
                
                if not loan:
                    print(f"   ⚠️  Vault transaction without loan disbursement:")
                    print(f"      Type: Loan Disbursement")
                    print(f"      Amount: K{vault_txn.amount:,.2f}")
                    print(f"      Loan: {vault_txn.loan.application_number if vault_txn.loan else 'N/A'}")
                    print(f"      Date: {vault_txn.transaction_date.strftime('%Y-%m-%d %H:%M')}")
                    orphaned_count += 1
        
        if orphaned_count == 0:
            print(f"   ✅ No orphaned vault transactions found")
    
    if not branch_has_issues:
        print(f"\n✅ No issues found for {branch.name}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if total_issues == 0:
    print("\n✅ NO MISSING TRANSACTIONS FOUND!")
    print("All payment collections and disbursements have corresponding vault transactions.")
else:
    print(f"\n❌ FOUND {total_issues} MISSING VAULT TRANSACTION(S)")
    print("\nRecommendations:")
    print("1. Review the missing transactions listed above")
    print("2. Check if payments were confirmed but vault transactions failed")
    print("3. Manually create vault transactions for missing records if needed")
    print("4. Investigate why vault transactions were not created")

print("\n" + "=" * 80)
print("CHECK COMPLETE")
print("=" * 80)
