from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.models import Loan, LoanApplication, LoanType, SecurityDeposit
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create loan from approved application'

    def add_arguments(self, parser):
        parser.add_argument('application_number', type=str, help='Application number (e.g., LA-49FD63AA)')

    def handle(self, *args, **options):
        app_number = options['application_number']
        
        try:
            loan_app = LoanApplication.objects.get(application_number=app_number)
        except LoanApplication.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Application {app_number} not found'))
            return
        
        if loan_app.status != 'approved':
            self.stdout.write(self.style.ERROR(f'Application {app_number} is not approved (status: {loan_app.status})'))
            return
        
        # Check if loan already exists
        existing = Loan.objects.filter(borrower=loan_app.borrower, principal_amount=loan_app.loan_amount).first()
        if existing:
            self.stdout.write(self.style.WARNING(f'Loan may already exist: {existing.application_number}'))
            response = input('Continue anyway? (yes/no): ')
            if response.lower() != 'yes':
                return
        
        # Get or create loan type
        loan_type = LoanType.objects.filter(is_active=True).first()
        if not loan_type:
            loan_type = LoanType.objects.create(
                name='Standard',
                description='Standard loan',
                interest_rate=Decimal('45.00'),
                min_amount=Decimal('100.00'),
                max_amount=Decimal('1000000.00'),
                repayment_frequency='daily',
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS('Created default loan type'))
        
        freq = loan_app.repayment_frequency
        interest_rate = Decimal('40.00') if freq == 'daily' else Decimal('45.00')
        term_days = loan_app.duration_days if freq == 'daily' else None
        term_weeks = (loan_app.duration_days // 7) if freq == 'weekly' else None
        
        # Create loan
        loan = Loan(
            borrower=loan_app.borrower,
            loan_officer=loan_app.loan_officer,
            loan_type=loan_type,
            principal_amount=loan_app.loan_amount,
            purpose=loan_app.purpose,
            status='approved',
            repayment_frequency=freq,
            interest_rate=interest_rate,
            term_days=term_days,
            term_weeks=term_weeks,
            payment_amount=Decimal('0'),
            approval_date=timezone.now(),
        )
        loan.save()
        
        self.stdout.write(self.style.SUCCESS(f'Created loan: {loan.application_number}'))
        
        # Handle security based on frequency
        if freq == 'daily':
            # Daily loans don't require security
            SecurityDeposit.objects.create(
                loan=loan,
                required_amount=Decimal('0'),
                paid_amount=Decimal('0'),
                is_verified=True,
                verification_date=timezone.now(),
            )
            loan.upfront_payment_verified = True
            loan.save(update_fields=['upfront_payment_verified'])
            
            self.stdout.write(self.style.SUCCESS(f'Daily loan - no security required. Ready to disburse!'))
        else:
            # Weekly loans require security
            required = loan.principal_amount * Decimal('0.10')
            SecurityDeposit.objects.create(
                loan=loan,
                required_amount=required,
                paid_amount=Decimal('0'),
                is_verified=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Weekly loan - requires K{required} security deposit'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nLoan {loan.application_number} created successfully for {loan.borrower.get_full_name()}'
            )
        )
