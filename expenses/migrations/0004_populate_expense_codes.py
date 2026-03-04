# Generated migration to populate ExpenseCode table with predefined codes

from django.db import migrations


def populate_expense_codes(apps, schema_editor):
    """Populate ExpenseCode table with predefined codes"""
    ExpenseCode = apps.get_model('expenses', 'ExpenseCode')
    
    expense_codes = [
        {
            'code': 'EXP-001',
            'name': 'Cleaning costs',
            'description': 'Cleaning supplies and services for branch office'
        },
        {
            'code': 'EXP-002',
            'name': 'Stationery',
            'description': 'Office stationery and supplies'
        },
        {
            'code': 'EXP-003',
            'name': 'Rentals',
            'description': 'Office rent and equipment rentals'
        },
        {
            'code': 'EXP-004',
            'name': 'Talk time',
            'description': 'Mobile phone airtime and communication costs'
        },
        {
            'code': 'EXP-005',
            'name': 'Transport',
            'description': 'Transportation and fuel costs'
        },
    ]
    
    for code_data in expense_codes:
        ExpenseCode.objects.get_or_create(
            code=code_data['code'],
            defaults={
                'name': code_data['name'],
                'description': code_data['description'],
                'is_active': True
            }
        )


def reverse_populate_expense_codes(apps, schema_editor):
    """Reverse: Remove populated expense codes"""
    ExpenseCode = apps.get_model('expenses', 'ExpenseCode')
    codes_to_remove = ['EXP-001', 'EXP-002', 'EXP-003', 'EXP-004', 'EXP-005']
    ExpenseCode.objects.filter(code__in=codes_to_remove).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0003_remove_expense_is_approved'),
    ]

    operations = [
        migrations.RunPython(populate_expense_codes, reverse_populate_expense_codes),
    ]
