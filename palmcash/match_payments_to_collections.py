#!/usr/bin/env python
"""
Script to match existing payments to PaymentCollection records
This will update collections with actual payment data
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
from payments.models import PaymentCollection, Payment
from loans.models import Loan


def match_payments_to_collections():
    """Match existing payments to collections"""
    
    print("Matching payments to collections...")
    
    # Get all completed payments
    completed_payments = Payment.objects.filter(status='completed')
    print(f"Found {completed_payments.count()} completed payments")
    
    updated_count = 0
    matched_count = 0
    
    for payment in completed_payments:
        try:
            # Try to find collection by loan and date (exact match first)
            payment_date = payment.payment_date.date()
            collection = PaymentCollection.objects.filter(
                loan=payment.loan,
                collection_date=payment_date
            ).first()
            
            if collection:
                # Update existing collection
                collection.collected_amount = payment.amount
                collection.collected_by = payment.processed_by
                collection.actual_collection_date = payment.payment_date
                collection.status = 'completed'
                collection.is_partial = payment.amount < collection.expected_amount
                collection.save()
                
                updated_count += 1
                print(f"✓ Updated collection for Loan {payment.loan.application_number} - Payment K{payment.amount}")
            else:
                # Try to find nearest collection date for this loan
                nearest_collection = PaymentCollection.objects.filter(
                    loan=payment.loan,
                    status='scheduled'
                ).order_by('collection_date').first()
                
                if nearest_collection:
                    # Update nearest collection
                    nearest_collection.collected_amount = payment.amount
                    nearest_collection.collected_by = payment.processed_by
                    nearest_collection.actual_collection_date = payment.payment_date
                    nearest_collection.status = 'completed'
                    nearest_collection.is_partial = payment.amount < nearest_collection.expected_amount
                    nearest_collection.save()
                    
                    matched_count += 1
                    print(f"✓ Matched payment to nearest collection for Loan {payment.loan.application_number} - Payment K{payment.amount}")
                else:
                    # Create new collection if none exists
                    PaymentCollection.objects.create(
                        loan=payment.loan,
                        collection_date=payment_date,
                        expected_amount=payment.amount,
                        collected_amount=payment.amount,
                        status='completed',
                        collected_by=payment.processed_by,
                        actual_collection_date=payment.payment_date,
                        is_partial=False
                    )
                    
                    updated_count += 1
                    print(f"✓ Created new collection for Loan {payment.loan.application_number} - Payment K{payment.amount}")
                    
        except Exception as e:
            print(f"Error processing payment {payment.payment_number}: {e}")
    
    print(f"\nResults:")
    print(f"Updated existing collections: {updated_count}")
    print(f"Matched to nearest collections: {matched_count}")


def update_upfront_payments():
    """Update collections for upfront payments"""
    
    print("\nUpdating upfront payments...")
    
    # Get loans with upfront payments
    loans_with_upfront = Loan.objects.filter(upfront_payment_paid__gt=0)
    print(f"Found {loans_with_upfront.count()} loans with upfront payments")
    
    updated_count = 0
    
    for loan in loans_with_upfront:
        try:
            # Find or create collection for upfront payment
            upfront_date = loan.upfront_payment_date.date() if loan.upfront_payment_date else loan.application_date
            
            collection, created = PaymentCollection.objects.get_or_create(
                loan=loan,
                collection_date=upfront_date,
                defaults={
                    'expected_amount': loan.upfront_payment_paid,
                    'collected_amount': loan.upfront_payment_paid,
                    'status': 'completed',
                    'actual_collection_date': loan.upfront_payment_date or timezone.now(),
                    'is_partial': False
                }
            )
            
            if not created:
                # Update existing collection
                collection.collected_amount = loan.upfront_payment_paid
                collection.status = 'completed'
                collection.actual_collection_date = loan.upfront_payment_date or timezone.now()
                collection.save()
            
            updated_count += 1
            print(f"✓ Updated upfront payment collection for Loan {loan.application_number} - K{loan.upfront_payment_paid}")
            
        except Exception as e:
            print(f"Error processing upfront payment for Loan {loan.application_number}: {e}")
    
    print(f"Updated {updated_count} upfront payment collections")


def print_final_summary():
    """Print final summary of all collections"""
    
    print("\n" + "="*60)
    print("FINAL PAYMENT COLLECTION SUMMARY")
    print("="*60)
    
    total_collections = PaymentCollection.objects.count()
    scheduled = PaymentCollection.objects.filter(status='scheduled').count()
    completed = PaymentCollection.objects.filter(status='completed').count()
    
    print(f"Total Collections: {total_collections}")
    print(f"Scheduled: {scheduled}")
    print(f"Completed: {completed}")
    
    if total_collections > 0:
        total_expected = PaymentCollection.objects.aggregate(
            total=Sum('expected_amount')
        )['total'] or Decimal('0')
        
        total_collected = PaymentCollection.objects.aggregate(
            total=Sum('collected_amount')
        )['total'] or Decimal('0')
        
        print(f"Total Expected: K{total_expected:,.2f}")
        print(f"Total Collected: K{total_collected:,.2f}")
        print(f"Collection Rate: {(total_collected/total_expected*100):.1f}%" if total_expected > 0 else "N/A")
        
        # Show breakdown by loan
        print(f"\nCollections by Loan:")
        loans = Loan.objects.filter(collections__isnull=False).distinct()
        for loan in loans[:10]:  # Show first 10 loans
            collections = PaymentCollection.objects.filter(loan=loan)
            loan_total_expected = collections.aggregate(total=Sum('expected_amount'))['total'] or Decimal('0')
            loan_total_collected = collections.aggregate(total=Sum('collected_amount'))['total'] or Decimal('0')
            completed_count = collections.filter(status='completed').count()
            
            print(f"  {loan.application_number}: {collections.count()} collections, K{loan_total_collected:,.2f} collected ({completed_count} completed)")


if __name__ == "__main__":
    print("Payment Matching Script")
    print("="*30)
    
    # Show current state
    print_final_summary()
    
    # Match payments to collections
    match_payments_to_collections()
    
    # Update upfront payments
    update_upfront_payments()
    
    # Show final state
    print_final_summary()
    
    print("\n✅ Script completed successfully!")
    print("Now check the Collection Details page to see all payment data!")
