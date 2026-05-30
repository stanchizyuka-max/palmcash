#!/usr/bin/env python
"""
Diagnose why Chazanga branch payments on Thursday weren't recorded in vault
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from payments.models import Payment
from expenses.models import VaultTransaction
from clients.models import Branch
from django.utils import timezone

# Get Thursday's date (adjust as needed)
# Assuming "Thursday" means the most recent Thursday
today = timezone.now().date()
days_since_thursday = (today.weekday() - 3) % 7
last_thursday = today - timedelta(days=days_since_thursday if days_since_thursday > 0 else 0)

print('=' * 70)
print('CHAZANGA VAULT RECORDING DIAGNOSTIC')
print('=' * 70)
print(f'Checking date: {last_thursday}')
print()

# Check if Chazanga branch exists
print('1. CHECKING BRANCH')
print('-' * 70)
chazanga_branches = Branch.objects.filter(name__icontains='chazanga')
print(f'Branches matching "chazanga": {chazanga_branches.count()}')
for branch in chazanga_branches:
    print(f'  - {branch.name} (ID: {branch.id})')

if not chazanga_branches.exists():
    print('  ⚠️  WARNING: No branch found with "chazanga" in name!')
    print('  Available branches:')
    for branch in Branch.objects.all():
        print(f'    - {branch.name}')
print()

# Get Chazanga payments on Thursday
print('2. PAYMENTS FROM CHAZANGA ON THURSDAY')
print('-' * 70)

# Try different branch name variations
branch_variations = ['Chazanga', 'chazanga', 'CHAZANGA']
all_chazanga_payments = Payment.objects.none()

for branch_name in branch_variations:
    payments = Payment.objects.filter(
        loan__loan_officer__officer_assignment__branch__iexact=branch_name,
        payment_date__date=last_thursday,
        status='completed'
    ).select_related('loan', 'loan__loan_officer', 'processed_by')
    
    if payments.exists():
        print(f'Found {payments.count()} payments with branch name "{branch_name}"')
        all_chazanga_payments = payments
        break

if not all_chazanga_payments.exists():
    print('⚠️  No completed payments found for Chazanga on Thursday')
    print('Checking all payments on Thursday...')
    all_thursday_payments = Payment.objects.filter(
        payment_date__date=last_thursday,
        status='completed'
    ).select_related('loan__loan_officer')
    
    print(f'Total payments on Thursday: {all_thursday_payments.count()}')
    for p in all_thursday_payments[:10]:
        officer_branch = 'N/A'
        if p.loan.loan_officer and hasattr(p.loan.loan_officer, 'officer_assignment'):
            officer_branch = p.loan.loan_officer.officer_assignment.branch
        print(f'  - Payment #{p.id}: Loan {p.loan.application_number}, Branch: {officer_branch}')
else:
    print(f'Total Chazanga payments on Thursday: {all_chazanga_payments.count()}')
    print()
    
    # Check each payment
    print('3. CHECKING VAULT TRANSACTIONS')
    print('-' * 70)
    
    for payment in all_chazanga_payments:
        print(f'\nPayment #{payment.id}:')
        print(f'  Loan: {payment.loan.application_number}')
        print(f'  Amount: K{payment.amount}')
        print(f'  Date: {payment.payment_date}')
        print(f'  Status: {payment.status}')
        
        # Check loan officer assignment
        if payment.loan.loan_officer:
            officer = payment.loan.loan_officer
            print(f'  Loan Officer: {officer.get_full_name()}')
            if hasattr(officer, 'officer_assignment') and officer.officer_assignment:
                print(f'  Officer Branch: {officer.officer_assignment.branch}')
            else:
                print(f'  ⚠️  Officer has NO branch assignment!')
        else:
            print(f'  ⚠️  Loan has NO loan officer!')
        
        # Check if vault transaction exists
        vault_tx = VaultTransaction.objects.filter(
            loan=payment.loan,
            transaction_type='payment_collection',
            amount=payment.amount,
            transaction_date__date=last_thursday
        ).first()
        
        if vault_tx:
            print(f'  ✅ Vault transaction found: #{vault_tx.id}')
            print(f'     Branch: {vault_tx.branch}')
            print(f'     Vault Type: {vault_tx.vault_type}')
            print(f'     Balance After: K{vault_tx.balance_after}')
        else:
            print(f'  ❌ NO VAULT TRANSACTION FOUND!')
            print(f'     This payment was NOT recorded in the vault!')

print()
print('=' * 70)
print('SUMMARY')
print('=' * 70)

# Count missing vault transactions
missing_count = 0
missing_amount = 0

for payment in all_chazanga_payments:
    vault_tx = VaultTransaction.objects.filter(
        loan=payment.loan,
        transaction_type='payment_collection',
        amount=payment.amount,
        transaction_date__date=last_thursday
    ).first()
    
    if not vault_tx:
        missing_count += 1
        missing_amount += payment.amount

print(f'Total Chazanga payments on Thursday: {all_chazanga_payments.count()}')
print(f'Payments missing vault transactions: {missing_count}')
print(f'Total amount not recorded in vault: K{missing_amount:,.2f}')

if missing_count > 0:
    print()
    print('POSSIBLE CAUSES:')
    print('1. Loan officers not assigned to Chazanga branch')
    print('2. Branch name mismatch (e.g., "Chazanga" vs "chazanga")')
    print('3. Database error during vault recording (silently caught)')
    print('4. Branch object not found in database')
    print()
    print('RECOMMENDED ACTIONS:')
    print('1. Check loan officer assignments for Chazanga')
    print('2. Verify branch name consistency')
    print('3. Run fix script to record missing vault transactions')
    print('4. Update payment confirmation to log vault errors properly')
