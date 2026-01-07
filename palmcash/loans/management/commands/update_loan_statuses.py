from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from loans.models import Loan
from payments.models import PaymentSchedule


class Command(BaseCommand):
    help = 'Update loan statuses based on payment history and overdue status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-overdue',
            type=int,
            default=90,
            help='Number of days overdue before marking loan as defaulted (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        days_overdue_threshold = options['days_overdue']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(f'Checking loan statuses (dry run: {dry_run})...')
        )
        
        # Get active loans
        active_loans = Loan.objects.filter(status='active')
        
        updated_completed = 0
        updated_defaulted = 0
        
        for loan in active_loans:
            # Check if loan should be marked as completed
            if self._is_loan_completed(loan):
                if not dry_run:
                    loan.status = 'completed'
                    loan.save()
                    self._create_completion_notification(loan)
                
                updated_completed += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"[DRY RUN] " if dry_run else ""}Loan {loan.application_number} marked as COMPLETED'
                    )
                )
            
            # Check if loan should be marked as defaulted
            elif self._is_loan_defaulted(loan, days_overdue_threshold):
                if not dry_run:
                    loan.status = 'defaulted'
                    loan.save()
                    self._create_default_notification(loan)
                
                updated_defaulted += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'{"[DRY RUN] " if dry_run else ""}Loan {loan.application_number} marked as DEFAULTED '
                        f'(overdue by {self._get_days_overdue(loan)} days)'
                    )
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"DRY RUN " if dry_run else ""}Summary:\n'
                f'- Loans marked as completed: {updated_completed}\n'
                f'- Loans marked as defaulted: {updated_defaulted}\n'
                f'- Total loans processed: {updated_completed + updated_defaulted}'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\nThis was a dry run. Use --dry-run=False to apply changes.'
                )
            )

    def _is_loan_completed(self, loan):
        """Check if loan is fully paid"""
        # Check if all payment schedules are paid
        unpaid_schedules = PaymentSchedule.objects.filter(loan=loan, is_paid=False).count()
        
        # Also check if balance is zero or negative
        balance_cleared = loan.balance_remaining is not None and loan.balance_remaining <= 0
        
        return unpaid_schedules == 0 or balance_cleared

    def _is_loan_defaulted(self, loan, days_threshold):
        """Check if loan should be marked as defaulted"""
        days_overdue = self._get_days_overdue(loan)
        return days_overdue >= days_threshold

    def _get_days_overdue(self, loan):
        """Get the number of days the loan is overdue"""
        # Find the oldest unpaid payment that's overdue
        overdue_payments = PaymentSchedule.objects.filter(
            loan=loan,
            is_paid=False,
            due_date__lt=date.today()
        ).order_by('due_date')
        
        if overdue_payments.exists():
            oldest_overdue = overdue_payments.first()
            return (date.today() - oldest_overdue.due_date).days
        
        return 0

    def _create_completion_notification(self, loan):
        """Create notification for loan completion"""
        try:
            from notifications.models import Notification, NotificationTemplate
            
            try:
                template = NotificationTemplate.objects.get(notification_type='loan_completed')
                
                message = template.message_template.format(
                    borrower_name=loan.borrower.full_name,
                    loan_number=loan.application_number,
                    total_amount=f"{loan.total_amount:,.2f}" if loan.total_amount else "0.00"
                )
                
                Notification.objects.create(
                    recipient=loan.borrower,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel=template.channel,
                    recipient_address=loan.borrower.email or str(loan.borrower.phone_number),
                    scheduled_at=timezone.now(),
                    loan=loan
                )
            except NotificationTemplate.DoesNotExist:
                pass  # Template not configured
        except ImportError:
            pass  # Notifications app not available

    def _create_default_notification(self, loan):
        """Create notification for loan default"""
        try:
            from notifications.models import Notification, NotificationTemplate
            
            try:
                template = NotificationTemplate.objects.get(notification_type='loan_defaulted')
                
                message = template.message_template.format(
                    borrower_name=loan.borrower.full_name,
                    loan_number=loan.application_number,
                    days_overdue=self._get_days_overdue(loan),
                    balance_remaining=f"{loan.balance_remaining:,.2f}" if loan.balance_remaining else "0.00"
                )
                
                Notification.objects.create(
                    recipient=loan.borrower,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel=template.channel,
                    recipient_address=loan.borrower.email or str(loan.borrower.phone_number),
                    scheduled_at=timezone.now(),
                    loan=loan
                )
            except NotificationTemplate.DoesNotExist:
                pass  # Template not configured
        except ImportError:
            pass  # Notifications app not available
