from django.core.management.base import BaseCommand
from accounts.models import User
from clients.models import OfficerAssignment, Branch


class Command(BaseCommand):
    help = 'Assign a loan officer to a branch'

    def add_arguments(self, parser):
        parser.add_argument('officer_username', type=str, help='Username of the loan officer')
        parser.add_argument('branch_name', type=str, help='Name of the branch')
        parser.add_argument(
            '--max-groups',
            type=int,
            default=15,
            help='Maximum number of groups this officer can manage (default: 15)'
        )
        parser.add_argument(
            '--max-clients',
            type=int,
            default=50,
            help='Maximum number of clients this officer can handle (default: 50)'
        )

    def handle(self, *args, **options):
        officer_username = options['officer_username']
        branch_name = options['branch_name']
        max_groups = options['max_groups']
        max_clients = options['max_clients']

        # Get the officer
        try:
            officer = User.objects.get(username=officer_username, role='loan_officer')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ Loan officer "{officer_username}" not found'))
            return

        # Check if branch exists
        try:
            branch = Branch.objects.get(name=branch_name)
        except Branch.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'⚠ Branch "{branch_name}" does not exist in database'))
            self.stdout.write('Available branches:')
            for b in Branch.objects.all():
                self.stdout.write(f'  - {b.name}')
            return

        # Get or create assignment
        assignment, created = OfficerAssignment.objects.get_or_create(officer=officer)

        # Update assignment
        assignment.branch = branch_name
        assignment.max_groups = max_groups
        assignment.max_clients = max_clients
        assignment.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created assignment for {officer.full_name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Updated assignment for {officer.full_name}'))

        self.stdout.write(f'  Branch: {branch_name}')
        self.stdout.write(f'  Max Groups: {max_groups}')
        self.stdout.write(f'  Max Clients: {max_clients}')
