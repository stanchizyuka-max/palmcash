"""
Script to create notification templates for the LoanVista system
Run this script once to set up all notification templates

Usage: python setup_notification_templates.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from notifications.models import NotificationTemplate


def create_templates():
    """Create all notification templates"""
    
    templates = [
        {
            'name': 'Loan Approved Notification',
            'notification_type': 'loan_approved',
            'channel': 'in_app',
            'subject': 'Loan Application Approved! 🎉',
            'message_template': 'Congratulations! Your loan application #{loan_number} for K{amount} has been approved. The funds will be disbursed shortly.',
            'is_active': True
        },
        {
            'name': 'Loan Rejected Notification',
            'notification_type': 'loan_rejected',
            'channel': 'in_app',
            'subject': 'Loan Application Update',
            'message_template': 'Your loan application #{loan_number} requires attention. Reason: {reason}. Please review and consider reapplying after addressing the issues.',
            'is_active': True
        },
        {
            'name': 'Loan Disbursed Notification',
            'notification_type': 'loan_disbursed',
            'channel': 'in_app',
            'subject': 'Loan Disbursed Successfully! 💰',
            'message_template': 'Your loan #{loan_number} for K{amount} has been disbursed. The funds should be available in your account shortly. Your first payment is due in 30 days.',
            'is_active': True
        },
        {
            'name': 'Document Approved Notification',
            'notification_type': 'document_approved',
            'channel': 'in_app',
            'subject': 'Document Approved ✓',
            'message_template': 'Your document "{document_title}" ({document_type}) has been verified and approved! You can now proceed with your loan application.',
            'is_active': True
        },
        {
            'name': 'Document Rejected Notification',
            'notification_type': 'document_rejected',
            'channel': 'in_app',
            'subject': 'Document Requires Attention',
            'message_template': 'Your document "{document_title}" ({document_type}) needs revision. Reason: {reason}. Please upload a corrected version.',
            'is_active': True
        },
        {
            'name': 'Payment Received Notification',
            'notification_type': 'payment_received',
            'channel': 'in_app',
            'subject': 'Payment Confirmed ✓',
            'message_template': 'Your payment of K{amount} for loan #{loan_number} has been confirmed. Payment reference: {payment_number}. Thank you!',
            'is_active': True
        },
        {
            'name': 'Payment Due Notification',
            'notification_type': 'payment_due',
            'channel': 'in_app',
            'subject': 'Payment Due Reminder',
            'message_template': 'Reminder: Your payment of K{amount} for loan #{loan_number} is due on {due_date}. Please make your payment to avoid late fees.',
            'is_active': True
        },
        {
            'name': 'Payment Overdue Notification',
            'notification_type': 'payment_overdue',
            'channel': 'in_app',
            'subject': 'URGENT: Payment Overdue ⚠️',
            'message_template': 'Your payment of K{amount} for loan #{loan_number} is now {days_overdue} days overdue. Please make your payment immediately to avoid additional penalties.',
            'is_active': True
        },
        {
            'name': 'Document Uploaded Notification',
            'notification_type': 'document_uploaded',
            'channel': 'in_app',
            'subject': 'New Document Uploaded - Review Required',
            'message_template': 'A new {document_type} document "{document_title}" has been uploaded by {client_name}. Please review it as soon as possible.',
            'is_active': True
        },
        {
            'name': 'New User Registration',
            'notification_type': 'user_registered',
            'channel': 'in_app',
            'subject': 'New User Registration 👤',
            'message_template': 'New user {user_name} ({email}) has registered as a {role}. Please review their account.',
            'is_active': True
        },
        {
            'name': 'New Loan Application',
            'notification_type': 'loan_application_submitted',
            'channel': 'in_app',
            'subject': 'New Loan Application 📋',
            'message_template': '{borrower_name} has submitted a new loan application #{loan_number} for K{amount}. Please review and process.',
            'is_active': True
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    for template_data in templates:
        template, created = NotificationTemplate.objects.update_or_create(
            notification_type=template_data['notification_type'],
            defaults=template_data
        )
        
        if created:
            created_count += 1
            print(f"✓ Created: {template.name}")
        else:
            updated_count += 1
            print(f"↻ Updated: {template.name}")
    
    print("\n" + "="*60)
    print(f"Summary:")
    print(f"  Created: {created_count} templates")
    print(f"  Updated: {updated_count} templates")
    print(f"  Total: {created_count + updated_count} templates")
    print("="*60)
    print("\n✓ Notification templates setup complete!")


if __name__ == '__main__':
    print("Setting up notification templates...")
    print("="*60)
    create_templates()
