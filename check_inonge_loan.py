#!/usr/bin/env python
"""
Check Inonge's loan in Kamwala South branch
Verify if disbursement was recorded in vault
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan
from expenses.models import VaultTransaction
from accounts.models import User
from clients.models import Branch

print("\n" + "="*70)
print("CHECK INONGE'S LOAN - KAMWALA SOUTH BRANCH")
print("="*70)

# Find Inonge
print("\n🔍 Searching for borrower 'Inonge'...")
borrowers = User.objects.filter(
    role='borrower',
    first_name__icontains='inonge'
) | User.objects.filter(
    role='borrower',
    last_name__icontains='inonge'
)

if not borrowers.exists():
    print("❌ No borrower found with name 'Inonge'")
    print("\nSearching all borrowers with similar names...")
    similar = User.objects.filter(role='borrower').filter(
        first_name__icontains='ino'
    ) | User.objects.filter(role='borrower').filter(
        last_name__icontains='ino'
    )
    if similar.exists():
        print(f"\nFound {similar.count()} similar name(s):")
        for user in similar:
            print(f"  - {user.get_full_name()} (ID: {user.id})")
    exit()

print(f"\n✅ Found {borrowers.count()} borrower(s) named Inonge:")
for borrower in borrowers:
    print(f"  - {borrower.get_full_name()} (ID: {borrower.id})")

# Check loans for each Inonge
for borrower in borrowers:
    print("\n" + "="*70)
    print(f"CHECKING LOANS FOR: {borrower.get_full_name()}")
    print("="*70)
    
    # Get all loans for this borrower
    loans = Loan.objects.filter(borrower=borrower).order_by('-disbursement_date')
    
    if not loans.exists():
        print(f"\n❌ No loans found for {borrower.get_full_name()}")
        continue
    
    print(f"\n📊 Total loans: {loans.count()}")
    
    # Check each loan
    for i, loan in enumerate(loans, 1):
        print(f"\n{'-'*70}")
        print(f"LOAN #{i}")
        print(f"{'-'*70}")
        print(f"Loan Number:        {loan.loan_number}")
        print(f"Status:             {loan.status}")
        print(f"Amount:             K{loan.loan_amount}")
        print(f"Disbursement Date:  {loan.disbursement_date}")
        print(f"Repayment Type:     {loan.get_repayment_frequency_display()}")
        
        # Get branch info
        branch_name = "Unknown"
        if hasattr(loan, 'application') and loan.application:
            if hasattr(loan.application.loan_officer, 'officer_assignment'):
                branch_name = loan.application.loan_officer.officer_assignment.branch
        
        print(f"Branch:             {branch_name}")
        
        # Check if this is Kamwala South
        is_kamwala_south = 'kamwala' in branch_name.lower() and 'south' in branch_name.lower()
        if is_kamwala_south:
            print(f"\n✅ This loan is in KAMWALA SOUTH BRANCH")
        
        # Check if loan is active
        if loan.status == 'active':
            print(f"\n✅ Loan is ACTIVE")
            
            # Check for vault transaction
            print(f"\n🔍 Checking vault transactions for this disbursement...")
            
            vault_txs = VaultTransaction.objects.filter(
                loan=loan,
                transaction_type='loan_disbursement',
                direction='out',
                amount=loan.loan_amount
            )
            
            if vault_txs.exists():
                print(f"\n✅ Found {vault_txs.count()} vault transaction(s):")
                for vtx in vault_txs:
                    print(f"\n  Vault Transaction ID: {vtx.id}")
                    print(f"  Branch:               {vtx.branch}")
                    print(f"  Vault Type:           {vtx.vault_type}")
                    print(f"  Amount:               K{vtx.amount}")
                    print(f"  Direction:            {vtx.direction}")
                    print(f"  Transaction Date:     {vtx.transaction_date}")
                    print(f"  Reference:            {vtx.reference_number}")
                    print(f"  Balance After:        K{vtx.balance_after}")
                    print(f"  Description:          {vtx.description}")
            else:
                print(f"\n❌ NO VAULT TRANSACTION FOUND!")
                print(f"\n⚠️  PROBLEM DETECTED:")
                print(f"   Loan {loan.loan_number} is ACTIVE")
                print(f"   Amount: K{loan.loan_amount}")
                print(f"   Disbursed: {loan.disbursement_date}")
                print(f"   But NO vault transaction recorded!")
                print(f"\n   This means the vault was NOT debited for this disbursement.")
                
                # Check if there are any vault transactions for this branch around that date
                print(f"\n🔍 Checking other vault transactions around disbursement date...")
                from datetime import timedelta
                date_from = loan.disbursement_date - timedelta(days=1)
                date_to = loan.disbursement_date + timedelta(days=1)
                
                nearby_txs = VaultTransaction.objects.filter(
                    branch__icontains='kamwala',
                    transaction_date__date__gte=date_from,
                    transaction_date__date__lte=date_to,
                    transaction_type='loan_disbursement'
                ).order_by('transaction_date')
                
                if nearby_txs.exists():
                    print(f"\n   Found {nearby_txs.count()} disbursement(s) around that date:")
                    for tx in nearby_txs:
                        print(f"   - {tx.transaction_date.date()} | K{tx.amount} | {tx.description[:40]}")
                else:
                    print(f"\n   No other disbursements found around {loan.disbursement_date}")
        else:
            print(f"\n⚠️  Loan status: {loan.status} (not active)")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

# Count active loans without vault transactions
active_loans_no_vault = 0
for borrower in borrowers:
    loans = Loan.objects.filter(borrower=borrower, status='active')
    for loan in loans:
        vault_txs = VaultTransaction.objects.filter(
            loan=loan,
            transaction_type='loan_disbursement',
            direction='out'
        )
        if not vault_txs.exists():
            active_loans_no_vault += 1

if active_loans_no_vault > 0:
    print(f"\n⚠️  Found {active_loans_no_vault} active loan(s) without vault transactions")
    print(f"\n💡 RECOMMENDED ACTION:")
    print(f"   1. Verify the loan details above")
    print(f"   2. Check if disbursement actually happened")
    print(f"   3. If disbursement happened, create vault transaction manually")
    print(f"   4. Or use a script to retroactively record the disbursement")
else:
    print(f"\n✅ All active loans have vault transactions recorded")

print("\n" + "="*70)
print("END OF CHECK")
print("="*70 + "\n")

