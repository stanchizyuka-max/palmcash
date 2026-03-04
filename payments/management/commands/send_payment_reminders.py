"""
Management command to send payment reminders for upcoming and overdue payments
Usage: python manage.py send_payment_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from payments.models import PaymentSchedule
from common.email_utils import send_payment_due_email, send_payment_overdue_email


class Command(BaseCommand):
    help = 'Send payment reminders for upcoming and overdue payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=3,
            help='Number of days before due date to send reminder (default: 3)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually sending emails'
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent'))
        
        today = timezone.now().date()
        reminder_date = today + timedelta(days=days_before)
        
        # Find upcoming payments
        upcoming_payments = PaymentSchedule.objects.filter(
            due_date=reminder_date,
            is_paid=False,
            loan__status='active'
        ).select_related('loan', 'loan__borrower')
        
        # Find overdue payments
        overdue_payments = PaymentSchedule.objects.filter(
            due_date__lt=today,
            is_paid=False,
            loan__status='active'
        ).select_related('loan', 'loan__borrower')
        
        # Send upcoming payment reminders
        upcoming_count = 0
        for payment in upcoming_payments:
            days_until_due = (payment.due_date - today).days
            
            if not dry_run:
                try:
                    send_payment_due_email(
                        loan=payment.loan,
                        payment_amount=payment.total_amount,
                        due_date=payment.due_date,
                        days_until_due=days_until_due
                    )
                    upcoming_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Sent reminder to {payment.loan.borrower.email} for payment due on {payment.due_date}'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Failed to send reminder to {payment.loan.borrower.email}: {str(e)}'
                        )
                    )
            else:
                upcoming_count += 1
                self.stdout.write(
                    f'Would send reminder to {payment.loan.borrower.email} for payment due on {payment.due_date}'
                )
        
        # Send overdue payment reminders
        overdue_count = 0
        for payment in overdue_payments:
            days_overdue = (today - payment.due_date).days
            late_fee = payment.penalty_amount if payment.penalty_amount else 0
            
            if not dry_run:
                try:
                    send_payment_overdue_email(
                        loan=payment.loan,
                        payment_amount=payment.total_amount,
                        due_date=payment.due_date,
                        days_overdue=days_overdue,
                        late_fee=late_fee
                    )
                    overdue_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Sent overdue notice to {payment.loan.borrower.email} ({days_overdue} days overdue)'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Failed to send overdue notice to {payment.loan.borrower.email}: {str(e)}'
                        )
                    )
            else:
                overdue_count += 1
                self.stdout.write(
                    f'Would send overdue notice to {payment.loan.borrower.email} ({days_overdue} days overdue)'
                )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  Upcoming payment reminders: {upcoming_count}')
        self.stdout.write(f'  Overdue payment notices: {overdue_count}')
        self.stdout.write(f'  Total emails: {upcoming_count + overdue_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No emails were actually sent'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Payment reminders sent successfully!'))
