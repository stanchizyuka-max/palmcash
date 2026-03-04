from django.core.management.base import BaseCommand
from loans.models import Loan
from payments.models import Payment
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Fix upfront payments by updating upfront_payment_paid based on completed payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--borrower',
            type=str,
            help='Username of borrower to fix (optional)',
        )

    def handle(self, *args, **options):
        borrower_username = options.get('borrower')
        
        if borrower_username:
            # Fix for specific borrower
            self.fix_borrower_upfront(borrower_username)
        else:
            # Fix all loans with upfront payments
            self.fix_all_upfront_payments()
    
    def fix_borrower_upfront(self, username):
        """Fix upfront payment for a specific borrower"""
        try:
            from accounts.models import User
            # Try to find by username first, then by first_name
            try:
                borrower = User.objects.get(username=username)
            except User.DoesNotExist:
                # Try searching by first_name
                borrower = User.objects.get(first_name__iexact=username)
            
            # Find all loans for this borrower
            loans = Loan.objects.filter(borrower=borrower)
            
            self.stdout.write(f"Found {loans.count()} loans for {borrower.get_full_name()}")
            
            for loan in loans:
                self.fix_loan_upfront(loan)
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
    
    def fix_all_upfront_payments(self):
        """Fix upfront payments for all loans"""
        # Find all loans with upfront payment requirements
        loans = Loan.objects.filter(upfront_payment_required__gt=0)
        
        self.stdout.write(f"Found {loans.count()} loans with upfront payment requirements")
        
        for loan in loans:
            self.fix_loan_upfront(loan)
    
    def fix_loan_upfront(self, loan):
        """Fix upfront payment for a specific loan"""
        # Find completed payments without a payment schedule (upfront payments)
        upfront_payments = Payment.objects.filter(
            loan=loan,
            status='completed',
            payment_schedule__isnull=True
        )
        
        if upfront_payments.count() == 0:
            return
        
        total_upfront_paid = Decimal('0')
        for payment in upfront_payments:
            total_upfront_paid += payment.amount
        
        # Update the loan if the amount differs
        if loan.upfront_payment_paid != total_upfront_paid:
            old_amount = loan.upfront_payment_paid
            loan.upfront_payment_paid = total_upfront_paid
            loan.upfront_payment_date = upfront_payments.first().payment_date
            loan.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {loan.application_number}: Updated upfront from K{old_amount} to K{total_upfront_paid}'
                )
            )
        else:
            self.stdout.write(f'  {loan.application_number}: Already correct (K{total_upfront_paid})')
