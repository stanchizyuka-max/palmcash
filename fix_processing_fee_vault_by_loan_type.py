#!/usr/bin/env python
"""
Fix processing fee vault transactions to match loan repayment frequency
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanApplication, DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from clients.models import Branch
from django.db import transaction as db_transaction
from decimal import Decimal

print("=" * 80)
print("FIXING PROCESSING FEE VAULT TYPES TO MATCH LOAN TYPE")
print("=" * 80)

# Find all processing fee vault transactions
processing_fee_txs = VaultTransaction.objects.filter(
    transaction_type='deposit',
    description__icontains='processing fee'
).order_by('transaction_date')

print(f"\nFound {processing_fee_txs.count()} processing fee transactions")

if processing_fee_txs.count() == 0:
    print("✓ No processing fee transactions found")
else:
    print("\nChecking and fixing transactions:")
    print("-" * 80)
    
    fixed_count = 0
    
    for tx in processing_fee_txs:
        # Extract application number from description
        # Format: "Processing fee for application LA-XXXXXXXX..."
        try:
            app_number = tx.description.split('application ')[1].split(' ')[0].split(')')[0]
        except:
            print(f"\n❌ TX ID {tx.id}: Could not extract application number from description")
            continue
        
        # Find the loan application
        app = LoanApplication.objects.filter(application_number=app_number).first()
        
        if not app:
            print(f"\n❌ TX ID {tx.id}: Application {app_number} not found")
            continue
        
        # Get the correct vault type from loan's repayment frequency
        correct_vault_type = app.repayment_frequency  # 'daily' or 'weekly'
        current_vault_type = tx.vault_type
        
        print(f"\nTransaction ID {tx.id}:")
        print(f"  App: {app_number}")
        print(f"  Borrower: {app.borrower.get_full_name()}")
        print(f"  Branch: {tx.branch}")
        print(f"  Amount: K{tx.amount:,.2f}")
        print(f"  Loan Type: {app.repayment_frequency}")
        print(f"  Current Vault: {current_vault_type}")
        print(f"  Correct Vault: {correct_vault_type}")
        
        if current_vault_type == correct_vault_type:
            print(f"  ✓ Already correct")
            continue
        
        # Need to fix this transaction
        print(f"  🔧 Fixing: {current_vault_type} → {correct_vault_type}")
        
        try:
            with db_transaction.atomic():
                branch = Branch.objects.filter(name=tx.branch).first()
                if not branch:
                    print(f"  ❌ Branch not found")
                    continue
                
                # Remove from old vault
                if current_vault_type == 'daily':
                    old_vault, _ = DailyVault.objects.get_or_create(branch=branch)
                else:
                    old_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
                
                old_vault.balance -= tx.amount
                old_vault.total_inflows -= tx.amount
                old_vault.save(update_fields=['balance', 'total_inflows', 'updated_at'])
                print(f"  ✓ Removed K{tx.amount:,.2f} from {current_vault_type} vault (new balance: K{old_vault.balance:,.2f})")
                
                # Add to correct vault
                if correct_vault_type == 'daily':
                    new_vault, _ = DailyVault.objects.get_or_create(branch=branch)
                else:
                    new_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
                
                new_vault.balance += tx.amount
                new_vault.total_inflows += tx.amount
                new_vault.save(update_fields=['balance', 'total_inflows', 'updated_at'])
                print(f"  ✓ Added K{tx.amount:,.2f} to {correct_vault_type} vault (new balance: K{new_vault.balance:,.2f})")
                
                # Update transaction
                tx.vault_type = correct_vault_type
                tx.balance_after = new_vault.balance
                tx.description = f'Processing fee for application {app_number} ({correct_vault_type} loan)'
                tx.save(update_fields=['vault_type', 'balance_after', 'description'])
                print(f"  ✓ Updated transaction")
                
                fixed_count += 1
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total processing fee transactions: {processing_fee_txs.count()}")
print(f"Transactions fixed: {fixed_count}")

# Show final state
print("\nFinal state of processing fee transactions:")
all_txs = VaultTransaction.objects.filter(
    transaction_type='deposit',
    description__icontains='processing fee'
).order_by('-transaction_date')

for tx in all_txs:
    print(f"  - {tx.transaction_date.date()} | {tx.branch} | K{tx.amount:,.2f} | {tx.vault_type} vault")

print("\n" + "=" * 80)
print("✓ COMPLETE")
print("=" * 80)
