from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from .models import Loan, LoanType, LoanDocument
from .forms import LoanApplicationForm, LoanDocumentForm, DocumentVerificationForm

class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'loans/list.html'
    context_object_name = 'loans'
    paginate_by = 20
    
    def get_queryset(self):
        if self.request.user.role == 'borrower':
            return Loan.objects.filter(borrower=self.request.user)
        return Loan.objects.all()

class LoanDetailView(LoginRequiredMixin, DetailView):
    model = Loan
    template_name = 'loans/detail.html'
    context_object_name = 'loan'
    
    def get_queryset(self):
        if self.request.user.role == 'borrower':
            return Loan.objects.filter(borrower=self.request.user).select_related('security_deposit', 'borrower')
        return Loan.objects.all().select_related('security_deposit', 'borrower')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loan = self.get_object()
        
        # Explicitly get the correct security deposit for this loan ONLY
        from .models import SecurityDeposit
        try:
            # FORCE correct security deposit association
            security_deposit = SecurityDeposit.objects.get(loan=loan)
            loan.security_deposit = security_deposit  # Override any wrong association
        except SecurityDeposit.DoesNotExist:
            loan.security_deposit = None
        
        # Add loan-specific document information
        context['documents'] = loan.loan_documents.all()[:5]  # Show first 5 documents
        context['document_count'] = loan.loan_documents.count()
        context['verified_documents'] = loan.loan_documents.filter(is_verified=True).count()
        context['pending_documents'] = loan.loan_documents.filter(is_verified=False).count()
        
        # Also add client verification documents
        from documents.models import ClientDocument
        context['client_documents'] = ClientDocument.objects.filter(client=loan.borrower)
        context['client_document_count'] = context['client_documents'].count()
        context['client_verified_documents'] = context['client_documents'].filter(status='approved').count()
        context['client_pending_documents'] = context['client_documents'].filter(status='pending').count()
        
        # Check if user can upload documents
        context['can_upload_documents'] = (
            self.request.user.role == 'borrower' and 
            loan.borrower == self.request.user and 
            loan.status in ['pending', 'approved']
        )
        
        return context

