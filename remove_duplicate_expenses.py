#!/usr/bin/env python
"""
SAFELY remove duplicate expenses after review
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import Expense, VaultTransaction
from django.db import transaction

print("\n" + "="*70)
print("DUPLICATE EXPENSE REMOVER")
print("="*70)

print("\n⚠️  WARNING: This script will DELETE duplicate expenses!")
print("⚠️  Make sure you have reviewed the duplicates first!")
print("⚠️  Run check_duplicate_expenses.py first to identify duplicates!")
print("\n" + "="*70)

# Get user confirmation
response = input("\nHave you run check_duplicate_expenses.py and reviewed the results? (yes/no): ")
if response.lower() != 'yes':
    print("\n❌ Aborted. Please run check_duplicate_expenses.py first.")
    exit()

response = input("\nDo you have a database backup? (yes/no): ")
if response.lower() != 'yes':
    print("\n❌ Aborted. Please backup your database first!")
    print("   Run: mysqldump -u username -p palmcash_db > backup_before_cleanup.sql")
    exit()

# Strategy: Find and remove exact duplicates
branch_name = "MANDEVU BRANCH"
expenses = Expense.objects.filter(branch=branch_name).order_by('expense_date', 'amount', 'created_at')

print(f"\n🔍 Analyzing expenses in: {branch_name}")
print(f"📊 Total expenses: {expenses.count()}")

# Find exact duplicates
exact_duplicates = []
seen = {}

for expense in expenses:
    key = (
        expense.expense_date,
        expense.amount,
        expense.description.strip().lower() if expense.description else '',
        expense.expense_code_id
    )
    
    if key in seen:
        # This is a duplicate - keep the first one, mark this for deletion
        exact_duplicates.append({
            'keep': seen[key],
            'delete': expense,
        })
    else:
        seen[key] = expense

if not exact_duplicates:
    print("\n✅ No exact duplicates found. Nothing to delete.")
    exit()

print(f"\n⚠️  Found {len(exact_duplicates)} duplicate expense(s) to remove:\n")

for i, dup in enumerate(exact_duplicates, 1):
    keep = dup['keep']
    delete = dup['delete']
    print(f"Duplicate #{i}:")
    print(f"  KEEPING: ID {keep.id} - {keep.expense_date} - K{keep.amount} - {keep.description}")
    print(f"           Recorded at: {keep.created_at}")
    print(f"  DELETING: ID {delete.id} - {delete.expense_date} - K{delete.amount} - {delete.description}")
    print(f"            Recorded at: {delete.created_at}")
    print()

print("="*70)
total_amount = sum(dup['delete'].amount for dup in exact_duplicates)
print(f"\nTotal duplicates to delete: {len(exact_duplicates)}")
print(f"Total amount to be removed: K{total_amount}")
print("\n⚠️  This will also reverse the vault transactions for these expenses!")
print("="*70)

response = input("\nProceed with deletion? Type 'DELETE' to confirm: ")
if response != 'DELETE':
    print("\n❌ Aborted. No changes made.")
    exit()

# Perform deletion with transaction rollback safety
print("\n🔄 Processing deletions...")

deleted_count = 0
reversed_vault_count = 0
errors = []

with transaction.atomic():
    for i, dup in enumerate(exact_duplicates, 1):
        expense_to_delete = dup['delete']
        
        try:
            # Find and reverse the vault transaction
            vault_tx = VaultTransaction.objects.filter(
                branch=expense_to_delete.branch,
                transaction_type='expense',
                amount=expense_to_delete.amount,
                description__icontains=expense_to_delete.title,
                direction='out'
            ).order_by('-transaction_date').first()
            
            if vault_tx:
                # Create reversal transaction
                from loans import vault_services
                from clients.models import Branch
                
                branch_obj = Branch.objects.filter(name=expense_to_delete.branch).first()
                if branch_obj:
                    # Return money to vault
                    vault_services.record_expense_reversal(
                        branch=branch_obj,
                        amount=expense_to_delete.amount,
                        reason=f"Duplicate expense removal - ID {expense_to_delete.id}",
                        original_expense=expense_to_delete,
                        reversed_by=None,  # System reversal
                        vault_type=vault_tx.vault_type
                    )
                    reversed_vault_count += 1
            
            # Delete the expense
            expense_to_delete.delete()
            deleted_count += 1
            print(f"  ✅ Deleted expense ID {expense_to_delete.id}")
            
        except Exception as e:
            error_msg = f"Failed to delete expense ID {expense_to_delete.id}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ {error_msg}")

print("\n" + "="*70)
print("DELETION COMPLETE")
print("="*70)
print(f"\n✅ Successfully deleted: {deleted_count} expense(s)")
print(f"✅ Vault transactions reversed: {reversed_vault_count}")

if errors:
    print(f"\n⚠️  Errors encountered: {len(errors)}")
    for error in errors:
        print(f"  - {error}")
else:
    print("\n✅ No errors encountered")

# Verify
remaining = Expense.objects.filter(branch=branch_name).count()
print(f"\n📊 Remaining expenses in {branch_name}: {remaining}")

print("\n" + "="*70)
print("DONE")
print("="*70 + "\n")

print("💡 NEXT STEPS:")
print("1. Run check_duplicate_expenses.py again to verify no duplicates remain")
print("2. Check vault balances to ensure they're correct")
print("3. Review expense list in the dashboard")
print()
