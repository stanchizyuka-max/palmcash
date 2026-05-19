#!/usr/bin/env python
"""
Reject duplicate approved loans where borrower already has an active loan.
This prevents multiple active loans per borrower.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan
from django.db.models import Count

print("=" * 70)
print("REJECTING DUPLICATE APPROVED LOANS")
print("=" * 70)
print()

# Find borrowers with multiple approved/active loans
print("Step 1: Finding borrowers with multiple approved/active loans...")
print()

# Get all borrowers who have more than one loan in approved/active/disbursed status
from django.db.models import Q

problem_borrowers = Loan.objects.filter(
    status__in=['approved', 'active', 'disbursed']
).values('borrower').annotate(
    loan_count=Count('id')
).filter(loan_count__gt=1)

print(f"Found {problem_borrowers.count()} borrowers with multiple approved/active loans")
print()

if problem_borrowers.count() == 0:
    print("✓ No duplicate loans found. All borrowers have at most one active loan.")
    print("=" * 70)
    sys.exit(0)

# Process each borrower
rejected_count = 0
kept_count = 0

for borrower_data in problem_borrowers:
    borrower_id = borrower_data['borrower']
    
    # Get all approved/active/disbursed loans for this borrower
    loans = Loan.objects.filter(
        borrower_id=borrower_id,
        status__in=['approved', 'active', 'disbursed']
    ).order_by('created_at')  # Oldest first
    
    borrower = loans.first().borrower
    print(f"Borrower: {borrower.get_full_name()}")
    print(f"  Found {loans.count()} loans:")
    
    # Keep the first active/disbursed loan, or the oldest approved loan
    # Reject all others
    active_loan = loans.filter(status__in=['active', 'disbursed']).first()
    
    if active_loan:
        # Keep the active/disbursed loan, reject all approved ones
        keep_loan = active_loan
        loans_to_reject = loans.exclude(pk=keep_loan.pk)
    else:
        # No active loan, keep the oldest approved loan
        keep_loan = loans.first()
        loans_to_reject = loans.exclude(pk=keep_loan.pk)
    
    print(f"  ✓ KEEPING: {keep_loan.application_number} (Status: {keep_loan.status}, Created: {keep_loan.created_at.strftime('%Y-%m-%d')})")
    kept_count += 1
    
    for loan in loans_to_reject:
        print(f"  ✗ REJECTING: {loan.application_number} (Status: {loan.status}, Created: {loan.created_at.strftime('%Y-%m-%d')})")
        
        # Reject the loan
        loan.status = 'rejected'
        loan.rejection_reason = 'Borrower already has an active loan. Only one active loan per borrower is allowed.'
        loan.save()
        rejected_count += 1
    
    print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Borrowers processed: {problem_borrowers.count()}")
print(f"Loans kept: {kept_count}")
print(f"Loans rejected: {rejected_count}")
print()
print("✓ All duplicate loans have been rejected.")
print("=" * 70)
