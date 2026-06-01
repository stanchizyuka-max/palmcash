#!/usr/bin/env python
"""
Diagnostic script to check month closing transactions in the database.
This will help identify why the history page shows 0 closings.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')

print(f"DEBUG: BASE_DIR = {BASE_DIR}")
print(f"DEBUG: .env file path = {BASE_DIR / 'palmcash' / '.env'}")
print(f"DEBUG: .env file exists = {(BASE_DIR / 'palmcash' / '.env').exists()}")

# Try to load .env if it exists
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / 'palmcash' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"DEBUG: Loaded .env from {env_path}")
    else:
        print(f"DEBUG: No .env file found at {env_path}")
except ImportError:
    print("DEBUG: python-dotenv not installed, skipping .env loading")

print(f"DEBUG: DB_HOST from env = {os.environ.get('DB_HOST', 'NOT SET')}")

django.setup()

from expenses.models import VaultTransaction
from clients.models import Branch
from django.db.models import Count, Q
import re

print("=" * 70)
print("MONTH CLOSING DIAGNOSTICS")
print("=" * 70)

# 1. Check all branches
print("\n1. BRANCHES IN SYSTEM:")
print("-" * 70)
branches = Branch.objects.filter(is_active=True)
for branch in branches:
    print(f"   - {branch.name}")

# 2. Check all month_close transactions
print("\n2. ALL MONTH_CLOSE TRANSACTIONS:")
print("-" * 70)
closings = VaultTransaction.objects.filter(
    transaction_type='month_close'
).order_by('-transaction_date')

print(f"Total month_close transactions: {closings.count()}")

if closings.exists():
    print("\nTransaction Details:")
    for closing in closings:
        print(f"\n   Transaction ID: {closing.id}")
        print(f"   Branch: {closing.branch}")
        print(f"   Vault Type: {closing.vault_type}")
        print(f"   Amount: K{closing.amount:,.2f}")
        print(f"   Date: {closing.transaction_date}")
        print(f"   Description: {closing.description}")
        print(f"   Reference: {closing.reference_number}")
        print(f"   Recorded By: {closing.recorded_by.get_full_name() if closing.recorded_by else 'N/A'}")
else:
    print("   ❌ NO month_close transactions found!")

# 3. Check transactions by branch
print("\n3. MONTH_CLOSE TRANSACTIONS BY BRANCH:")
print("-" * 70)
for branch in branches:
    branch_closings = VaultTransaction.objects.filter(
        branch=branch.name,
        transaction_type='month_close'
    )
    print(f"   {branch.name}: {branch_closings.count()} transactions")
    
    if branch_closings.exists():
        # Try to extract months
        months = set()
        for closing in branch_closings:
            month_match = re.search(r'Month closing — ([\d-]+)', closing.description)
            if month_match:
                months.add(month_match.group(1))
        
        if months:
            print(f"      Months closed: {', '.join(sorted(months))}")

# 4. Check for transactions with different description formats
print("\n4. CHECKING FOR ALTERNATIVE TRANSACTION FORMATS:")
print("-" * 70)

# Check for any transactions with "closing" in description
alt_closings = VaultTransaction.objects.filter(
    Q(description__icontains='closing') | Q(description__icontains='close')
).exclude(transaction_type='month_close')

print(f"Transactions with 'closing' in description (not month_close type): {alt_closings.count()}")

if alt_closings.exists():
    print("\nAlternative closing transactions found:")
    for txn in alt_closings[:10]:  # Show first 10
        print(f"   - Type: {txn.transaction_type}, Branch: {txn.branch}")
        print(f"     Description: {txn.description[:100]}")

# 5. Check recent vault transactions to see what's being created
print("\n5. RECENT VAULT TRANSACTIONS (Last 20):")
print("-" * 70)
recent = VaultTransaction.objects.all().order_by('-transaction_date')[:20]

for txn in recent:
    print(f"   {txn.transaction_date.strftime('%Y-%m-%d %H:%M')} | {txn.branch:15} | {txn.transaction_type:20} | K{txn.amount:>10,.2f} | {txn.description[:50]}")

# 6. Summary and recommendations
print("\n" + "=" * 70)
print("SUMMARY & RECOMMENDATIONS:")
print("=" * 70)

total_closings = closings.count()
if total_closings == 0:
    print("❌ NO MONTH CLOSING TRANSACTIONS FOUND")
    print("\nPossible reasons:")
    print("1. Month closing feature was never used before")
    print("2. Transactions were deleted")
    print("3. Transactions are using a different transaction_type")
    print("4. Database was restored from an old backup")
    print("\nRecommendation:")
    print("- Try closing a month manually to create new transactions")
    print("- Check if the vault_month_close view is working correctly")
else:
    print(f"✅ Found {total_closings} month_close transactions")
    
    # Check if they're properly formatted
    properly_formatted = 0
    for closing in closings:
        if re.search(r'Month closing — ([\d-]+)', closing.description):
            properly_formatted += 1
    
    print(f"   - {properly_formatted} have proper description format")
    print(f"   - {total_closings - properly_formatted} have non-standard format")
    
    if properly_formatted < total_closings:
        print("\n⚠️  Some transactions have non-standard description format")
        print("   This may prevent them from appearing in history")
        print("\nRecommendation:")
        print("- Update transaction descriptions to match format:")
        print("  'Month closing — YYYY-MM. Daily/Weekly vault closing balance: K...'")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
