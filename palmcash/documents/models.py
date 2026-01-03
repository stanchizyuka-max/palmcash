from django.db import models
from django.conf import settings
import os

def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    return f"documents/{instance.document_type}/{instance.user.username}/{filename}"

class DocumentType(models.Model):
    """Types of documents that can be uploaded"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=False)
    max_file_size_mb = models.IntegerField(default=5)
    allowed_extensions = models.CharField(max_length=200, default='pdf,jpg,jpeg,png')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def get_allowed_extensions_list(self):
        return [ext.strip() for ext in self.allowed_extensions.split(',')]

class Document(models.Model):
    """Document uploads for users and loans"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    
    # File Information
    file = models.FileField(upload_to=document_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField()  # in bytes
    
    # Document Details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    document_number = models.CharField(max_length=100, blank=True)  # ID number, passport number, etc.
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Status and Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_documents')
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.full_name}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    @property
    def file_extension(self):
        return os.path.splitext(self.original_filename)[1].lower().lstrip('.')
    
    @property
    def is_expired(self):
        if self.expiry_date:
            from datetime import date
            return self.expiry_date < date.today()
        return False
    
    class Meta:
        ordering = ['-uploaded_at']