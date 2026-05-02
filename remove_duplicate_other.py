#!/usr/bin/env python
"""
Remove duplicate 'Other' entries from ExpenseCode
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import ExpenseCode, Expense

print("=" * 70)
print("REMOVING DUPLICATE 'OTHER' ENTRIES FROM EXPENSECODE")
print("=" * 70)

# Check ExpenseCode for duplicates
print("\nChecking ExpenseCode for duplicates...")
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

# Show final state
print("\n" + "=" * 70)
print("FINAL STATE")
print("=" * 70)

print("\nExpense Codes:")
codes = ExpenseCode.objects.filter(is_active=True).order_by('code')
for code in codes:
    expense_count = Expense.objects.filter(expense_code=code).count()
    print(f"  - {code.code}: {code.name} (ID: {code.id}, Used by {expense_count} expenses)")

print("\n" + "=" * 70)
print("✓ CLEANUP COMPLETE")
print("=" * 70)
