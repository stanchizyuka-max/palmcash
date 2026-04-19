"""
Management command to reset all application data.
Clears all users, loans, payments, securities, vault, groups, etc.
Keeps: migrations, loan types, branches structure (optional)

Usage:
    python manage.py reset_data
    python manage.py reset_data --keep-branches
    python manage.py reset_data --keep-loan-types
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Reset all application data — removes all users, loans, payments, vault, groups, etc.'

    def add_arguments(self, parser):
        parser.add_argument('--keep-branches', action='store_true', help='Keep branch records')
        parser.add_argument('--keep-loan-types', action='store_true', help='Keep loan type records')
        parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')

    def handle(self, *args, **options):
        if not options['yes']:
            confirm = input(
                '\n⚠️  WARNING: This will DELETE ALL DATA including users, loans, payments, vault, groups.\n'
                'This cannot be undone.\n\n'
                'Type YES to confirm: '
            )
            if confirm.strip() != 'YES':
                self.stdout.write(self.style.WARNING('Aborted.'))
                return

        self.stdout.write('Starting data reset...')

        # Order matters — delete children before parents
        models_to_clear = [
            # Payments
            ('payments', 'PassbookEntry'),
            ('payments', 'DefaultCollection'),
            ('payments', 'PaymentCollection'),
            ('payments', 'PaymentSchedule'),
            ('payments', 'Payment'),
            # Securities
            ('loans', 'SecurityTransaction'),
            ('loans', 'SecurityTopUpRequest'),
            ('loans', 'SecurityReturnRequest'),
            ('loans', 'SecurityDeposit'),
            # Loans
            ('loans', 'LoanDocument'),
            ('loans', 'LoanApprovalRequest'),
            ('loans', 'ManagerLoanApproval'),
            ('loans', 'ApprovalLog'),
            ('loans', 'LoanApplication'),
            ('loans', 'Loan'),
            # Vault
            ('expenses', 'VaultTransaction'),
            ('loans', 'BranchVault'),
            # Expenses
            ('expenses', 'Expense'),
            ('expenses', 'FundsTransfer'),
            ('expenses', 'BankDeposit'),
            # Clients / Groups
            ('clients', 'CollectionAuditLog'),
            ('clients', 'DisbursementAuditLog'),
            ('clients', 'ApprovalAuditLog'),
            ('clients', 'AdminAuditLog'),
            ('clients', 'ClientAssignmentAuditLog'),
            ('clients', 'ClientTransferLog'),
            ('clients', 'OfficerTransferLog'),
            ('clients', 'LoanApprovalQueue'),
            ('clients', 'GroupMembership'),
            ('clients', 'OfficerAssignment'),
            ('clients', 'BorrowerGroup'),
            # Documents
            ('documents', 'ClientDocument'),
            ('documents', 'ClientVerification'),
            # Notifications
            ('notifications', 'Notification'),
            # Internal messages
            ('internal_messages', 'ThreadMessage'),
            ('internal_messages', 'MessageThread'),
            ('internal_messages', 'Message'),
            # Accounts / Users
            ('accounts', 'UserActivityLog'),
            ('accounts', 'UserLoginSession'),
        ]

        for app, model_name in models_to_clear:
            try:
                from django.apps import apps
                model = apps.get_model(app, model_name)
                count = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f'  ✓ Cleared {model_name} ({count} records)')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Skipped {model_name}: {e}'))

        # Clear users (except keep superusers option)
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            count = User.objects.count()
            User.objects.all().delete()
            self.stdout.write(f'  ✓ Cleared Users ({count} records)')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠ Skipped Users: {e}'))

        # Optionally keep branches
        if not options['keep_branches']:
            try:
                from clients.models import Branch
                count = Branch.objects.count()
                Branch.objects.all().delete()
                self.stdout.write(f'  ✓ Cleared Branches ({count} records)')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Skipped Branches: {e}'))

        # Optionally keep loan types
        if not options['keep_loan_types']:
            try:
                from loans.models import LoanType
                count = LoanType.objects.count()
                LoanType.objects.all().delete()
                self.stdout.write(f'  ✓ Cleared LoanTypes ({count} records)')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Skipped LoanTypes: {e}'))

        # Reset sequences (PostgreSQL)
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 'SELECT SETVAL(' || quote_literal(quote_ident(schemaname) || '.' || quote_ident(sequencename)) || ', 1, false);'
                    FROM pg_sequences WHERE schemaname = 'public';
                """)
                statements = cursor.fetchall()
            with connection.cursor() as cursor:
                for (stmt,) in statements:
                    cursor.execute(stmt)
            self.stdout.write('  ✓ Reset all ID sequences')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠ Could not reset sequences: {e}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Data reset complete!'))
        self.stdout.write('Run: python manage.py setup_admin  — to recreate the admin user')
