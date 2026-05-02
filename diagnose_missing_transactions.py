#!/usr/bin/env python
"""
Diagnose missing vault transactions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from clients.models import Branch
from datetime import date

# Check Kamwala south transactions
branch_name = "Kamwala south"
today = date(2026, 5, 1)

print("=" * 70)
print(f"DIAGNOSTIC: {branch_name} Transactions on {today}")
print("=" * 70)

# Get ALL transactions for this branch on this date
all_txs = VaultTransaction.objects.filter(
    branch=branch_name,
    transaction_date__date=today
).order_by('transaction_date', 'id')

print(f"\nTotal transactions found: {all_txs.count()}")
print("\nTransaction Details:")
print("-" * 70)

for tx in all_txs:
    print(f"ID: {tx.id}")
    print(f"  Type: {tx.get_transaction_type_display()}")
    print(f"  Direction: {tx.direction}")
    print(f"  Amount: K{tx.amount}")
    print(f"  Vault Type: {tx.vault_type}")
    print(f"  Balance After: K{tx.balance_after}")
    print(f"  Time: {tx.transaction_date}")
    print(f"  Description: {tx.description}")
    print("-" * 70)

# Check for transactions without vault_type
print("\nTransactions WITHOUT vault_type:")
no_vault_type = VaultTransaction.objects.filter(
    branch=branch_name,
    transaction_date__date=today,
    vault_type__isnull=True
)
print(f"Count: {no_vault_type.count()}")

# Check for transactions with empty vault_type
print("\nTransactions with EMPTY vault_type:")
empty_vault_type = VaultTransaction.objects.filter(
    branch=branch_name,
    transaction_date__date=today,
    vault_type=''
)
print(f"Count: {empty_vault_type.count()}")

# Group by vault_type
print("\n" + "=" * 70)
print("Transactions by Vault Type:")
print("=" * 70)

for vault_type in ['daily', 'weekly', None, '']:
    if vault_type is None:
        txs = VaultTransaction.objects.filter(
            branch=branch_name,
            transaction_date__date=today,
            vault_type__isnull=True
        )
        label = "NULL"
    elif vault_type == '':
        txs = VaultTransaction.objects.filter(
            branch=branch_name,
            transaction_date__date=today,
            vault_type=''
        )
        label = "EMPTY"
    else:
        txs = VaultTransaction.objects.filter(
            branch=branch_name,
            transaction_date__date=today,
            vault_type=vault_type
        )
        label = vault_type.upper()
    
    if txs.exists():
        print(f"\n{label} Vault: {txs.count()} transactions")
        for tx in txs:
            print(f"  - {tx.get_transaction_type_display()}: K{tx.amount} ({tx.direction})")

# Check the actual vault balances
print("\n" + "=" * 70)
print("Current Vault Balances:")
print("=" * 70)

from loans.models import DailyVault, WeeklyVault

branch = Branch.objects.get(name=branch_name)

try:
    daily = DailyVault.objects.get(branch=branch)
    print(f"Daily Vault: K{daily.balance}")
except DailyVault.DoesNotExist:
    print("Daily Vault: Not created")

try:
    weekly = WeeklyVault.objects.get(branch=branch)
    print(f"Weekly Vault: K{weekly.balance}")
except WeeklyVault.DoesNotExist:
    print("Weekly Vault: Not created")

# Check old BranchVault
from loans.models import BranchVault
try:
    old_vault = BranchVault.objects.get(branch=branch)
    print(f"OLD BranchVault: K{old_vault.balance} ⚠️ (This should not be used!)")
except BranchVault.DoesNotExist:
    print("OLD BranchVault: Not created")

print("\n" + "=" * 70)
