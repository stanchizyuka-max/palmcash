#!/usr/bin/env python
"""
Check for duplicate expenses in MANDEVU BRANCH (and other branches)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import Expense
from django.db.models import Count, Q
from collections import defaultdict

print("\n" + "="*70)
print("DUPLICATE EXPENSES CHECKER")
print("="*70)

# Focus on MANDEVU BRANCH
branch_name = "MANDEVU BRANCH"

print(f"\n🔍 Checking for duplicate expenses in: {branch_name}")
print("-" * 70)

# Get all expenses for MANDEVU BRANCH
expenses = Expense.objects.filter(branch=branch_name).order_by('expense_date', 'amount')

print(f"\n📊 Total expenses in {branch_name}: {expenses.count()}")

# Strategy 1: Find exact duplicates (same amount, date, description)
print("\n" + "="*70)
print("STRATEGY 1: Exact Duplicates (Same Amount, Date, Description)")
print("="*70)

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
        exact_duplicates.append({
            'original': seen[key],
            'duplicate': expense,
            'key': key
        })
    else:
        seen[key] = expense

if exact_duplicates:
    print(f"\n⚠️  Found {len(exact_duplicates)} exact duplicate(s):\n")
    for i, dup in enumerate(exact_duplicates, 1):
        orig = dup['original']
        dupe = dup['duplicate']
        print(f"Duplicate Set #{i}:")
        print(f"  Original ID: {orig.id}")
        print(f"    Date: {orig.expense_date}")
        print(f"    Amount: K{orig.amount}")
        print(f"    Description: {orig.description}")
        print(f"    Category: {orig.expense_code.name if orig.expense_code else 'None'}")
        print(f"    Recorded by: {orig.recorded_by.get_full_name()}")
        print(f"    Recorded at: {orig.created_at}")
        print(f"\n  Duplicate ID: {dupe.id}")
        print(f"    Date: {dupe.expense_date}")
        print(f"    Amount: K{dupe.amount}")
        print(f"    Description: {dupe.description}")
        print(f"    Category: {dupe.expense_code.name if dupe.expense_code else 'None'}")
        print(f"    Recorded by: {dupe.recorded_by.get_full_name()}")
        print(f"    Recorded at: {dupe.created_at}")
        print(f"  Time difference: {(dupe.created_at - orig.created_at).total_seconds() / 60:.1f} minutes")
        print("-" * 70)
else:
    print("\n✅ No exact duplicates found")

# Strategy 2: Find near duplicates (same amount and date, within 1 hour)
print("\n" + "="*70)
print("STRATEGY 2: Near Duplicates (Same Amount & Date, Within 1 Hour)")
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
    for i, dup in enumerate(near_duplicates, 1):
        exp1 = dup['expense1']
        exp2 = dup['expense2']
        print(f"Near Duplicate Set #{i}:")
        print(f"  Expense 1 ID: {exp1.id}")
        print(f"    Date: {exp1.expense_date}")
        print(f"    Amount: K{exp1.amount}")
        print(f"    Description: {exp1.description}")
        print(f"    Recorded at: {exp1.created_at}")
        print(f"\n  Expense 2 ID: {exp2.id}")
        print(f"    Date: {exp2.expense_date}")
        print(f"    Amount: K{exp2.amount}")
        print(f"    Description: {exp2.description}")
        print(f"    Recorded at: {exp2.created_at}")
        print(f"  Time difference: {dup['time_diff_minutes']:.1f} minutes")
        print("-" * 70)
else:
    print("\n✅ No near duplicates found")

# Strategy 3: Group by date and amount to find potential duplicates
print("\n" + "="*70)
print("STRATEGY 3: Grouped Analysis (Same Date & Amount)")
print("="*70)

grouped = defaultdict(list)
for expense in expenses:
    key = (expense.expense_date, expense.amount)
    grouped[key].append(expense)

duplicates_by_group = {k: v for k, v in grouped.items() if len(v) > 1}

if duplicates_by_group:
    print(f"\n⚠️  Found {len(duplicates_by_group)} group(s) with multiple expenses:\n")
    for i, ((date, amount), exps) in enumerate(duplicates_by_group.items(), 1):
        print(f"Group #{i}: {date} - K{amount} ({len(exps)} expenses)")
        for exp in exps:
            print(f"  ID: {exp.id} | {exp.description[:50]} | By: {exp.recorded_by.get_full_name()} | At: {exp.created_at}")
        print("-" * 70)
else:
    print("\n✅ No grouped duplicates found")

# Strategy 4: Check for same description on same day
print("\n" + "="*70)
print("STRATEGY 4: Same Description on Same Day")
print("="*70)

desc_duplicates = defaultdict(list)
for expense in expenses:
    if expense.description:
        key = (expense.expense_date, expense.description.strip().lower())
        desc_duplicates[key].append(expense)

desc_dups = {k: v for k, v in desc_duplicates.items() if len(v) > 1}

if desc_dups:
    print(f"\n⚠️  Found {len(desc_dups)} description duplicate(s):\n")
    for i, ((date, desc), exps) in enumerate(desc_dups.items(), 1):
        print(f"Duplicate #{i}: {date} - '{desc}'")
        total_amount = sum(exp.amount for exp in exps)
        print(f"  Total amount: K{total_amount} ({len(exps)} expenses)")
        for exp in exps:
            print(f"    ID: {exp.id} | K{exp.amount} | By: {exp.recorded_by.get_full_name()} | At: {exp.created_at}")
        print("-" * 70)
else:
    print("\n✅ No description duplicates found")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"\nBranch: {branch_name}")
print(f"Total Expenses: {expenses.count()}")
print(f"Exact Duplicates: {len(exact_duplicates)}")
print(f"Near Duplicates: {len(near_duplicates)}")
print(f"Grouped Duplicates: {len(duplicates_by_group)}")
print(f"Description Duplicates: {len(desc_dups)}")

# Check all branches
print("\n" + "="*70)
print("CHECKING ALL BRANCHES")
print("="*70)

from clients.models import Branch

all_branches = Branch.objects.filter(is_active=True)
for branch in all_branches:
    branch_expenses = Expense.objects.filter(branch=branch.name)
    
    # Quick check for exact duplicates
    seen_branch = {}
    branch_exact_dups = 0
    
    for expense in branch_expenses:
        key = (
            expense.expense_date,
            expense.amount,
            expense.description.strip().lower() if expense.description else '',
            expense.expense_code_id
        )
        if key in seen_branch:
            branch_exact_dups += 1
        else:
            seen_branch[key] = expense
    
    status = "⚠️" if branch_exact_dups > 0 else "✅"
    print(f"{status} {branch.name}: {branch_expenses.count()} expenses, {branch_exact_dups} exact duplicates")

print("\n" + "="*70)
print("END OF CHECK")
print("="*70 + "\n")

# Generate IDs to delete if duplicates found
if exact_duplicates:
    print("\n💡 SUGGESTED ACTION:")
    print("\nTo delete the duplicate expenses, you can use:")
    print("\nfrom expenses.models import Expense")
    duplicate_ids = [dup['duplicate'].id for dup in exact_duplicates]
    print(f"duplicate_ids = {duplicate_ids}")
    print("# Review these IDs carefully before deleting!")
    print("# Expense.objects.filter(id__in=duplicate_ids).delete()")
    print("\n⚠️  WARNING: Always backup database before deleting!")
