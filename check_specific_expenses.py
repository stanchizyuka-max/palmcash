#!/usr/bin/env python
"""
Check specific expense IDs to verify if they are duplicates
IDs to check: 470, 250, 310, 210

USAGE: Run this on the server where the database is accessible
  ssh into server, then run: python check_specific_expenses.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import Expense
from collections import defaultdict

print("\n" + "="*70)
print("CHECK SPECIFIC EXPENSES")
print("="*70)

# The IDs to check
EXPENSE_IDS = [470, 250, 310, 210]

print(f"\nChecking expense IDs: {EXPENSE_IDS}")
print("="*70)

expenses = []
for exp_id in EXPENSE_IDS:
    try:
        expense = Expense.objects.get(id=exp_id)
        expenses.append(expense)
    except Expense.DoesNotExist:
        print(f"\n❌ Expense ID {exp_id} not found in database")

if not expenses:
    print("\n❌ No expenses found. Exiting.")
    exit()

print(f"\n✅ Found {len(expenses)} expense(s)\n")

# Display each expense in detail
for i, expense in enumerate(expenses, 1):
    print(f"{'='*70}")
    print(f"EXPENSE #{i} - ID: {expense.id}")
    print(f"{'='*70}")
    print(f"Branch:           {expense.branch}")
    print(f"Date:             {expense.expense_date}")
    print(f"Amount:           K{expense.amount}")
    print(f"Title:            {expense.title}")
    print(f"Description:      {expense.description}")
    print(f"Category:         {expense.expense_code.name if expense.expense_code else 'None'}")
    print(f"Category Code:    {expense.expense_code.code if expense.expense_code else 'None'}")
    print(f"Expense Type:     {expense.expense_type}")
    print(f"Status:           {expense.status}")
    print(f"Recorded by:      {expense.recorded_by.get_full_name() if expense.recorded_by else 'Unknown'}")
    print(f"Recorded at:      {expense.created_at}")
    print(f"Updated at:       {expense.updated_at}")
    if expense.approved_by:
        print(f"Approved by:      {expense.approved_by.get_full_name()}")
        print(f"Approval date:    {expense.approval_date}")
    print()

# Group by key characteristics to find duplicates
print("="*70)
print("DUPLICATE ANALYSIS")
print("="*70)

# Strategy 1: Exact match (date, amount, description)
print("\n📊 STRATEGY 1: Exact Match (Date + Amount + Description)")
print("-" * 70)

grouped_exact = defaultdict(list)
for expense in expenses:
    key = (
        expense.expense_date,
        expense.amount,
        expense.description.strip().lower() if expense.description else '',
    )
    grouped_exact[key].append(expense)

found_exact = False
for key, exps in grouped_exact.items():
    if len(exps) > 1:
        found_exact = True
        date, amount, desc = key
        print(f"\n⚠️  DUPLICATE GROUP: {date} | K{amount}")
        print(f"Description: {desc[:60]}...")
        for exp in exps:
            print(f"  - ID {exp.id}: Recorded by {exp.recorded_by.get_full_name() if exp.recorded_by else 'Unknown'} at {exp.created_at}")

if not found_exact:
    print("✅ No exact duplicates found among these expenses")

# Strategy 2: Same date and amount
print("\n📊 STRATEGY 2: Same Date + Amount (Different Descriptions)")
print("-" * 70)

grouped_date_amount = defaultdict(list)
for expense in expenses:
    key = (expense.expense_date, expense.amount)
    grouped_date_amount[key].append(expense)

found_date_amount = False
for key, exps in grouped_date_amount.items():
    if len(exps) > 1:
        found_date_amount = True
        date, amount = key
        print(f"\n⚠️  SAME DATE & AMOUNT: {date} | K{amount}")
        for exp in exps:
            print(f"  - ID {exp.id}: {exp.description[:50]}")
            print(f"    Recorded by {exp.recorded_by.get_full_name() if exp.recorded_by else 'Unknown'} at {exp.created_at}")

if not found_date_amount:
    print("✅ No expenses with same date and amount")

# Strategy 3: Same amount only
print("\n📊 STRATEGY 3: Same Amount (Different Dates)")
print("-" * 70)

grouped_amount = defaultdict(list)
for expense in expenses:
    grouped_amount[expense.amount].append(expense)

found_amount = False
for amount, exps in grouped_amount.items():
    if len(exps) > 1:
        found_amount = True
        print(f"\n⚠️  SAME AMOUNT: K{amount}")
        for exp in exps:
            print(f"  - ID {exp.id}: {exp.expense_date} | {exp.description[:40]}")

if not found_amount:
    print("✅ No expenses with same amount")

# Strategy 4: Check if these are part of larger duplicate groups
print("\n📊 STRATEGY 4: Check for Related Duplicates in Database")
print("-" * 70)

for expense in expenses:
    # Find other expenses with same date, amount, and description
    similar = Expense.objects.filter(
        expense_date=expense.expense_date,
        amount=expense.amount,
        description__iexact=expense.description.strip() if expense.description else ''
    ).exclude(id=expense.id)
    
    if similar.exists():
        print(f"\n⚠️  Expense ID {expense.id} has {similar.count()} similar expense(s):")
        print(f"   Date: {expense.expense_date} | Amount: K{expense.amount}")
        print(f"   Description: {expense.description[:50]}")
        for sim in similar:
            print(f"   - Similar ID {sim.id}: Recorded at {sim.created_at}")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

total_amount = sum(exp.amount for exp in expenses)
print(f"\nExpenses checked: {len(expenses)}")
print(f"Total amount: K{total_amount}")
print(f"Branch(es): {', '.join(set(exp.branch for exp in expenses))}")
print(f"Date range: {min(exp.expense_date for exp in expenses)} to {max(exp.expense_date for exp in expenses)}")

print("\n💡 RECOMMENDATION:")
if found_exact:
    print("⚠️  These expenses appear to be EXACT DUPLICATES")
    print("   They have the same date, amount, and description")
    print("   Consider removing the later recorded ones")
elif found_date_amount:
    print("⚠️  These expenses have the same date and amount")
    print("   Review descriptions to confirm if they are duplicates")
else:
    print("✅ These expenses do NOT appear to be duplicates")
    print("   They have different dates, amounts, or descriptions")

print("\n" + "="*70)
print("END OF CHECK")
print("="*70 + "\n")

