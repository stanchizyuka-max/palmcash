#!/usr/bin/env python
"""
Quick test script to verify PaymentCollection creation
This script can be run to test the signals and collection creation
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from payments.models import PaymentCollection, PaymentSchedule
from loans.models import Loan


def test_payment_collection_creation():
    """Test PaymentCollection creation from PaymentSchedule"""
    
    print("Testing PaymentCollection creation...")
    
    # Get a sample loan with payment schedules
    loans_with_schedules = Loan.objects.filter(payment_schedule__isnull=False).distinct()
    
    if not loans_with_schedules.exists():
        print("No loans with payment schedules found. Creating test data...")
        return create_test_data()
    
    loan = loans_with_schedules.first()
    print(f"Testing with loan: {loan.application_number}")
    
    # Get payment schedules for this loan
    schedules = PaymentSchedule.objects.filter(loan=loan)
    print(f"Found {schedules.count()} payment schedules")
    
    # Check if collections exist
    collections = PaymentCollection.objects.filter(loan=loan)
    print(f"Found {collections.count()} payment collections")
    
    # Show details
    print("\nPayment Schedules:")
    for schedule in schedules[:3]:
        print(f"  Schedule {schedule.installment_number}: Due {schedule.due_date}, Amount: K{schedule.total_amount}")
        
        collection = PaymentCollection.objects.filter(
            loan=loan,
            collection_date=schedule.due_date
        ).first()
        
        if collection:
            print(f"    -> Collection exists: Status={collection.status}, Expected=K{collection.expected_amount}, Collected=K{collection.collected_amount}")
        else:
            print(f"    -> No collection found")
    
    return True


def create_test_data():
    """Create test data for PaymentCollection"""
    
    print("Creating test data...")
    
    # Get an active loan
    active_loan = Loan.objects.filter(status='active').first()
    
    if not active_loan:
        print("No active loans found. Please create a loan first.")
        return False
    
    print(f"Using loan: {active_loan.application_number}")
    
    # Create a test payment schedule
    from datetime import date, timedelta
    
    due_date = date.today() + timedelta(days=7)
    
    schedule, created = PaymentSchedule.objects.get_or_create(
        loan=active_loan,
        installment_number=1,
        defaults={
            'due_date': due_date,
            'principal_amount': active_loan.principal_amount / 10,
            'interest_amount': Decimal('100.00'),
            'total_amount': (active_loan.principal_amount / 10) + Decimal('100.00'),
            'is_paid': False
        }
    )
    
    if created:
        print(f"Created payment schedule: Due {due_date}, Amount: K{schedule.total_amount}")
        
        # Check if collection was created by signal
        collection = PaymentCollection.objects.filter(
            loan=active_loan,
            collection_date=due_date
        ).first()
        
        if collection:
            print(f"✓ PaymentCollection created automatically: Status={collection.status}")
            return True
        else:
            print("✗ PaymentCollection was not created automatically")
            return False
    else:
        print("Payment schedule already exists")
        return True


def show_summary():
    """Show current PaymentCollection summary"""
    
    print("\n" + "="*50)
    print("CURRENT PAYMENT COLLECTION SUMMARY")
    print("="*50)
    
    total_collections = PaymentCollection.objects.count()
    scheduled = PaymentCollection.objects.filter(status='scheduled').count()
    completed = PaymentCollection.objects.filter(status='completed').count()
    
    print(f"Total Collections: {total_collections}")
    print(f"Scheduled: {scheduled}")
    print(f"Completed: {completed}")
    
    if total_collections > 0:
        from django.db.models import Sum
        total_expected = PaymentCollection.objects.aggregate(
            total=Sum('expected_amount')
        )['total'] or Decimal('0')
        
        total_collected = PaymentCollection.objects.aggregate(
            total=Sum('collected_amount')
        )['total'] or Decimal('0')
        
        print(f"Total Expected: K{total_expected:,.2f}")
        print(f"Total Collected: K{total_collected:,.2f}")
        print(f"Collection Rate: {(total_collected/total_expected*100):.1f}%" if total_expected > 0 else "N/A")


if __name__ == "__main__":
    print("PaymentCollection Test Script")
    print("="*30)
    
    # Show current state
    show_summary()
    
    # Test collection creation
    success = test_payment_collection_creation()
    
    # Show final state
    show_summary()
    
    if success:
        print("\n✓ Test completed successfully!")
        print("You can now check the Collection Details page.")
    else:
        print("\n✗ Test failed. Please check the error messages above.")
