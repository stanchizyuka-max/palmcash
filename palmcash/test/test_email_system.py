"""
Script to test the email notification system
This will send test emails to verify your email configuration

Usage: python test_email_system.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User
from common.email_utils import send_welcome_email


def test_basic_email():
    """Test basic email sending"""
    print("\n1. Testing basic email sending...")
    print("-" * 60)
    
    try:
        send_mail(
            subject='Test Email from Palm Cash',
            message='This is a test email to verify your email configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        print("✓ Basic email sent successfully!")
        print(f"  Check your inbox at: {settings.EMAIL_HOST_USER}")
        return True
    except Exception as e:
        print(f"✗ Failed to send basic email: {str(e)}")
        return False


def test_template_email():
    """Test template-based email sending"""
    print("\n2. Testing template-based email...")
    print("-" * 60)
    
    try:
        # Get a user to send test email to
        user = User.objects.filter(email__isnull=False).exclude(email='').first()
        
        if not user:
            print("✗ No users with email addresses found in database")
            print("  Please create a user with an email address first")
            return False
        
        print(f"  Sending welcome email to: {user.email}")
        success = send_welcome_email(user)
        
        if success:
            print("✓ Template email sent successfully!")
            print(f"  Check inbox at: {user.email}")
            return True
        else:
            print("✗ Failed to send template email")
            return False
            
    except Exception as e:
        print(f"✗ Error sending template email: {str(e)}")
        return False


def check_email_settings():
    """Check email configuration"""
    print("\nEmail Configuration:")
    print("=" * 60)
    print(f"  Backend: {settings.EMAIL_BACKEND}")
    print(f"  Host: {settings.EMAIL_HOST}")
    print(f"  Port: {settings.EMAIL_PORT}")
    print(f"  Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"  From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"  Host User: {settings.EMAIL_HOST_USER}")
    print(f"  Password Set: {'Yes' if settings.EMAIL_HOST_PASSWORD else 'No'}")
    print("=" * 60)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Palm Cash Email System Test")
    print("=" * 60)
    
    # Check configuration
    check_email_settings()
    
    # Test basic email
    basic_success = test_basic_email()
    
    # Test template email
    template_success = test_template_email()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    print(f"  Basic Email: {'✓ PASS' if basic_success else '✗ FAIL'}")
    print(f"  Template Email: {'✓ PASS' if template_success else '✗ FAIL'}")
    print("=" * 60)
    
    if basic_success and template_success:
        print("\n✓ All tests passed! Email system is working correctly.")
        print("\nNext steps:")
        print("  1. Run: python setup_notification_templates.py")
        print("  2. Test the full system by creating a loan application")
        print("  3. Set up scheduled payment reminders")
    else:
        print("\n✗ Some tests failed. Please check your email configuration.")
        print("\nTroubleshooting:")
        print("  1. Verify SMTP credentials in settings.py")
        print("  2. Check if your email provider allows SMTP access")
        print("  3. For Gmail, use an App Password (not your regular password)")
        print("  4. Check firewall/antivirus settings")
        print("  5. Try with a different email provider")


if __name__ == '__main__':
    main()
