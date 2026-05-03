#!/usr/bin/env python
"""
List all processing fees to find the missing one
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanApplication
from expenses.models import VaultTransaction
from datetime import datetime, timedelta

print("=" * 80)
print("ALL PROCESSING FEES (LAST 7 DAYS)")
print("=" * 80)

# Get all applications with processing fees from last 7 days
recent_date = datetime.now() - timedelta(days=7)
apps_with_fees = LoanApplication.objects.filter(
    processing_fee__isnull=False,
    processing_fee__gt=0,
    created_at__gte=recent_date
).order_by('-created_at')

print(f"\nFound {apps_with_fees.count()} applications with processing fees:")
print("-" * 80)

for app in apps_with_fees:
    # Check for vault transaction
    vault_tx = VaultTransaction.objects.filter(
        description__icontains=app.application_number
    ).first()
    
    has_vault = "✅" if vault_tx else "❌"
    verified = "✅" if app.processing_fee_verified else "⏳"
    
    print(f"\n{app.application_number}")
    print(f"  Borrower: {app.borrower.get_full_name()}")
    print(f"  Amount: K{app.processing_fee:,.2f}")
    print(f"  Loan Type: {app.repayment_frequency}")
    print(f"  Verified: {verified} {app.processing_fee_verified}")
    print(f"  In Vault: {has_vault}")
    print(f"  Created: {app.created_at}")
    
    if app.loan_officer:
        print(f"  Officer: {app.loan_officer.get_full_name()}")
        if hasattr(app.loan_officer, 'officer_assignment'):
            print(f"  Branch: {app.loan_officer.officer_assignment.branch}")
        else:
            print(f"  Branch: ❌ NO ASSIGNMENT")
    else:
        print(f"  Officer: ❌ NONE")
    
    if vault_tx:
        print(f"  Vault TX: ID {vault_tx.id} | {vault_tx.vault_type} vault | K{vault_tx.amount:,.2f}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total = apps_with_fees.count()
with_vault = sum(1 for app in apps_with_fees if VaultTransaction.objects.filter(description__icontains=app.application_number).exists())
without_vault = total - with_vault

print(f"Total applications with fees: {total}")
print(f"With vault transaction: {with_vault} ✅")
print(f"WITHOUT vault transaction: {without_vault} ❌")

if without_vault > 0:
    print(f"\n⚠️  {without_vault} processing fee(s) not recorded in vault!")
    print("These need to be manually added to the vault.")

print("\n" + "=" * 80)
