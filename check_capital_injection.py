#!/usr/bin/env python
"""
Diagnostic script to check where the capital injection went
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from clients.models import Branch
from datetime import date

# Find the capital injection from May 1, 2026
today = date(2026, 5, 1)

capital_injections = VaultTransaction.objects.filter(
    transaction_type='capital_injection',
    transaction_date__date=today,
    amount=1000.00
)

print("=" * 60)
print("CAPITAL INJECTION DIAGNOSTIC")
print("=" * 60)
print(f"\nSearching for capital injections on {today}...")
print(f"Found {capital_injections.count()} transaction(s)\n")

for tx in capital_injections:
    print(f"Transaction ID: {tx.id}")
    print(f"Branch: {tx.branch}")
    print(f"Vault Type: {tx.vault_type}")
    print(f"Amount: K{tx.amount}")
    print(f"Direction: {tx.direction}")
    print(f"Balance After: K{tx.balance_after}")
    print(f"Description: {tx.description}")
    print(f"Reference: {tx.reference_number}")
    print(f"Recorded By: {tx.recorded_by.get_full_name() if tx.recorded_by else 'N/A'}")
    print(f"Transaction Date: {tx.transaction_date}")
    print("-" * 60)

# List all active branches
print("\nAll Active Branches:")
print("-" * 60)
branches = Branch.objects.filter(is_active=True).order_by('name')
for branch in branches:
    print(f"- {branch.name} (ID: {branch.pk}, Code: {branch.code})")

# Check if "Kamwala south" exists
print("\n" + "=" * 60)
kamwala_south = Branch.objects.filter(name__icontains='kamwala').filter(name__icontains='south').first()
if kamwala_south:
    print(f"✓ Found 'Kamwala south' branch: {kamwala_south.name} (ID: {kamwala_south.pk})")
    
    # Check transactions for this branch
    kamwala_txs = VaultTransaction.objects.filter(
        branch=kamwala_south.name,
        transaction_date__date=today
    )
    print(f"  Transactions for this branch on {today}: {kamwala_txs.count()}")
    for tx in kamwala_txs:
        print(f"  - {tx.get_transaction_type_display()}: K{tx.amount} ({tx.direction})")
else:
    print("✗ 'Kamwala south' branch not found")
    
    # Try to find similar branches
    similar = Branch.objects.filter(name__icontains='kamwala')
    if similar.exists():
        print("\n  Similar branches found:")
        for b in similar:
            print(f"  - {b.name}")

print("=" * 60)
