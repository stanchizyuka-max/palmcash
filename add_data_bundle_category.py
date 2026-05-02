#!/usr/bin/env python
"""
Add Data Bundle expense category
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import ExpenseCategory

# Check if it already exists
existing = ExpenseCategory.objects.filter(name='Data Bundle').first()

if existing:
    print(f"✓ 'Data Bundle' category already exists (ID: {existing.id})")
else:
    # Create the category
    category = ExpenseCategory.objects.create(
        name='Data Bundle',
        description='Mobile data bundles and internet expenses',
        is_active=True
    )
    print(f"✓ Created 'Data Bundle' category (ID: {category.id})")

# Show all categories
print("\nAll Expense Categories:")
print("=" * 60)
categories = ExpenseCategory.objects.filter(is_active=True).order_by('name')
for cat in categories:
    print(f"  - {cat.name}")

print(f"\nTotal: {categories.count()} active categories")
