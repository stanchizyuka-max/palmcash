#!/usr/bin/env python
"""
Reset all security deposits to K0.00 for all branches.
This is a one-time fix for securities that weren't reset during old month closings.
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
from clients.models import Branch
from django.db.models import Sum

print("=" * 70)
print("SECURITY DEPOSIT RESET SCRIPT")
print("=" * 70)

# Get all branches
branches = Branch.objects.filter(is_active=True)

print("\n1. CURRENT SECURITY DEPOSITS BY BRANCH:")
print("-" * 70)

from loans.models import Loan

total_before = 0
for branch in branches:
    # Get all loans for this branch
    branch_loans = Loan.objects.filter(branch=branch)
    
    # Get security deposits for these loans
    securities = SecurityDeposit.objects.filter(
        loan__in=branch_loans,
        is_verified=True,
        paid_amount__gt=0
    )
    
    branch_total = securities.aggregate(total=Sum('paid_amount'))['total'] or 0
    total_before += branch_total
    
    print(f"   {branch.name:20} - {securities.count():3} deposits - K{branch_total:,.2f}")

print(f"\n   {'TOTAL':20} - K{total_before:,.2f}")

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
for branch in branches:
    # Get all loans for this branch
    branch_loans = Loan.objects.filter(branch=branch)
    
    securities = SecurityDeposit.objects.filter(
        loan__in=branch_loans,
        is_verified=True,
        paid_amount__gt=0
    )
    
    count = securities.count()
    if count > 0:
        securities.update(paid_amount=0)
        print(f"   ✅ {branch.name:20} - Reset {count} deposits to K0.00")
    else:
        print(f"   ⏭️  {branch.name:20} - No deposits to reset")

print("\n3. VERIFICATION:")
print("-" * 70)

total_after = 0
for branch in branches:
    # Get all loans for this branch
    branch_loans = Loan.objects.filter(branch=branch)
    
    securities = SecurityDeposit.objects.filter(
        loan__in=branch_loans,
        is_verified=True,
        paid_amount__gt=0
    )
    
    branch_total = securities.aggregate(total=Sum('paid_amount'))['total'] or 0
    total_after += branch_total
    
    print(f"   {branch.name:20} - {securities.count():3} deposits - K{branch_total:,.2f}")

print(f"\n   {'TOTAL':20} - K{total_after:,.2f}")

print("\n" + "=" * 70)
print("SUMMARY:")
print("=" * 70)
print(f"   Before: K{total_before:,.2f}")
print(f"   After:  K{total_after:,.2f}")
print(f"   Reset:  K{total_before:,.2f}")

if total_after == 0:
    print("\n✅ SUCCESS: All security deposits have been reset to K0.00")
else:
    print(f"\n⚠️  WARNING: {total_after:,.2f} still remaining in security deposits")

print("\n" + "=" * 70)
print("COMPLETE")
print("=" * 70)
