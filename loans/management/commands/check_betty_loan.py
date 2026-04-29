from django.core.management.base import BaseCommand
from loans.models import Loan, LoanApplication
from accounts.models import User


class Command(BaseCommand):
    help = 'Check Betty\'s loan status'

    def handle(self, *args, **options):
        # Find Betty
        bettys = User.objects.filter(first_name__icontains='betty', role='borrower')
        
        self.stdout.write(f'\nFound {bettys.count()} users named Betty:')
        for betty in bettys:
            self.stdout.write(f'  - {betty.get_full_name()} (ID: {betty.id})')
            
            # Check loan applications
            apps = LoanApplication.objects.filter(borrower=betty).order_by('-created_at')
            self.stdout.write(f'    Loan Applications: {apps.count()}')
            for app in apps[:5]:  # Show last 5
                self.stdout.write(
                    f'      {app.application_number}: {app.status} - '
                    f'K{app.loan_amount} ({app.repayment_frequency}) - '
                    f'Created: {app.created_at.strftime("%Y-%m-%d %H:%M")}'
                )
            
            # Check loans
            loans = Loan.objects.filter(borrower=betty).order_by('-created_at')
            self.stdout.write(f'    Loans: {loans.count()}')
            for loan in loans[:5]:  # Show last 5
                self.stdout.write(
                    f'      {loan.application_number}: {loan.status} - '
                    f'K{loan.principal_amount} ({loan.repayment_frequency}) - '
                    f'Upfront verified: {loan.upfront_payment_verified} - '
                    f'Created: {loan.created_at.strftime("%Y-%m-%d %H:%M")}'
                )
                
                # Check security deposit
                try:
                    sec = loan.security_deposit
                    self.stdout.write(
                        f'        Security: Required K{sec.required_amount}, '
                        f'Paid K{sec.paid_amount}, Verified: {sec.is_verified}'
                    )
                except:
                    self.stdout.write(f'        Security: NOT FOUND')
        
        # Also check all approved daily loans
        self.stdout.write(f'\n\nAll Approved Daily Loans:')
        daily_approved = Loan.objects.filter(
            repayment_frequency='daily',
            status='approved'
        ).order_by('-created_at')
        
        self.stdout.write(f'Found {daily_approved.count()} approved daily loans:')
        for loan in daily_approved[:10]:
            self.stdout.write(
                f'  {loan.application_number}: {loan.borrower.get_full_name()} - '
                f'K{loan.principal_amount} - '
                f'Upfront verified: {loan.upfront_payment_verified} - '
                f'Officer: {loan.loan_officer.get_full_name() if loan.loan_officer else "None"}'
            )
