"""
Identify and relabel vault transactions that are processing fees
"""
import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction

print("=" * 70)
print("IDENTIFYING PROCESSING FEES IN VAULT TRANSACTIONS")
print("=" * 70)

# Search patterns that might indicate processing fees
search_patterns = [
    'processing fee',
    'processing',
    'fee',
    'loan fee',
    'application fee',
    'admin fee',
    'service fee',
]

print("\n🔍 Searching for potential processing fee transactions...")
print("   Looking for keywords in description fields:")
for pattern in search_patterns:
    print(f"   - '{pattern}'")

# Find transactions that might be processing fees
potential_fees = []

for pattern in search_patterns:
    transactions = VaultTransaction.objects.filter(
        description__icontains=pattern
    ).exclude(
        transaction_type='processing_fee'
    )
    
    for tx in transactions:
        if tx not in potential_fees:
            potential_fees.append(tx)

print(f"\n✓ Found {len(potential_fees)} potential processing fee transaction(s)")

if len(potential_fees) == 0:
    print("\n" + "=" * 70)
    print("NO PROCESSING FEES FOUND")
    print("=" * 70)
    print("\nNo transactions found with processing fee keywords in description.")
    print("\nOptions:")
    print("  1. Processing fees might be recorded without specific descriptions")
    print("  2. They might be mixed with other transaction types")
    print("  3. No processing fees have been recorded yet")
    print("\nTo manually identify processing fees:")
    print("  - Check 'Cash Deposit' transactions")
    print("  - Look for small amounts (e.g., K50-K200)")
    print("  - Check transaction dates around loan disbursements")
    sys.exit(0)

# Show found transactions
print("\n📋 Potential Processing Fee Transactions:")
print("-" * 70)

for i, tx in enumerate(potential_fees, 1):
    print(f"\n{i}. Transaction ID: {tx.id}")
    print(f"   Date: {tx.transaction_date}")
    print(f"   Type: {tx.get_transaction_type_display()}")
    print(f"   Amount: K{tx.amount}")
    print(f"   Direction: {tx.direction.upper()}")
    print(f"   Branch: {tx.branch}")
    print(f"   Description: {tx.description[:100]}..." if len(tx.description) > 100 else f"   Description: {tx.description}")
    if tx.loan:
        print(f"   Loan: {tx.loan.application_number}")

# Ask for confirmation
print("\n" + "=" * 70)
print("CONFIRMATION")
print("=" * 70)

print(f"\nFound {len(potential_fees)} transaction(s) that might be processing fees.")
print("\nDo you want to relabel these as 'Processing Fee'?")
print("This will change their transaction_type to 'processing_fee'.")

response = input("\nType 'yes' to proceed, or 'no' to cancel: ").strip().lower()

if response != 'yes':
    print("\n❌ Cancelled. No changes made.")
    sys.exit(0)

# Relabel transactions
print("\n🔄 Relabeling transactions...")
updated_count = 0

for tx in potential_fees:
    old_type = tx.get_transaction_type_display()
    tx.transaction_type = 'processing_fee'
    tx.save()
    updated_count += 1
    print(f"   ✓ Transaction {tx.id}: {old_type} → Processing Fee")

print("\n" + "=" * 70)
print(f"✓ SUCCESS! Updated {updated_count} transaction(s)")
print("=" * 70)

print("\nTransactions have been relabeled as 'Processing Fee'.")
print("You can now filter by 'Processing Fee' in the vault history.")
print("\n" + "=" * 70)
