#!/usr/bin/env python
"""
Remove duplicate 'Other' entries from ExpenseCode and ExpenseCategory
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import ExpenseCode, ExpenseCategory, Expense

print("=" * 70)
print("REMOVING DUPLICATE 'OTHER' ENTRIES")
print("=" * 70)

# 1. Fix ExpenseCategory duplicates
print("\n1. Checking ExpenseCategory for duplicates...")
print("-" * 70)

other_categories = ExpenseCategory.objects.filter(name__iexact='other').order_by('id')
print(f"Found {other_categories.count()} 'Other' categories")

if other_categories.count() > 1:
    # Keep the first one, delete the rest
    keep_category = other_categories.first()
    duplicates = other_categories.exclude(id=keep_category.id)
    
    print(f"\nKeeping: ID {keep_category.id} - {keep_category.name}")
    print(f"Removing {duplicates.count()} duplicate(s):")
    
    for dup in duplicates:
        # Update any expenses using this duplicate to use the kept one
        expenses_using_dup = Expense.objects.filter(category=dup)
        count = expenses_using_dup.count()
        
        if count > 0:
            print(f"  - ID {dup.id}: Updating {count} expense(s) to use ID {keep_category.id}")
            expenses_using_dup.update(category=keep_category)
        else:
            print(f"  - ID {dup.id}: No expenses using this category")
        
        dup.delete()
        print(f"    ✓ Deleted duplicate ID {dup.id}")
    
    print(f"\n✓ Removed {duplicates.count()} duplicate ExpenseCategory entries")
else:
    print("✓ No duplicate ExpenseCategory entries found")

# 2. Fix ExpenseCode duplicates
print("\n2. Checking ExpenseCode for duplicates...")
print("-" * 70)

other_codes = ExpenseCode.objects.filter(name__iexact='other').order_by('id')
print(f"Found {other_codes.count()} 'Other' expense codes")

if other_codes.count() > 1:
    # Keep the first one, delete the rest
    keep_code = other_codes.first()
    duplicates = other_codes.exclude(id=keep_code.id)
    
    print(f"\nKeeping: ID {keep_code.id} - {keep_code.code} - {keep_code.name}")
    print(f"Removing {duplicates.count()} duplicate(s):")
    
    for dup in duplicates:
        # Update any expenses using this duplicate to use the kept one
        expenses_using_dup = Expense.objects.filter(expense_code=dup)
        count = expenses_using_dup.count()
        
        if count > 0:
            print(f"  - ID {dup.id} ({dup.code}): Updating {count} expense(s) to use ID {keep_code.id}")
            expenses_using_dup.update(expense_code=keep_code)
        else:
            print(f"  - ID {dup.id} ({dup.code}): No expenses using this code")
        
        dup.delete()
        print(f"    ✓ Deleted duplicate ID {dup.id}")
    
    print(f"\n✓ Removed {duplicates.count()} duplicate ExpenseCode entries")
else:
    print("✓ No duplicate ExpenseCode entries found")

# 3. Show final state
print("\n" + "=" * 70)
print("FINAL STATE")
print("=" * 70)

print("\nExpense Categories:")
categories = ExpenseCategory.objects.filter(is_active=True).order_by('name')
for cat in categories:
    expense_count = Expense.objects.filter(category=cat).count()
    print(f"  - {cat.name} (ID: {cat.id}, Used by {expense_count} expenses)")

print("\nExpense Codes:")
codes = ExpenseCode.objects.filter(is_active=True).order_by('code')
for code in codes:
    expense_count = Expense.objects.filter(expense_code=code).count()
    print(f"  - {code.code}: {code.name} (ID: {code.id}, Used by {expense_count} expenses)")

print("\n" + "=" * 70)
print("✓ CLEANUP COMPLETE")
print("=" * 70)
