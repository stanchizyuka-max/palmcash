#!/usr/bin/env python
"""
Search for specific clients and check their branch assignments
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

# Django imports
from django.db.models import Q
from accounts.models import User
from loans.models import Loan
from payments.models import Payment

print("\n" + "="*70)
print("SEARCH FOR MISSING CLIENTS")
print("="*70)

# Ask for client names
print("\n💡 Enter the names of the missing clients (or press Enter to search all KUKU clients)")
client_names = input("Client names (comma-separated): ").strip()

if client_names:
    # Search for specific clients
    names = [name.strip() for name in client_names.split(',')]
    
    print(f"\n🔍 Searching for: {', '.join(names)}")
    
    borrowers = []
    for name in names:
        # Search by first name or last name
        found = User.objects.filter(
            role='borrower'
        ).filter(
            Q(first_name__icontains=name) | Q(last_name__icontains=name)
        )
        borrowers.extend(list(found))
    
    # Remove duplicates
    borrowers = list(set(borrowers))
    
else:
    # Search all KUKU clients
    print(f"\n🔍 Searching for all KUKU branch clients...")
    
    # Find all borrowers with KUKU officers
    kuku_loans = Loan.objects.filter(
        loan_officer__officer_assignment__branch__iexact='KUKU'
    ).values_list('borrower_id', flat=True).distinct()
    
    borrowers = User.objects.filter(id__in=kuku_loans, role='borrower')

if not borrowers:
    print(f"\n❌ No clients found")
    exit()

print(f"\n✅ Found {len(borrowers)} client(s)")

# Check each borrower
print(f"\n{'='*70}")
print(f"CLIENT DETAILS:")
print(f"{'='*70}")

for borrower in borrowers:
    print(f"\n{'='*70}")
    print(f"📋 {borrower.get_full_name()}")
    print(f"{'='*70}")
    print(f"   ID: {borrower.id}")
    print(f"   Username: {borrower.username}")
    print(f"   Registered: {borrower.date_joined.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Phone: {borrower.phone_number}")
    
    # Check assigned officer
    assigned_officer = borrower.assigned_officer
    if assigned_officer:
        print(f"\n   👤 Assigned Officer: {assigned_officer.get_full_name()}")
        if hasattr(assigned_officer, 'officer_assignment'):
            print(f"      Branch: {assigned_officer.officer_assignment.branch}")
        else:
            print(f"      ⚠️  Officer has no branch assignment!")
    else:
        print(f"\n   ⚠️  NO ASSIGNED OFFICER")
    
    # Check loans
    loans = Loan.objects.filter(borrower=borrower).order_by('-created_at')
    print(f"\n   💼 LOANS ({loans.count()}):")
    
    if loans.exists():
        for loan in loans:
            print(f"\n      Loan: {loan.application_number}")
            print(f"      Status: {loan.status}")
            print(f"      Amount: K{loan.principal_amount}")
            print(f"      Created: {loan.created_at.strftime('%Y-%m-%d %H:%M')}")
            
            if loan.loan_officer:
                print(f"      Loan Officer: {loan.loan_officer.get_full_name()}")
                if hasattr(loan.loan_officer, 'officer_assignment'):
                    loan_branch = loan.loan_officer.officer_assignment.branch
                    print(f"      Loan Branch: {loan_branch}")
                    
                    # Check for mismatch
                    if assigned_officer and hasattr(assigned_officer, 'officer_assignment'):
                        assigned_branch = assigned_officer.officer_assignment.branch
                        if loan_branch.lower() != assigned_branch.lower():
                            print(f"      ⚠️  MISMATCH: Loan in {loan_branch}, but borrower assigned to {assigned_branch}")
                else:
                    print(f"      ⚠️  Loan officer has no branch assignment!")
            else:
                print(f"      ⚠️  No loan officer")
    else:
        print(f"      No loans found")
    
    # Check payments
    payments = Payment.objects.filter(loan__borrower=borrower).order_by('-created_at')
    print(f"\n   💰 PAYMENTS ({payments.count()}):")
    
    if payments.exists():
        for payment in payments[:5]:  # Show last 5 payments
            print(f"\n      Payment: {payment.payment_number}")
            print(f"      Amount: K{payment.amount}")
            print(f"      Date: {payment.payment_date.strftime('%Y-%m-%d')}")
            print(f"      Status: {payment.status}")
            print(f"      Loan: {payment.loan.application_number}")
        
        if payments.count() > 5:
            print(f"\n      ... and {payments.count() - 5} more payment(s)")
    else:
        print(f"      No payments found")
    
    # Check if visible in KUKU branch view
    print(f"\n   👁️  VISIBILITY:")
    
    # Check if borrower should appear in KUKU branch
    should_be_in_kuku = False
    
    if assigned_officer and hasattr(assigned_officer, 'officer_assignment'):
        if 'kuku' in assigned_officer.officer_assignment.branch.lower():
            should_be_in_kuku = True
            print(f"      ✅ Should appear in KUKU branch (assigned officer is in KUKU)")
        else:
            print(f"      ❌ Should NOT appear in KUKU branch (assigned to {assigned_officer.officer_assignment.branch})")
    else:
        print(f"      ⚠️  Cannot determine (no assigned officer or no branch)")
    
    # Check if any loans are in KUKU
    kuku_loans_count = Loan.objects.filter(
        borrower=borrower,
        loan_officer__officer_assignment__branch__iexact='KUKU'
    ).count()
    
    if kuku_loans_count > 0:
        print(f"      📋 Has {kuku_loans_count} loan(s) with KUKU officers")

# Summary
print(f"\n{'='*70}")
print(f"SUMMARY:")
print(f"{'='*70}")

print(f"\n💡 POSSIBLE REASONS FOR MISSING CLIENTS:")
print(f"   1. Assigned officer was moved to a different branch")
print(f"   2. Borrower was never assigned to a KUKU officer")
print(f"   3. Loan officer is different from assigned officer")
print(f"   4. Client list view is filtering by assigned_officer, not loan_officer")

print(f"\n🔧 TO FIX:")
print(f"   - If client should be in KUKU, reassign them to a KUKU officer")
print(f"   - Use: python manage.py assign_officer_to_branch")
print(f"   - Or manually update in admin panel")

print(f"\n{'='*70}\n")
