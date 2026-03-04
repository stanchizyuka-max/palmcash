from django.core.management.base import BaseCommand
from expenses.models import ExpenseCode


class Command(BaseCommand):
    help = 'Setup predefined expense codes for branch managers'

    def handle(self, *args, **options):
        # Define predefined expense codes
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

        created_count = 0
        for code_data in expense_codes:
            code, created = ExpenseCode.objects.get_or_create(
                code=code_data['code'],
                defaults={
                    'name': code_data['name'],
                    'description': code_data['description'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created expense code: {code.code} - {code.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Expense code already exists: {code.code} - {code.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} new expense codes')
        )
