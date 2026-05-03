#!/usr/bin/env python
"""
Check the most recent processing fee
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanApplication
from expenses.models import VaultTransaction
from datetime import datetime, timedelta

print("=" * 80)
print("CHECKING LATEST PROCESSING FEES")
print("=" * 80)

# Get processing fees from last hour
recent = datetime.now() - timedelta(hours=1)
recent_fees = LoanApplication.objects.filter(
    processing_fee__gt=0,
    created_at__gte=recent
).order_by('-created_at')

print(f"\nProcessing fees recorded in last hour: {recent_fees.count()}")

for app in recent_fees:
    vault_tx = VaultTransaction.objects.filter(
        description__icontains=app.application_number
    ).first()
    
    has_vault = "✅" if vault_tx else "❌"
    
    print(f"\n{'=' * 80}")
    print(f"App: {app.application_number}")
    print(f"Borrower: {app.borrower.get_full_name()}")
    print(f"Amount: K{app.processing_fee:,.2f}")
    print(f"Loan Type: {app.repayment_frequency}")
    print(f"Recorded By: {app.processing_fee_recorded_by.get_full_name() if app.processing_fee_recorded_by else 'N/A'}")
    print(f"Verified: {app.processing_fee_verified}")
    print(f"Created: {app.created_at}")
    print(f"In Vault: {has_vault}")
    
    if app.loan_officer and hasattr(app.loan_officer, 'officer_assignment'):
        print(f"Branch: {app.loan_officer.officer_assignment.branch}")
    else:
        print(f"Branch: ❌ NO ASSIGNMENT")
    
    if vault_tx:
        print(f"\nVault Transaction:")
        print(f"  ID: {vault_tx.id}")
        print(f"  Type: {vault_tx.vault_type} vault")
        print(f"  Amount: K{vault_tx.amount:,.2f}")
        print(f"  Date: {vault_tx.transaction_date}")
    else:
        print(f"\n❌ NO VAULT TRANSACTION")
        print(f"   Check server logs for error details")

print("\n" + "=" * 80)
