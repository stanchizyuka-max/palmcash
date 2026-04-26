from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from loans.models import Loan
from clients.models import BorrowerGroup

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix Shucco Zulu assignment to correct Precious officer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--precious-id',
            type=int,
            help='ID of the correct Precious officer (64 or 65)',
            required=True
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually perform the changes (dry run by default)'
        )

    def handle(self, *args, **options):
        precious_id = options['precious_id']
        execute = options['execute']
        
        # Get the correct Precious officer
        try:
            precious_officer = User.objects.get(id=precious_id, role='loan_officer')
            self.stdout.write(f"Target officer: {precious_officer.first_name} {precious_officer.last_name} (ID: {precious_id})")
        except User.DoesNotExist:
            self.stdout.write(f"❌ Officer with ID {precious_id} not found")
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
        loan = Loan.objects.filter(borrower=client).first()
        if not loan:
            self.stdout.write("❌ No loan found for client")
            return
        
        self.stdout.write(f"Loan: {loan.application_number} (Current officer: {loan.loan_officer})")

        # Get the group
        group = BorrowerGroup.objects.filter(
            members__borrower=client,
            members__is_active=True
        ).first()
        
        if group:
            self.stdout.write(f"Group: {group.name} (Current officer: {group.assigned_officer})")

        if not execute:
            self.stdout.write("\n🔍 DRY RUN - Changes that would be made:")
            self.stdout.write(f"  - Update loan officer: {loan.loan_officer} → {precious_officer}")
            if group:
                self.stdout.write(f"  - Update group officer: {group.assigned_officer} → {precious_officer}")
            self.stdout.write(f"  - Update client assignment: {client.assigned_officer} → {precious_officer}")
            self.stdout.write("\nRun with --execute to apply changes")
            return

        # Apply changes
        self.stdout.write("\n✅ EXECUTING CHANGES:")
        
        # Update loan officer
        old_loan_officer = loan.loan_officer
        loan.loan_officer = precious_officer
        loan.save()
        self.stdout.write(f"  ✓ Loan officer: {old_loan_officer} → {precious_officer}")

        # Update group officer
        if group:
            old_group_officer = group.assigned_officer
            group.assigned_officer = precious_officer
            group.save()
            self.stdout.write(f"  ✓ Group officer: {old_group_officer} → {precious_officer}")

        # Update client assignment
        old_assigned_officer = client.assigned_officer
        client.assigned_officer = precious_officer
        client.save()
        self.stdout.write(f"  ✓ Client assignment: {old_assigned_officer} → {precious_officer}")

        self.stdout.write(f"\n🎉 SUCCESS: Shucco Zulu is now assigned to {precious_officer.first_name} {precious_officer.last_name}")
        self.stdout.write("Precious can now create top-up requests for this client.")