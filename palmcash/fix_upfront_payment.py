#!/usr/bin/env python
"""
Fix upfront payment for jane phiri's loan
This script updates the upfront_payment_paid field based on completed payments
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan
from payments.models import Payment
from decimal import Decimal
from django.utils import timezone

# Find jane phiri's loan
try:
    # Find the borrower
    from accounts.models import User
    jane = User.objects.get(username='jane phiri')
    
    # Find her active loan
    loan = Loan.objects.get(borrower=jane, status='active')
    
    print(f"Found loan: {loan.application_number}")
    print(f"Upfront Required: K{loan.upfront_payment_required}")
    print(f"Upfront Paid (before): K{loan.upfront_payment_paid}")
    
    # Find completed payments without a payment schedule (upfront payments)
    upfront_payments = Payment.objects.filter(
        loan=loan,
        status='completed',
        payment_schedule__isnull=True
    )
    
    print(f"Found {upfront_payments.count()} upfront payments")
    
    total_upfront_paid = Decimal('0')
    for payment in upfront_payments:
        print(f"  - Payment {payment.payment_number}: K{payment.amount}")
        total_upfront_paid += payment.amount
    
    # Update the loan
    if total_upfront_paid > 0:
        loan.upfront_payment_paid = total_upfront_paid
        loan.upfront_payment_date = upfront_payments.first().payment_date
        loan.save()
        
        print(f"\nUpdated upfront_payment_paid to: K{loan.upfront_payment_paid}")
        print("✓ Loan updated successfully!")
    else:
        print("No upfront payments found to update")
        
except User.DoesNotExist:
    print("Error: jane phiri user not found")
except Loan.DoesNotExist:
    print("Error: Active loan not found for jane phiri")
except Exception as e:
    print(f"Error: {e}")
