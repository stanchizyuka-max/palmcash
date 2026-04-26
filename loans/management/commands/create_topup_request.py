from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from loans.models import Loan, SecurityTopUpRequest
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create the missing K200 top-up request for Shucco Zulu'

    def add_arguments(self, parser):
        parser.add_argument(
            '--officer-id',
            type=int,
            help='ID of the officer to create the request as',
            required=True
        )
        parser.add_argument(
            '--amount',
            type=float,
            default=200.0,
            help='Top-up amount (default: 200)'
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually create the request (dry run by default)'
        )

    def handle(self, *args, **options):
        officer_id = options['officer_id']
        amount = Decimal(str(options['amount']))
        execute = options['execute']
        
        # Get the officer
        try:
            officer = User.objects.get(id=officer_id, role='loan_officer')
            self.stdout.write(f"Officer: {officer.first_name} {officer.last_name} (ID: {officer_id})")
        except User.DoesNotExist:
            self.stdout.write(f"❌ Officer with ID {officer_id} not found")
            return

        # Get Shucco Zulu
        try:
            client = User.objects.get(
                first_name__icontains='shucco',
                last_name__icontains='zulu',
                role='borrower'
            )
            self.stdout.write(f"Client: {client.first_name} {client.last_name}")
        except User.DoesNotExist:
            self.stdout.write("❌ Shucco Zulu not found")
            return

        # Get the loan
        loan = Loan.objects.filter(borrower=client, status='active').first()
        if not loan:
            self.stdout.write("❌ No active loan found for client")
            return
        
        self.stdout.write(f"Loan: {loan.application_number}")

        # Check if officer can access this client
        from clients.models import GroupMembership
        can_access = (
            client.assigned_officer == officer or
            GroupMembership.objects.filter(
                borrower=client,
                group__assigned_officer=officer,
                is_active=True
            ).exists()
        )
        
        if not can_access:
            self.stdout.write(f"❌ Officer {officer.first_name} cannot access this client")
            self.stdout.write("   Use fix_shucco_assignment command first")
            return

        # Check for existing requests
        existing = SecurityTopUpRequest.objects.filter(
            loan=loan,
            requested_amount=amount,
            status='pending'
        ).exists()
        
        if existing:
            self.stdout.write(f"❌ Pending K{amount} request already exists")
            return

        if not execute:
            self.stdout.write(f"\n🔍 DRY RUN - Request that would be created:")
            self.stdout.write(f"  - Loan: {loan.application_number}")
            self.stdout.write(f"  - Amount: K{amount}")
            self.stdout.write(f"  - Officer: {officer.first_name} {officer.last_name}")
            self.stdout.write(f"  - Reason: Manual creation of missing top-up request")
            self.stdout.write("\nRun with --execute to create the request")
            return

        # Create the request
        request = SecurityTopUpRequest.objects.create(
            loan=loan,
            requested_amount=amount,
            reason=f"Manual creation of missing K{amount} top-up request for loan amount increase",
            requested_by=officer,
            status='pending'
        )
        
        self.stdout.write(f"\n🎉 SUCCESS: Created top-up request")
        self.stdout.write(f"  - Request ID: {request.id}")
        self.stdout.write(f"  - Amount: K{request.requested_amount}")
        self.stdout.write(f"  - Status: {request.status}")
        self.stdout.write(f"  - Date: {request.requested_date}")
        self.stdout.write("\nRequest is now visible in manager's pending approvals!")