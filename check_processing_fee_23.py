#!/usr/bin/env python
"""
Check the K23 processing fee and why it's not in the vault
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanApplication
from expenses.models import VaultTransaction
from decimal import Decimal

print("=" * 80)
print("CHECKING K23 PROCESSING FEE")
print("=" * 80)

# Find the K23 processing fee
fee_23 = LoanApplication.objects.filter(
    processing_fee=Decimal('23.00')
).order_by('-created_at')

print(f"\nFound {fee_23.count()} application(s) with K23 processing fee:")

for app in fee_23:
    print(f"\n{'=' * 80}")
    print(f"Application: {app.application_number}")
    print(f"Borrower: {app.borrower.get_full_name()}")
    print(f"Loan Amount: K{app.loan_amount:,.2f}")
    print(f"Repayment Frequency: {app.repayment_frequency}")
    print(f"Processing Fee: K{app.processing_fee:,.2f}")
    print(f"Fee Recorded By: {app.processing_fee_recorded_by.get_full_name() if app.processing_fee_recorded_by else 'Not recorded'}")
    print(f"Fee Verified: {app.processing_fee_verified}")
    print(f"Fee Verified By: {app.processing_fee_verified_by.get_full_name() if app.processing_fee_verified_by else 'Not verified'}")
    print(f"Fee Verified At: {app.processing_fee_verified_at}")
    print(f"Created At: {app.created_at}")
    
    # Check if officer has branch assignment
    if app.loan_officer:
        print(f"Loan Officer: {app.loan_officer.get_full_name()}")
        if hasattr(app.loan_officer, 'officer_assignment'):
            print(f"Officer Branch: {app.loan_officer.officer_assignment.branch}")
        else:
            print(f"Officer Branch: ❌ NO BRANCH ASSIGNMENT")
    else:
        print(f"Loan Officer: ❌ NO OFFICER ASSIGNED")
    
    # Check for vault transaction
    vault_tx = VaultTransaction.objects.filter(
        description__icontains=app.application_number
    ).first()
    
    if vault_tx:
        print(f"\n✅ VAULT TRANSACTION EXISTS:")
        print(f"   ID: {vault_tx.id}")
        print(f"   Type: {vault_tx.get_transaction_type_display()}")
        print(f"   Branch: {vault_tx.branch}")
        print(f"   Vault Type: {vault_tx.vault_type}")
        print(f"   Amount: K{vault_tx.amount:,.2f}")
        print(f"   Date: {vault_tx.transaction_date}")
        print(f"   Description: {vault_tx.description}")
    else:
        print(f"\n❌ NO VAULT TRANSACTION FOUND")
        print(f"   This means the processing fee was NOT recorded in the vault")
        print(f"   Possible reasons:")
        print(f"   1. Officer has no branch assignment")
        print(f"   2. Error occurred during vault recording")
        print(f"   3. Fee was recorded before vault integration was added")

print("\n" + "=" * 80)
print("ALL PROCESSING FEE VAULT TRANSACTIONS")
print("=" * 80)

all_processing_txs = VaultTransaction.objects.filter(
    transaction_type='deposit',
    description__icontains='processing fee'
).order_by('-transaction_date')

print(f"\nTotal: {all_processing_txs.count()} transactions")
for tx in all_processing_txs:
    print(f"  - {tx.transaction_date.date()} | {tx.branch} | K{tx.amount:,.2f} | {tx.vault_type} vault")

print("\n" + "=" * 80)
