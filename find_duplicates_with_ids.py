#!/usr/bin/env python
"""
Find duplicate expenses and show their actual IDs
This will help identify which IDs to delete
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import Expense
from collections import defaultdict

print("\n" + "="*70)
print("FIND DUPLICATE EXPENSES WITH IDs")
print("="*70)

# Focus on MANDEVU BRANCH
branch_name = "MANDEVU BRANCH"

print(f"\n🔍 Checking for duplicate expenses in: {branch_name}")
print("-" * 70)

# Get all expenses for MANDEVU BRANCH
expenses = Expense.objects.filter(branch__iexact=branch_name).order_by('expense_date', 'amount', 'created_at')

print(f"\n📊 Total expenses in {branch_name}: {expenses.count()}")

# Find exact duplicates (same amount, date, description)
print("\n" + "="*70)
print("EXACT DUPLICATES (Same Date, Amount, Description)")
print("="*70)

seen = {}
exact_duplicates = []

for expense in expenses:
    key = (
        expense.expense_date,
        expense.amount,
        expense.description.strip().lower() if expense.description else '',
        expense.expense_code_id
    )
    
    if key in seen:
        exact_duplicates.append({
            'original': seen[key],
            'duplicate': expense,
        })
    else:
        seen[key] = expense

if exact_duplicates:
    print(f"\n⚠️  Found {len(exact_duplicates)} exact duplicate(s):\n")
    
    duplicate_ids_to_delete = []
    
    for i, dup in enumerate(exact_duplicates, 1):
        orig = dup['original']
        dupe = dup['duplicate']
        
        print(f"{'='*70}")
        print(f"DUPLICATE SET #{i}")
        print(f"{'='*70}")
        
        print(f"\n✅ KEEP THIS ONE (First recorded):")
        print(f"   ID: {orig.id}")
        print(f"   Date: {orig.expense_date}")
        print(f"   Amount: K{orig.amount}")
        print(f"   Title: {orig.title}")
        print(f"   Description: {orig.description}")
        print(f"   Category: {orig.expense_code.name if orig.expense_code else 'None'}")
        print(f"   Recorded by: {orig.recorded_by.get_full_name() if orig.recorded_by else 'Unknown'}")
        print(f"   Recorded at: {orig.created_at}")
        print(f"   Status: {orig.status}")
        
        print(f"\n❌ DELETE THIS ONE (Duplicate):")
        print(f"   ID: {dupe.id}")
        print(f"   Date: {dupe.expense_date}")
        print(f"   Amount: K{dupe.amount}")
        print(f"   Title: {dupe.title}")
        print(f"   Description: {dupe.description}")
        print(f"   Category: {dupe.expense_code.name if dupe.expense_code else 'None'}")
        print(f"   Recorded by: {dupe.recorded_by.get_full_name() if dupe.recorded_by else 'Unknown'}")
        print(f"   Recorded at: {dupe.created_at}")
        print(f"   Status: {dupe.status}")
        
        time_diff = (dupe.created_at - orig.created_at).total_seconds() / 60
        print(f"\n   ⏱️  Time difference: {time_diff:.1f} minutes")
        
        duplicate_ids_to_delete.append(dupe.id)
        print()
    
    print("="*70)
    print("SUMMARY OF IDs TO DELETE")
    print("="*70)
    print(f"\nTotal duplicates to delete: {len(duplicate_ids_to_delete)}")
    print(f"IDs to delete: {duplicate_ids_to_delete}")
    
    total_amount = sum(dup['duplicate'].amount for dup in exact_duplicates)
    print(f"Total amount to be removed: K{total_amount}")
    
    print("\n💡 NEXT STEPS:")
    print("1. Review the duplicates above carefully")
    print("2. Confirm these are actual duplicates (not separate expenses)")
    print("3. Create a database backup:")
    print("   mysqldump -u username -p palmcash_db > backup_$(date +%Y%m%d).sql")
    print("4. Update remove_specific_duplicates.py with these IDs:")
    print(f"   DUPLICATE_IDS = {duplicate_ids_to_delete}")
    print("5. Run: python remove_specific_duplicates.py")
    
else:
    print("\n✅ No exact duplicates found")

# Also check for near duplicates (same date/amount, within 1 hour)
print("\n" + "="*70)
print("NEAR DUPLICATES (Same Date & Amount, Within 1 Hour)")
print("="*70)

from datetime import timedelta

near_duplicates = []
expenses_list = list(expenses)

for i, exp1 in enumerate(expenses_list):
    for exp2 in expenses_list[i+1:]:
        # Same date and amount
        if exp1.expense_date == exp2.expense_date and exp1.amount == exp2.amount:
            # Within 1 hour of each other
            time_diff = abs((exp2.created_at - exp1.created_at).total_seconds())
            if time_diff <= 3600:  # 1 hour
                near_duplicates.append({
                    'expense1': exp1,
                    'expense2': exp2,
                    'time_diff_minutes': time_diff / 60
                })

if near_duplicates:
    print(f"\n⚠️  Found {len(near_duplicates)} near duplicate(s):\n")
    
    near_duplicate_ids = []
    
    for i, dup in enumerate(near_duplicates, 1):
        exp1 = dup['expense1']
        exp2 = dup['expense2']
        
        print(f"Near Duplicate Set #{i}:")
        print(f"  Expense 1 ID: {exp1.id} | {exp1.expense_date} | K{exp1.amount}")
        print(f"    Description: {exp1.description}")
        print(f"    Recorded at: {exp1.created_at}")
        print(f"  Expense 2 ID: {exp2.id} | {exp2.expense_date} | K{exp2.amount}")
        print(f"    Description: {exp2.description}")
        print(f"    Recorded at: {exp2.created_at}")
        print(f"  Time difference: {dup['time_diff_minutes']:.1f} minutes")
        print("-" * 70)
        
        near_duplicate_ids.append(exp2.id)
    
    print(f"\nNear duplicate IDs (later ones): {near_duplicate_ids}")
else:
    print("\n✅ No near duplicates found")

print("\n" + "="*70)
print("END OF CHECK")
print("="*70 + "\n")

