#!/usr/bin/env python
"""
Fix missing vault transactions for Chazanga branch payments on Thursday
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
from loans.vault_services import record_payment_collection

# Get Thursday's date
today = timezone.now().date()
days_since_thursday = (today.weekday() - 3) % 7
last_thursday = today - timedelta(days=days_since_thursday if days_since_thursday > 0 else 0)

print('=' * 70)
print('FIXING CHAZANGA VAULT TRANSACTIONS')
print('=' * 70)
print(f'Target date: {last_thursday}')
print()

# Get Chazanga branch
chazanga = Branch.objects.filter(name__icontains='chazanga').first()
if not chazanga:
    print('❌ ERROR: Chazanga branch not found!')
    print('Available branches:')
    for branch in Branch.objects.all():
        print(f'  - {branch.name}')
    exit(1)

print(f'✅ Found branch: {chazanga.name}')
print()

# Get Chazanga payments on Thursday
payments = Payment.objects.filter(
    loan__loan_officer__officer_assignment__branch__iexact=chazanga.name,
    payment_date__date=last_thursday,
    status='completed'
).select_related('loan', 'loan__loan_officer', 'processed_by')

print(f'Found {payments.count()} completed payments from Chazanga on Thursday')
print()

if payments.count() == 0:
    print('No payments to fix.')
    exit(0)

# Check and fix each payment
fixed_count = 0
skipped_count = 0
error_count = 0
total_amount_fixed = 0

for payment in payments:
    print(f'Processing Payment #{payment.id}:')
    print(f'  Loan: {payment.loan.application_number}')
    print(f'  Amount: K{payment.amount}')
    print(f'  Date: {payment.payment_date}')
    
    # Check if vault transaction already exists
    existing_vault_tx = VaultTransaction.objects.filter(
        loan=payment.loan,
        transaction_type='payment_collection',
        amount=payment.amount,
        transaction_date__date=last_thursday
    ).first()
    
    if existing_vault_tx:
        print(f'  ⏭️  SKIPPED: Vault transaction already exists (#{existing_vault_tx.id})')
        skipped_count += 1
    else:
        # Record the missing vault transaction
        try:
            vault_tx = record_payment_collection(
                loan=payment.loan,
                amount=payment.amount,
                recorded_by=payment.processed_by or payment.loan.loan_officer
            )
            
            if vault_tx:
                print(f'  ✅ FIXED: Created vault transaction #{vault_tx.id}')
                print(f'     Branch: {vault_tx.branch}')
                print(f'     Vault Type: {vault_tx.vault_type}')
                print(f'     Balance After: K{vault_tx.balance_after}')
                fixed_count += 1
                total_amount_fixed += payment.amount
            else:
                print(f'  ❌ ERROR: record_payment_collection returned None')
                print(f'     Possible cause: Branch not found for loan officer')
                error_count += 1
        except Exception as e:
            print(f'  ❌ ERROR: {e}')
            error_count += 1
    
    print()

print('=' * 70)
print('SUMMARY')
print('=' * 70)
print(f'Total payments processed: {payments.count()}')
print(f'Vault transactions created: {fixed_count}')
print(f'Already existed (skipped): {skipped_count}')
print(f'Errors: {error_count}')
print(f'Total amount recorded in vault: K{total_amount_fixed:,.2f}')
print()

if fixed_count > 0:
    print('✅ Fix completed successfully!')
    print()
    print('NEXT STEPS:')
    print('1. Verify vault balance for Chazanga branch')
    print('2. Check vault transaction history')
    print('3. Update payment confirmation code to log vault errors')
elif error_count > 0:
    print('⚠️  Some payments could not be fixed.')
    print('Please check loan officer assignments and branch names.')
else:
    print('ℹ️  All payments already had vault transactions.')