class LoanApplicationView(LoginRequiredMixin, CreateView):
    model = Loan
    form_class = LoanApplicationForm
    template_name = 'loans/apply.html'
    success_url = reverse_lazy('loans:list')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if borrower has outstanding loans
        if request.user.role == 'borrower':
            outstanding_loans = Loan.objects.filter(
                borrower=request.user,
                status__in=['pending', 'active', 'approved', 'disbursed']
            )
            
            if outstanding_loans.exists():
                messages.error(
                    request, 
                    'You cannot apply for a new loan while you have outstanding loans. '
                    'Please complete your current loan payments before applying for a new loan.'
                )
                return redirect('loans:list')
            
            # Check if borrower has verified documents
            from documents.models import ClientDocument
            verified_documents = ClientDocument.objects.filter(
                client=request.user,
                status='approved'
            ).exists()
            
            if not verified_documents:
                messages.error(
                    request,
                    'You must upload and have at least one document verified by an administrator '
                    'before you can apply for a loan. Please upload your documents first.'
                )
                return redirect('documents:list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add information about user's loan history
        if self.request.user.role == 'borrower':
            context['user_loans'] = Loan.objects.filter(borrower=self.request.user)
            context['completed_loans'] = context['user_loans'].filter(status='completed').count()
            context['can_apply'] = not context['user_loans'].filter(
                status__in=['pending', 'active', 'approved', 'disbursed']
            ).exists()
            
            # Check document verification status
            from documents.models import ClientDocument
            context['has_verified_documents'] = ClientDocument.objects.filter(
                client=self.request.user,
                status='approved'
            ).exists()
            
            # Pre-select loan type if provided in URL
            loan_type_id = self.request.GET.get('loan_type')
            if loan_type_id:
                try:
                    context['selected_loan_type'] = LoanType.objects.get(id=loan_type_id, is_active=True)
                except LoanType.DoesNotExist:
                    pass
        
        return context
    
    def form_valid(self, form):
        # Double-check before saving (security measure)
        if self.request.user.role == 'borrower':
            outstanding_loans = Loan.objects.filter(
                borrower=self.request.user,
                status__in=['pending', 'active', 'approved', 'disbursed']
            )
            
            if outstanding_loans.exists():
                messages.error(
                    self.request,
                    'Cannot submit application: You have outstanding loans that must be completed first.'
                )
                return redirect('loans:list')
        
        form.instance.borrower = self.request.user
        # Set interest rate from loan type
        if form.instance.loan_type:
            form.instance.interest_rate = form.instance.loan_type.interest_rate
        
        response = super().form_valid(form)
        
        # Create approval request for high-value loans (K6,000+)
        if self.object.principal_amount >= 6000:
            from loans.models import LoanApprovalRequest
            LoanApprovalRequest.objects.create(
                loan=self.object,
                requested_by=self.request.user,
                status='pending'
            )
        
        # Notify admins about new loan application
        self._notify_admins_of_application(self.object)
        
        messages.success(self.request, 'Loan application submitted successfully! Please proceed to pay the 10% upfront payment.')
        
        # Redirect to upfront payment page instead of loans list
        return redirect('payments:upfront_payment', loan_id=self.object.pk)
    
    def _notify_admins_of_application(self, loan):
        """Notify admins, managers, and loan officers about new loan application"""
        try:
            from notifications.models import Notification, NotificationTemplate
            from accounts.models import User
            
            # Get the notification template
            try:
                template = NotificationTemplate.objects.get(
                    notification_type='loan_application_submitted',
                    is_active=True
                )
            except NotificationTemplate.DoesNotExist:
                return
            
            # Get all administrators, managers, and loan officers
            admins = User.objects.filter(role__in=['admin', 'manager', 'loan_officer'])
            
            for admin in admins:
                # Format the message using the template
                message = template.message_template.format(
                    borrower_name=loan.borrower.full_name,
                    loan_number=loan.application_number,
                    amount=f"{loan.principal_amount:,.2f}"
                )
                
                Notification.objects.create(
                    recipient=admin,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel=template.channel,
                    recipient_address=admin.email or '',
                    scheduled_at=timezone.now(),
                    loan=loan,
                    status='sent'
                )
        except Exception as e:
            # Don't fail application if notification fails
            print(f"Error creating loan application notification: {e}")

class LoanEditView(LoginRequiredMixin, View):
    """View for editing loan applications"""
    
    def get(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        
        # Check permissions
        if request.user.role == 'borrower' and loan.borrower != request.user:
            messages.error(request, 'You do not have permission to edit this loan.')
            return redirect('loans:detail', pk=pk)
        
        # Only allow editing of pending or draft loans
        if loan.status not in ['pending', 'draft']:
            messages.error(request, f'Cannot edit loan with status "{loan.get_status_display()}". Only pending or draft loans can be edited.')
            return redirect('loans:detail', pk=pk)
        
        # Render the edit template
        from .forms import LoanApplicationForm
        form = LoanApplicationForm(instance=loan)
        
        return render(request, 'loans/edit.html', {
            'loan': loan,
            'form': form
        })
    
    def post(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        
        # Check permissions
        if request.user.role == 'borrower' and loan.borrower != request.user:
            messages.error(request, 'You do not have permission to edit this loan.')
            return redirect('loans:detail', pk=pk)
        
        # Only allow editing of pending or draft loans
        if loan.status not in ['pending', 'draft']:
            messages.error(request, f'Cannot edit loan with status "{loan.get_status_display()}". Only pending or draft loans can be edited.')
            return redirect('loans:detail', pk=pk)
        
        from .forms import LoanApplicationForm
        form = LoanApplicationForm(request.POST, instance=loan)
        
        if form.is_valid():
            # Update interest rate from loan type if changed
            if form.instance.loan_type:
                form.instance.interest_rate = form.instance.loan_type.interest_rate
            
            form.save()
            messages.success(request, f'Loan application {loan.application_number} has been updated successfully!')
            return redirect('loans:detail', pk=pk)
        else:
            return render(request, 'loans/edit.html', {
                'loan': loan,
                'form': form
            })

class ApproveLoanView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """Redirect GET requests to loan detail page with helpful message"""
        messages.info(
            request,
            'To approve a loan, please go to the loan detail page and click the "Approve Loan" button.'
        )
        return redirect('loans:detail', pk=pk)
    
    def post(self, request, pk):
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            messages.error(request, 'You do not have permission to approve loans.')
            return redirect('loans:detail', pk=pk)
        
        # Check if loan officer meets minimum groups requirement
        if request.user.role == 'loan_officer':
            if not request.user.can_approve_loans():
                active_groups_count = request.user.get_active_groups_count()
                messages.error(
                    request,
                    f'Loan officers must manage at least 15 active groups to approve loans. '
                    f'You currently manage {active_groups_count} active group(s). '
                    f'Please contact your manager to be assigned more groups.'
                )
                return redirect('loans:detail', pk=pk)
        
        loan = get_object_or_404(Loan, pk=pk)
        loan.status = 'approved'
        loan.loan_officer = request.user
        loan.approval_notes = request.POST.get('approval_notes', '')
        loan.save()
        
        # Send approval email
        from common.email_utils import send_loan_approved_email
        try:
            send_loan_approved_email(loan)
        except Exception as e:
            print(f"Error sending approval email: {e}")
        
        # Create notification
        self._create_notification(loan, 'loan_approved')
        
        messages.success(request, f'Loan {loan.application_number} has been approved.')
        return redirect('loans:detail', pk=pk)
    
    def _create_notification(self, loan, notification_type):
        """Create in-app notification for loan approval"""
        try:
            from notifications.models import Notification, NotificationTemplate
            
            template = NotificationTemplate.objects.filter(
                notification_type=notification_type,
                is_active=True
            ).first()
            
            if template:
                message = template.message_template.format(
                    loan_number=loan.application_number,
                    amount=loan.principal_amount
                )
                
                Notification.objects.create(
                    recipient=loan.borrower,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel='in_app',
                    recipient_address=loan.borrower.email or '',
                    scheduled_at=timezone.now(),
                    loan=loan,
                    status='sent'
                )
        except Exception as e:
            print(f"Error creating notification: {e}")

class RejectLoanView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """Redirect GET requests to loan detail page with helpful message"""
        messages.info(
            request,
            'To reject a loan, please go to the loan detail page and click the "Reject Loan" button.'
        )
        return redirect('loans:detail', pk=pk)
    
    def post(self, request, pk):
        if request.user.role not in ['admin', 'loan_officer']:
            messages.error(request, 'You do not have permission to reject loans.')
            return redirect('loans:detail', pk=pk)
        
        loan = get_object_or_404(Loan, pk=pk)
        loan.status = 'rejected'
        loan.loan_officer = request.user
        loan.rejection_reason = request.POST.get('reason', '')
        loan.save()
        
        # Send rejection email
        from common.email_utils import send_loan_rejected_email
        try:
            send_loan_rejected_email(loan)
        except Exception as e:
            print(f"Error sending rejection email: {e}")
        
        # Create notification
        self._create_notification(loan, 'loan_rejected')
        
        messages.success(request, f'Loan {loan.application_number} has been rejected.')
        return redirect('loans:detail', pk=pk)
    
    def _create_notification(self, loan, notification_type):
        """Create in-app notification for loan rejection"""
        try:
            from notifications.models import Notification, NotificationTemplate
            
            template = NotificationTemplate.objects.filter(
                notification_type=notification_type,
                is_active=True
            ).first()
            
            if template:
                message = template.message_template.format(
                    loan_number=loan.application_number,
                    reason=loan.rejection_reason or 'Not specified'
                )
                
                Notification.objects.create(
                    recipient=loan.borrower,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel='in_app',
                    recipient_address=loan.borrower.email or '',
                    scheduled_at=timezone.now(),
                    loan=loan,
                    status='sent'
                )
        except Exception as e:
            print(f"Error creating notification: {e}")

class DisburseLoanView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """Redirect GET requests to loan detail page with helpful message"""
        messages.info(
            request,
            'To disburse a loan, please go to the loan detail page and click the "Disburse Loan" button.'
        )
        return redirect('loans:detail', pk=pk)
    
    def post(self, request, pk):
        # Only managers can disburse loans
        if request.user.role != 'manager':
            messages.error(request, 'Only managers can disburse loans.')
            return redirect('loans:detail', pk=pk)
        
        try:
            loan = get_object_or_404(Loan, pk=pk)
            
            # Validate loan status
            if loan.status not in ['approved', 'completed']:
                messages.error(request, f'Only approved or completed loans can be disbursed. Current status: {loan.status}')
                return redirect('loans:detail', pk=pk)
            
            # If loan is completed but has a payment schedule, don't allow re-disbursement
            if loan.status == 'completed' and loan.payment_schedule.all().exists():
                messages.error(request, 'This loan is already completed with a payment schedule. Cannot disburse again.')
                return redirect('loans:detail', pk=pk)
            
            # For approved loans, validate security deposit is verified
            # For completed loans being fixed, skip this check (legacy data)
            if loan.status == 'approved':
                try:
                    from loans.models import SecurityDeposit
                    security_deposit = loan.security_deposit
                    if not security_deposit.is_verified:
                        messages.error(request, 'Security deposit must be verified before disbursement.')
                        return redirect('loans:detail', pk=pk)
                except SecurityDeposit.DoesNotExist:
                    messages.error(request, 'Security deposit not found. Please submit and verify security deposit before disbursement.')
                    return redirect('loans:detail', pk=pk)
            
            # Update loan status to disbursed
            from django.utils import timezone
            from datetime import timedelta
            
            loan.status = 'disbursed'
            loan.disbursement_date = timezone.now()
            
            # Calculate maturity date based on repayment frequency
            if loan.repayment_frequency == 'daily' and loan.term_days and loan.term_days > 0:
                loan.maturity_date = (loan.disbursement_date + timedelta(days=loan.term_days)).date()
            elif loan.repayment_frequency == 'weekly' and loan.term_weeks and loan.term_weeks > 0:
                loan.maturity_date = (loan.disbursement_date + timedelta(days=7 * loan.term_weeks)).date()
            elif loan.term_months and loan.term_months > 0:
                loan.maturity_date = (loan.disbursement_date + timedelta(days=30 * loan.term_months)).date()
            
            loan.save()
            
            # Log the disbursement action
            try:
                from loans.models import ApprovalLog
                branch_name = request.user.managed_branch.name if request.user.managed_branch else 'Unknown'
                ApprovalLog.objects.create(
                    approval_type='loan_disbursement',
                    loan=loan,
                    manager=request.user,
                    action='approve',
                    comments=f'Loan disbursed: K{loan.principal_amount}',
                    branch=branch_name
                )
            except Exception as e:
                print(f"Error logging disbursement: {e}")
            
            # Generate payment schedule
            try:
                from .utils import generate_payment_schedule
                generate_payment_schedule(loan)
            except Exception as e:
                print(f"Warning: Payment schedule generation: {str(e)}")
            
            # Update loan status to active after payment schedule is created
            loan.status = 'active'
            loan.save()
            
            # Send disbursement email
            try:
                from common.email_utils import send_loan_disbursed_email
                send_loan_disbursed_email(loan)
            except Exception as e:
                print(f"Error sending disbursement email: {e}")
            
            messages.success(request, f'Loan {loan.application_number} has been disbursed successfully!')
            return redirect('loans:detail', pk=pk)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error disbursing loan: {str(e)}')
            return redirect('loans:detail', pk=pk)
    
    def _create_notification(self, loan, notification_type):
        """Create in-app notification for loan disbursement"""
        try:
            from notifications.models import Notification, NotificationTemplate
            
            template = NotificationTemplate.objects.filter(
                notification_type=notification_type,
                is_active=True
            ).first()
            
            if template:
                message = template.message_template.format(
                    loan_number=loan.application_number,
                    amount=loan.principal_amount
                )
                
                Notification.objects.create(
                    recipient=loan.borrower,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel='in_app',
                    recipient_address=loan.borrower.email or '',
                    scheduled_at=timezone.now(),
                    loan=loan,
                    status='sent'
                )
        except Exception as e:
            print(f"Error creating notification: {e}")

class LoanCalculatorView(LoginRequiredMixin, TemplateView):
    template_name = 'loans/calculator.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loan_types'] = LoanType.objects.filter(is_active=True)
        return context

class LoanStatusDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'loans/status_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get loan statistics by status
        from django.db.models import Count, Sum, Q
        
        if self.request.user.role == 'borrower':
            # Borrower sees only their loans
            loans_queryset = Loan.objects.filter(borrower=self.request.user)
        else:
            # Staff sees all loans
            loans_queryset = Loan.objects.all()
        
        # Status counts
        status_stats = loans_queryset.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('principal_amount')
        ).order_by('status')
        
        context['status_stats'] = status_stats
        
        # Recent loans (from system launch or last 30 days, whichever is more recent)
        from datetime import date, timedelta
        from common.utils import get_system_launch_date
        
        recent_date = date.today() - timedelta(days=30)
        system_launch = get_system_launch_date()
        
        # Use the more recent date between system launch and 30 days ago
        filter_date = max(recent_date, system_launch)
        
        context['recent_loans'] = loans_queryset.filter(
            application_date__date__gte=filter_date
        ).order_by('-application_date')[:10]
        
        context['system_launch_date'] = system_launch
        context['filter_date'] = filter_date
        
        # Overdue loans (for staff only)
        if self.request.user.role in ['admin', 'loan_officer']:
            overdue_loans = []
            for loan in loans_queryset.filter(status='active'):
                if loan.is_overdue:
                    overdue_loans.append(loan)
            context['overdue_loans'] = overdue_loans[:10]  # Limit to 10 for performance
        
        # Summary totals
        context['total_loans'] = loans_queryset.count()
        context['active_loans'] = loans_queryset.filter(status='active').count()
        context['pending_loans'] = loans_queryset.filter(status='pending').count()
        context['completed_loans'] = loans_queryset.filter(status='completed').count()
        
        return context


class LoanDocumentUploadView(LoginRequiredMixin, CreateView):
    model = LoanDocument
    form_class = LoanDocumentForm
    template_name = 'loans/upload_document.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.loan = get_object_or_404(Loan, pk=kwargs['loan_id'])
        
        # Check permissions
        if request.user.role == 'borrower' and self.loan.borrower != request.user:
            messages.error(request, 'You can only upload documents for your own loans.')
            return redirect('loans:detail', pk=self.loan.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.loan = self.loan
        form.instance.uploaded_by = self.request.user
        
        # Create notification for administrators
        self._notify_admins_of_new_document(form.instance)
        
        messages.success(self.request, 'Document uploaded successfully! Administrators will review it shortly.')
        return super().form_valid(form)
    
    def _notify_admins_of_new_document(self, document):
        """Notify administrators about new document upload"""
        try:
            from notifications.models import Notification, NotificationTemplate
            from accounts.models import User
            
            # Get the notification template
            try:
                template = NotificationTemplate.objects.get(
                    notification_type='document_uploaded',
                    is_active=True
                )
            except NotificationTemplate.DoesNotExist:
                # If no template exists, skip notification
                return
            
            # Get all administrators and loan officers
            admins = User.objects.filter(role__in=['admin', 'loan_officer'])
            
            for admin in admins:
                # Format the message using the template
                message = template.message_template.format(
                    document_type=document.get_document_type_display(),
                    loan_number=document.loan.application_number,
                    borrower_name=document.uploaded_by.full_name
                )
                
                Notification.objects.create(
                    recipient=admin,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel=template.channel,
                    recipient_address=admin.email or '',
                    scheduled_at=timezone.now(),
                    loan=document.loan
                )
        except ImportError:
            pass  # Notifications app not available
    
    def get_success_url(self):
        return reverse_lazy('loans:detail', kwargs={'pk': self.loan.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loan'] = self.loan
        return context


class LoanDocumentListView(LoginRequiredMixin, ListView):
    model = LoanDocument
    template_name = 'loans/document_list.html'
    context_object_name = 'documents'
    
    def dispatch(self, request, *args, **kwargs):
        self.loan = get_object_or_404(Loan, pk=kwargs['loan_id'])
        
        # Check permissions
        if request.user.role == 'borrower' and self.loan.borrower != request.user:
            messages.error(request, 'You can only view documents for your own loans.')
            return redirect('loans:detail', pk=self.loan.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return LoanDocument.objects.filter(loan=self.loan).order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loan'] = self.loan
        context['can_upload'] = (
            self.request.user.role == 'borrower' and 
            self.loan.borrower == self.request.user and 
            self.loan.status in ['pending', 'approved']
        )
        return context


class DocumentVerificationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role not in ['admin', 'loan_officer']:
            messages.error(request, 'You do not have permission to verify documents.')
            return redirect('loans:document_list', loan_id=request.POST.get('loan_id', 1))
        
        document = get_object_or_404(LoanDocument, pk=pk)
        form = DocumentVerificationForm(request.POST, instance=document)
        
        if form.is_valid():
            document = form.save(commit=False)
            document.verified_by = request.user
            document.verified_at = timezone.now()
            document.save()
            
            status = 'verified' if document.is_verified else 'rejected'
            messages.success(request, f'Document has been {status}.')
        else:
            messages.error(request, 'Error updating document verification.')
        
        return redirect('loans:document_list', loan_id=document.loan.pk)


class DocumentDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        document = get_object_or_404(LoanDocument, pk=pk)
        
        # Check permissions
        if request.user.role == 'borrower' and document.loan.borrower != request.user:
            messages.error(request, 'You do not have permission to access this document.')
            return redirect('loans:list')
        
        # Check if file exists
        if not document.document_file:
            messages.error(
                request, 
                f'File not available for download. The document "{document.original_filename}" '
                'may not have been properly uploaded or the file is missing.'
            )
            if request.user.role == 'borrower':
                return redirect('loans:document_list', loan_id=document.loan.pk)
            else:
                return redirect('loans:document_review_dashboard')
        
        try:
            # Check if file exists on disk
            if not document.document_file.storage.exists(document.document_file.name):
                messages.error(
                    request,
                    f'File "{document.original_filename}" not found on server. '
                    'The file may have been moved or deleted.'
                )
                if request.user.role == 'borrower':
                    return redirect('loans:document_list', loan_id=document.loan.pk)
                else:
                    return redirect('loans:document_review_dashboard')
            
            # Determine content type based on file extension
            import mimetypes
            content_type, _ = mimetypes.guess_type(document.original_filename)
            if not content_type:
                content_type = 'application/octet-stream'
            
            response = HttpResponse(
                document.document_file.read(),
                content_type=content_type
            )
            response['Content-Disposition'] = f'attachment; filename="{document.original_filename}"'
            return response
            
        except Exception as e:
            messages.error(
                request,
                f'Error downloading file "{document.original_filename}": {str(e)}'
            )
            if request.user.role == 'borrower':
                return redirect('loans:document_list', loan_id=document.loan.pk)
            else:
                return redirect('loans:document_review_dashboard')


class DocumentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(LoanDocument, pk=pk)
        
        # Check permissions - only borrower can delete their own documents, and only if loan is pending
        if (request.user.role == 'borrower' and 
            document.loan.borrower == request.user and 
            document.loan.status == 'pending'):
            
            document.delete()
            messages.success(request, 'Document deleted successfully.')
        else:
            messages.error(request, 'You cannot delete this document.')
        
        return redirect('loans:document_list', loan_id=document.loan.pk)


class AdminDeleteLoanDocumentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role not in ['admin', 'loan_officer']:
            messages.error(request, 'You do not have permission to delete loan documents.')
            return redirect('loans:list')
        
        document = get_object_or_404(LoanDocument, pk=pk)
        
        # Store document info for the success message
        doc_type = document.get_document_type_display()
        loan_number = document.loan.application_number
        
        # Delete the file from storage if it exists
        if document.document_file:
            try:
                document.document_file.delete(save=False)
            except Exception as e:
                messages.warning(request, f'File could not be deleted from storage: {e}')
        
        # Delete the document record
        document.delete()
        
        messages.success(
            request, 
            f'Loan document "{doc_type}" for loan {loan_number} has been permanently deleted.'
        )
        
        # Redirect based on where the request came from
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', reverse_lazy('loans:document_review_dashboard')))
        return redirect(next_url)


class DocumentReviewDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'loans/document_review_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin handles authentication, but check if user is authenticated first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'loan_officer']:
            messages.error(request, 'You do not have permission to access the document review dashboard.')
            return redirect('loans:list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all documents that need review
        pending_documents = LoanDocument.objects.filter(is_verified=False).order_by('-uploaded_at')
        verified_documents = LoanDocument.objects.filter(is_verified=True).order_by('-verified_at')[:10]
        
        # Group by loan for better organization
        loans_with_pending_docs = {}
        for doc in pending_documents:
            loan_id = doc.loan.id
            if loan_id not in loans_with_pending_docs:
                loans_with_pending_docs[loan_id] = {
                    'loan': doc.loan,
                    'documents': []
                }
            loans_with_pending_docs[loan_id]['documents'].append(doc)
        
        context['loans_with_pending_docs'] = loans_with_pending_docs.values()
        context['pending_count'] = pending_documents.count()
        context['verified_documents'] = verified_documents
        context['total_documents'] = LoanDocument.objects.count()
        context['verified_count'] = LoanDocument.objects.filter(is_verified=True).count()
        
        return context


class LoanEditView(LoginRequiredMixin, View):
    """Edit loan details - only for admins and loan officers"""
    
    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin handles authentication, but check if user is authenticated first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        # Only admins and loan officers can edit loans
        if request.user.role not in ['admin', 'loan_officer', 'manager'] and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to edit loans.')
            return redirect('loans:list')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        loan_types = LoanType.objects.filter(is_active=True)
        
        context = {
            'loan': loan,
            'loan_types': loan_types,
        }
        return render(request, 'loans/edit.html', context)
    
    def post(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        
        try:
            # Update loan details
            loan_type_id = request.POST.get('loan_type')
            if loan_type_id:
                loan.loan_type = LoanType.objects.get(id=loan_type_id)
            
            # Update financial details
            principal_amount = request.POST.get('principal_amount')
            if principal_amount:
                loan.principal_amount = Decimal(principal_amount)
            
            interest_rate = request.POST.get('interest_rate')
            if interest_rate:
                loan.interest_rate = Decimal(interest_rate)
            
            term_months = request.POST.get('term_months')
            if term_months:
                loan.term_months = int(term_months)
            
            # Update purpose and collateral
            purpose = request.POST.get('purpose')
            if purpose:
                loan.purpose = purpose
            
            collateral_description = request.POST.get('collateral_description')
            if collateral_description is not None:
                loan.collateral_description = collateral_description
            
            collateral_value = request.POST.get('collateral_value')
            if collateral_value:
                loan.collateral_value = Decimal(collateral_value) if collateral_value else None
            
            # Update status if provided
            status = request.POST.get('status')
            if status and status in dict(Loan.STATUS_CHOICES):
                loan.status = status
            
            # Update notes
            approval_notes = request.POST.get('approval_notes')
            if approval_notes is not None:
                loan.approval_notes = approval_notes
            
            loan.save()
            
            messages.success(request, f'Loan {loan.application_number} updated successfully!')
            return redirect('loans:detail', pk=loan.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating loan: {str(e)}')
            return redirect('loans:edit', pk=pk)


class LoanTypesManageView(LoginRequiredMixin, TemplateView):
    """View for managing loan types"""
    template_name = 'loans/loan_types_manage.html'
    
    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin handles authentication, but check if user is authenticated first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to manage loan types.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Avg
        
        loan_types = LoanType.objects.all().order_by('-is_active', 'name')
        
        context['loan_types'] = loan_types
        context['active_count'] = loan_types.filter(is_active=True).count()
        context['inactive_count'] = loan_types.filter(is_active=False).count()
        context['avg_interest_rate'] = loan_types.aggregate(Avg('interest_rate'))['interest_rate__avg'] or 0
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle creating/updating loan types"""
        try:
            loan_type_id = request.POST.get('loan_type_id')
            
            if loan_type_id:
                # Update existing
                loan_type = get_object_or_404(LoanType, id=loan_type_id)
                action = 'updated'
            else:
                # Create new
                loan_type = LoanType()
                action = 'created'
            
            # Update basic fields
            loan_type.name = request.POST.get('name')
            loan_type.description = request.POST.get('description')
            loan_type.interest_rate = request.POST.get('interest_rate', 45.00)
            loan_type.min_amount = request.POST.get('min_amount')
            loan_type.max_amount = request.POST.get('max_amount')
            loan_type.is_active = request.POST.get('is_active') == 'true'
            
            # Update repayment frequency
            loan_type.repayment_frequency = request.POST.get('repayment_frequency')
            
            # Update term fields based on frequency
            if loan_type.repayment_frequency == 'daily':
                loan_type.min_term_days = request.POST.get('min_term_days')
                loan_type.max_term_days = request.POST.get('max_term_days')
                loan_type.min_term_weeks = None
                loan_type.max_term_weeks = None
            elif loan_type.repayment_frequency == 'weekly':
                loan_type.min_term_weeks = request.POST.get('min_term_weeks')
                loan_type.max_term_weeks = request.POST.get('max_term_weeks')
                loan_type.min_term_days = None
                loan_type.max_term_days = None
            
            # Clear deprecated monthly fields
            loan_type.min_term_months = None
            loan_type.max_term_months = None
            
            loan_type.save()
            
            messages.success(request, f'Loan type "{loan_type.name}" has been {action} successfully!')
            return redirect('loans:manage_loan_types')
            
        except Exception as e:
            messages.error(request, f'Error saving loan type: {str(e)}')
            return redirect('loans:manage_loan_types')


class LoanDocumentsManageView(LoginRequiredMixin, TemplateView):
    """View for managing all loan documents"""
    template_name = 'loans/loan_documents_manage.html'
    
    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin handles authentication, but check if user is authenticated first
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'loan_officer', 'manager'] and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to manage loan documents.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import datetime, timedelta
        
        # Get all documents
        all_documents = LoanDocument.objects.all().select_related('loan', 'uploaded_by', 'verified_by')
        
        # Statistics
        context['total_documents'] = all_documents.count()
        context['pending_count'] = all_documents.filter(is_verified=False).count()
        context['verified_count'] = all_documents.filter(is_verified=True).count()
        
        # Monthly uploads
        first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context['monthly_uploads'] = all_documents.filter(uploaded_at__gte=first_day_of_month).count()
        
        # Group documents by loan
        loans_with_docs = {}
        for doc in all_documents.order_by('-uploaded_at'):
            loan_id = doc.loan.id
            if loan_id not in loans_with_docs:
                loans_with_docs[loan_id] = {
                    'loan': doc.loan,
                    'documents': []
                }
            loans_with_docs[loan_id]['documents'].append(doc)
        
        context['loans_with_documents'] = loans_with_docs.values()
        
        return context


class UpfrontPaymentView(LoginRequiredMixin, View):
    """View for submitting upfront payment"""
    template_name = 'loans/upfront_payment.html'
    
    def get(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        
        # Check permissions
        if request.user.role == 'borrower' and loan.borrower != request.user:
            messages.error(request, "You don't have permission to access this loan.")
            return redirect('loans:list')
        
        # Check if loan is in correct status
        if loan.status not in ['pending', 'approved']:
            messages.error(request, "Upfront payment can only be made for pending or approved loans.")
            return redirect('loans:detail', pk=loan.pk)
        
        # Check if already paid
        if loan.upfront_payment_verified:
            messages.info(request, "Upfront payment has already been verified for this loan.")
            return redirect('loans:detail', pk=loan.pk)
        
        from .forms_upfront import UpfrontPaymentForm
        form = UpfrontPaymentForm(loan=loan)
        
        context = {
            'loan': loan,
            'form': form,
            'upfront_amount': loan.upfront_payment_required,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        
        # Check permissions
        if request.user.role == 'borrower' and loan.borrower != request.user:
            messages.error(request, "You don't have permission to access this loan.")
            return redirect('loans:list')
        
        from .forms_upfront import UpfrontPaymentForm
        form = UpfrontPaymentForm(request.POST, request.FILES, loan=loan)
        
        if form.is_valid():
            # Update loan with upfront payment info
            loan.upfront_payment_paid = form.cleaned_data['amount_paid']
            loan.upfront_payment_date = timezone.now()
            loan.upfront_payment_verified = False  # Needs admin verification
            loan.save()
            
            # Get or create security deposit record and UPDATE the paid amount
            from .models import SecurityDeposit
            deposit, created = SecurityDeposit.objects.get_or_create(
                loan=loan,
                defaults={
                    'required_amount': loan.upfront_payment_required or (loan.principal_amount * Decimal('0.10')),
                    'paid_amount': Decimal('0')
                }
            )
            
            # Update the security deposit with the actual payment amount
            deposit.paid_amount = form.cleaned_data['amount_paid']
            deposit.payment_date = timezone.now()
            deposit.payment_method = form.cleaned_data.get('payment_method', 'cash')
            deposit.payment_reference = form.cleaned_data.get('payment_reference', '')
            deposit.save()
            
            # Create a notification for admin
            from notifications.models import Notification, NotificationTemplate
            try:
                # Get or create payment notification template
                template, created = NotificationTemplate.objects.get_or_create(
                    name='Upfront Payment Notification',
                    defaults={
                        'notification_type': 'payment',
                        'channel': 'email',
                        'subject_template': 'Upfront Payment Submitted - {loan_number}',
                        'message_template': '{borrower_name} has submitted an upfront payment of K{amount} for loan {loan_number}. Payment method: {payment_method}. Reference: {payment_reference}. Please verify the payment.',
                        'is_active': True
                    }
                )
                
                Notification.objects.create(
                    recipient=loan.loan_officer if loan.loan_officer else request.user,
                    template=template,
                    subject=f'Upfront Payment Submitted - {loan.application_number}',
                    message=f'{loan.borrower.full_name} has submitted an upfront payment of K{loan.upfront_payment_paid:,.2f} for loan {loan.application_number}. Payment method: {form.cleaned_data["payment_method"]}. Reference: {form.cleaned_data["payment_reference"]}. Please verify payment.',
                    channel='email',
                    recipient_address=loan.loan_officer.email if loan.loan_officer else request.user.email,
                    scheduled_at=timezone.now(),
                    loan=loan
                )
            except Exception as e:
                # Don't fail the payment if notification fails
                print(f"Notification creation failed: {e}")
            
            messages.success(
                request,
                f'Upfront payment of K{loan.upfront_payment_paid:,.2f} has been submitted successfully! '
                'Your payment will be verified by our team within 24 hours.'
            )
            return redirect('loans:detail', pk=loan.pk)
        
        context = {
            'loan': loan,
            'form': form,
            'upfront_amount': loan.upfront_payment_required,
        }
        return render(request, self.template_name, context)


class VerifyUpfrontPaymentView(LoginRequiredMixin, View):
    """View for staff to verify upfront payments"""
    
    def post(self, request, pk):
        # Only staff can verify
        if request.user.role not in ['loan_officer', 'manager'] and not request.user.is_superuser:
            messages.error(request, "You don't have permission to verify payments.")
            return redirect('loans:detail', pk=pk)
        
        loan = get_object_or_404(Loan, pk=pk)
        action = request.POST.get('action')
        
        if action == 'verify':
            loan.upfront_payment_verified = True
            loan.save()
            
            # Notify borrower
            from notifications.models import Notification, NotificationTemplate
            try:
                # Get or create verification notification template
                template, created = NotificationTemplate.objects.get_or_create(
                    name='Upfront Payment Verified',
                    defaults={
                        'notification_type': 'payment',
                        'channel': 'email',
                        'subject_template': 'Upfront Payment Verified - {loan_number}',
                        'message_template': 'Your upfront payment of K{amount} has been verified. Your loan application will now proceed to the next stage.',
                        'is_active': True
                    }
                )
                
                Notification.objects.create(
                    recipient=loan.borrower,
                    template=template,
                    subject=f'Upfront Payment Verified - {loan.application_number}',
                    message=f'Your upfront payment of K{loan.upfront_payment_paid:,.2f} has been verified. Your loan application will now proceed to the next stage.',
                    channel='email',
                    recipient_address=loan.borrower.email,
                    scheduled_at=timezone.now(),
                    loan=loan
                )
            except Exception as e:
                # Don't fail verification if notification fails
                print(f"Notification creation failed: {e}")
            
            messages.success(request, f'Upfront payment of K{loan.upfront_payment_paid:,.2f} has been verified.')
        
        elif action == 'reject':
            loan.upfront_payment_paid = 0
            loan.upfront_payment_date = None
            loan.upfront_payment_verified = False
            loan.save()
            
            # Notify borrower
            from notifications.models import Notification, NotificationTemplate
            try:
                # Get or create rejection notification template
                template, created = NotificationTemplate.objects.get_or_create(
                    name='Upfront Payment Rejected',
                    defaults={
                        'notification_type': 'payment',
                        'channel': 'email',
                        'subject_template': 'Upfront Payment Rejected - {loan_number}',
                        'message_template': 'Your upfront payment has been rejected. Please contact us or submit a new payment with correct details.',
                        'is_active': True
                    }
                )
                
                Notification.objects.create(
                    recipient=loan.borrower,
                    template=template,
                    subject=f'Upfront Payment Rejected - {loan.application_number}',
                    message=f'Your upfront payment has been rejected. Please contact us or submit a new payment with correct details.',
                    channel='email',
                    recipient_address=loan.borrower.email,
                    scheduled_at=timezone.now(),
                    loan=loan
                )
            except Exception as e:
                # Don't fail rejection if notification fails
                print(f"Notification creation failed: {e}")
            
            messages.warning(request, 'Upfront payment has been rejected.')
        
        return redirect('loans:detail', pk=pk)



class RecordSecurityDepositView(LoginRequiredMixin, View):
    """Record security deposit payment"""
    
    def post(self, request, pk):
        if request.user.role not in ['admin', 'loan_officer', 'manager']:
            messages.error(request, 'You do not have permission to record deposits.')
            return redirect('loans:detail', pk=pk)
        
        loan = get_object_or_404(Loan, pk=pk)
        
        # Get or create security deposit record
        from .models import SecurityDeposit
        deposit, created = SecurityDeposit.objects.get_or_create(
            loan=loan,
            defaults={
                'required_amount': loan.upfront_payment_required or (loan.principal_amount * Decimal('0.10')),
                'paid_amount': Decimal('0')
            }
        )
        
        # Get payment details from form
        from decimal import Decimal
        try:
            paid_amount = Decimal(request.POST.get('paid_amount', '0'))
            payment_method = request.POST.get('payment_method', 'cash')
            receipt_number = request.POST.get('receipt_number', '')
            notes = request.POST.get('notes', '')
            
            # Update deposit record
            deposit.paid_amount = paid_amount
            deposit.payment_date = timezone.now()
            deposit.payment_method = payment_method
            deposit.receipt_number = receipt_number
            deposit.notes = notes
            deposit.save()
            
            # Also update loan record for backward compatibility
            loan.upfront_payment_paid = paid_amount
            loan.upfront_payment_date = timezone.now()
            loan.save(update_fields=['upfront_payment_paid', 'upfront_payment_date'])
            
            messages.success(
                request,
                f'Security deposit of {paid_amount} recorded successfully. '
                f'Awaiting verification by admin/manager.'
            )
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid payment amount: {e}')
        
        return redirect('loans:detail', pk=pk)


class VerifySecurityDepositView(LoginRequiredMixin, View):
    """Verify security deposit payment"""
    
    def get(self, request, pk):
        """Show verification confirmation page"""
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'Only admins and managers can verify deposits.')
            return redirect('loans:detail', pk=pk)
        
        loan = get_object_or_404(Loan, pk=pk)
        
        try:
            from .models import SecurityDeposit
            deposit = SecurityDeposit.objects.get(loan=loan)
            
            context = {
                'loan': loan,
                'deposit': deposit,
            }
            return render(request, 'loans/verify_security_deposit.html', context)
            
        except SecurityDeposit.DoesNotExist:
            messages.error(request, 'No security deposit record found for this loan.')
            return redirect('loans:detail', pk=pk)
    
    def post(self, request, pk):
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'Only admins and managers can verify deposits.')
            return redirect('loans:detail', pk=pk)
        
        loan = get_object_or_404(Loan, pk=pk)
        
        try:
            from .models import SecurityDeposit
            deposit = SecurityDeposit.objects.get(loan=loan)
            
            # Verify the deposit
            deposit.verify(request.user)
            
            # Also update loan record for backward compatibility
            loan.upfront_payment_verified = True
            
            # If loan was approved and deposit is now verified, activate the loan
            if loan.status == 'approved':
                loan.status = 'active'
                loan.activation_date = timezone.now()
            
            loan.save(update_fields=['upfront_payment_verified', 'status', 'activation_date'])
            
            messages.success(
                request,
                f'Security deposit for loan {loan.application_number} has been verified. '
                f'Loan can now be disbursed.'
            )
        except SecurityDeposit.DoesNotExist:
            messages.error(request, 'No security deposit record found for this loan.')
        
        return redirect('loans:detail', pk=pk)
