#!/usr/bin/env python
"""
Fix Chazanga negative vault balance
This script will:
1. Identify missing vault transactions
2. Create missing payment collection transactions
3. If still negative, suggest capital injection
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from clients.models import Branch
from expenses.models import VaultTransaction
from loans.models import DailyVault, WeeklyVault
from payments.models import Payment
from loans.vault_services import record_payment_collection
from django.db.models import Sum
from decimal import Decimal

print('=' * 80)
print('FIXING CHAZANGA NEGATIVE VAULT BALANCE')
print('=' * 80)
print()

# Get Chazanga branch
chazanga = Branch.objects.get(name__iexact='chazanga')
print(f'Branch: {chazanga.name}')
print()

# Get current balance
daily_vault = DailyVault.objects.filter(branch=chazanga).first()
weekly_vault = WeeklyVault.objects.filter(branch=chazanga).first()
current_balance = (daily_vault.balance if daily_vault else Decimal(0)) + (weekly_vault.balance if weekly_vault else Decimal(0))

print(f'Current Vault Balance: K{current_balance:,.2f}')
print()

# Find payments without vault transactions
print('STEP 1: Finding payments without vault transactions')
print('-' * 80)

chazanga_payments = Payment.objects.filter(
    loan__loan_officer__officer_assignment__branch__iexact='chazanga',
    status='completed'
).select_related('loan', 'processed_by')

missing_payments = []
for payment in chazanga_payments:
    vault_tx = VaultTransaction.objects.filter(
        loan=payment.loan,
        transaction_type='payment_collection',
        amount=payment.amount
    ).first()
    
    if not vault_tx:
        missing_payments.append(payment)

print(f'Found {len(missing_payments)} payments without vault transactions')
print()

if len(missing_payments) > 0:
    print('STEP 2: Creating missing vault transactions')
    print('-' * 80)
    
    fixed_count = 0
    fixed_amount = Decimal('0')
    
    for payment in missing_payments:
        print(f'Payment #{payment.id}: Loan {payment.loan.application_number}, K{payment.amount}')
        
        try:
            vault_tx = record_payment_collection(
                loan=payment.loan,
                amount=payment.amount,
                recorded_by=payment.processed_by or payment.loan.loan_officer
            )
            
            if vault_tx:
                print(f'  ✅ Created vault transaction #{vault_tx.id}')
                fixed_count += 1
                fixed_amount += payment.amount
            else:
                print(f'  ❌ Failed: record_payment_collection returned None')
        except Exception as e:
            print(f'  ❌ Error: {e}')
        print()
    
    print(f'Created {fixed_count} vault transactions totaling K{fixed_amount:,.2f}')
    print()
    
    # Refresh vault balance
    daily_vault = DailyVault.objects.filter(branch=chazanga).first()
    weekly_vault = WeeklyVault.objects.filter(branch=chazanga).first()
    new_balance = (daily_vault.balance if daily_vault else Decimal(0)) + (weekly_vault.balance if weekly_vault else Decimal(0))
    
    print(f'New Vault Balance: K{new_balance:,.2f}')
    print(f'Change: K{(new_balance - current_balance):,.2f}')
    print()
    
    current_balance = new_balance
else:
    print('No missing payment vault transactions found')
    print()

# Check if still negative
print('=' * 80)
print('FINAL STATUS')
print('=' * 80)
print()

if current_balance < 0:
    print(f'⚠️  Vault is still NEGATIVE: K{current_balance:,.2f}')
    print()
    print('This means:')
    print('- More money was disbursed than collected')
    print('- Capital injection is needed to correct the balance')
    print()
    
    needed = abs(current_balance)
    print(f'💰 Capital injection needed: K{needed:,.2f}')
    print()
    print('To inject capital, run:')
    print(f'python manage.py shell')
    print(f'>>> from clients.models import Branch')
    print(f'>>> from loans.vault_services import record_capital_injection')
    print(f'>>> from accounts.models import User')
    print(f'>>> branch = Branch.objects.get(name__iexact="chazanga")')
    print(f'>>> admin = User.objects.filter(role="admin").first()')
    print(f'>>> record_capital_injection(branch, {needed}, "Correction for negative balance", admin, vault_type="weekly")')
    print()
elif current_balance == 0:
    print('✅ Vault balance is now ZERO')
else:
    print(f'✅ Vault balance is POSITIVE: K{current_balance:,.2f}')

print()
print('=' * 80)
print('FIX COMPLETE')
print('=' * 80)
