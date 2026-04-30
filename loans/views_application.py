from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, UpdateView, TemplateView, DetailView, View
from django.contrib import messages
from django.urls import reverse_lazy
import uuid

from accounts.models import User
from .models import LoanApplication
from .forms_application import LoanApplicationForm


class SelectBorrowerView(LoginRequiredMixin, TemplateView):
    template_name = 'loans/select_borrower.html'
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search query from GET parameters
        search_query = self.request.GET.get('search', '').strip()
        
        if self.request.user.role == 'loan_officer':
            from django.db.models import Q
            borrower_ids = User.objects.filter(
                Q(assigned_officer=self.request.user) |
                Q(group_memberships__group__assigned_officer=self.request.user),
                role='borrower'
            ).values_list('id', flat=True).distinct()
            borrowers = User.objects.filter(id__in=borrower_ids)
        elif self.request.user.role == 'manager':
            try:
                from django.db.models import Q
                manager_branch = self.request.user.managed_branch.name
                borrowers = User.objects.filter(
                    Q(assigned_officer__officer_assignment__branch=manager_branch) |
                    Q(group_memberships__group__branch=manager_branch, group_memberships__is_active=True),
                    role='borrower'
                ).distinct()
            except:
                borrowers = User.objects.filter(role='borrower')
        else:
            borrowers = User.objects.filter(role='borrower')
        
        # Apply search filter if search query exists
        if search_query:
            from django.db.models import Q
            borrowers = borrowers.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(phone_number__icontains=search_query) |
                Q(national_id__icontains=search_query)
            )
        
        context['borrowers'] = borrowers.order_by('first_name', 'last_name')
        context['search_query'] = search_query
        return context


