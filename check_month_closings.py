#!/usr/bin/env python
"""Check month closing transactions"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction

print('=' * 70)
print('CHECKING MONTH CLOSING TRANSACTIONS')
print('=' * 70)
print()

# Get all month_close transactions
closings = VaultTransaction.objects.filter(
    transaction_type='month_close'
).order_by('-transaction_date')

print(f'Total month_close transactions: {closings.count()}')
print()

if closings.count() > 0:
    print('RECENT CLOSINGS:')
    print('-' * 70)
    for closing in closings[:10]:
        print(f'ID: {closing.id}')
        print(f'  Branch: {closing.branch}')
        print(f'  Vault Type: {closing.vault_type}')
        print(f'  Amount: K{closing.amount}')
        print(f'  Date: {closing.transaction_date}')
        print(f'  Description: {closing.description}')
        print(f'  Recorded by: {closing.recorded_by}')
        print()
else:
    print('No month closing transactions found!')
    print()
    print('Checking all transaction types:')
    all_types = VaultTransaction.objects.values('transaction_type').distinct()
    for t in all_types:
        count = VaultTransaction.objects.filter(transaction_type=t['transaction_type']).count()
        print(f'  - {t["transaction_type"]}: {count}')
