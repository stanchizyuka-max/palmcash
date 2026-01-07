#!/usr/bin/env python
"""
Debug script to check Collection Details view logic
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.contrib.auth.models import User
from payments.models import PaymentCollection
from loans.models import Loan
from accounts.models import User as AccountUser


def debug_collection_details():
    """Debug collection details for different user roles"""
    
    print("Debugging Collection Details View Logic")
    print("="*50)
    
    # Check total collections first
    total_collections = PaymentCollection.objects.all()
    print(f"Total PaymentCollection records in database: {total_collections.count()}")
    
    # Show some sample collections
    print("\nSample collections:")
    for collection in total_collections[:5]:
        print(f"  Loan: {collection.loan.application_number}, Date: {collection.collection_date}, Expected: K{collection.expected_amount}, Collected: K{collection.collected_amount}, Status: {collection.status}")
    
    # Check users and their roles
    print(f"\nUsers in system:")
    users = User.objects.filter(is_active=True)
    for user in users:
        print(f"  {user.username} - Role: {user.role}")
        
        # Test what collections this user would see
        if user.role == 'admin':
            user_collections = PaymentCollection.objects.all()
        elif user.role == 'loan_officer':
            user_collections = PaymentCollection.objects.filter(
                loan__loan_officer=user
            )
        elif user.role == 'manager':
            if hasattr(user, 'managed_branch') and user.managed_branch:
                user_collections = PaymentCollection.objects.filter(
                    loan__loan_officer__officer_assignment__branch=user.managed_branch.name
                )
            else:
                user_collections = PaymentCollection.objects.none()
        else:
            user_collections = PaymentCollection.objects.none()
        
        print(f"    -> Would see {user_collections.count()} collections")
        
        # Show first few collections for this user
        for collection in user_collections[:3]:
            print(f"       Loan: {collection.loan.application_number}, Amount: K{collection.collected_amount}")
    
    # Check loan officers and their assignments
    print(f"\nLoan Officers and their loans:")
    officers = User.objects.filter(role='loan_officer')
    for officer in officers:
        officer_loans = Loan.objects.filter(loan_officer=officer)
        print(f"  {officer.username}: {officer_loans.count()} loans")
        for loan in officer_loans[:3]:
            print(f"    - {loan.application_number}")
    
    # Check branch assignments
    print(f"\nBranch Assignments:")
    try:
        from clients.models import OfficerAssignment
        assignments = OfficerAssignment.objects.all()
        for assignment in assignments[:10]:
            print(f"  {assignment.officer.username} -> {assignment.branch}")
    except Exception as e:
        print(f"  Error checking assignments: {e}")


if __name__ == "__main__":
    debug_collection_details()
