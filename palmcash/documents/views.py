from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Document, DocumentType

class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'documents/list.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        if self.request.user.role == 'borrower':
            return Document.objects.filter(user=self.request.user)
        return Document.objects.all()

class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = 'documents/detail.html'
    context_object_name = 'document'
    
    def get_queryset(self):
        if self.request.user.role == 'borrower':
            return Document.objects.filter(user=self.request.user)
        return Document.objects.all()

class DocumentUploadView(LoginRequiredMixin, CreateView):
    model = Document
    template_name = 'documents/upload.html'
    fields = ['document_type', 'title', 'description', 'file']
    success_url = reverse_lazy('documents:list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Create notification for document upload
        self._create_document_upload_notification(form.instance)
        
        messages.success(self.request, 'Document uploaded successfully! It will be reviewed by our team.')
        return response
    
    def _create_document_upload_notification(self, document):
        """Create notifications when a document is uploaded"""
        try:
            from notifications.models import Notification, NotificationTemplate
            from django.utils import timezone
            
            # Notify loan officers and admins about the new document
            from accounts.models import User
            
            # Get all loan officers and admins
            reviewers = User.objects.filter(role__in=['loan_officer', 'admin'])
            
            # Get the notification template
            template = NotificationTemplate.objects.filter(
                notification_type='document_uploaded',
                is_active=True
            ).first()
            
            if template:
                for reviewer in reviewers:
                    message = template.message_template.format(
                        client_name=document.user.get_full_name() or document.user.username,
                        document_title=document.title,
                        document_type=document.document_type.name
                    )
                    
                    Notification.objects.create(
                        recipient=reviewer,
                        template=template,
                        subject=template.subject,
                        message=message,
                        channel='in_app',
                        recipient_address=reviewer.email or '',
                        scheduled_at=timezone.now(),
                        status='sent'
                    )
        except Exception as e:
            print(f"Error creating document upload notification: {e}")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_types'] = DocumentType.objects.filter(is_active=True)
        return context

class ApproveDocumentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role not in ['admin', 'loan_officer']:
            messages.error(request, 'You do not have permission to approve documents.')
            return redirect('documents:detail', pk=pk)
        
        document = get_object_or_404(Document, pk=pk)
        document.status = 'approved'
        document.reviewed_by = request.user
        from django.utils import timezone
        document.review_date = timezone.now()
        document.review_notes = request.POST.get('notes', '')
        document.save()
        
        # Send approval email
        from common.email_utils import send_document_approved_email
        try:
            send_document_approved_email(document)
        except Exception as e:
            print(f"Error sending document approval email: {e}")
        
        # Create notification
        self._create_notification(document, 'document_approved')
        
        messages.success(request, f'Document "{document.title}" has been approved.')
        return redirect('documents:detail', pk=pk)
    
    def _create_notification(self, document, notification_type):
        """Create in-app notification for document approval"""
        try:
            from notifications.models import Notification, NotificationTemplate
            from django.utils import timezone
            
            template = NotificationTemplate.objects.filter(
                notification_type=notification_type,
                is_active=True
            ).first()
            
            if template:
                message = template.message_template.format(
                    document_title=document.title,
                    document_type=document.document_type.name
                )
                
                Notification.objects.create(
                    recipient=document.user,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel='in_app',
                    recipient_address=document.user.email or '',
                    scheduled_at=timezone.now(),
                    status='sent'
                )
        except Exception as e:
            print(f"Error creating notification: {e}")

class RejectDocumentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role not in ['admin', 'loan_officer']:
            messages.error(request, 'You do not have permission to reject documents.')
            return redirect('documents:detail', pk=pk)
        
        document = get_object_or_404(Document, pk=pk)
        document.status = 'rejected'
        document.reviewed_by = request.user
        from django.utils import timezone
        document.review_date = timezone.now()
        document.review_notes = request.POST.get('reason', '')
        document.save()
        
        # Send rejection email
        from common.email_utils import send_document_rejected_email
        try:
            send_document_rejected_email(document)
        except Exception as e:
            print(f"Error sending document rejection email: {e}")
        
        # Create notification
        self._create_notification(document, 'document_rejected')
        
        messages.success(request, f'Document "{document.title}" has been rejected.')
        return redirect('documents:detail', pk=pk)
    
    def _create_notification(self, document, notification_type):
        """Create in-app notification for document rejection"""
        try:
            from notifications.models import Notification, NotificationTemplate
            from django.utils import timezone
            
            template = NotificationTemplate.objects.filter(
                notification_type=notification_type,
                is_active=True
            ).first()
            
            if template:
                message = template.message_template.format(
                    document_title=document.title,
                    document_type=document.document_type.name,
                    reason=document.review_notes or 'Not specified'
                )
                
                Notification.objects.create(
                    recipient=document.user,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel='in_app',
                    recipient_address=document.user.email or '',
                    scheduled_at=timezone.now(),
                    status='sent'
                )
        except Exception as e:
            print(f"Error creating notification: {e}")


class DocumentReviewDashboardView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'documents/review_dashboard.html'
    context_object_name = 'documents'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'loan_officer']:
            messages.error(request, 'You do not have permission to access the document review dashboard.')
            return redirect('documents:list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Document.objects.filter(status='pending').order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        total_documents = Document.objects.count()
        approved_documents = Document.objects.filter(status='approved').count()
        
        context['total_documents'] = total_documents
        context['pending_documents'] = Document.objects.filter(status='pending').count()
        context['approved_documents'] = approved_documents
        context['rejected_documents'] = Document.objects.filter(status='rejected').count()
        
        # Calculate approval percentage
        context['approval_percentage'] = (approved_documents / total_documents * 100) if total_documents > 0 else 0
        
        # Recent activity (from system launch or last 7 days, whichever is more recent)
        from datetime import date, timedelta
        from common.utils import get_system_launch_date, format_system_period
        
        recent_date = date.today() - timedelta(days=7)
        system_launch = get_system_launch_date()
        
        # Use the more recent date between system launch and 7 days ago
        filter_date = max(recent_date, system_launch)
        
        context['recent_uploads'] = Document.objects.filter(uploaded_at__date__gte=filter_date).count()
        context['recent_reviews'] = Document.objects.filter(review_date__date__gte=filter_date).count()
        context['system_launch_date'] = system_launch
        context['activity_period'] = format_system_period(filter_date)
        
        # Group pending documents by user
        pending_by_user = {}
        for doc in context['documents']:
            user_id = doc.user.id
            if user_id not in pending_by_user:
                pending_by_user[user_id] = {
                    'user': doc.user,
                    'documents': []
                }
            pending_by_user[user_id]['documents'].append(doc)
        
        context['pending_by_user'] = pending_by_user.values()
        
        return context


class DeleteDocumentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        
        # Check permissions
        # Borrowers can only delete their own pending documents
        if request.user.role == 'borrower':
            if document.user != request.user:
                messages.error(request, 'You can only delete your own documents.')
                return redirect('documents:list')
            if document.status != 'pending':
                messages.error(request, 'You can only delete pending documents.')
                return redirect('documents:detail', pk=pk)
        # Staff can delete any document
        elif request.user.role not in ['admin', 'loan_officer', 'manager']:
            messages.error(request, 'You do not have permission to delete documents.')
            return redirect('documents:list')
        
        # Store document info for the success message
        doc_title = document.title
        doc_user = document.user.full_name
        
        # Delete the file from storage if it exists
        if document.file:
            try:
                document.file.delete(save=False)
            except Exception as e:
                messages.warning(request, f'File could not be deleted from storage: {e}')
        
        # Delete the document record
        document.delete()
        
        messages.success(
            request, 
            f'Document "{doc_title}" has been permanently deleted.'
        )
        
        # Redirect to documents list
        return redirect('documents:list')


class BulkDeleteDocumentsView(LoginRequiredMixin, View):
    def post(self, request):
        if request.user.role not in ['admin', 'loan_officer']:
            messages.error(request, 'You do not have permission to delete documents.')
            return redirect('documents:list')
        
        document_ids = request.POST.getlist('document_ids')
        
        if not document_ids:
            messages.error(request, 'No documents selected for deletion.')
            return redirect('documents:list')
        
        # Get documents to delete
        documents = Document.objects.filter(id__in=document_ids)
        
        if not documents.exists():
            messages.error(request, 'No valid documents found for deletion.')
            return redirect('documents:list')
        
        deleted_count = 0
        for document in documents:
            # Delete the file from storage if it exists
            if document.file:
                try:
                    document.file.delete(save=False)
                except Exception:
                    pass  # Continue even if file deletion fails
            
            document.delete()
            deleted_count += 1
        
        messages.success(
            request, 
            f'{deleted_count} document{"s" if deleted_count != 1 else ""} have been permanently deleted.'
        )
        
        return redirect('documents:list')



class DocumentsManageView(LoginRequiredMixin, ListView):
    """View for managing all user documents"""
    model = Document
    template_name = 'documents/documents_manage.html'
    context_object_name = 'documents'
    paginate_by = 50
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'loan_officer', 'manager'] and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to manage documents.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Document.objects.all().select_related('user', 'document_type', 'reviewed_by')
        
        # Filter by status if provided
        status_filter = self.request.GET.get('status', 'all')
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import datetime
        
        # Statistics
        all_docs = Document.objects.all()
        context['total_documents'] = all_docs.count()
        context['pending_count'] = all_docs.filter(status='pending').count()
        context['approved_count'] = all_docs.filter(status='approved').count()
        context['rejected_count'] = all_docs.filter(status='rejected').count()
        
        # Monthly uploads
        first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context['monthly_uploads'] = all_docs.filter(uploaded_at__gte=first_day_of_month).count()
        
        # Current filter
        context['current_filter'] = self.request.GET.get('status', 'all')
        
        return context


