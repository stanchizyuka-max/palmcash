#!/usr/bin/env python
"""
Find clients that were registered in KUKU branch but are no longer showing
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

# Django imports
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import User
from loans.models import Loan, LoanApplication
from payments.models import Payment

print("\n" + "="*70)
print("FIND MISSING KUKU CLIENTS")
print("="*70)

# Get date range for this week (Monday to Friday)
today = timezone.now().date()
monday = today - timedelta(days=today.weekday())  # Start of this week
friday = monday + timedelta(days=4)

print(f"\n📅 Checking registrations from Monday ({monday}) to Friday ({friday})")

# Find all borrowers registered this week
recent_borrowers = User.objects.filter(
    role='borrower',
    date_joined__date__gte=monday,
    date_joined__date__lte=friday
).order_by('date_joined')

print(f"\n✅ Found {recent_borrowers.count()} borrower(s) registered this week")

# Check each borrower's branch assignment
print(f"\n{'='*70}")
print(f"BORROWER DETAILS:")
print(f"{'='*70}")

kuku_borrowers = []
other_borrowers = []

for borrower in recent_borrowers:
    # Get borrower's assigned officer
    assigned_officer = borrower.assigned_officer
    
    # Get borrower's branch through officer assignment
    branch = 'Unknown'
    if assigned_officer and hasattr(assigned_officer, 'officer_assignment'):
        branch = assigned_officer.officer_assignment.branch
    
    # Get borrower's loans
    loans = Loan.objects.filter(borrower=borrower).order_by('-created_at')
    loan_count = loans.count()
    
    # Get borrower's payments
    payments = Payment.objects.filter(loan__borrower=borrower).order_by('-created_at')
    payment_count = payments.count()
    
    print(f"\n📋 {borrower.get_full_name()}")
    print(f"   ID: {borrower.id}")
    print(f"   Registered: {borrower.date_joined.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Assigned Officer: {assigned_officer.get_full_name() if assigned_officer else 'None'}")
    print(f"   Branch: {branch}")
    print(f"   Loans: {loan_count}")
    print(f"   Payments: {payment_count}")
    
    if loan_count > 0:
        latest_loan = loans.first()
        print(f"   Latest Loan: {latest_loan.application_number} ({latest_loan.status})")
        if latest_loan.loan_officer and hasattr(latest_loan.loan_officer, 'officer_assignment'):
            loan_branch = latest_loan.loan_officer.officer_assignment.branch
            print(f"   Loan Branch: {loan_branch}")
    
    if payment_count > 0:
        latest_payment = payments.first()
        print(f"   Latest Payment: K{latest_payment.amount} on {latest_payment.payment_date.strftime('%Y-%m-%d')}")
    
    # Categorize by branch
    if 'kuku' in branch.lower():
        kuku_borrowers.append(borrower)
    else:
        other_borrowers.append(borrower)

# Summary
print(f"\n{'='*70}")
print(f"SUMMARY:")
print(f"{'='*70}")

print(f"\n✅ KUKU Branch: {len(kuku_borrowers)} borrower(s)")
for b in kuku_borrowers:
    print(f"   - {b.get_full_name()} (ID: {b.id})")

print(f"\n📍 Other Branches: {len(other_borrowers)} borrower(s)")
for b in other_borrowers:
    officer = b.assigned_officer
    branch = 'Unknown'
    if officer and hasattr(officer, 'officer_assignment'):
        branch = officer.officer_assignment.branch
    print(f"   - {b.get_full_name()} (ID: {b.id}) - {branch}")

# Check for borrowers with payments but no assigned officer
print(f"\n{'='*70}")
print(f"CHECKING FOR ORPHANED BORROWERS:")
print(f"{'='*70}")

orphaned = []
for borrower in recent_borrowers:
    if not borrower.assigned_officer:
        payments = Payment.objects.filter(loan__borrower=borrower)
        if payments.exists():
            orphaned.append(borrower)
            print(f"\n⚠️  {borrower.get_full_name()} (ID: {borrower.id})")
            print(f"   - No assigned officer")
            print(f"   - Has {payments.count()} payment(s)")
            
            # Check loans
            loans = Loan.objects.filter(borrower=borrower)
            for loan in loans:
                loan_officer = loan.loan_officer
                loan_branch = 'Unknown'
                if loan_officer and hasattr(loan_officer, 'officer_assignment'):
                    loan_branch = loan_officer.officer_assignment.branch
                print(f"   - Loan {loan.application_number}: Officer={loan_officer.get_full_name() if loan_officer else 'None'}, Branch={loan_branch}")

if not orphaned:
    print(f"\n✅ No orphaned borrowers found")

# Search specifically for KUKU-related activity
print(f"\n{'='*70}")
print(f"SEARCHING FOR KUKU-RELATED ACTIVITY:")
print(f"{'='*70}")

# Find all loans with KUKU officers
kuku_loans = Loan.objects.filter(
    loan_officer__officer_assignment__branch__iexact='KUKU',
    created_at__date__gte=monday,
    created_at__date__lte=friday
).select_related('borrower', 'loan_officer')

print(f"\n📋 Found {kuku_loans.count()} loan(s) with KUKU officers this week:")
for loan in kuku_loans:
    print(f"\n   Loan: {loan.application_number}")
    print(f"   Borrower: {loan.borrower.get_full_name()} (ID: {loan.borrower.id})")
    print(f"   Officer: {loan.loan_officer.get_full_name()}")
    print(f"   Created: {loan.created_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Status: {loan.status}")
    
    # Check if borrower is assigned to KUKU
    if loan.borrower.assigned_officer:
        if hasattr(loan.borrower.assigned_officer, 'officer_assignment'):
            borrower_branch = loan.borrower.assigned_officer.officer_assignment.branch
            if 'kuku' not in borrower_branch.lower():
                print(f"   ⚠️  MISMATCH: Borrower assigned to {borrower_branch}, but loan is in KUKU")

# Find payments in KUKU
kuku_payments = Payment.objects.filter(
    loan__loan_officer__officer_assignment__branch__iexact='KUKU',
    created_at__date__gte=monday,
    created_at__date__lte=friday
).select_related('loan', 'loan__borrower')

print(f"\n💰 Found {kuku_payments.count()} payment(s) for KUKU loans this week:")
for payment in kuku_payments:
    print(f"\n   Payment: {payment.payment_number}")
    print(f"   Borrower: {payment.loan.borrower.get_full_name()} (ID: {payment.loan.borrower.id})")
    print(f"   Loan: {payment.loan.application_number}")
    print(f"   Amount: K{payment.amount}")
    print(f"   Date: {payment.payment_date.strftime('%Y-%m-%d')}")

print(f"\n{'='*70}")
print(f"\n💡 TIP: If clients are missing, check:")
print(f"   1. Their assigned_officer field")
print(f"   2. Whether the officer's branch assignment changed")
print(f"   3. Whether the loan officer is different from assigned officer")

print(f"\n{'='*70}\n")
