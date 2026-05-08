#!/usr/bin/env python
"""
Remove specific duplicate expenses by ID
IDs to remove: 470, 250, 310, 210
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import Expense, VaultTransaction
from django.db import transaction
from decimal import Decimal

print("\n" + "="*70)
print("REMOVE SPECIFIC DUPLICATE EXPENSES")
print("="*70)

# The duplicate IDs to remove
DUPLICATE_IDS = [470, 250, 310, 210]

print(f"\n⚠️  WARNING: This will delete {len(DUPLICATE_IDS)} expense records!")
print(f"IDs to delete: {DUPLICATE_IDS}")
print("\n" + "="*70)

# First, show details of what will be deleted
print("\n📋 EXPENSES TO BE DELETED:\n")

expenses_to_delete = []
total_amount = Decimal('0.00')

for exp_id in DUPLICATE_IDS:
    try:
        expense = Expense.objects.get(id=exp_id)
        expenses_to_delete.append(expense)
        total_amount += expense.amount
        
        print(f"ID: {expense.id}")
        print(f"  Branch: {expense.branch}")
        print(f"  Date: {expense.expense_date}")
        print(f"  Amount: K{expense.amount}")
        print(f"  Title: {expense.title}")
        print(f"  Description: {expense.description}")
        print(f"  Category: {expense.expense_code.name if expense.expense_code else 'None'}")
        print(f"  Recorded by: {expense.recorded_by.get_full_name() if expense.recorded_by else 'Unknown'}")
        print(f"  Recorded at: {expense.created_at}")
        print(f"  Status: {expense.status}")
        print("-" * 70)
    except Expense.DoesNotExist:
        print(f"❌ Expense ID {exp_id} not found in database")
        print("-" * 70)

if not expenses_to_delete:
    print("\n❌ No expenses found to delete. Exiting.")
    exit()

print(f"\n📊 SUMMARY:")
print(f"Total expenses to delete: {len(expenses_to_delete)}")
print(f"Total amount: K{total_amount}")
print("\n" + "="*70)

# Confirmation 1
response = input("\nHave you reviewed the expenses above? (yes/no): ")
if response.lower() != 'yes':
    print("\n❌ Aborted. No changes made.")
    exit()

# Confirmation 2
response = input("\nDo you have a database backup? (yes/no): ")
if response.lower() != 'yes':
    print("\n❌ Aborted. Please backup your database first!")
    print("   Run: mysqldump -u username -p palmcash_db > backup_before_cleanup.sql")
    exit()

# Confirmation 3
print("\n⚠️  FINAL WARNING: This will permanently delete these expenses!")
print("⚠️  This action cannot be undone!")
response = input("\nType 'DELETE' to confirm: ")
if response != 'DELETE':
    print("\n❌ Aborted. No changes made.")
    exit()

# Perform deletion with transaction rollback safety
print("\n🔄 Processing deletions...")

deleted_count = 0
vault_reversed_count = 0
errors = []

with transaction.atomic():
    for expense in expenses_to_delete:
        try:
            expense_id = expense.id
            expense_amount = expense.amount
            expense_branch = expense.branch
            expense_title = expense.title
            
            # Find related vault transaction
            vault_tx = VaultTransaction.objects.filter(
                branch__iexact=expense_branch,
                transaction_type='expense',
                amount=expense_amount,
                direction='out'
            ).order_by('-transaction_date').first()
            
            if vault_tx:
                print(f"  Found vault transaction ID {vault_tx.id} for expense {expense_id}")
                
                # Create reversal transaction (return money to vault)
                from django.utils import timezone
                from clients.models import Branch
                
                branch_obj = Branch.objects.filter(name__iexact=expense_branch).first()
                if branch_obj:
                    # Get current vault balance
                    from dashboard.vault_views import _get_vault_balance
                    current_balance = _get_vault_balance(expense_branch, vault_tx.vault_type)
                    new_balance = current_balance + expense_amount
                    
                    # Create reversal transaction
                    reversal_tx = VaultTransaction.objects.create(
                        transaction_type='expense',
                        direction='in',  # Money coming back
                        branch=expense_branch,
                        vault_type=vault_tx.vault_type,
                        amount=expense_amount,
                        balance_after=new_balance,
                        description=f"REVERSAL: Duplicate expense removed - {expense_title} (Original ID: {expense_id})",
                        reference_number=f"REV-EXP-{expense_id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                        recorded_by=expense.recorded_by,
                        transaction_date=timezone.now()
                    )
                    vault_reversed_count += 1
                    print(f"  ✅ Created reversal transaction ID {reversal_tx.id}")
            
            # Delete the expense
            expense.delete()
            deleted_count += 1
            print(f"  ✅ Deleted expense ID {expense_id}")
            
        except Exception as e:
            error_msg = f"Failed to delete expense ID {expense.id}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ {error_msg}")
            # Re-raise to trigger rollback
            raise

print("\n" + "="*70)
print("DELETION COMPLETE")
print("="*70)
print(f"\n✅ Successfully deleted: {deleted_count} expense(s)")
print(f"✅ Vault transactions reversed: {vault_reversed_count}")

if errors:
    print(f"\n⚠️  Errors encountered: {len(errors)}")
    for error in errors:
        print(f"  - {error}")
else:
    print("\n✅ No errors encountered")

# Verify
from clients.models import Branch
mandevu = Branch.objects.filter(name__iexact="MANDEVU BRANCH").first()
if mandevu:
    remaining = Expense.objects.filter(branch__iexact="MANDEVU BRANCH").count()
    print(f"\n📊 Remaining expenses in MANDEVU BRANCH: {remaining}")

print("\n" + "="*70)
print("DONE")
print("="*70 + "\n")

print("💡 NEXT STEPS:")
print("1. Check the vault balance in MANDEVU BRANCH")
print("2. Verify the expenses list in the dashboard")
print("3. Run check_duplicate_expenses.py again to confirm no duplicates remain")
print()

