#!/usr/bin/env python
"""
Create vault transactions for verified processing fees that don't have them
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanApplication, WeeklyVault
from expenses.models import VaultTransaction
from clients.models import Branch
from django.utils import timezone
from django.db import transaction as db_transaction

print("=" * 80)
print("CREATING MISSING PROCESSING FEE VAULT TRANSACTIONS")
print("=" * 80)

# Find all verified processing fees
verified_fees = LoanApplication.objects.filter(
    processing_fee__gt=0,
    processing_fee_verified=True
).select_related('loan_officer', 'borrower').order_by('processing_fee_verified_at')

print(f"\nFound {verified_fees.count()} verified processing fees")

if verified_fees.count() == 0:
    print("✓ No verified processing fees found")
else:
    print("\nChecking for missing vault transactions:")
    print("-" * 80)
    
    created_count = 0
    
    for app in verified_fees:
        # Check if vault transaction exists for this processing fee
        existing_tx = VaultTransaction.objects.filter(
            description__icontains=f'application {app.application_number}'
        ).first()
        
        if existing_tx:
            print(f"\n✓ App {app.application_number}: Vault transaction already exists (ID: {existing_tx.id})")
            continue
        
        # Get the officer's branch
        if not app.loan_officer or not hasattr(app.loan_officer, 'officer_assignment'):
            print(f"\n❌ App {app.application_number}: No officer or branch assignment - skipping")
            continue
        
        branch_name = app.loan_officer.officer_assignment.branch
        branch = Branch.objects.filter(name=branch_name).first()
        
        if not branch:
            print(f"\n❌ App {app.application_number}: Branch '{branch_name}' not found - skipping")
            continue
        
        print(f"\n📝 App {app.application_number}: Creating vault transaction")
        print(f"   Borrower: {app.borrower.get_full_name()}")
        print(f"   Officer: {app.loan_officer.get_full_name()}")
        print(f"   Branch: {branch.name}")
        print(f"   Amount: K{app.processing_fee:,.2f}")
        print(f"   Verified: {app.processing_fee_verified_at}")
        
        try:
            with db_transaction.atomic():
                # Use WeeklyVault for processing fees
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
                vault.balance += app.processing_fee
                vault.total_inflows += app.processing_fee
                vault.last_transaction_date = app.processing_fee_verified_at or timezone.now()
                vault.save(update_fields=['balance', 'total_inflows', 'last_transaction_date', 'updated_at'])
                
                tx = VaultTransaction.objects.create(
                    transaction_type='deposit',
                    direction='in',
                    branch=branch.name,
                    vault_type='weekly',
                    amount=app.processing_fee,
                    balance_after=vault.balance,
                    description=f'Processing fee for application {app.application_number} (verified)',
                    reference_number=f'PF-{app.application_number}',
                    recorded_by=app.processing_fee_verified_by or app.loan_officer,
                    transaction_date=app.processing_fee_verified_at or timezone.now(),
                )
                
                print(f"   ✓ Created vault transaction ID {tx.id}")
                print(f"   ✓ Vault balance: K{vault.balance:,.2f}")
                created_count += 1
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Verified processing fees: {verified_fees.count()}")
print(f"Vault transactions created: {created_count}")

# Show all processing fee vault transactions
all_processing_txs = VaultTransaction.objects.filter(
    transaction_type='deposit',
    description__icontains='processing fee'
).order_by('-transaction_date')

print(f"\nAll processing fee vault transactions ({all_processing_txs.count()}):")
for tx in all_processing_txs:
    print(f"  - {tx.transaction_date.date()} | {tx.branch} | K{tx.amount:,.2f} | {tx.vault_type} vault")
    print(f"    {tx.description}")

print("\n" + "=" * 80)
print("✓ COMPLETE")
print("=" * 80)
