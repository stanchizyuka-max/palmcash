"""
Diagnostic command to check weekly loan data and payment schedules.
"""
from django.core.management.base import BaseCommand
from loans.models import Loan
from payments.models import PaymentSchedule


class Command(BaseCommand):
    help = 'Check weekly loan data and payment schedules'

    def handle(self, *args, **options):
        # Get all weekly loans
        weekly_loans = Loan.objects.filter(
            repayment_frequency='weekly'
        ).order_by('-created_at')[:10]  # Last 10 weekly loans

        if not weekly_loans:
            self.stdout.write(
                self.style.WARNING('No weekly loans found in the system.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'\nFound {weekly_loans.count()} weekly loan(s). Showing details:\n')
        )

        for loan in weekly_loans:
            installments = PaymentSchedule.objects.filter(loan=loan).count()
            
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'Loan: {loan.application_number}')
            self.stdout.write(f'Borrower: {loan.borrower.get_full_name()}')
            self.stdout.write(f'Status: {loan.status}')
            self.stdout.write(f'Principal: K{loan.principal_amount}')
            self.stdout.write(f'Created: {loan.created_at.strftime("%Y-%m-%d %H:%M")}')
            self.stdout.write(f'\nLoan Fields:')
            self.stdout.write(f'  term_days: {loan.term_days}')
            self.stdout.write(f'  term_weeks: {loan.term_weeks}')
            self.stdout.write(f'  term_months: {loan.term_months}')
            self.stdout.write(f'\nPayment Schedule:')
            self.stdout.write(f'  Installments created: {installments}')
            
            # Calculate what it should be
            if loan.term_days:
                expected_from_days = loan.term_days // 7
                self.stdout.write(f'  Expected from term_days: {expected_from_days} (term_days={loan.term_days} ÷ 7)')
            else:
                self.stdout.write(f'  Expected from term_days: N/A (term_days not set)')
            
            if loan.term_weeks:
                self.stdout.write(f'  Expected from term_weeks: {loan.term_weeks}')
            
            # Check if it matches
            if loan.term_weeks and installments != loan.term_weeks:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ⚠ MISMATCH: {installments} installments but term_weeks={loan.term_weeks}'
                    )
                )
            elif loan.term_days:
                expected = loan.term_days // 7
                if installments != expected:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ⚠ MISMATCH: {installments} installments but should be {expected} based on term_days'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ OK: Installments match expected count'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ? Cannot verify - no term_days or term_weeks set'
                    )
                )

        self.stdout.write(f'\n{"="*60}\n')