class BorrowerDetailForApplicationView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'loans/borrower_detail_for_application.html'
    context_object_name = 'borrower'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['loan_officer', 'manager', 'admin']:
            messages.error(request, 'Only loan officers can submit loan applications.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        borrower = self.object
        context['borrower_info'] = {
            'personal': {
                'full_name': borrower.get_full_name(),
                'email': borrower.email,
                'phone_number': borrower.phone_number,
                'date_of_birth': borrower.date_of_birth,
                'national_id': borrower.national_id,
                'is_verified': borrower.is_verified,
            },
            'employment': {
                'status': borrower.employment_status,
                'employer_name': borrower.employer_name,
                'monthly_income': borrower.monthly_income,
            },
            'address': {
                'address': borrower.address,
                'province': borrower.province,
                'district': borrower.district,
                'residential_area': borrower.residential_area,
            }
        }
        return context


class SubmitLoanApplicationView(LoginRequiredMixin, CreateView):
    model = LoanApplication
    form_class = LoanApplicationForm
    template_name = 'loans/submit_application.html'
    success_url = reverse_lazy('loans:applications_list')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['loan_officer', 'admin']:
            messages.error(request, 'Only loan officers can submit loan applications.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        initial = super().get_initial()
        borrower_id = self.request.GET.get('borrower')
        if borrower_id:
            try:
                initial['borrower'] = User.objects.get(id=borrower_id)
            except User.DoesNotExist:
                pass
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Restrict group dropdown to only this officer's groups
        if 'group' in form.fields:
            from clients.models import BorrowerGroup
            user = self.request.user
            if user.role == 'loan_officer':
                form.fields['group'].queryset = BorrowerGroup.objects.filter(
                    assigned_officer=user, is_active=True
                )
            elif user.role == 'manager':
                try:
                    branch = user.managed_branch
                    form.fields['group'].queryset = BorrowerGroup.objects.filter(
                        assigned_officer__officer_assignment__branch=branch.name,
                        is_active=True
                    )
                except Exception:
                    pass
        return form
    
    def form_valid(self, form):
        loan_app = form.save(commit=False)
        loan_app.loan_officer = self.request.user
        loan_app.application_number = f"LA-{uuid.uuid4().hex[:8].upper()}"
        loan_app.status = 'pending'
        loan_app.save()
        
        # Redirect to processing fee form instead of applications list
        messages.success(
            self.request,
            f'Loan application {loan_app.application_number} submitted for {loan_app.borrower.get_full_name()}. '
            f'Please record the processing fee.'
        )
        
        return redirect('loans:record_processing_fee', pk=loan_app.pk)


class LoanApplicationsListView(LoginRequiredMixin, ListView):
    model = LoanApplication
    template_name = 'loans/applications_list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        # Get base queryset based on user role
        if self.request.user.role == 'loan_officer':
            queryset = LoanApplication.objects.filter(loan_officer=self.request.user)
        elif self.request.user.role == 'manager':
            try:
                branch = self.request.user.managed_branch
                if not branch:
                    return LoanApplication.objects.none()
                branch_name = branch.name
                from django.db.models import Q
                # Only show applications where the loan officer is from this branch
                queryset = LoanApplication.objects.filter(
                    loan_officer__officer_assignment__branch__iexact=branch_name
                ).distinct()
            except Exception:
                queryset = LoanApplication.objects.all()
        else:
            queryset = LoanApplication.objects.all()
        
        # Apply filters
        client_search = self.request.GET.get('client', '').strip()
        officer_filter = self.request.GET.get('officer', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        
        if client_search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(borrower__first_name__icontains=client_search) |
                Q(borrower__last_name__icontains=client_search)
            )
        
        if officer_filter:
            queryset = queryset.filter(loan_officer_id=officer_filter)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('borrower', 'loan_officer').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get list of officers for filter dropdown
        if self.request.user.role == 'manager':
            try:
                branch = self.request.user.managed_branch
                if branch:
                    from accounts.models import User
                    context['officers'] = User.objects.filter(
                        role='loan_officer',
                        officer_assignment__branch__iexact=branch.name
                    ).order_by('first_name', 'last_name')
            except:
                context['officers'] = []
        elif self.request.user.role == 'admin':
            from accounts.models import User
            context['officers'] = User.objects.filter(role='loan_officer').order_by('first_name', 'last_name')
        else:
            context['officers'] = []
        
        # Pass filter values to template
        context['filters'] = {
            'client': self.request.GET.get('client', ''),
            'officer': self.request.GET.get('officer', ''),
            'status': self.request.GET.get('status', ''),
        }
        
        return context


class LoanApplicationDetailView(LoginRequiredMixin, DetailView):
    """View-only page for loan application details"""
    model = LoanApplication
    template_name = 'loans/application_detail_view.html'
    context_object_name = 'application'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['borrower'] = self.object.borrower
        return context


class ApproveLoanApplicationView(LoginRequiredMixin, UpdateView):
    model = LoanApplication
    fields = ['status', 'rejection_reason']
    template_name = 'loans/approve_application.html'
    success_url = reverse_lazy('loans:applications_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user has permission to approve
        if request.user.role not in ['manager', 'admin']:
            messages.error(request, 'Only managers and admins can approve loan applications.')
            return redirect('dashboard:dashboard')
        
        # Check if application exists and user has access to it
        try:
            app = self.get_object()
            # Managers can only approve applications from their branch
            if request.user.role == 'manager':
                try:
                    branch = request.user.managed_branch
                    # Check if loan officer is from manager's branch
                    if app.loan_officer.officer_assignment.branch != branch.name:
                        messages.error(request, 'You can only approve applications from your branch.')
                        return redirect('dashboard:dashboard')
                except Exception:
                    messages.error(request, 'Unable to verify branch access.')
                    return redirect('dashboard:dashboard')
        except Exception as e:
            messages.error(request, f'Application not found: {e}')
            return redirect('dashboard:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['status'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        })
        form.fields['rejection_reason'].widget = __import__('django.forms', fromlist=['Textarea']).Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Enter reason if rejecting...'
        })
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['borrower'] = self.object.borrower
        context['application'] = self.object
        return context
    
    def form_valid(self, form):
        loan_app = form.save(commit=False)

        if loan_app.status == 'approved':
            # Block if processing fee not verified
            if loan_app.processing_fee and not loan_app.processing_fee_verified:
                messages.error(
                    self.request,
                    f'Cannot approve — processing fee of K{loan_app.processing_fee:,.2f} has not been verified. '
                    f'Please verify the fee first.'
                )
                return redirect('loans:approve_application', pk=loan_app.pk)
            from django.utils import timezone
            loan_app.approved_by = self.request.user
            loan_app.approval_date = timezone.now()
            loan_app.save()

            # Create the actual Loan from this application
            try:
                from loans.models import Loan, LoanType
                import uuid

                loan_type = LoanType.objects.filter(is_active=True).first()
                if not loan_type:
                    from decimal import Decimal as D
                    loan_type = LoanType.objects.create(
                        name='Standard',
                        description='Standard loan',
                        interest_rate=D('45.00'),
                        min_amount=D('100.00'),
                        max_amount=D('1000000.00'),
                        repayment_frequency='daily',
                        is_active=True,
                    )

                if loan_type:
                    from decimal import Decimal
                    freq = loan_app.repayment_frequency
                    interest_rate = Decimal('40.00') if freq == 'daily' else Decimal('45.00')
                    
                    # duration_days already stores actual days (converted in form for weekly loans)
                    term_days = loan_app.duration_days if freq == 'daily' else None
                    term_weeks = (loan_app.duration_days // 7) if freq == 'weekly' else None
                    
                    loan = Loan(
                        borrower=loan_app.borrower,
                        loan_officer=loan_app.loan_officer,
                        loan_type=loan_type,
                        principal_amount=loan_app.loan_amount,
                        purpose=loan_app.purpose,
                        status='approved',
                        repayment_frequency=freq,
                        interest_rate=interest_rate,
                        term_days=term_days,
                        term_weeks=term_weeks,
                        payment_amount=Decimal('0'),
                        approval_date=timezone.now(),
                    )
                    loan.save()

                    # For DAILY loans: Skip security deposit requirement
                    # For WEEKLY loans: Carry forward existing security or require new deposit
                    if freq == 'daily':
                        # Daily loans don't require security - mark as ready to disburse
                        from loans.models import SecurityDeposit
                        SecurityDeposit.objects.create(
                            loan=loan,
                            required_amount=Decimal('0'),
                            paid_amount=Decimal('0'),
                            is_verified=True,  # Auto-verify for daily loans
                            verification_date=timezone.now(),
                        )
                        loan.upfront_payment_verified = True
                        loan.save(update_fields=['upfront_payment_verified'])
                        
                        messages.success(
                            self.request,
                            f'Application {loan_app.application_number} approved. '
                            f'Loan {loan.application_number} created (Daily loan - no security required). Ready to disburse.'
                        )
                    else:
                        # Weekly loans require security - try carry forward
                        try:
                            from loans.models import SecurityDeposit
                            from loans.security_services import apply_carry_forward
                            from loans.vault_services import record_security_deposit

                            # Find the most recent completed loan with verified security for this borrower
                            previous_loan = Loan.objects.filter(
                                borrower=loan_app.borrower,
                                status='completed',
                                security_deposit__is_verified=True,
                            ).order_by('-updated_at').first()

                            if previous_loan:
                                # Create a security deposit record for the new loan first
                                from decimal import Decimal
                                required = loan.principal_amount * Decimal('0.10')
                                new_deposit, _ = SecurityDeposit.objects.get_or_create(
                                    loan=loan,
                                    defaults={
                                        'required_amount': required,
                                        'paid_amount': Decimal('0'),
                                        'is_verified': False,
                                    }
                                )
                                # Carry forward security from old loan
                                txn, err = apply_carry_forward(previous_loan, loan, loan_app.loan_officer)
                                if txn:
                                    # If carry forward covers full required amount, mark deposit and loan as verified
                                    new_deposit.refresh_from_db()
                                    if new_deposit.paid_amount >= required:
                                        new_deposit.is_verified = True
                                        new_deposit.verification_date = timezone.now()
                                        new_deposit.save(update_fields=['is_verified', 'verification_date'])
                                        # Also mark the loan's upfront payment as verified
                                        # so it goes straight to Ready to Disburse
                                        loan.upfront_payment_paid = new_deposit.paid_amount
                                        loan.upfront_payment_verified = True
                                        loan.save(update_fields=['upfront_payment_paid', 'upfront_payment_verified'])
                                    # No vault entry here — money is already in the vault from the original deposit
                                    # Vault only changes when NEW cash comes in (top-up) or goes out (return)
                            else:
                                # No previous security - create empty deposit record
                                from decimal import Decimal
                                required = loan.principal_amount * Decimal('0.10')
                                SecurityDeposit.objects.get_or_create(
                                    loan=loan,
                                    defaults={
                                        'required_amount': required,
                                        'paid_amount': Decimal('0'),
                                        'is_verified': False,
                                    }
                                )
                        except Exception as e:
                            # Non-fatal — loan is still created
                            print(f"Carry forward error: {e}")

                        messages.success(
                            self.request,
                            f'Application {loan_app.application_number} approved. '
                            f'Loan {loan.application_number} created — security carried forward, ready to disburse.'
                            if loan.upfront_payment_verified else
                            f'Application {loan_app.application_number} approved. '
                            f'Loan {loan.application_number} created — officer can now initiate 10% upfront payment.'
                        )
                else:
                    messages.warning(
                        self.request,
                        f'Application approved but no loan type found. Please create a loan type first.'
                    )
            except Exception as e:
                messages.warning(self.request, f'Application approved but loan creation failed: {e}')

        elif loan_app.status == 'rejected':
            loan_app.save()
            messages.warning(self.request, f'Loan application {loan_app.application_number} rejected.')

        return redirect(self.success_url)


class VerifyProcessingFeeView(LoginRequiredMixin, View):
    """Manager verifies the processing fee on a loan application."""

    def post(self, request, pk):
        if request.user.role not in ['manager', 'admin']:
            messages.error(request, 'Only managers can verify processing fees.')
            return redirect('loans:applications_list')

        app = get_object_or_404(LoanApplication, pk=pk)

        if not app.processing_fee:
            messages.error(request, 'No processing fee recorded for this application.')
            return redirect('loans:approve_application', pk=pk)

        if app.processing_fee_verified:
            messages.info(request, 'Processing fee already verified.')
            return redirect('loans:approve_application', pk=pk)

        from django.utils import timezone
        app.processing_fee_verified = True
        app.processing_fee_verified_by = request.user
        app.processing_fee_verified_at = timezone.now()
        app.save(update_fields=['processing_fee_verified', 'processing_fee_verified_by', 'processing_fee_verified_at'])

        messages.success(request, f'Processing fee of K{app.processing_fee:,.2f} verified.')
        return redirect('loans:approve_application', pk=pk)


class RecordProcessingFeeView(LoginRequiredMixin, View):
    """Loan officer records the processing fee for a loan application."""
    template_name = 'loans/record_processing_fee.html'
    
    def get(self, request, pk):
        if request.user.role not in ['loan_officer', 'manager', 'admin']:
            messages.error(request, 'Only loan officers can record processing fees.')
            return redirect('loans:applications_list')
        
        app = get_object_or_404(LoanApplication, pk=pk)
        
        # Check if processing fee already recorded
        if app.processing_fee:
            messages.info(request, 'Processing fee already recorded for this application.')
            return redirect('loans:applications_list')
        
        return render(request, self.template_name, {
            'application': app,
            'borrower': app.borrower,
        })
    
    def post(self, request, pk):
        if request.user.role not in ['loan_officer', 'manager', 'admin']:
            messages.error(request, 'Only loan officers can record processing fees.')
            return redirect('loans:applications_list')
        
        app = get_object_or_404(LoanApplication, pk=pk)
        
        from decimal import Decimal, InvalidOperation
        fee_str = request.POST.get('processing_fee', '').strip()
        
        try:
            fee = Decimal(fee_str)
            if fee <= 0:
                raise ValueError()
        except (InvalidOperation, ValueError):
            messages.error(request, 'Please enter a valid processing fee amount greater than zero.')
            return render(request, self.template_name, {
                'application': app,
                'borrower': app.borrower,
            })
        
        app.processing_fee = fee
        app.processing_fee_recorded_by = request.user
        app.processing_fee_verified = False
        app.save(update_fields=['processing_fee', 'processing_fee_recorded_by', 'processing_fee_verified'])
        
        # Record vault inflow for processing fee
        try:
            from loans.vault_services import _get_or_create_vault, _ref
            from expenses.models import VaultTransaction
            from clients.models import Branch
            from django.utils import timezone as tz
            
            branch_name = request.user.officer_assignment.branch if hasattr(request.user, 'officer_assignment') else ''
            branch = Branch.objects.filter(name__iexact=branch_name).first() if branch_name else None
            
            if branch:
                vault = _get_or_create_vault(branch)
                vault.balance += fee
                vault.save(update_fields=['balance', 'updated_at'])
                VaultTransaction.objects.create(
                    transaction_type='deposit',
                    direction='in',
                    branch=branch.name,
                    amount=fee,
                    balance_after=vault.balance,
                    description=f'Processing fee for application {app.application_number} — pending verification',
                    reference_number=_ref(),
                    recorded_by=request.user,
                    transaction_date=tz.now(),
                )
        except Exception as e:
            print(f"Vault fee record error: {e}")
        
        messages.success(
            request,
            f'Processing fee K{fee:,.2f} recorded for application {app.application_number}. '
            f'Awaiting manager verification.'
        )
        return redirect('loans:applications_list')
