from django.db import models
from django.conf import settings

class NotificationTemplate(models.Model):
    """Templates for different types of notifications"""
    
    TYPE_CHOICES = [
        ('loan_approved', 'Loan Approved'),
        ('loan_rejected', 'Loan Rejected'),
        ('payment_due', 'Payment Due'),
        ('payment_overdue', 'Payment Overdue'),
        ('payment_received', 'Payment Received'),
        ('payment_rejected', 'Payment Rejected'),
        ('loan_disbursed', 'Loan Disbursed'),
        ('document_required', 'Document Required'),
        ('document_uploaded', 'Document Uploaded'),
        ('document_approved', 'Document Approved'),
        ('document_rejected', 'Document Rejected'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App Notification'),
    ]
    
    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES, unique=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    subject = models.CharField(max_length=200, blank=True)  # For email
    message_template = models.TextField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"

class Notification(models.Model):
    """Individual notification records"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    
    # Message Content
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    
    # Delivery Information
    channel = models.CharField(max_length=20, choices=NotificationTemplate.CHANNEL_CHOICES)
    recipient_address = models.CharField(max_length=200)  # email or phone number
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Related Objects
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, null=True, blank=True)
    payment = models.ForeignKey('payments.Payment', on_delete=models.CASCADE, null=True, blank=True)
    
    # Error Information
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.template.name} to {self.recipient.username}"
    
    def mark_as_read(self):
        if not self.read_at:
            from django.utils import timezone
            self.read_at = timezone.now()
            self.status = 'read'
            self.save()
    
    class Meta:
        ordering = ['-created_at']
