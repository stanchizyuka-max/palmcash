from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from loans.models import LoanType
from documents.models import DocumentType
from notifications.models import NotificationTemplate

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate initial data for LoanVista'

    def handle(self, *args, **options):
        self.stdout.write('Creating initial data...')
        
        # Create loan types (amounts in ZMW)
        loan_types = [
            {
                'name': 'Personal Loan',
                'description': 'Unsecured personal loans for various purposes',
                'interest_rate': 18.0,  # Higher rate typical for Zambia
                'min_amount': 2000,     # K2,000
                'max_amount': 250000,   # K250,000
                'min_term_months': 6,
                'max_term_months': 60,
            },
            {
                'name': 'Business Loan',
                'description': 'Loans for business expansion and operations',
                'interest_rate': 15.0,
                'min_amount': 25000,    # K25,000
                'max_amount': 1000000,  # K1,000,000
                'min_term_months': 12,
                'max_term_months': 84,
            },
            {
                'name': 'Auto Loan',
                'description': 'Vehicle financing with competitive rates',
                'interest_rate': 12.0,
                'min_amount': 25000,    # K25,000
                'max_amount': 500000,   # K500,000
                'min_term_months': 24,
                'max_term_months': 72,
            },
            {
                'name': 'Home Improvement Loan',
                'description': 'Loans for home renovation and improvement',
                'interest_rate': 14.0,
                'min_amount': 10000,    # K10,000
                'max_amount': 375000,   # K375,000
                'min_term_months': 12,
                'max_term_months': 60,
            },
            {
                'name': 'Agricultural Loan',
                'description': 'Loans for farming and agricultural activities',
                'interest_rate': 16.0,
                'min_amount': 15000,    # K15,000
                'max_amount': 750000,   # K750,000
                'min_term_months': 6,
                'max_term_months': 48,
            },
        ]
        
        for loan_type_data in loan_types:
            loan_type, created = LoanType.objects.get_or_create(
                name=loan_type_data['name'],
                defaults=loan_type_data
            )
            if created:
                self.stdout.write(f'Created loan type: {loan_type.name}')
        
        # Create document types
        document_types = [
            {'name': 'National ID', 'description': 'Government issued identification', 'is_required': True},
            {'name': 'Proof of Income', 'description': 'Salary slips or income statements', 'is_required': True},
            {'name': 'Bank Statements', 'description': 'Recent bank account statements', 'is_required': True},
            {'name': 'Employment Letter', 'description': 'Letter from employer', 'is_required': False},
            {'name': 'Collateral Documents', 'description': 'Property or asset documentation', 'is_required': False},
            {'name': 'Business License', 'description': 'Business registration documents', 'is_required': False},
            {'name': 'Tax Returns', 'description': 'Recent tax return documents', 'is_required': False},
        ]
        
        for doc_type_data in document_types:
            doc_type, created = DocumentType.objects.get_or_create(
                name=doc_type_data['name'],
                defaults=doc_type_data
            )
            if created:
                self.stdout.write(f'Created document type: {doc_type.name}')
        
        # Create notification templates
        templates = [
            {
                'name': 'Loan Application Received',
                'notification_type': 'loan_approved',
                'channel': 'email',
                'subject': 'Loan Application Approved - LoanVista',
                'message_template': 'Dear {borrower_name}, your loan application #{application_number} has been approved for K{amount}. Please visit our office to complete the disbursement process.',
            },
            {
                'name': 'Payment Due Reminder',
                'notification_type': 'payment_due',
                'channel': 'sms',
                'message_template': 'Reminder: Your loan payment of K{amount} is due on {due_date}. Please make your payment to avoid late fees.',
            },
            {
                'name': 'Payment Overdue Notice',
                'notification_type': 'payment_overdue',
                'channel': 'email',
                'subject': 'Overdue Payment Notice - LoanVista',
                'message_template': 'Dear {borrower_name}, your payment of K{amount} was due on {due_date} and is now overdue. Please make your payment immediately to avoid additional penalties.',
            },
            {
                'name': 'Payment Received Confirmation',
                'notification_type': 'payment_received',
                'channel': 'email',
                'subject': 'Payment Confirmed - LoanVista',
                'message_template': 'Dear {borrower_name}, your payment of K{amount} for loan {loan_number} has been successfully processed and confirmed. Payment reference: {payment_number}.',
            },
            {
                'name': 'Payment Rejected Notice',
                'notification_type': 'payment_rejected',
                'channel': 'email',
                'subject': 'Payment Rejected - LoanVista',
                'message_template': 'Dear {borrower_name}, your payment of K{amount} for loan {loan_number} has been rejected. Please contact our office or resubmit your payment. Reference: {payment_number}.',
            },
        ]
        
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                notification_type=template_data['notification_type'],
                defaults=template_data
            )
            if created:
                self.stdout.write(f'Created notification template: {template.name}')
        
        # Create sample users
        if not User.objects.filter(username='loan_officer').exists():
            loan_officer = User.objects.create_user(
                username='loan_officer',
                email='officer@loanvista.com',
                password='password123',
                first_name='John',
                last_name='Officer',
                role='loan_officer'
            )
            self.stdout.write('Created loan officer user')
        
        if not User.objects.filter(username='borrower1').exists():
            borrower = User.objects.create_user(
                username='borrower1',
                email='borrower@example.com',
                password='password123',
                first_name='Jane',
                last_name='Doe',
                role='borrower'
            )
            self.stdout.write('Created sample borrower user')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated initial data!'))