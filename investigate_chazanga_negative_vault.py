#!/usr/bin/env python
"""
Investigate why Chazanga vault has negative balance
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from clients.models import Branch
from expenses.models import VaultTransaction
from loans.models import DailyVault, WeeklyVault, Loan
from payments.models import Payment
from django.db.models import Sum, Q
from decimal import Decimal

print('=' * 80)
print('CHAZANGA VAULT NEGATIVE BALANCE INVESTIGATION')
print('=' * 80)
print()

# Get Chazanga branch
chazanga = Branch.objects.get(name__iexact='chazanga')
print(f'Branch: {chazanga.name}')
print()

# Get vault balances
daily_vault = DailyVault.objects.filter(branch=chazanga).first()
weekly_vault = WeeklyVault.objects.filter(branch=chazanga).first()

print('CURRENT VAULT BALANCES')
print('-' * 80)
print(f'Daily Vault: K{daily_vault.balance if daily_vault else 0}')
print(f'Weekly Vault: K{weekly_vault.balance if weekly_vault else 0}')
print(f'Total: K{(daily_vault.balance if daily_vault else Decimal(0)) + (weekly_vault.balance if weekly_vault else Decimal(0))}')
print()

# Get all vault transactions for Chazanga
print('VAULT TRANSACTIONS SUMMARY')
print('-' * 80)
vault_txns = VaultTransaction.objects.filter(branch__iexact='chazanga').order_by('transaction_date')
print(f'Total Transactions: {vault_txns.count()}')
print()

# Summarize by type and direction
inflows = vault_txns.filter(direction='in')
outflows = vault_txns.filter(direction='out')

total_inflows = inflows.aggregate(total=Sum('amount'))['total'] or Decimal('0')
total_outflows = outflows.aggregate(total=Sum('amount'))['total'] or Decimal('0')

print(f'Total Inflows: K{total_inflows:,.2f}')
print(f'Total Outflows: K{total_outflows:,.2f}')
print(f'Net (Inflows - Outflows): K{(total_inflows - total_outflows):,.2f}')
print()

# Break down by transaction type
print('BREAKDOWN BY TRANSACTION TYPE')
print('-' * 80)

from django.db.models import Count
transaction_types = vault_txns.values('transaction_type', 'direction').annotate(
    count=Count('id'),
    total=Sum('amount')
).order_by('transaction_type')

for tx_type in transaction_types:
    direction_symbol = '➕' if tx_type['direction'] == 'in' else '➖'
    print(f"{direction_symbol} {tx_type['transaction_type']}: {tx_type['count']} transactions, K{tx_type['total']:,.2f}")
print()

# Show recent transactions
print('RECENT TRANSACTIONS (Last 20)')
print('-' * 80)
recent = vault_txns.order_by('-transaction_date')[:20]
for tx in recent:
    direction_symbol = '➕' if tx.direction == 'in' else '➖'
    loan_info = f" (Loan: {tx.loan.application_number})" if tx.loan else ""
    print(f"{tx.transaction_date.strftime('%Y-%m-%d %H:%M')} | {direction_symbol} {tx.transaction_type:25s} | K{tx.amount:>10,.2f} | Balance: K{tx.balance_after:>10,.2f}{loan_info}")
print()

# Check for loans from Chazanga
print('LOANS FROM CHAZANGA')
print('-' * 80)
chazanga_loans = Loan.objects.filter(
    loan_officer__officer_assignment__branch__iexact='chazanga'
)
print(f'Total Loans: {chazanga_loans.count()}')
print(f'Active Loans: {chazanga_loans.filter(status="active").count()}')
print(f'Completed Loans: {chazanga_loans.filter(status="completed").count()}')
print()

# Check for disbursed loans
disbursed_loans = chazanga_loans.filter(status__in=['active', 'completed', 'disbursed'])
total_disbursed = disbursed_loans.aggregate(total=Sum('principal_amount'))['total'] or Decimal('0')
print(f'Total Disbursed Amount: K{total_disbursed:,.2f}')
print()

# Check for payments
print('PAYMENTS FROM CHAZANGA')
print('-' * 80)
chazanga_payments = Payment.objects.filter(
    loan__loan_officer__officer_assignment__branch__iexact='chazanga',
    status='completed'
)
total_payments = chazanga_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
print(f'Total Completed Payments: {chazanga_payments.count()}')
print(f'Total Payment Amount: K{total_payments:,.2f}')
print()

# Calculate expected vault balance
print('=' * 80)
print('ANALYSIS')
print('=' * 80)
print()

# Expected balance based on transactions
expected_balance = total_inflows - total_outflows
actual_balance = (daily_vault.balance if daily_vault else Decimal(0)) + (weekly_vault.balance if weekly_vault else Decimal(0))

print(f'Expected Balance (from transactions): K{expected_balance:,.2f}')
print(f'Actual Balance (from vaults): K{actual_balance:,.2f}')
print(f'Discrepancy: K{(actual_balance - expected_balance):,.2f}')
print()

if actual_balance < 0:
    print('⚠️  NEGATIVE VAULT BALANCE DETECTED!')
    print()
    print('Possible Causes:')
    print('1. Loans were disbursed without sufficient capital injection')
    print('2. Security deposits were returned but not collected')
    print('3. Missing payment collection vault transactions')
    print('4. Incorrect vault transaction recording')
    print('5. Manual vault adjustments needed')
    print()
    print('Recommended Actions:')
    print('1. Review all vault transactions for accuracy')
    print('2. Check if all payments have corresponding vault transactions')
    print('3. Verify all disbursements were properly recorded')
    print('4. Consider capital injection to correct negative balance')
    print()
    
    # Calculate how much capital injection is needed
    needed = abs(actual_balance)
    print(f'💰 Capital injection needed to zero balance: K{needed:,.2f}')
    print()

# Check for missing payment vault transactions
print('CHECKING FOR MISSING PAYMENT VAULT TRANSACTIONS')
print('-' * 80)
missing_count = 0
missing_amount = Decimal('0')

for payment in chazanga_payments:
    vault_tx = VaultTransaction.objects.filter(
        loan=payment.loan,
        transaction_type='payment_collection',
        amount=payment.amount
    ).first()
    
    if not vault_tx:
        missing_count += 1
        missing_amount += payment.amount
        print(f'❌ Payment #{payment.id} (K{payment.amount}) - NO VAULT TRANSACTION')

if missing_count > 0:
    print()
    print(f'Total Missing: {missing_count} payments, K{missing_amount:,.2f}')
    print('These payments need vault transactions created!')
else:
    print('✅ All payments have vault transactions')
print()

print('=' * 80)
print('INVESTIGATION COMPLETE')
print('=' * 80)
