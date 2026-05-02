#!/usr/bin/env python
"""
Add Data Bundle expense code
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import ExpenseCode

# Check if it already exists
existing = ExpenseCode.objects.filter(name='Data Bundle').first()

if existing:
    print(f"✓ 'Data Bundle' expense code already exists (ID: {existing.id}, Code: {existing.code})")
else:
    # Find the next available code number
    existing_codes = ExpenseCode.objects.filter(code__startswith='EXP-').order_by('-code')
    if existing_codes.exists():
        last_code = existing_codes.first().code
        # Extract number from code like "EXP-006"
        try:
            last_num = int(last_code.split('-')[1])
            next_num = last_num + 1
        except:
            next_num = 7  # Default if parsing fails
    else:
        next_num = 1
    
    new_code = f"EXP-{next_num:03d}"
    
    # Create the expense code
    expense_code = ExpenseCode.objects.create(
        code=new_code,
        name='Data Bundle',
        description='Mobile data bundles and internet expenses',
        is_active=True
    )
    print(f"✓ Created 'Data Bundle' expense code (ID: {expense_code.id}, Code: {new_code})")

# Show all expense codes
print("\nAll Expense Codes:")
print("=" * 60)
codes = ExpenseCode.objects.filter(is_active=True).order_by('code')
for code in codes:
    print(f"  - {code.code}: {code.name}")

print(f"\nTotal: {codes.count()} active expense codes")
