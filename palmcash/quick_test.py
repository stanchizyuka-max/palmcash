#!/usr/bin/env python
"""
Quick test to verify collection assignments
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from accounts.models import User
from payments.models import PaymentCollection
from loans.models import Loan


def quick_test():
    """Quick test of collection assignments"""
    
    print("Quick Collection Test")
    print("="*30)
    
    # Test 1: Check total collections
    total = PaymentCollection.objects.count()
    print(f"Total collections in DB: {total}")
    
    # Test 2: Check loan officer assignments
    loan_officer = User.objects.filter(role='loan_officer').first()
    if loan_officer:
        officer_loans = Loan.objects.filter(loan_officer=loan_officer)
        officer_collections = PaymentCollection.objects.filter(loan__loan_officer=loan_officer)
        print(f"Loan officer {loan_officer.username}:")
        print(f"  - Assigned loans: {officer_loans.count()}")
        print(f"  - Collections: {officer_collections.count()}")
        
        # Show sample collections
        for collection in officer_collections[:3]:
            print(f"    * Loan {collection.loan.application_number}: K{collection.collected_amount} ({collection.status})")
    
    # Test 3: Test the exact query from the view
    print(f"\nTesting exact view query for loan officer:")
    if loan_officer:
        view_collections = PaymentCollection.objects.filter(
            loan__loan_officer=loan_officer
        ).order_by('-collection_date')
        print(f"View query result: {view_collections.count()} collections")
        
        # Test pagination
        from django.core.paginator import Paginator
        paginator = Paginator(view_collections, 50)
        page_obj = paginator.get_page(1)
        print(f"Page 1 collections: {len(page_obj.object_list)}")
    
    # Test 4: Check manager query
    manager = User.objects.filter(role='manager').first()
    if manager and hasattr(manager, 'managed_branch') and manager.managed_branch:
        manager_collections = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=manager.managed_branch.name
        )
        print(f"\nManager {manager.username} ({manager.managed_branch.name}):")
        print(f"  - Collections: {manager_collections.count()}")
    
    # Test 5: Admin query
    admin = User.objects.filter(role='admin').first()
    if admin:
        admin_collections = PaymentCollection.objects.all()
        print(f"\nAdmin {admin.username}:")
        print(f"  - Collections: {admin_collections.count()}")


if __name__ == "__main__":
    quick_test()
