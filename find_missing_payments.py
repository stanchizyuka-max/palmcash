#!/usr/bin/env python
"""
Find the K700 and K4,350 payments mentioned by the user
"""
import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from payments.models import Payment, PaymentCollection, MultiSchedulePayment
from expenses.models import VaultTransaction
from clients.models import Branch
from decimal import Decimal

# Get Kamwala south branch
branch = Branch.objects.get(name='Kamwala south')
today = date.today()
yesterday = today - timedelta(days=1)

print("=" * 80)
print(f"SEARCHING FOR K700 AND K4,350 PAYMENTS")
print(f"Branch: {branch.name}")
print(f"Today: {today}")
print("=" * 80)

# Search for K700 payment
print("\n1. SEARCHING FOR K700 PAYMENT")
print("-" * 80)

# Check Payment model
payment_700 = Payment.objects.filter(
    loan__loan_officer__officer_assignment__branch=branch.name,
    amount=Decimal('700.00')
).order_by('-payment_date')[:5]

if payment_700.exists():
    print(f"Found {payment_700.count()} Payment records with K700:")
    for p in payment_700:
        print(f"  - Payment ID {p.id}: K{p.amount}")
        print(f"    Loan: {p.loan.id} | Status: {p.status}")
        print(f"    Date: {p.payment_date} | Created: {p.created_at}")
        print()
else:
    print("No Payment records found with K700")

# Check PaymentCollection model
collection_700 = PaymentCollection.objects.filter(
    loan__loan_officer__officer_assignment__branch=branch.name,
    collected_amount=Decimal('700.00')
).order_by('-collection_date')[:5]

if collection_700.exists():
    print(f"\nFound {collection_700.count()} PaymentCollection records with K700:")
    for c in collection_700:
        print(f"  - Collection ID {c.id}: Collected K{c.collected_amount}")
        print(f"    Loan: {c.loan.id} | Status: {c.loan.status}")
        print(f"    Date: {c.collection_date} | Created: {c.created_at}")
        print()
else:
    print("\nNo PaymentCollection records found with K700")

# Check VaultTransaction for K700
vault_700 = VaultTransaction.objects.filter(
    branch=branch.name,
    amount=Decimal('700.00'),
    transaction_type='payment_collection'
).order_by('-transaction_date')[:5]

if vault_700.exists():
    print(f"\nFound {vault_700.count()} VaultTransaction records with K700:")
    for v in vault_700:
        print(f"  - Vault TX ID {v.id}: K{v.amount}")
        print(f"    Type: {v.transaction_type} | Vault: {v.vault_type}")
        print(f"    Date: {v.transaction_date}")
        print(f"    Description: {v.description}")
        print()
else:
    print("\nNo VaultTransaction records found with K700")

# Search for K4,350 payment
print("\n2. SEARCHING FOR K4,350 PAYMENT")
print("-" * 80)

# Check Payment model
payment_4350 = Payment.objects.filter(
    loan__loan_officer__officer_assignment__branch=branch.name,
    amount=Decimal('4350.00')
).order_by('-payment_date')[:5]

if payment_4350.exists():
    print(f"Found {payment_4350.count()} Payment records with K4,350:")
    for p in payment_4350:
        print(f"  - Payment ID {p.id}: K{p.amount}")
        print(f"    Loan: {p.loan.id} | Status: {p.status}")
        print(f"    Date: {p.payment_date} | Created: {p.created_at}")
        print()
else:
    print("No Payment records found with K4,350")

# Check PaymentCollection model
collection_4350 = PaymentCollection.objects.filter(
    loan__loan_officer__officer_assignment__branch=branch.name,
    collected_amount=Decimal('4350.00')
).order_by('-collection_date')[:5]

if collection_4350.exists():
    print(f"\nFound {collection_4350.count()} PaymentCollection records with K4,350:")
    for c in collection_4350:
        print(f"  - Collection ID {c.id}: Collected K{c.collected_amount}")
        print(f"    Loan: {c.loan.id} | Status: {c.loan.status}")
        print(f"    Date: {c.collection_date} | Created: {c.created_at}")
        print()
else:
    print("\nNo PaymentCollection records found with K4,350")

# Check VaultTransaction for K4,350
vault_4350 = VaultTransaction.objects.filter(
    branch=branch.name,
    amount=Decimal('4350.00'),
    transaction_type='payment_collection'
).order_by('-transaction_date')[:5]

if vault_4350.exists():
    print(f"\nFound {vault_4350.count()} VaultTransaction records with K4,350:")
    for v in vault_4350:
        print(f"  - Vault TX ID {v.id}: K{v.amount}")
        print(f"    Type: {v.transaction_type} | Vault: {v.vault_type}")
        print(f"    Date: {v.transaction_date}")
        print(f"    Description: {v.description}")
        print()
else:
    print("\nNo VaultTransaction records found with K4,350")

# Check recent vault transactions for today
print("\n3. ALL PAYMENT COLLECTIONS IN VAULT TODAY")
print("-" * 80)
vault_today = VaultTransaction.objects.filter(
    branch=branch.name,
    transaction_type='payment_collection',
    transaction_date__date=today
).order_by('-transaction_date')

if vault_today.exists():
    print(f"Found {vault_today.count()} payment collection vault transactions today:")
    total = Decimal('0')
    for v in vault_today:
        print(f"  - K{v.amount:,.2f} | {v.vault_type} vault | {v.transaction_date}")
        print(f"    Description: {v.description}")
        total += v.amount
    print(f"\nTotal vault collections today: K{total:,.2f}")
else:
    print("No payment collection vault transactions found for today")

# Check if there are manual collections (not linked to PaymentCollection)
print("\n4. CHECKING FOR MANUAL COLLECTIONS")
print("-" * 80)
manual_collections = VaultTransaction.objects.filter(
    branch=branch.name,
    transaction_type='payment_collection',
    transaction_date__date=today,
    payment__isnull=True  # Not linked to a Payment record
).order_by('-transaction_date')

if manual_collections.exists():
    print(f"Found {manual_collections.count()} manual collection vault transactions:")
    for v in manual_collections:
        print(f"  - K{v.amount:,.2f} | {v.description}")
else:
    print("No manual collections found (all are linked to Payment records)")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)
print("\nThe dashboard shows K219.64 because that's what's in PaymentCollection for today.")
print("The K700 and K4,350 payments you mentioned might be:")
print("  1. From a different date (check vault transactions above)")
print("  2. Manual vault collections (not linked to PaymentCollection)")
print("  3. Recorded in a different way")
print("\nCheck the vault transaction details above to find them.")
print("=" * 80)
