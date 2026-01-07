#!/usr/bin/env python
"""
Script to create PaymentCollection records for existing PaymentSchedule records
Run this script to populate PaymentCollection data for existing loans
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
from django.db.models import Sum
from payments.models import PaymentCollection, PaymentSchedule
from loans.models import Loan


def create_payment_collections():
    """Create PaymentCollection records for existing PaymentSchedule records"""
    
    print("Starting PaymentCollection creation process...")
    
    # Get all payment schedules that don't have corresponding collections
    payment_schedules = PaymentSchedule.objects.all()
    total_schedules = payment_schedules.count()
    created_count = 0
    skipped_count = 0
    
    print(f"Found {total_schedules} payment schedules to process")
    
    for schedule in payment_schedules:
        try:
            # Check if PaymentCollection already exists
            existing_collection = PaymentCollection.objects.filter(
                loan=schedule.loan,
                collection_date=schedule.due_date
            ).first()
            
            if existing_collection:
                print(f"Skipping - Collection already exists for Loan {schedule.loan.application_number} on {schedule.due_date}")
                skipped_count += 1
                continue
            
            # Create new PaymentCollection
            collection = PaymentCollection.objects.create(
                loan=schedule.loan,
                collection_date=schedule.due_date,
                expected_amount=schedule.total_amount,
                collected_amount=Decimal('0'),
                status='completed' if schedule.is_paid else 'scheduled'
            )
            
            # If payment schedule is paid, update collection details
            if schedule.is_paid:
                collection.collected_amount = schedule.total_amount
                collection.actual_collection_date = timezone.now()
                collection.status = 'completed'
                collection.save()
            
            created_count += 1
            print(f"Created collection for Loan {schedule.loan.application_number} on {schedule.due_date} - Status: {collection.status}")
            
        except Exception as e:
            print(f"Error processing schedule {schedule.id}: {e}")
    
    print(f"\nProcess completed!")
    print(f"Total schedules processed: {total_schedules}")
    print(f"Collections created: {created_count}")
    print(f"Collections skipped (already exist): {skipped_count}")


def update_collections_from_payments():
    """Update PaymentCollection records from actual Payment records"""
    
    print("\nUpdating collections from actual payments...")
    
    from payments.models import Payment
    
    payments = Payment.objects.filter(status='completed')
    updated_count = 0
    
    for payment in payments:
        try:
            # Find corresponding collection
            collection = PaymentCollection.objects.filter(
                loan=payment.loan,
                collection_date=payment.payment_date.date()
            ).first()
            
            if collection:
                # Update collection with payment details
                collection.collected_amount = payment.amount
                collection.collected_by = payment.processed_by
                collection.actual_collection_date = payment.payment_date
                collection.status = 'completed'
                collection.is_partial = payment.amount < collection.expected_amount
                collection.save()
                
                updated_count += 1
                print(f"Updated collection for Loan {payment.loan.application_number} with payment K{payment.amount}")
            else:
                print(f"No collection found for payment {payment.payment_number}")
                
        except Exception as e:
            print(f"Error updating collection from payment {payment.payment_number}: {e}")
    
    print(f"Updated {updated_count} collections from payment records")


def print_summary():
    """Print summary of current PaymentCollection data"""
    
    print("\n" + "="*50)
    print("PAYMENT COLLECTION SUMMARY")
    print("="*50)
    
    total_collections = PaymentCollection.objects.count()
    scheduled_collections = PaymentCollection.objects.filter(status='scheduled').count()
    completed_collections = PaymentCollection.objects.filter(status='completed').count()
    
    total_expected = PaymentCollection.objects.aggregate(
        total=Sum('expected_amount')
    )['total'] or Decimal('0')
    
    total_collected = PaymentCollection.objects.aggregate(
        total=Sum('collected_amount')
    )['total'] or Decimal('0')
    
    print(f"Total Collections: {total_collections}")
    print(f"Scheduled: {scheduled_collections}")
    print(f"Completed: {completed_collections}")
    print(f"Total Expected: K{total_expected:,.2f}")
    print(f"Total Collected: K{total_collected:,.2f}")
    print(f"Collection Rate: {(total_collected/total_expected*100):.1f}%" if total_expected > 0 else "N/A")


if __name__ == "__main__":
    print("PaymentCollection Data Migration Script")
    print("="*40)
    
    # Show current state
    print_summary()
    
    # Create collections from payment schedules
    create_payment_collections()
    
    # Update collections from actual payments
    update_collections_from_payments()
    
    # Show final state
    print_summary()
    
    print("\nScript completed successfully!")
    print("You can now check the Collection Details page to see the data.")
