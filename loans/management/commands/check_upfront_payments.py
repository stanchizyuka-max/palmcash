"""
Diagnostic command to check upfront payment status for loans.
"""
from django.core.management.base import BaseCommand
from loans.models import Loan
from django.db.models import Q


class Command(BaseCommand):
    help = 'Check upfront payment status for loans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--borrower',
            type=str,
            help='Filter by borrower name (partial match)',
        )

    def handle(self, *args, **options):
        borrower_name = options.get('borrower')

        # Get loans with upfront payments
        loans = Loan.objects.filter(
            Q(upfront_payment_paid__gt=0) | Q(security_deposit__paid_amount__gt=0)
        ).select_related('borrower', 'loan_officer', 'security_deposit')

        if borrower_name:
            loans = loans.filter(
                Q(borrower__first_name__icontains=borrower_name) |
                Q(borrower__last_name__icontains=borrower_name)
            )
        
        loans = loans.order_by('-created_at')[:20]

        if not loans:
            self.stdout.write(
                self.style.WARNING('No loans with upfront payments found.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'\nFound {loans.count()} loan(s) with upfront payments:\n')
        )

        for loan in loans:
            self.stdout.write(f'\n{"="*70}')
            self.stdout.write(f'Loan: {loan.application_number}')
            self.stdout.write(f'Borrower: {loan.borrower.get_full_name()}')
            self.stdout.write(f'Officer: {loan.loan_officer.get_full_name() if loan.loan_officer else "None"}')
            self.stdout.write(f'Status: {loan.status}')
            self.stdout.write(f'Frequency: {loan.repayment_frequency}')
            self.stdout.write(f'Created: {loan.created_at.strftime("%Y-%m-%d %H:%M")}')
            
            self.stdout.write(f'\nUpfront Payment (Loan model):')
            self.stdout.write(f'  Required: K{loan.upfront_payment_required or 0:.2f}')
            self.stdout.write(f'  Paid: K{loan.upfront_payment_paid:.2f}')
            self.stdout.write(f'  Date: {loan.upfront_payment_date.strftime("%Y-%m-%d %H:%M") if loan.upfront_payment_date else "Not set"}')
            self.stdout.write(f'  Verified: {loan.upfront_payment_verified}')
            
            if hasattr(loan, 'security_deposit') and loan.security_deposit:
                dep = loan.security_deposit
                self.stdout.write(f'\nSecurity Deposit:')
                self.stdout.write(f'  Required: K{dep.required_amount:.2f}')
                self.stdout.write(f'  Paid: K{dep.paid_amount:.2f}')
                self.stdout.write(f'  Payment Date: {dep.payment_date.strftime("%Y-%m-%d %H:%M") if dep.payment_date else "Not set"}')
                self.stdout.write(f'  Verified: {dep.is_verified}')
                self.stdout.write(f'  Verified By: {dep.verified_by.get_full_name() if dep.verified_by else "None"}')
            else:
                self.stdout.write(f'\nSecurity Deposit: None')
            
            # Check if it should appear in manager's pending list
            should_appear = (
                loan.status == 'approved' and
                (
                    (loan.upfront_payment_paid > 0 and not loan.upfront_payment_verified) or
                    (hasattr(loan, 'security_deposit') and loan.security_deposit and 
                     loan.security_deposit.paid_amount > 0 and not loan.security_deposit.is_verified)
                )
            )
            
            if should_appear:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ This loan SHOULD appear in manager\'s pending verifications'
                    )
                )
            else:
                reasons = []
                if loan.status != 'approved':
                    reasons.append(f'Status is "{loan.status}" (needs to be "approved")')
                if loan.upfront_payment_paid == 0:
                    reasons.append('No upfront payment recorded')
                if loan.upfront_payment_verified:
                    reasons.append('Upfront payment already verified')
                if hasattr(loan, 'security_deposit') and loan.security_deposit:
                    if loan.security_deposit.is_verified:
                        reasons.append('Security deposit already verified')
                
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠ This loan will NOT appear in manager\'s pending verifications'
                    )
                )
                for reason in reasons:
                    self.stdout.write(f'  - {reason}')

        self.stdout.write(f'\n{"="*70}\n')
