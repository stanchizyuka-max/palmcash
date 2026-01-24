from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models import Payment, PaymentSchedule
from loans.models import Loan
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix overdue payment status by marking completed payments as paid in payment schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--borrower',
            type=str,
            help='Username of borrower to fix payments for',
        )
        parser.add_argument(
            '--loan',
            type=str,
            help='Loan application number to fix',
        )

    def handle(self, *args, **options):
        borrower_username = options.get('borrower')
        loan_app_number = options.get('loan')

        # Get completed payments that haven't updated their payment schedules
        completed_payments = Payment.objects.filter(status='completed')

        if borrower_username:
            try:
                borrower = User.objects.get(username=borrower_username)
                completed_payments = completed_payments.filter(loan__borrower=borrower)
                self.stdout.write(f"Filtering for borrower: {borrower.get_full_name()}")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Borrower with username "{borrower_username}" not found'))
                return

        if loan_app_number:
            completed_payments = completed_payments.filter(loan__application_number=loan_app_number)
            self.stdout.write(f"Filtering for loan: {loan_app_number}")

        fixed_count = 0
        for payment in completed_payments:
            if payment.payment_schedule:
                if not payment.payment_schedule.is_paid:
                    # Mark the payment schedule as paid
                    payment.payment_schedule.is_paid = True
                    payment.payment_schedule.paid_date = payment.payment_date.date()
                    payment.payment_schedule.save()
                    fixed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Fixed: Payment {payment.payment_number} for {payment.loan.application_number} '
                            f'(Schedule #{payment.payment_schedule.installment_number})'
                        )
                    )

        # Also check for overdue payments that should be marked as paid
        overdue_payments = PaymentSchedule.objects.filter(
            is_paid=False,
            due_date__lt=timezone.now().date()
        )

        if borrower_username:
            overdue_payments = overdue_payments.filter(loan__borrower=borrower)

        if loan_app_number:
            overdue_payments = overdue_payments.filter(loan__application_number=loan_app_number)

        # Check if these overdue payments have completed payments
        for schedule in overdue_payments:
            completed_payment = Payment.objects.filter(
                payment_schedule=schedule,
                status='completed'
            ).first()

            if completed_payment:
                schedule.is_paid = True
                schedule.paid_date = completed_payment.payment_date.date()
                schedule.save()
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Fixed overdue: Payment {completed_payment.payment_number} for {schedule.loan.application_number} '
                        f'(Schedule #{schedule.installment_number})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully fixed {fixed_count} payment schedule(s)')
        )
