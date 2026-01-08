#!/usr/bin/env python
import os
import sys
import django

# Add project path
sys.path.append('/home/stan13/palmcash/palmcash')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')

# Setup Django
django.setup()

from loans.models import SecurityDeposit, Loan
from django.db import connection

print("=== SECURITY DEPOSIT DEBUG ===")
print()

# Check ALL security deposits
all_deposits = SecurityDeposit.objects.all()
print(f"1. Total security deposits in database: {all_deposits.count()}")

for deposit in all_deposits:
    print(f"   Deposit ID: {deposit.id}")
    print(f"   Loan: {deposit.loan.application_number if deposit.loan else 'None'}")
    print(f"   Required: K{deposit.required_amount}")
    print(f"   Paid: K{deposit.paid_amount}")
    print(f"   Is Verified: {deposit.is_verified}")
    print(f"   Payment Date: {deposit.payment_date}")
    print(f"   Created: {deposit.created_at}")
    print()

# Check pending deposits (paid > 0, not verified)
pending_deposits = SecurityDeposit.objects.filter(
    paid_amount__gt=0,
    is_verified=False
)
print(f"2. Pending deposits (paid > 0, not verified): {pending_deposits.count()}")

for deposit in pending_deposits:
    print(f"   Pending Deposit ID: {deposit.id}")
    print(f"   Loan: {deposit.loan.application_number if deposit.loan else 'None'}")
    print(f"   Amount: K{deposit.paid_amount}")
    print(f"   Created: {deposit.created_at}")
    print()

# Check loan LA-81A75673 specifically
try:
    loan = Loan.objects.get(application_number='LA-81A75673')
    print(f"3. Loan LA-81A75673 found:")
    print(f"   Status: {loan.status}")
    print(f"   Upfront Payment Required: K{loan.upfront_payment_required}")
    print(f"   Upfront Payment Paid: K{loan.upfront_payment_paid}")
    print(f"   Upfront Payment Date: {loan.upfront_payment_date}")
    print(f"   Upfront Payment Verified: {loan.upfront_payment_verified}")
    
    # Check if loan has security deposit
    try:
        deposit = SecurityDeposit.objects.get(loan=loan)
        print(f"   Security Deposit Found: YES (ID: {deposit.id})")
        print(f"   Deposit Required: K{deposit.required_amount}")
        print(f"   Deposit Paid: K{deposit.paid_amount}")
        print(f"   Deposit Verified: {deposit.is_verified}")
    except SecurityDeposit.DoesNotExist:
        print(f"   Security Deposit Found: NO")
    
except Loan.DoesNotExist:
    print("3. Loan LA-81A75673: NOT FOUND")

# Check recent deposits (last 10 minutes)
from datetime import datetime, timedelta
recent_time = datetime.now() - timedelta(minutes=10)
recent_deposits = SecurityDeposit.objects.filter(created_at__gte=recent_time)
print(f"4. Recent deposits (last 10 minutes): {recent_deposits.count()}")

for deposit in recent_deposits:
    print(f"   Recent Deposit ID: {deposit.id}")
    print(f"   Loan: {deposit.loan.application_number if deposit.loan else 'None'}")
    print(f"   Created: {deposit.created_at}")
    print()

print("=== END DEBUG ===")
