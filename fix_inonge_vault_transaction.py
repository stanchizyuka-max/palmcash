#!/usr/bin/env python
"""
Fix missing vault transaction for Inonge's loan (LV-000035)
This will retroactively record the disbursement in the vault
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan
from expenses.models import VaultTransaction
from clients.models import Branch
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

print("\n" + "="*70)
print("FIX MISSING VAULT TRANSACTION FOR INONGE'S LOAN")
print("="*70)

# Get the loan
try:
    loan = Loan.objects.get(application_number='LV-000035')
except Loan.DoesNotExist:
    print("\n❌ Loan LV-000035 not found!")
    exit()

print(f"\n📋 LOAN DETAILS:")
print(f"Application Number: {loan.application_number}")
print(f"Borrower:           {loan.borrower.get_full_name()}")
print(f"Status:             {loan.status}")
print(f"Principal Amount:   K{loan.principal_amount}")
print(f"Disbursement Date:  {loan.disbursement_date}")
print(f"Loan Type:          {loan.loan_type.name if loan.loan_type else 'Unknown'}")
print(f"Repayment Freq:     {loan.get_repayment_frequency_display()}")

# Check if vault transaction already exists
existing_tx = VaultTransaction.objects.filter(
    loan=loan,
    transaction_type='loan_disbursement',
    direction='out'
)

if existing_tx.exists():
    print(f"\n✅ Vault transaction already exists!")
    print(f"Transaction ID: {existing_tx.first().id}")
    print(f"Nothing to fix.")
    exit()

print(f"\n❌ Confirmed: No vault transaction exists for this loan")

# Determine the branch
print(f"\n🔍 Determining branch...")

# Try to get branch from loan officer
branch_name = None
if loan.loan_officer and hasattr(loan.loan_officer, 'officer_assignment'):
    branch_name = loan.loan_officer.officer_assignment.branch
    print(f"Branch from loan officer: {branch_name}")
else:
    print("Could not determine branch from loan officer")
    print("\nAvailable branches:")
    branches = Branch.objects.filter(is_active=True)
    for i, branch in enumerate(branches, 1):
        print(f"  {i}. {branch.name}")
    
    branch_choice = input("\nEnter branch number (or branch name): ").strip()
    
    if branch_choice.isdigit():
        branch_idx = int(branch_choice) - 1
        if 0 <= branch_idx < branches.count():
            branch_name = branches[branch_idx].name
    else:
        branch_name = branch_choice

if not branch_name:
    print("\n❌ Branch not specified. Exiting.")
    exit()

print(f"\n✅ Using branch: {branch_name}")

# Determine vault type
vault_type = 'weekly' if loan.repayment_frequency == 'weekly' else 'daily'
print(f"Vault type: {vault_type}")

# Get current vault balance
from loans import vault_services

try:
    # Get branch object
    branch_obj = Branch.objects.filter(name__iexact=branch_name).first()
    if branch_obj:
        vault_balances = vault_services.get_vault_balances(branch_obj)
        current_balance = vault_balances.get(vault_type, Decimal('0.00'))
        print(f"\nCurrent {vault_type} vault balance: K{current_balance}")
    else:
        print(f"\n⚠️  Branch '{branch_name}' not found in database")
        current_balance = Decimal('0.00')
except Exception as e:
    print(f"\n⚠️  Could not get current vault balance: {e}")
    current_balance = Decimal('0.00')

new_balance = current_balance - loan.principal_amount
print(f"New balance after disbursement: K{new_balance}")

if new_balance < 0:
    print(f"\n⚠️  WARNING: This will result in a negative vault balance!")
    print(f"   Current: K{current_balance}")
    print(f"   Disbursement: K{loan.principal_amount}")
    print(f"   New balance: K{new_balance}")
    print(f"\n   This suggests the vault balance may be incorrect.")

# Confirmation
print("\n" + "="*70)
print("READY TO CREATE VAULT TRANSACTION")
print("="*70)
print(f"\nThis will:")
print(f"  1. Create a vault transaction for loan {loan.application_number}")
print(f"  2. Record disbursement of K{loan.principal_amount}")
print(f"  3. Debit the {vault_type} vault in {branch_name}")
print(f"  4. Set transaction date to {loan.disbursement_date}")
print(f"  5. Link transaction to the loan")

response = input("\nProceed? (yes/no): ")
if response.lower() != 'yes':
    print("\n❌ Aborted. No changes made.")
    exit()

# Create the vault transaction
print("\n🔄 Creating vault transaction...")

try:
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
            description=f"Loan disbursement to {loan.borrower.get_full_name()} - RETROACTIVE ENTRY",
            reference_number=ref_number,
            loan=loan,
            recorded_by=loan.loan_officer,
            transaction_date=loan.disbursement_date
        )
        
        print(f"\n✅ Vault transaction created successfully!")
        print(f"\nTransaction Details:")
        print(f"  ID:                 {vault_tx.id}")
        print(f"  Reference:          {vault_tx.reference_number}")
        print(f"  Branch:             {vault_tx.branch}")
        print(f"  Vault Type:         {vault_tx.vault_type}")
        print(f"  Amount:             K{vault_tx.amount}")
        print(f"  Direction:          {vault_tx.direction}")
        print(f"  Balance After:      K{vault_tx.balance_after}")
        print(f"  Transaction Date:   {vault_tx.transaction_date}")
        print(f"  Linked to Loan:     {vault_tx.loan.application_number}")

except Exception as e:
    print(f"\n❌ Error creating vault transaction: {e}")
    print("Transaction rolled back. No changes made.")
    exit()

print("\n" + "="*70)
print("DONE")
print("="*70)

print("\n💡 NEXT STEPS:")
print("1. Verify the vault balance in the dashboard")
print("2. Check the vault transactions list")
print("3. Confirm the loan shows the vault transaction")
print()

