from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from loans.models import Loan, LoanApprovalRequest, SecurityDeposit
from payments.models import PaymentCollection, PassbookEntry, MultiSchedulePayment, PaymentSchedule
from documents.models import ClientDocument, ClientVerification


class Command(BaseCommand):
    help = 'Delete all borrowers and their related data (loans, payments, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            confirm = input('Are you sure you want to delete all borrowers and their data? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Deletion cancelled.'))
                return

        with transaction.atomic():
            # Get all borrowers
            borrowers = User.objects.filter(role='borrower')
            borrower_count = borrowers.count()
            
            self.stdout.write(f'Found {borrower_count} borrowers to delete')
            
            # Delete related data first
            # Delete payment collections
            payment_collections = PaymentCollection.objects.filter(
                loan__borrower__in=borrowers
            )
            pc_count = payment_collections.count()
            payment_collections.delete()
            self.stdout.write(f'Deleted {pc_count} payment collections')
            
            # Delete passbook entries
            passbook_entries = PassbookEntry.objects.filter(
                loan__borrower__in=borrowers
            )
            pb_count = passbook_entries.count()
            passbook_entries.delete()
            self.stdout.write(f'Deleted {pb_count} passbook entries')
            
            # Delete multi-schedule payments
            multi_payments = MultiSchedulePayment.objects.filter(
                loan__borrower__in=borrowers
            )
            mp_count = multi_payments.count()
            multi_payments.delete()
            self.stdout.write(f'Deleted {mp_count} multi-schedule payments')
            
            # Delete payment schedules
            payment_schedules = PaymentSchedule.objects.filter(
                loan__borrower__in=borrowers
            )
            ps_count = payment_schedules.count()
            payment_schedules.delete()
            self.stdout.write(f'Deleted {ps_count} payment schedules')
            
            # Delete security deposits
            security_deposits = SecurityDeposit.objects.filter(
                loan__borrower__in=borrowers
            )
            sd_count = security_deposits.count()
            security_deposits.delete()
            self.stdout.write(f'Deleted {sd_count} security deposits')
            
            # Delete loan approval requests
            loan_approvals = LoanApprovalRequest.objects.filter(
                loan__borrower__in=borrowers
            )
            la_count = loan_approvals.count()
            loan_approvals.delete()
            self.stdout.write(f'Deleted {la_count} loan approval requests')
            
            # Delete client documents
            client_docs = ClientDocument.objects.filter(
                client__in=borrowers
            )
            cd_count = client_docs.count()
            client_docs.delete()
            self.stdout.write(f'Deleted {cd_count} client documents')
            
            # Delete client verifications
            client_verifs = ClientVerification.objects.filter(
                client__in=borrowers
            )
            cv_count = client_verifs.count()
            client_verifs.delete()
            self.stdout.write(f'Deleted {cv_count} client verifications')
            
            # Delete loans
            loans = Loan.objects.filter(borrower__in=borrowers)
            loan_count = loans.count()
            loans.delete()
            self.stdout.write(f'Deleted {loan_count} loans')
            
            # Remove borrowers from groups
            for borrower in borrowers:
                borrower.group_memberships.all().delete()
            self.stdout.write('Removed borrowers from groups')
            
            # Delete borrower users
            borrowers.delete()
            self.stdout.write(f'Deleted {borrower_count} borrower users')

        self.stdout.write(self.style.SUCCESS('\n✓ All borrower data has been successfully deleted!'))
        self.stdout.write(self.style.SUCCESS('You can now start fresh with new borrowers and loans.'))