class DocumentTypesManageView(LoginRequiredMixin, TemplateView):
    """View for managing document types"""
    template_name = 'documents/document_types_manage.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to manage document types.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        document_types = DocumentType.objects.all().order_by('-is_active', 'name')
        
        context['document_types'] = document_types
        context['active_count'] = document_types.filter(is_active=True).count()
        context['inactive_count'] = document_types.filter(is_active=False).count()
        context['required_count'] = document_types.filter(is_required=True).count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle creating/updating document types"""
        try:
            doc_type_id = request.POST.get('doc_type_id')
            
            if doc_type_id:
                # Update existing
                doc_type = get_object_or_404(DocumentType, id=doc_type_id)
                action = 'updated'
            else:
                # Create new
                doc_type = DocumentType()
                action = 'created'
            
            # Update fields
            doc_type.name = request.POST.get('name')
            doc_type.description = request.POST.get('description')
            doc_type.max_file_size_mb = request.POST.get('max_file_size_mb')
            doc_type.allowed_extensions = request.POST.get('allowed_extensions')
            doc_type.is_required = request.POST.get('is_required') == 'on'
            doc_type.is_active = request.POST.get('is_active') == 'on'
            
            doc_type.save()
            
            messages.success(request, f'Document type "{doc_type.name}" has been {action} successfully!')
            return redirect('documents:manage_document_types')
            
        except Exception as e:
            messages.error(request, f'Error saving document type: {str(e)}')
            return redirect('documents:manage_document_types')
