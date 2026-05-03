#!/usr/bin/env python
"""
Fix missing loan disbursement vault transactions.
This script finds all disbursed loans that don't have corresponding vault transactions
and creates them.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan, DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from clients.models import Branch
from django.db import transaction as db_transaction
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 80)
print("FIXING MISSING LOAN DISBURSEMENT VAULT TRANSACTIONS")
print("=" * 80)

# Find all disbursed/active/completed loans
disbursed_loans = Loan.objects.filter(
    status__in=['disbursed', 'active', 'completed', 'defaulted'],
    disbursement_date__isnull=False
).select_related('loan_officer', 'borrower').order_by('disbursement_date')

print(f"\nFound {disbursed_loans.count()} disbursed loans")
print("\nChecking which ones are missing vault transactions...\n")

fixed_count = 0
error_count = 0
already_exists_count = 0

for loan in disbursed_loans:
    # Check if vault transaction already exists
    existing_tx = VaultTransaction.objects.filter(
        loan=loan,
        transaction_type='loan_disbursement',
        direction='out'
    ).first()
    
    if existing_tx:
        already_exists_count += 1
        print(f"✓ {loan.application_number}: Vault transaction already exists (K{loan.principal_amount:,.2f})")
        continue
    
    # Get the loan officer's branch
    officer = loan.loan_officer
    if not officer:
        error_count += 1
        print(f"✗ {loan.application_number}: No loan officer found - SKIPPED")
        continue
    
    if not hasattr(officer, 'officer_assignment'):
        error_count += 1
        print(f"✗ {loan.application_number}: Officer {officer.get_full_name()} has no branch assignment - SKIPPED")
        continue
    
    # Get branch object - handle both Branch object and string cases
    branch_ref = officer.officer_assignment.branch
    
    if isinstance(branch_ref, Branch):
        branch = branch_ref
    elif isinstance(branch_ref, str):
        # If it's a string, look up the branch
        branch = Branch.objects.filter(name__iexact=branch_ref).first()
        if not branch:
            error_count += 1
            print(f"✗ {loan.application_number}: Branch '{branch_ref}' not found - SKIPPED")
            continue
    else:
        error_count += 1
        print(f"✗ {loan.application_number}: Invalid branch reference type: {type(branch_ref)} - SKIPPED")
        continue
    
    vault_type = loan.repayment_frequency  # 'daily' or 'weekly'
    
    try:
        with db_transaction.atomic():
            # Get or create the appropriate vault
            if vault_type == 'daily':
                vault, _ = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            
            # Update vault balance (subtract disbursement)
            vault.balance -= loan.principal_amount
            vault.total_outflows += loan.principal_amount
            vault.last_transaction_date = loan.disbursement_date
            vault.save(update_fields=['balance', 'total_outflows', 'last_transaction_date', 'updated_at'])
            
            # Create vault transaction
            VaultTransaction.objects.create(
                transaction_type='loan_disbursement',
                direction='out',
                branch=branch.name,
                vault_type=vault_type,
                amount=loan.principal_amount,
                balance_after=vault.balance,
                description=f'Disbursement for {loan.application_number} ({vault_type} vault) - RETROACTIVE FIX',
                reference_number=f'DISB-{loan.application_number}',
                loan=loan,
                recorded_by=officer,
                transaction_date=loan.disbursement_date,
            )
            
            fixed_count += 1
            print(f"✓ {loan.application_number}: Created vault transaction for K{loan.principal_amount:,.2f} in {branch.name} {vault_type} vault")
            
    except Exception as e:
        error_count += 1
        logger.error(f"Error fixing {loan.application_number}: {e}", exc_info=True)
        print(f"✗ {loan.application_number}: ERROR - {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total loans checked: {disbursed_loans.count()}")
print(f"Already had vault transactions: {already_exists_count}")
print(f"Successfully fixed: {fixed_count}")
print(f"Errors/Skipped: {error_count}")
print("=" * 80)

if fixed_count > 0:
    print(f"\n✓ Successfully created {fixed_count} missing disbursement vault transactions!")
    print("  The vault balances have been updated accordingly.")
    print("\n⚠️  NOTE: Vault balances have been REDUCED by the disbursement amounts.")
    print("  If your vault balance is now negative, you may need to inject capital.")
else:
    print("\n✓ No missing disbursement transactions found. All loans are properly recorded!")
