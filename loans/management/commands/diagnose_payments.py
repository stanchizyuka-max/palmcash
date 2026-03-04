from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models import Payment, PaymentSchedule
from loans.models import Loan
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Diagnose payment and schedule issues for a borrower'

    def add_arguments(self, parser):
        parser.add_argument(
            '--borrower',
            type=str,
            help='Username of borrower to diagnose',
        )
        parser.add_argument(
            '--loan',
            type=str,
            help='Loan application number to diagnose',
        )

    def handle(self, *args, **options):
        borrower_username = options.get('borrower')
        loan_app_number = options.get('loan')

        if not borrower_username and not loan_app_number:
            self.stdout.write(self.style.ERROR('Please provide --borrower or --loan'))
            return

        # Get borrower
        if borrower_username:
            try:
                borrower = User.objects.get(username=borrower_username)
                self.stdout.write(f"\n{'='*60}")
                self.stdout.write(f"BORROWER: {borrower.get_full_name()} ({borrower.username})")
                self.stdout.write(f"{'='*60}\n")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Borrower with username "{borrower_username}" not found'))
                return

            # Get all loans for this borrower
            loans = Loan.objects.filter(borrower=borrower)
        else:
            loans = Loan.objects.filter(application_number=loan_app_number)
            if not loans.exists():
                self.stdout.write(self.style.ERROR(f'Loan with application number "{loan_app_number}" not found'))
                return

        for loan in loans:
            self.stdout.write(f"\n{'─'*60}")
            self.stdout.write(f"LOAN: {loan.application_number} - {loan.get_status_display()}")
            self.stdout.write(f"Amount: K{loan.principal_amount:,.2f}")
            self.stdout.write(f"{'─'*60}\n")

            # Get payment schedules
            schedules = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
            self.stdout.write(f"PAYMENT SCHEDULES ({schedules.count()}):")
            for schedule in schedules:
                status = "✓ PAID" if schedule.is_paid else "✗ UNPAID"
                overdue = " (OVERDUE)" if schedule.is_overdue else ""
                self.stdout.write(
                    f"  Schedule #{schedule.installment_number}: K{schedule.total_amount:,.2f} "
                    f"due {schedule.due_date} - {status}{overdue}"
                )

            # Get payments
            payments = Payment.objects.filter(loan=loan).order_by('-payment_date')
            self.stdout.write(f"\nPAYMENTS ({payments.count()}):")
            for payment in payments:
                schedule_info = f"→ Schedule #{payment.payment_schedule.installment_number}" if payment.payment_schedule else "→ NO SCHEDULE LINKED"
                self.stdout.write(
                    f"  {payment.payment_number}: K{payment.amount:,.2f} "
                    f"({payment.get_status_display()}) on {payment.payment_date.date()} "
                    f"{schedule_info}"
                )

            # Check for unpaid schedules with completed payments
            self.stdout.write(f"\nANALYSIS:")
            unpaid_schedules = schedules.filter(is_paid=False)
            if unpaid_schedules.exists():
                self.stdout.write(f"  Found {unpaid_schedules.count()} unpaid schedule(s)")
                for schedule in unpaid_schedules:
                    # Check if there's a completed payment for this schedule
                    completed_payment = Payment.objects.filter(
                        payment_schedule=schedule,
                        status='completed'
                    ).first()
                    if completed_payment:
                        self.stdout.write(
                            self.style.WARNING(
                                f"    ⚠ Schedule #{schedule.installment_number} is unpaid but has completed payment: {completed_payment.payment_number}"
                            )
                        )
                    else:
                        # Check if there's any payment for this schedule
                        any_payment = Payment.objects.filter(payment_schedule=schedule).first()
                        if any_payment:
                            self.stdout.write(
                                f"    ℹ Schedule #{schedule.installment_number} has payment {any_payment.payment_number} with status: {any_payment.get_status_display()}"
                            )
                        else:
                            self.stdout.write(
                                f"    ℹ Schedule #{schedule.installment_number} has no payments"
                            )
            else:
                self.stdout.write(f"  ✓ All schedules are marked as paid")

            # Check for unlinked payments
            unlinked_payments = payments.filter(payment_schedule__isnull=True)
            if unlinked_payments.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Found {unlinked_payments.count()} payment(s) not linked to any schedule"
                    )
                )
                for payment in unlinked_payments:
                    self.stdout.write(f"    - {payment.payment_number}: K{payment.amount:,.2f} ({payment.get_status_display()})")

        self.stdout.write(f"\n{'='*60}\n")
