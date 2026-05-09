#!/usr/bin/env python
"""
Automatically fix missing vault transaction for Inonge's loan (LV-000035)
No manual confirmation required - runs automatically
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
print("AUTO-FIX: MISSING VAULT TRANSACTION FOR INONGE'S LOAN")
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

print(f"\n❌ Confirmed: No vault transaction exists")

# Get branch
branch_name = None
if loan.loan_officer and hasattr(loan.loan_officer, 'officer_assignment'):
    branch_name = loan.loan_officer.officer_assignment.branch
    print(f"Branch: {branch_name}")

if not branch_name:
    print("\n❌ Could not determine branch. Exiting.")
    exit()

# Determine vault type
vault_type = 'weekly' if loan.repayment_frequency == 'weekly' else 'daily'
print(f"Vault type: {vault_type}")

# Get current vault balance
from loans import vault_services

branch_obj = Branch.objects.filter(name__iexact=branch_name).first()
if not branch_obj:
    print(f"\n❌ Branch '{branch_name}' not found in database")
    exit()

vault_balances = vault_services.get_vault_balances(branch_obj)
current_balance = vault_balances.get(vault_type, Decimal('0.00'))
new_balance = current_balance - loan.principal_amount

print(f"\nCurrent {vault_type} vault balance: K{current_balance}")
print(f"New balance after disbursement: K{new_balance}")

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
            description=f"Loan disbursement to {loan.borrower.get_full_name()} - RETROACTIVE ENTRY (Auto-fixed)",
            reference_number=ref_number,
            loan=loan,
            recorded_by=loan.loan_officer,
            transaction_date=loan.disbursement_date
        )
        
        print(f"\n✅ SUCCESS! Vault transaction created!")
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
    import traceback
    traceback.print_exc()
    exit()

print("\n" + "="*70)
print("DONE - VAULT TRANSACTION FIXED")
print("="*70)

print("\n💡 WHAT WAS FIXED:")
print(f"  ✅ Created vault transaction for loan {loan.application_number}")
print(f"  ✅ Debited K{loan.principal_amount} from {vault_type} vault")
print(f"  ✅ Updated vault balance from K{current_balance} to K{new_balance}")
print(f"  ✅ Linked transaction to loan")
print(f"  ✅ Set transaction date to {loan.disbursement_date}")

print("\n📊 VERIFICATION:")
print("  1. Check vault balance in dashboard - should show K1,273.00")
print("  2. Check vault transactions list - should show the disbursement")
print("  3. Check loan detail page - should show vault transaction linked")

print("\n" + "="*70 + "\n")

