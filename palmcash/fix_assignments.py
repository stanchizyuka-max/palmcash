#!/usr/bin/env python
"""
Script to fix loan officer assignments and update collections
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from accounts.models import User
from payments.models import PaymentCollection, Payment
from loans.models import Loan


def assign_loans_to_officer():
    """Assign existing loans to the loan officer"""
    
    print("Assigning loans to loan officer...")
    
    # Get the loan officer
    loan_officer = User.objects.filter(role='loan_officer').first()
    if not loan_officer:
        print("No loan officer found!")
        return
    
    print(f"Found loan officer: {loan_officer.username}")
    
    # Get all loans without loan officer
    unassigned_loans = Loan.objects.filter(loan_officer__isnull=True)
    print(f"Found {unassigned_loans.count()} unassigned loans")
    
    # Assign loans to the officer
    count = unassigned_loans.update(loan_officer=loan_officer)
    print(f"Assigned {count} loans to {loan_officer.username}")
    
    return loan_officer


def update_collections_from_payments():
    """Update collections with actual payment amounts"""
    
    print("\nUpdating collections from payments...")
    
    # Get all completed payments
    completed_payments = Payment.objects.filter(status='completed')
    print(f"Found {completed_payments.count()} completed payments")
    
    updated_count = 0
    
    for payment in completed_payments:
        try:
            # Find collection for this loan (any date)
            collection = PaymentCollection.objects.filter(
                loan=payment.loan
            ).first()
            
            if collection and collection.collected_amount == 0:
                # Update the first collection for this loan
                collection.collected_amount = payment.amount
                collection.collected_by = payment.processed_by
                collection.actual_collection_date = payment.payment_date
                collection.status = 'completed'
                collection.is_partial = payment.amount < collection.expected_amount
                collection.save()
                
                updated_count += 1
                print(f"✓ Updated collection for Loan {payment.loan.application_number} - K{payment.amount}")
                
        except Exception as e:
            print(f"Error updating collection for payment {payment.payment_number}: {e}")
    
    print(f"Updated {updated_count} collections with payment data")


def show_final_status():
    """Show final status after fixes"""
    
    print("\n" + "="*60)
    print("FINAL STATUS")
    print("="*60)
    
    # Check loan officer
    loan_officer = User.objects.filter(role='loan_officer').first()
    if loan_officer:
        officer_loans = Loan.objects.filter(loan_officer=loan_officer)
        officer_collections = PaymentCollection.objects.filter(
            loan__loan_officer=loan_officer
        )
        
        print(f"Loan Officer: {loan_officer.username}")
        print(f"  Assigned Loans: {officer_loans.count()}")
        print(f"  Collections: {officer_collections.count()}")
        
        if officer_collections.exists():
            total_collected = officer_collections.aggregate(
                total=Sum('collected_amount')
            )['total'] or 0
            
            completed_count = officer_collections.filter(status='completed').count()
            print(f"  Total Collected: K{total_collected:,.2f}")
            print(f"  Completed Collections: {completed_count}")
    
    # Check manager
    manager = User.objects.filter(role='manager').first()
    if manager:
        manager_collections = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=manager.managed_branch.name
        )
        print(f"\nManager: {manager.username}")
        print(f"  Branch: {manager.managed_branch.name}")
        print(f"  Collections: {manager_collections.count()}")


if __name__ == "__main__":
    print("Loan Assignment and Collection Update Script")
    print("="*50)
    
    # Assign loans to officer
    loan_officer = assign_loans_to_officer()
    
    # Update collections with payment data
    update_collections_from_payments()
    
    # Show final status
    show_final_status()
    
    print("\n✅ Script completed!")
    print("Now check the Collection Details page as different users:")
    print("- Admin should see all collections")
    print("- Loan officer should see their assigned collections")
    print("- Manager should see branch collections")
