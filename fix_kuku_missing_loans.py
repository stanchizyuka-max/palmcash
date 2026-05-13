#!/usr/bin/env python
"""
Find and fix missing vault transactions for Carol and Kaluba's loans in KUKU branch
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan
from expenses.models import VaultTransaction
from accounts.models import User
from clients.models import Branch
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

print("\n" + "="*70)
print("FIX MISSING VAULT TRANSACTIONS - KUKU BRANCH")
print("="*70)

# Search for Carol
print("\n🔍 Searching for borrower 'Carol'...")
carol_users = User.objects.filter(
    role='borrower'
).filter(
    Q(first_name__icontains='carol') | Q(last_name__icontains='carol')
)

# Search for Kaluba
print("🔍 Searching for borrower 'Kaluba'...")
from django.db.models import Q
kaluba_users = User.objects.filter(
    role='borrower'
).filter(
    Q(first_name__icontains='kaluba') | Q(last_name__icontains='kaluba')
)

borrowers = list(carol_users) + list(kaluba_users)

if not borrowers:
    print("\n❌ No borrowers found with names 'Carol' or 'Kaluba'")
    exit()

print(f"\n✅ Found {len(borrowers)} borrower(s):")
for borrower in borrowers:
    print(f"  - {borrower.get_full_name()} (ID: {borrower.id})")

# Check loans for each borrower
missing_vault_loans = []

for borrower in borrowers:
    print(f"\n{'='*70}")
    print(f"CHECKING LOANS FOR: {borrower.get_full_name()}")
    print(f"{'='*70}")
    
    loans = Loan.objects.filter(borrower=borrower, status='active').order_by('-disbursement_date')
    
    if not loans.exists():
        print(f"  No active loans found")
        continue
    
    print(f"  Found {loans.count()} active loan(s)")
    
    for loan in loans:
        # Get branch
        branch_name = "Unknown"
        if loan.loan_officer and hasattr(loan.loan_officer, 'officer_assignment'):
            branch_name = loan.loan_officer.officer_assignment.branch
        
        # Check if it's KUKU branch
        is_kuku = 'kuku' in branch_name.lower()
        
        print(f"\n  Loan: {loan.application_number}")
        print(f"    Branch: {branch_name}")
        print(f"    Amount: K{loan.principal_amount}")
        print(f"    Disbursed: {loan.disbursement_date}")
        print(f"    Type: {loan.get_repayment_frequency_display()}")
        
        if not is_kuku:
            print(f"    ⚠️  Not in KUKU branch, skipping")
            continue
        
        # Check for vault transaction
        vault_tx = VaultTransaction.objects.filter(
            loan=loan,
            transaction_type='loan_disbursement',
            direction='out'
        ).first()
        
        if vault_tx:
            print(f"    ✅ Vault transaction exists (ID: {vault_tx.id})")
        else:
            print(f"    ❌ NO VAULT TRANSACTION FOUND!")
            missing_vault_loans.append({
                'loan': loan,
                'borrower': borrower,
                'branch': branch_name
            })

if not missing_vault_loans:
    print(f"\n✅ All loans have vault transactions!")
    print(f"Nothing to fix.")
    exit()

# Show summary of missing transactions
print(f"\n{'='*70}")
print(f"MISSING VAULT TRANSACTIONS SUMMARY")
print(f"{'='*70}")

total_missing_amount = sum(item['loan'].principal_amount for item in missing_vault_loans)

print(f"\nFound {len(missing_vault_loans)} loan(s) without vault transactions:")
for i, item in enumerate(missing_vault_loans, 1):
    loan = item['loan']
    print(f"\n{i}. {item['borrower'].get_full_name()}")
    print(f"   Loan: {loan.application_number}")
    print(f"   Branch: {item['branch']}")
    print(f"   Amount: K{loan.principal_amount}")
    print(f"   Disbursed: {loan.disbursement_date}")
    print(f"   Type: {loan.get_repayment_frequency_display()}")

print(f"\nTotal amount to deduct: K{total_missing_amount}")

# Ask for confirmation
print(f"\n{'='*70}")
print(f"READY TO FIX")
print(f"{'='*70}")

response = input("\nCreate missing vault transactions? (yes/no): ")
if response.lower() != 'yes':
    print("\n❌ Aborted. No changes made.")
    exit()

# Fix each missing transaction
print(f"\n🔄 Creating vault transactions...")

from loans import vault_services

fixed_count = 0
errors = []

for item in missing_vault_loans:
    loan = item['loan']
    branch_name = item['branch']
    
    try:
        # Get branch object
        branch = Branch.objects.filter(name__iexact=branch_name).first()
        if not branch:
            errors.append(f"Branch '{branch_name}' not found for loan {loan.application_number}")
            continue
        
        # Determine vault type
        vault_type = 'weekly' if loan.repayment_frequency == 'weekly' else 'daily'
        
        # Get current balance
        vault_balances = vault_services.get_vault_balances(branch)
        current_balance = vault_balances.get(vault_type, Decimal('0.00'))
        new_balance = current_balance - loan.principal_amount
        
        print(f"\n  Fixing {loan.application_number} ({item['borrower'].get_full_name()})...")
        print(f"    Current {vault_type} vault: K{current_balance}")
        print(f"    Amount to deduct: K{loan.principal_amount}")
        print(f"    New balance: K{new_balance}")
        
        with transaction.atomic():
            # Generate reference number
            ref_number = f"RETRO-DISB-{loan.application_number}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create vault transaction
            vault_tx = VaultTransaction.objects.create(
                transaction_type='loan_disbursement',
                direction='out',
                branch=branch_name,
                vault_type=vault_type,
                amount=loan.principal_amount,
                balance_after=new_balance,
                description=f"Loan disbursement to {item['borrower'].get_full_name()} - RETROACTIVE ENTRY (Auto-fixed)",
                reference_number=ref_number,
                loan=loan,
                recorded_by=loan.loan_officer,
                transaction_date=loan.disbursement_date
            )
            
            print(f"    ✅ Created vault transaction (ID: {vault_tx.id})")
            fixed_count += 1
            
    except Exception as e:
        error_msg = f"Failed to fix {loan.application_number}: {e}"
        errors.append(error_msg)
        print(f"    ❌ {error_msg}")

# Summary
print(f"\n{'='*70}")
print(f"DONE")
print(f"{'='*70}")

print(f"\n✅ Successfully fixed: {fixed_count} loan(s)")

if errors:
    print(f"\n❌ Errors: {len(errors)}")
    for error in errors:
        print(f"  - {error}")

print(f"\n💡 NEXT STEPS:")
print(f"1. Run: python verify_kuku_vault_balance.py")
print(f"2. Check vault dashboard for KUKU branch")
print(f"3. Verify the vault balances are correct")

print(f"\n{'='*70}\n")

