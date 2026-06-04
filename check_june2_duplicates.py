import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from django.utils import timezone
from datetime import datetime

# Find all transactions on June 2, 2026
june2_start = timezone.make_aware(datetime(2026, 6, 2, 0, 0, 0))
june2_end = timezone.make_aware(datetime(2026, 6, 2, 23, 59, 59))

june2_txs = VaultTransaction.objects.filter(
    timestamp__gte=june2_start,
    timestamp__lte=june2_end
).order_by('vault_type', 'branch', 'timestamp')

print("=" * 80)
print("ALL TRANSACTIONS ON JUNE 2, 2026")
print("=" * 80)

for tx in june2_txs:
    print(f"TX #{tx.id} | {tx.branch} {tx.vault_type} | {tx.direction} | K{tx.amount:,.2f} | {tx.description} | {tx.timestamp}")

print("\n" + "=" * 80)
print("MONTH CLOSING TRANSACTIONS ON JUNE 2 (TO BE DELETED)")
print("=" * 80)

month_closing_txs = june2_txs.filter(description__icontains='Month Closing')

for tx in month_closing_txs:
    print(f"TX #{tx.id} | {tx.branch} {tx.vault_type} | {tx.direction} | K{tx.amount:,.2f} | {tx.timestamp}")

print(f"\nTotal June 2 transactions: {june2_txs.count()}")
print(f"Month Closing transactions to delete: {month_closing_txs.count()}")
