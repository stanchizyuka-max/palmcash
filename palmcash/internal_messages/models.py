from django.db import models
from django.conf import settings
from django.utils import timezone


class Message(models.Model):
    """Internal messaging between staff members"""
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    
    subject = models.CharField(max_length=200)
    body = models.TextField()
    
    # Optional: Link to loan for context
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages'
    )
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.full_name} → {self.recipient.full_name}: {self.subject}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class MessageThread(models.Model):
    """Group messages into threads for better organization"""
    
    subject = models.CharField(max_length=200)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='message_threads'
    )
    
    # Optional: Link to loan for context
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_threads'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_threads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.subject
    
    @property
    def last_message(self):
        """Get the most recent message in thread"""
        return self.thread_messages.first()
    
    @property
    def unread_count(self, user):
        """Get unread message count for a user"""
        return self.thread_messages.filter(
            recipient=user,
            is_read=False
        ).count()


class ThreadMessage(models.Model):
    """Messages within a thread"""
    
    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='thread_messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='thread_messages_sent'
    )
    body = models.TextField()
    
    # Track who has read this message
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='read_thread_messages',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.full_name} in {self.thread.subject}"
