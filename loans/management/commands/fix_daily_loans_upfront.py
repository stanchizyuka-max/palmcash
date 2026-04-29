from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.models import Loan, SecurityDeposit
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix daily loans to mark upfront_payment_verified=True and create security deposits'

    def handle(self, *args, **options):
        # Find all approved daily loans without upfront_payment_verified
        daily_loans = Loan.objects.filter(
            repayment_frequency='daily',
            status='approved',
            upfront_payment_verified=False
        )
        
        self.stdout.write(f'Found {daily_loans.count()} daily loans to fix')
        
        fixed_count = 0
        for loan in daily_loans:
            # Create or update security deposit
            security, created = SecurityDeposit.objects.get_or_create(
                loan=loan,
                defaults={
                    'required_amount': Decimal('0'),
                    'paid_amount': Decimal('0'),
                    'is_verified': True,
                    'verification_date': timezone.now(),
                }
            )
            
            if not created and not security.is_verified:
                security.is_verified = True
                security.verification_date = timezone.now()
                security.save(update_fields=['is_verified', 'verification_date'])
            
            # Mark upfront payment as verified
            loan.upfront_payment_verified = True
            loan.save(update_fields=['upfront_payment_verified'])
            
            fixed_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Fixed loan {loan.application_number} for {loan.borrower.get_full_name()}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully fixed {fixed_count} daily loans'
            )
        )
