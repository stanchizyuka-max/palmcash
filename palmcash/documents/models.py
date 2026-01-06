from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os


def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    return f'documents/{instance.client.id}/{instance.document_type}/{filename}'


class ClientDocument(models.Model):
    """Store client identification documents"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('nrc_front', 'NRC Card - Front'),
        ('nrc_back', 'NRC Card - Back'),
        ('selfie', 'Live Photo (Selfie)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
        limit_choices_to={'role': 'borrower'}
    )
    
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        help_text='Type of document'
    )
    
    image = models.ImageField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        help_text='Document image (JPG or PNG)'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Document verification status'
    )
    
    # Verification details
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_client_documents',
        limit_choices_to={'role__in': ['manager', 'admin']},
        help_text='User who verified this document'
    )
    
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When document was verified'
    )
    
    verification_notes = models.TextField(
        blank=True,
        help_text='Notes from verification (e.g., reason for rejection)'
    )
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Client Document'
        verbose_name_plural = 'Client Documents'
        unique_together = ['client', 'document_type']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['status', '-uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.client.full_name} - {self.get_document_type_display()}"
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.image:
            return round(self.image.size / (1024 * 1024), 2)
        return 0
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.image:
            return os.path.splitext(self.image.name)[1].lower()
        return ''
    
    def approve(self, verified_by_user, notes=''):
        """Approve this document"""
        from django.utils import timezone
        self.status = 'approved'
        self.verified_by = verified_by_user
        self.verification_date = timezone.now()
        self.verification_notes = notes
        self.save()
    
    def reject(self, verified_by_user, reason):
        """Reject this document"""
        from django.utils import timezone
        self.status = 'rejected'
        self.verified_by = verified_by_user
        self.verification_date = timezone.now()
        self.verification_notes = reason
        self.save()


class ClientVerification(models.Model):
    """Track overall client verification status"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending - Documents Required'),
        ('documents_submitted', 'Documents Submitted - Awaiting Review'),
        ('documents_rejected', 'Documents Rejected - Resubmission Required'),
        ('verified', 'Verified - Ready for Loans'),
        ('rejected', 'Rejected - Cannot Apply for Loans'),
    ]
    
    client = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verification',
        limit_choices_to={'role': 'borrower'}
    )
    
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Overall verification status'
    )
    
    # Document completion tracking
    nrc_front_uploaded = models.BooleanField(default=False)
    nrc_back_uploaded = models.BooleanField(default=False)
    selfie_uploaded = models.BooleanField(default=False)
    
    # Approval tracking
    all_documents_approved = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_clients',
        limit_choices_to={'role__in': ['manager', 'admin']},
        help_text='User who verified this client'
    )
    
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When client was verified'
    )
    
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection (if applicable)'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Client Verification'
        verbose_name_plural = 'Client Verifications'
    
    def __str__(self):
        return f"{self.client.full_name} - {self.get_status_display()}"
    
    @property
    def all_documents_uploaded(self):
        """Check if all required documents are uploaded"""
        return self.nrc_front_uploaded and self.nrc_back_uploaded and self.selfie_uploaded
    
    @property
    def documents_pending_review(self):
        """Check if all documents are pending review"""
        if not self.all_documents_uploaded:
            return False
        
        pending = ClientDocument.objects.filter(
            client=self.client,
            status='pending'
        ).count()
        
        return pending == 3
    
    @property
    def any_document_rejected(self):
        """Check if any document has been rejected"""
        return ClientDocument.objects.filter(
            client=self.client,
            status='rejected'
        ).exists()
    
    def update_status(self):
        """Update verification status based on documents"""
        from django.utils import timezone
        
        # Get all documents
        documents = ClientDocument.objects.filter(client=self.client)
        
        if not documents.exists():
            self.status = 'pending'
            self.save()
            return
        
        # Check if all documents are uploaded
        if not self.all_documents_uploaded:
            self.status = 'pending'
            self.save()
            return
        
        # Check if any document is rejected
        if self.any_document_rejected:
            self.status = 'documents_rejected'
            self.save()
            return
        
        # Check if all documents are approved
        approved_count = documents.filter(status='approved').count()
        if approved_count == 3:
            self.status = 'verified'
            self.all_documents_approved = True
            self.verified_by = documents.first().verified_by
            self.verification_date = timezone.now()
            self.save()
            return
        
        # Check if all documents are pending
        pending_count = documents.filter(status='pending').count()
        if pending_count == 3:
            self.status = 'documents_submitted'
            self.save()
            return
    
    def can_apply_for_loan(self):
        """Check if client can apply for a loan"""
        return self.status == 'verified' and self.all_documents_approved
    
    def approve_all_documents(self, verified_by_user):
        """Approve all documents and mark client as verified"""
        from django.utils import timezone
        
        # Approve all documents
        documents = ClientDocument.objects.filter(client=self.client)
        for doc in documents:
            if doc.status != 'approved':
                doc.approve(verified_by_user, 'Approved by verification officer')
        
        # Update verification status
        self.status = 'verified'
        self.all_documents_approved = True
        self.verified_by = verified_by_user
        self.verification_date = timezone.now()
        self.save()
    
    def reject_all_documents(self, verified_by_user, reason):
        """Reject all documents and mark client as rejected"""
        # Reject all documents
        documents = ClientDocument.objects.filter(client=self.client)
        for doc in documents:
            if doc.status != 'rejected':
                doc.reject(verified_by_user, reason)
        
        # Update verification status
        self.status = 'documents_rejected'
        self.rejection_reason = reason
        self.verified_by = verified_by_user
        self.save()
