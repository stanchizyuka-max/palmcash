"""
Management command to fix payment schedules for weekly loans that have incorrect number of installments.
This fixes loans where term_weeks was calculated incorrectly (e.g., 3 instead of 21).
"""
from django.core.management.base import BaseCommand
from loans.models import Loan
from payments.models import PaymentSchedule
from datetime import timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix payment schedules for weekly loans with incorrect number of installments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without actually fixing',
        )
        parser.add_argument(
            '--loan-id',
            type=int,
            help='Fix a specific loan by ID (optional)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        loan_id = options.get('loan_id')

        # Get weekly loans
        if loan_id:
            loans = Loan.objects.filter(id=loan_id, repayment_frequency='weekly')
        else:
            loans = Loan.objects.filter(
                repayment_frequency='weekly',
                status__in=['active', 'disbursed']
            )

        fixed_count = 0
        
        for loan in loans:
            # Check if loan has incorrect schedule
            current_installments = PaymentSchedule.objects.filter(loan=loan).count()
            expected_installments = loan.term_weeks if loan.term_weeks else 0
            
            # If term_weeks is wrong (e.g., 3 when it should be 21), recalculate from duration_days
            if loan.loan_application and loan.loan_application.duration_days:
                correct_weeks = loan.loan_application.duration_days // 7
                if correct_weeks != loan.term_weeks:
                    self.stdout.write(
                        self.style.WARNING(
                            f'\nLoan {loan.application_number}:'
                        )
                    )
                    self.stdout.write(f'  Current term_weeks: {loan.term_weeks}')
                    self.stdout.write(f'  Correct term_weeks: {correct_weeks} (from {loan.loan_application.duration_days} days)')
                    self.stdout.write(f'  Current installments: {current_installments}')
                    self.stdout.write(f'  Expected installments: {correct_weeks}')
                    
                    if not dry_run:
                        # Update loan term_weeks
                        loan.term_weeks = correct_weeks
                        loan.save()
                        
                        # Regenerate payment schedule
                        self._regenerate_schedule(loan, correct_weeks)
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Fixed! Generated {correct_weeks} installments'
                            )
                        )
                        fixed_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [DRY RUN] Would fix to {correct_weeks} installments'
                            )
                        )
                        fixed_count += 1

        if fixed_count == 0:
            self.stdout.write(
                self.style.SUCCESS('\n✓ No loans need fixing!')
            )
        else:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠ Found {fixed_count} loan(s) that need fixing. '
                        f'Run without --dry-run to fix them.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Successfully fixed {fixed_count} loan(s)!'
                    )
                )

    def _regenerate_schedule(self, loan, term_weeks):
        """Regenerate payment schedule with correct number of installments"""
        # Delete existing schedule
        PaymentSchedule.objects.filter(loan=loan).delete()
        
        # Generate new schedule
        payment_amount = loan.payment_amount
        start_date = loan.disbursement_date.date()
        frequency_days = 7  # Weekly
        
        installment = 1
        current_date = start_date

        for _ in range(term_weeks):
            current_date += timedelta(days=frequency_days)

            PaymentSchedule.objects.create(
                loan=loan,
                installment_number=installment,
                due_date=current_date,
                principal_amount=round(payment_amount, 2),
                interest_amount=Decimal('0'),
                total_amount=round(payment_amount, 2),
            )
            installment += 1
        
        self.stdout.write(f'    Generated {term_weeks} payment schedules')
