#!/usr/bin/env python
"""
Simple script to reset ALL security deposits to K0.00 across all branches.
This doesn't filter by branch - it just resets everything.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')

# Try to load .env if it exists
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / 'palmcash' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

django.setup()

from loans.models import SecurityDeposit
from django.db.models import Sum, Count

print("=" * 70)
print("SIMPLE SECURITY DEPOSIT RESET SCRIPT")
print("=" * 70)

# Get all security deposits with balance > 0
print("\n1. CURRENT SECURITY DEPOSITS:")
print("-" * 70)

all_securities = SecurityDeposit.objects.filter(
    is_verified=True,
    paid_amount__gt=0
)

total_deposits = all_securities.count()
total_amount = all_securities.aggregate(total=Sum('paid_amount'))['total'] or 0

print(f"   Total Deposits: {total_deposits}")
print(f"   Total Amount:   K{total_amount:,.2f}")

if total_deposits > 0:
    print("\n   Sample deposits:")
    for deposit in all_securities[:10]:
        print(f"   - Loan {deposit.loan.application_number}: K{deposit.paid_amount:,.2f}")
    
    if total_deposits > 10:
        print(f"   ... and {total_deposits - 10} more")

# Ask for confirmation
print("\n" + "=" * 70)
print("⚠️  WARNING: This will reset ALL security deposits to K0.00")
print("=" * 70)
response = input("\nAre you sure you want to proceed? Type 'YES' to confirm: ")

if response.strip().upper() != 'YES':
    print("\n❌ Operation cancelled.")
    sys.exit(0)

print("\n2. RESETTING SECURITY DEPOSITS:")
print("-" * 70)

# Reset all security deposits
updated_count = all_securities.update(paid_amount=0)
print(f"   ✅ Reset {updated_count} security deposits to K0.00")

print("\n3. VERIFICATION:")
print("-" * 70)

# Verify reset
remaining = SecurityDeposit.objects.filter(
    is_verified=True,
    paid_amount__gt=0
)

remaining_count = remaining.count()
remaining_amount = remaining.aggregate(total=Sum('paid_amount'))['total'] or 0

print(f"   Remaining Deposits: {remaining_count}")
print(f"   Remaining Amount:   K{remaining_amount:,.2f}")

print("\n" + "=" * 70)
print("SUMMARY:")
print("=" * 70)
print(f"   Before: {total_deposits} deposits, K{total_amount:,.2f}")
print(f"   After:  {remaining_count} deposits, K{remaining_amount:,.2f}")
print(f"   Reset:  {updated_count} deposits")

if remaining_count == 0:
    print("\n✅ SUCCESS: All security deposits have been reset to K0.00")
else:
    print(f"\n⚠️  WARNING: {remaining_count} deposits still have balance")

print("\n" + "=" * 70)
print("COMPLETE")
print("=" * 70)
