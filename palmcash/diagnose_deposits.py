#!/usr/bin/env python
"""
Diagnostic script to check SecurityDeposit records in the database
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/stan13/palmcash/palmcash')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import SecurityDeposit, Loan
from datetime import datetime, date
from django.db.models import Sum, Count

print("=== Security Deposit Diagnostic ===")
print(f"Current date: {date.today()}")
print()

# Check total SecurityDeposit records
total_deposits = SecurityDeposit.objects.count()
print(f"Total SecurityDeposit records: {total_deposits}")

if total_deposits == 0:
    print("❌ No SecurityDeposit records found in the database!")
    print()
    print("This means:")
    print("1. No security deposits have been recorded yet")
    print("2. Security deposits are created when loans are disbursed")
    print("3. You need to create loans and record security deposits first")
    print()
    print("To fix this:")
    print("1. Create some loans first")
    print("2. Record security deposits for those loans")
    print("3. Or check if there are existing loans without security deposits")
else:
    print(f"✅ Found {total_deposits} SecurityDeposit records")
    
    # Check deposits with paid_amount > 0
    paid_deposits = SecurityDeposit.objects.filter(paid_amount__gt=0).count()
    print(f"Deposits with paid_amount > 0: {paid_deposits}")
    
    # Check deposits with payment_date
    dated_deposits = SecurityDeposit.objects.filter(payment_date__isnull=False).count()
    print(f"Deposits with payment_date: {dated_deposits}")
    
    # Check deposits in the selected date range
    start_date = datetime(2025, 12, 14).date()
    end_date = datetime(2026, 1, 13).date()
    range_deposits = SecurityDeposit.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        paid_amount__gt=0
    ).count()
    print(f"Deposits in date range (Dec 14, 2025 - Jan 13, 2026): {range_deposits}")
    
    if range_deposits == 0:
        print()
        print("❌ No deposits found in the selected date range!")
        print()
        # Show all deposits with dates
        all_deposits = SecurityDeposit.objects.filter(
            payment_date__isnull=False,
            paid_amount__gt=0
        ).order_by('-payment_date')[:10]
        
        if all_deposits:
            print("Recent deposits found:")
            for deposit in all_deposits:
                print(f"  - Loan #{deposit.loan.application_number}: K{deposit.paid_amount} on {deposit.payment_date}")
        else:
            print("No deposits with payment_date and paid_amount > 0 found!")

print()
print("=== Loan Information ===")
total_loans = Loan.objects.count()
print(f"Total loans: {total_loans}")

if total_loans > 0:
    # Check loans with security deposits
    loans_with_deposits = Loan.objects.filter(security_deposit__isnull=False).count()
    print(f"Loans with security deposits: {loans_with_deposits}")
    
    # Check active loans
    active_loans = Loan.objects.filter(status='active').count()
    print(f"Active loans: {active_loans}")
    
    if loans_with_deposits == 0:
        print()
        print("❌ No loans have security deposits associated with them!")
        print("Security deposits should be created automatically when loans are disbursed.")

print()
print("=== Recommendations ===")
if total_deposits == 0:
    print("1. Create a test loan first")
    print("2. Disburse the loan (this should create a security deposit)")
    print("3. Record the security deposit payment")
    print("4. Check the deposit report again")
elif range_deposits == 0:
    print("1. Try a broader date range")
    print("2. Check if deposits have payment dates set")
    print("3. Verify deposits have paid_amount > 0")
else:
    print("1. The deposit report should show data")
    print("2. Check the date range filtering")
    print("3. Verify user permissions")
