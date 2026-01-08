#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.contrib.auth.models import User
from payments.models import PaymentCollection
from loans.models import Loan

print("=== COLLECTION DEBUG ===")
print(f"Total PaymentCollections: {PaymentCollection.objects.count()}")
print(f"Total Loans: {Loan.objects.count()}")

# Check collections by status
print("\nCollections by status:")
for status in ['scheduled', 'in_progress', 'completed', 'cancelled']:
    count = PaymentCollection.objects.filter(status=status).count()
    print(f"  {status}: {count}")

# Check recent collections
print("\nRecent collections (last 10):")
recent = PaymentCollection.objects.order_by('-collection_date')[:10]
for collection in recent:
    print(f"  {collection.collection_date} - {collection.loan.application_number if collection.loan else 'No Loan'} - K{collection.expected_amount}")

# Check if any loans have collections
print("\nLoans with collections:")
loans_with_collections = PaymentCollection.objects.values_list('loan_id', flat=True).distinct()
print(f"  {len(loans_with_collections)} loans have collections")

# Check user roles
print("\nUsers by role:")
for role in ['admin', 'manager', 'loan_officer']:
    count = User.objects.filter(role=role).count()
    print(f"  {role}: {count}")

print("\n=== END DEBUG ===")
