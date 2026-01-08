#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import FundsTransfer, BankDeposit
from django.contrib.auth.models import User

print("=== FUND HISTORY DEBUG ===")
print(f"Total FundsTransfers: {FundsTransfer.objects.count()}")
print(f"Total BankDeposits: {BankDeposit.objects.count()}")

# Check recent transfers
print("\nRecent FundsTransfers (last 5):")
transfers = FundsTransfer.objects.order_by('-requested_date')[:5]
for transfer in transfers:
    print(f"  {transfer.requested_date} - {transfer.source_branch} → {transfer.destination_branch} - K{transfer.amount} - {transfer.status}")

# Check recent deposits
print("\nRecent BankDeposits (last 5):")
deposits = BankDeposit.objects.order_by('-requested_date')[:5]
for deposit in deposits:
    print(f"  {deposit.requested_date} - {deposit.bank_name} - K{deposit.amount} - {deposit.status}")

# Check users with managed branches
print("\nUsers with managed branches:")
managers = User.objects.filter(role='manager', managed_branch__isnull=False)
for manager in managers:
    print(f"  {manager.username} - {manager.managed_branch}")

print("\n=== END DEBUG ===")
