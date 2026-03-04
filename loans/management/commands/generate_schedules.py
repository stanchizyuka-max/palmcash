from django.core.management.base import BaseCommand
from loans.models import Loan
from loans.utils import generate_payment_schedule

class Command(BaseCommand):
    help = 'Generate payment schedules for all active loans without schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loan-id',
            type=int,
            help='Generate schedule for a specific loan ID',
        )

    def handle(self, *args, **options):
        loan_id = options.get('loan_id')
        
        if loan_id:
            # Generate for specific loan
            try:
                loan = Loan.objects.get(id=loan_id)
                generate_payment_schedule(loan)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully generated schedule for loan {loan.application_number}')
                )
            except Loan.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Loan with ID {loan_id} not found')
                )
        else:
            # Generate for all active loans without schedules
            active_loans = Loan.objects.filter(status__in=['active', 'disbursed'])
            count = 0
            
            for loan in active_loans:
                from payments.models import PaymentSchedule
                if not PaymentSchedule.objects.filter(loan=loan).exists():
                    generate_payment_schedule(loan)
                    count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Generated schedule for {loan.application_number}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully generated {count} payment schedules')
            )
