from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Set up user groups and permissions for LoanVista'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up groups and permissions...')

        # Create groups
        manager_group, created = Group.objects.get_or_create(name='Manager')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Manager group'))
        
        officer_group, created = Group.objects.get_or_create(name='LoanOfficer')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created LoanOfficer group'))

        # Get content types
        from loans.models import Loan
        from clients.models import Client
        from payments.models import Payment, PaymentSchedule
        from documents.models import Document

        loan_ct = ContentType.objects.get_for_model(Loan)
        client_ct = ContentType.objects.get_for_model(Client)
        payment_ct = ContentType.objects.get_for_model(Payment)
        schedule_ct = ContentType.objects.get_for_model(PaymentSchedule)
        document_ct = ContentType.objects.get_for_model(Document)

        # Manager permissions (full access except system admin)
        manager_permissions = [
            # Loans
            Permission.objects.get(codename='view_loan', content_type=loan_ct),
            Permission.objects.get(codename='add_loan', content_type=loan_ct),
            Permission.objects.get(codename='change_loan', content_type=loan_ct),
            Permission.objects.get(codename='delete_loan', content_type=loan_ct),
            
            # Clients
            Permission.objects.get(codename='view_client', content_type=client_ct),
            Permission.objects.get(codename='add_client', content_type=client_ct),
            Permission.objects.get(codename='change_client', content_type=client_ct),
            
            # Payments
            Permission.objects.get(codename='view_payment', content_type=payment_ct),
            Permission.objects.get(codename='add_payment', content_type=payment_ct),
            Permission.objects.get(codename='change_payment', content_type=payment_ct),
            Permission.objects.get(codename='view_paymentschedule', content_type=schedule_ct),
            
            # Documents
            Permission.objects.get(codename='view_document', content_type=document_ct),
            Permission.objects.get(codename='change_document', content_type=document_ct),
        ]

        manager_group.permissions.set(manager_permissions)
        self.stdout.write(self.style.SUCCESS(f'✓ Assigned {len(manager_permissions)} permissions to Manager group'))

        # Loan Officer permissions (limited to assigned loans)
        officer_permissions = [
            # Loans (view and create only)
            Permission.objects.get(codename='view_loan', content_type=loan_ct),
            Permission.objects.get(codename='add_loan', content_type=loan_ct),
            Permission.objects.get(codename='change_loan', content_type=loan_ct),
            
            # Clients (view and update basic info)
            Permission.objects.get(codename='view_client', content_type=client_ct),
            Permission.objects.get(codename='change_client', content_type=client_ct),
            
            # Payments (record and view)
            Permission.objects.get(codename='view_payment', content_type=payment_ct),
            Permission.objects.get(codename='add_payment', content_type=payment_ct),
            Permission.objects.get(codename='view_paymentschedule', content_type=schedule_ct),
            
            # Documents (view only)
            Permission.objects.get(codename='view_document', content_type=document_ct),
        ]

        officer_group.permissions.set(officer_permissions)
        self.stdout.write(self.style.SUCCESS(f'✓ Assigned {len(officer_permissions)} permissions to LoanOfficer group'))

        self.stdout.write(self.style.SUCCESS('\n✅ Groups and permissions setup complete!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Go to Django Admin')
        self.stdout.write('2. Assign users to Manager or LoanOfficer groups')
        self.stdout.write('3. Users will be redirected to their role-specific dashboard after login')
