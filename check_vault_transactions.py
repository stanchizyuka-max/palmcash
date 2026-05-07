#!/usr/bin/env python
"""
Check if vault transactions exist in the database
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from clients.models import Branch

print("\n" + "="*60)
print("VAULT TRANSACTIONS CHECK")
print("="*60)

# Get all branches
branches = Branch.objects.filter(is_active=True)
print(f"\n📍 Active Branches: {branches.count()}")
for branch in branches:
    print(f"   - {branch.name}")

# Get all vault transactions
all_transactions = VaultTransaction.objects.all()
print(f"\n💰 Total Vault Transactions: {all_transactions.count()}")

if all_transactions.count() == 0:
    print("\n⚠️  NO VAULT TRANSACTIONS FOUND IN DATABASE")
    print("\nPossible reasons:")
    print("1. Database is empty (fresh install)")
    print("2. Transactions were deleted")
    print("3. Wrong database connection")
else:
    # Show transactions by branch
    print("\n📊 Transactions by Branch:")
    for branch in branches:
        branch_txs = VaultTransaction.objects.filter(branch=branch.name)
        print(f"   {branch.name}: {branch_txs.count()} transactions")
    
    # Show recent transactions
    print("\n📝 Recent Transactions (last 10):")
    recent = VaultTransaction.objects.all().order_by('-transaction_date')[:10]
    for tx in recent:
        print(f"   {tx.transaction_date.date()} | {tx.branch} | {tx.transaction_type} | {tx.direction} | K{tx.amount}")

# Check if there are any loans
from loans.models import Loan
loans = Loan.objects.all()
print(f"\n🏦 Total Loans: {loans.count()}")

# Check if there are any expenses
from expenses.models import Expense
expenses = Expense.objects.all()
print(f"\n💸 Total Expenses: {expenses.count()}")

print("\n" + "="*60)
print("END OF CHECK")
print("="*60 + "\n")
