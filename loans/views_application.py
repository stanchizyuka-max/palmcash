from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, UpdateView, TemplateView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy
import uuid

from accounts.models import User
from .models import LoanApplication
from .forms_application import LoanApplicationForm


class SelectBorrowerView(LoginRequiredMixin, TemplateView):
    template_name = 'loans/select_borrower.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['loan_officer', 'manager', 'admin']:
            messages.error(request, 'Only loan officers can submit loan applications.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == 'loan_officer':
            from django.db.models import Q
            borrower_ids = User.objects.filter(
                Q(assigned_officer=self.request.user) |
                Q(group_memberships__group__assigned_officer=self.request.user),
                role='borrower'
            ).values_list('id', flat=True).distinct()
            context['borrowers'] = User.objects.filter(id__in=borrower_ids)
        elif self.request.user.role == 'manager':
            try:
                from django.db.models import Q
                manager_branch = self.request.user.managed_branch.name
                context['borrowers'] = User.objects.filter(
                    Q(assigned_officer__officer_assignment__branch=manager_branch) |
                    Q(group_memberships__group__branch=manager_branch, group_memberships__is_active=True),
                    role='borrower'
                ).distinct()
            except:
                context['borrowers'] = User.objects.filter(role='borrower')
        else:
            context['borrowers'] = User.objects.filter(role='borrower')
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
        if request.user.role not in ['loan_officer', 'manager', 'admin']:
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
    
    def form_valid(self, form):
        loan_app = form.save(commit=False)
        loan_app.loan_officer = self.request.user
        loan_app.application_number = f"LA-{uuid.uuid4().hex[:8].upper()}"
        loan_app.status = 'pending'
        loan_app.save()
        
        messages.success(
            self.request,
            f'Loan application {loan_app.application_number} submitted for {loan_app.borrower.get_full_name()}. '
            f'Awaiting manager approval.'
        )
        
        return redirect(self.success_url)


class LoanApplicationsListView(LoginRequiredMixin, ListView):
    model = LoanApplication
    template_name = 'loans/applications_list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        if self.request.user.role == 'loan_officer':
            return LoanApplication.objects.filter(loan_officer=self.request.user)
        elif self.request.user.role == 'manager':
            try:
                branch = self.request.user.managed_branch
                if not branch:
                    return LoanApplication.objects.none()
                branch_name = branch.name
                from django.db.models import Q
                return LoanApplication.objects.filter(
                    Q(loan_officer__officer_assignment__branch__iexact=branch_name) |
                    Q(loan_officer__officer_assignment__isnull=True,
                      borrower__group_memberships__group__branch__iexact=branch_name) |
                    Q(borrower__group_memberships__group__branch__iexact=branch_name)
                ).distinct()
            except Exception:
                return LoanApplication.objects.all()
        else:
            return LoanApplication.objects.all()


class ApproveLoanApplicationView(LoginRequiredMixin, UpdateView):
    model = LoanApplication
    fields = ['status', 'rejection_reason']
    template_name = 'loans/approve_application.html'
    success_url = reverse_lazy('loans:applications_list')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['manager', 'admin']:
            messages.error(request, 'Only managers can approve loan applications.')
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
        return context
    
    def form_valid(self, form):
        loan_app = form.save(commit=False)

        if loan_app.status == 'approved':
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
                    loan = Loan(
                        borrower=loan_app.borrower,
                        loan_officer=loan_app.loan_officer,
                        loan_type=loan_type,
                        principal_amount=loan_app.loan_amount,
                        purpose=loan_app.purpose,
                        status='approved',
                        repayment_frequency='daily',
                        term_days=loan_app.duration_days,
                        payment_amount=Decimal('0'),
                        approval_date=timezone.now(),
                    )
                    loan.save()
                    messages.success(
                        self.request,
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
