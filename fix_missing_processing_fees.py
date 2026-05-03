#!/usr/bin/env python
"""
Fix processing fees that were recorded but not added to the vault.
This script finds all processing fees that don't have corresponding vault transactions
and creates them.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanApplication, DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from django.utils import timezone as tz
from django.db import transaction as db_transaction
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 80)
print("FIXING MISSING PROCESSING FEE VAULT TRANSACTIONS")
print("=" * 80)

# Find all applications with processing fees
apps_with_fees = LoanApplication.objects.filter(
    processing_fee__gt=0,
    processing_fee_recorded_by__isnull=False
).select_related('processing_fee_recorded_by', 'loan_officer').order_by('created_at')

print(f"\nFound {apps_with_fees.count()} applications with processing fees")
print("\nChecking which ones are missing vault transactions...\n")

fixed_count = 0
error_count = 0
already_exists_count = 0

for app in apps_with_fees:
    # Check if vault transaction already exists
    existing_tx = VaultTransaction.objects.filter(
        description__icontains=app.application_number,
        transaction_type='deposit',
        amount=app.processing_fee
    ).first()
    
    if existing_tx:
        already_exists_count += 1
        print(f"✓ {app.application_number}: Vault transaction already exists (K{app.processing_fee:,.2f})")
        continue
    
    # Get the officer's branch
    officer = app.processing_fee_recorded_by or app.loan_officer
    if not officer:
        error_count += 1
        print(f"✗ {app.application_number}: No officer found - SKIPPED")
        continue
    
    if not hasattr(officer, 'officer_assignment'):
        error_count += 1
        print(f"✗ {app.application_number}: Officer {officer.get_full_name()} has no branch assignment - SKIPPED")
        continue
    
    branch = officer.officer_assignment.branch
    vault_type = app.repayment_frequency  # 'daily' or 'weekly'
    
    try:
        with db_transaction.atomic():
            # Get or create the appropriate vault
            if vault_type == 'daily':
                vault, _ = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            
            # Update vault balance
            vault.balance += app.processing_fee
            vault.total_inflows += app.processing_fee
            vault.last_transaction_date = tz.now()
            vault.save(update_fields=['balance', 'total_inflows', 'last_transaction_date', 'updated_at'])
            
            # Create vault transaction
            VaultTransaction.objects.create(
                transaction_type='deposit',
                direction='in',
                branch=branch.name,
                vault_type=vault_type,
                amount=app.processing_fee,
                balance_after=vault.balance,
                description=f'Processing fee for application {app.application_number} ({vault_type} loan) - RETROACTIVE FIX',
                reference_number=f'PF-{app.application_number}',
                recorded_by=officer,
                transaction_date=app.created_at,  # Use original application date
            )
            
            fixed_count += 1
            print(f"✓ {app.application_number}: Created vault transaction for K{app.processing_fee:,.2f} in {branch.name} {vault_type} vault")
            
    except Exception as e:
        error_count += 1
        logger.error(f"Error fixing {app.application_number}: {e}", exc_info=True)
        print(f"✗ {app.application_number}: ERROR - {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total applications checked: {apps_with_fees.count()}")
print(f"Already had vault transactions: {already_exists_count}")
print(f"Successfully fixed: {fixed_count}")
print(f"Errors/Skipped: {error_count}")
print("=" * 80)

if fixed_count > 0:
    print(f"\n✓ Successfully created {fixed_count} missing vault transactions!")
    print("  The vault balances have been updated accordingly.")
else:
    print("\n✓ No missing vault transactions found. All processing fees are properly recorded!")
