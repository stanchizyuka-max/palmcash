"""
Email utility functions for sending notifications
"""
from django.core.mail import send_mail
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_email_notification(subject, template_name, context, recipient_email, recipient_name=None):
    """
    Send an email notification using HTML template
    
    Args:
        subject: Email subject
        template_name: Path to HTML template (e.g., 'emails/loan_approved.html')
        context: Dictionary of context variables for template
        recipient_email: Recipient's email address
        recipient_name: Recipient's name (optional)
    
    Returns:
        Boolean indicating success
    """
    try:
        # Add common context variables
        context.update({
            'recipient_name': recipient_name,
            'site_name': 'PalmCash',
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
        })
        
        # Render HTML email
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=f"{settings.EMAIL_SUBJECT_PREFIX}{subject}",
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        email.attach_alternative(html_message, "text/html")
        
        # Send email
        email.send()
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_loan_approved_email(loan):
    """Send email when loan is approved"""
    context = {
        'loan': loan,
        'borrower': loan.borrower,
    }
    return send_email_notification(
        subject=f"Loan Application Approved - #{loan.application_number}",
        template_name='emails/loan_approved.html',
        context=context,
        recipient_email=loan.borrower.email,
        recipient_name=loan.borrower.full_name
    )


def send_loan_rejected_email(loan):
    """Send email when loan is rejected"""
    context = {
        'loan': loan,
        'borrower': loan.borrower,
        'rejection_reason': loan.rejection_reason,
    }
    return send_email_notification(
        subject=f"Loan Application Update - #{loan.application_number}",
        template_name='emails/loan_rejected.html',
        context=context,
        recipient_email=loan.borrower.email,
        recipient_name=loan.borrower.full_name
    )


def send_loan_disbursed_email(loan):
    """Send email when loan is disbursed"""
    context = {
        'loan': loan,
        'borrower': loan.borrower,
    }
    return send_email_notification(
        subject=f"Loan Disbursed - #{loan.application_number}",
        template_name='emails/loan_disbursed.html',
        context=context,
        recipient_email=loan.borrower.email,
        recipient_name=loan.borrower.full_name
    )


def send_document_approved_email(document):
    """Send email when document is approved"""
    context = {
        'document': document,
        'user': document.user,
    }
    return send_email_notification(
        subject=f"Document Approved - {document.title}",
        template_name='emails/document_approved.html',
        context=context,
        recipient_email=document.user.email,
        recipient_name=document.user.full_name
    )


def send_document_rejected_email(document):
    """Send email when document is rejected"""
    context = {
        'document': document,
        'user': document.user,
    }
    return send_email_notification(
        subject=f"Document Requires Attention - {document.title}",
        template_name='emails/document_rejected.html',
        context=context,
        recipient_email=document.user.email,
        recipient_name=document.user.full_name
    )


def send_payment_received_email(payment):
    """Send email when payment is received"""
    context = {
        'payment': payment,
        'loan': payment.loan,
        'borrower': payment.loan.borrower,
    }
    return send_email_notification(
        subject=f"Payment Confirmation - #{payment.payment_number}",
        template_name='emails/payment_received.html',
        context=context,
        recipient_email=payment.loan.borrower.email,
        recipient_name=payment.loan.borrower.full_name
    )


def send_welcome_email(user):
    """Send welcome email to new user"""
    context = {
        'user': user,
    }
    return send_email_notification(
        subject="Welcome to PalmCash!",
        template_name='emails/welcome.html',
        context=context,
        recipient_email=user.email,
        recipient_name=user.full_name
    )


def send_payment_due_email(loan, payment_amount, due_date, days_until_due):
    """Send email reminder for upcoming payment"""
    context = {
        'loan': loan,
        'borrower': loan.borrower,
        'payment_amount': payment_amount,
        'due_date': due_date,
        'days_until_due': days_until_due,
    }
    return send_email_notification(
        subject=f"Payment Due Reminder - Loan #{loan.application_number}",
        template_name='emails/payment_due.html',
        context=context,
        recipient_email=loan.borrower.email,
        recipient_name=loan.borrower.full_name
    )


def send_payment_overdue_email(loan, payment_amount, due_date, days_overdue, late_fee=None):
    """Send email for overdue payment"""
    total_due = payment_amount + (late_fee or 0)
    context = {
        'loan': loan,
        'borrower': loan.borrower,
        'payment_amount': payment_amount,
        'due_date': due_date,
        'days_overdue': days_overdue,
        'late_fee': late_fee,
        'total_due': total_due,
    }
    return send_email_notification(
        subject=f"URGENT: Payment Overdue - Loan #{loan.application_number}",
        template_name='emails/payment_overdue.html',
        context=context,
        recipient_email=loan.borrower.email,
        recipient_name=loan.borrower.full_name
    )
