from django.core.management.base import BaseCommand
from loans.models import LoanType


class Command(BaseCommand):
    help = 'Load initial loan types (Daily and Weekly loans)'

    def handle(self, *args, **options):
        # Check if loan types already exist
        if LoanType.objects.exists():
            self.stdout.write(
                self.style.WARNING('Loan types already exist. Skipping...')
            )
            return

        # Create Daily Loans
        daily_loan = LoanType.objects.create(
            name='Daily Loans',
            description='Short-term daily repayment loans with 40% interest rate over 56 days',
            interest_rate=40.00,
            max_amount=50000.00,
            min_amount=1000.00,
            repayment_frequency='daily',
            min_term_days=56,
            max_term_days=56,
            is_active=True
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created: {daily_loan.name}')
        )

        # Create Weekly Loans
        weekly_loan = LoanType.objects.create(
            name='Weekly Loans',
            description='Medium-term weekly repayment loans with 45% interest rate over 21 weeks',
            interest_rate=45.00,
            max_amount=100000.00,
            min_amount=5000.00,
            repayment_frequency='weekly',
            min_term_weeks=21,
            max_term_weeks=21,
            is_active=True
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created: {weekly_loan.name}')
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded loan types')
        )
