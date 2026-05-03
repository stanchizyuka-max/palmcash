#!/usr/bin/env python
"""
Clean up processing fee vault transactions that were created during the old workflow.
These transactions were created when the loan officer recorded the fee, but they should
only be created when the manager verifies the fee.

This script will:
1. Find all processing fee vault transactions
2. Check if the corresponding application has been verified by a manager
3. If NOT verified, remove the vault transaction and adjust the vault balance
4. If verified, keep the transaction (it's legitimate)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanApplication, DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from django.db import transaction as db_transaction
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 80)
print("CLEANING UP OLD PROCESSING FEE VAULT TRANSACTIONS")
print("=" * 80)

# Find all processing fee vault transactions
processing_fee_txs = VaultTransaction.objects.filter(
    transaction_type='deposit',
    description__icontains='processing fee for application'
).select_related('recorded_by').order_by('transaction_date')

print(f"\nFound {processing_fee_txs.count()} processing fee vault transactions")
print("\nChecking which ones should be removed...\n")

removed_count = 0
kept_count = 0
error_count = 0

for tx in processing_fee_txs:
    # Extract application number from description
    import re
    app_match = re.search(r'application (LA-[A-Z0-9]+)', tx.description)
    if not app_match:
        error_count += 1
        print(f"✗ Transaction {tx.id}: Could not extract application number - SKIPPED")
        continue
    
    app_number = app_match.group(1)
    
    try:
        app = LoanApplication.objects.get(application_number=app_number)
        
        # If the fee has been verified by a manager, keep the transaction
        if app.processing_fee_verified:
            kept_count += 1
            print(f"✓ {app_number}: Fee verified by manager - KEEPING transaction")
            continue
        
        # If NOT verified, this transaction was created prematurely - remove it
        with db_transaction.atomic():
            # Get the vault
            from clients.models import Branch
            branch = Branch.objects.filter(name__iexact=tx.branch).first()
            
            if not branch:
                error_count += 1
                print(f"✗ {app_number}: Branch '{tx.branch}' not found - SKIPPED")
                continue
            
            # Get the appropriate vault
            if tx.vault_type == 'daily':
                vault = DailyVault.objects.filter(branch=branch).first()
            else:
                vault = WeeklyVault.objects.filter(branch=branch).first()
            
            if not vault:
                error_count += 1
                print(f"✗ {app_number}: Vault not found - SKIPPED")
                continue
            
            # Remove the amount from vault balance
            vault.balance -= tx.amount
            vault.total_inflows -= tx.amount
            vault.save(update_fields=['balance', 'total_inflows', 'updated_at'])
            
            # Delete the transaction
            tx.delete()
            
            removed_count += 1
            print(f"✓ {app_number}: Removed premature vault transaction (K{tx.amount:,.2f}) - Fee not yet verified")
            
    except LoanApplication.DoesNotExist:
        error_count += 1
        print(f"✗ {app_number}: Application not found - SKIPPED")
    except Exception as e:
        error_count += 1
        logger.error(f"Error processing {app_number}: {e}", exc_info=True)
        print(f"✗ {app_number}: ERROR - {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total transactions checked: {processing_fee_txs.count()}")
print(f"Kept (verified by manager): {kept_count}")
print(f"Removed (not yet verified): {removed_count}")
print(f"Errors/Skipped: {error_count}")
print("=" * 80)

if removed_count > 0:
    print(f"\n✓ Successfully removed {removed_count} premature vault transactions!")
    print("  These will be re-created when the manager verifies the processing fees.")
else:
    print("\n✓ No premature transactions found. All processing fees are properly verified!")
