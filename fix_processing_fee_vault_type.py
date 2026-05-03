#!/usr/bin/env python
"""
Fix processing fee vault transactions that are missing vault_type
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from loans.models import WeeklyVault
from clients.models import Branch

print("=" * 80)
print("FIXING PROCESSING FEE VAULT TRANSACTIONS")
print("=" * 80)

# Find all processing fee transactions without vault_type
processing_fee_txs = VaultTransaction.objects.filter(
    transaction_type='deposit',
    description__icontains='processing fee',
    vault_type__isnull=True
) | VaultTransaction.objects.filter(
    transaction_type='deposit',
    description__icontains='processing fee',
    vault_type=''
)

print(f"\nFound {processing_fee_txs.count()} processing fee transactions without vault_type")

if processing_fee_txs.count() == 0:
    print("✓ No transactions need fixing")
else:
    print("\nFixing transactions:")
    print("-" * 80)
    
    for tx in processing_fee_txs:
        print(f"\nTransaction ID {tx.id}:")
        print(f"  Branch: {tx.branch}")
        print(f"  Amount: K{tx.amount:,.2f}")
        print(f"  Date: {tx.transaction_date}")
        print(f"  Description: {tx.description}")
        
        # Get the branch
        branch = Branch.objects.filter(name=tx.branch).first()
        
        if not branch:
            print(f"  ❌ Branch '{tx.branch}' not found - skipping")
            continue
        
        # Set vault_type to weekly
        tx.vault_type = 'weekly'
        
        # Recalculate balance_after using WeeklyVault
        vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
        
        # Get all transactions for this branch up to this transaction
        prior_txs = VaultTransaction.objects.filter(
            branch=tx.branch,
            vault_type='weekly',
            transaction_date__lt=tx.transaction_date
        ).order_by('transaction_date')
        
        # Calculate balance
        balance = vault.balance
        for prior_tx in prior_txs:
            if prior_tx.direction == 'in':
                balance -= prior_tx.amount
            else:
                balance += prior_tx.amount
        
        # Add this transaction
        balance += tx.amount
        tx.balance_after = balance
        
        tx.save(update_fields=['vault_type', 'balance_after'])
        print(f"  ✓ Fixed: vault_type='weekly', balance_after=K{balance:,.2f}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

# Show all processing fee transactions
all_processing_fees = VaultTransaction.objects.filter(
    transaction_type='deposit',
    description__icontains='processing fee'
).order_by('-transaction_date')

print(f"\nAll processing fee transactions ({all_processing_fees.count()}):")
for tx in all_processing_fees:
    vault_type_display = tx.vault_type if tx.vault_type else "❌ MISSING"
    print(f"  - {tx.transaction_date.date()} | {tx.branch} | K{tx.amount:,.2f} | {vault_type_display}")

print("\n" + "=" * 80)
print("✓ FIX COMPLETE")
print("=" * 80)
