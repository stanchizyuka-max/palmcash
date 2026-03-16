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
                manager_branch = self.request.user.managed_branch.name
                loan_officer_ids = User.objects.filter(
                    role='loan_officer',
                    officer_assignment__branch=manager_branch
                ).values_list('id', flat=True)
                return LoanApplication.objects.filter(loan_officer_id__in=loan_officer_ids)
            except:
                return LoanApplication.objects.none()
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
    
    def form_valid(self, form):
        loan_app = form.save(commit=False)
        
        if loan_app.status == 'approved':
            loan_app.approved_by = self.request.user
            from django.utils import timezone
            loan_app.approval_date = timezone.now()
            loan_app.save()
            
            messages.success(
                self.request,
                f'Loan application {loan_app.application_number} approved.'
            )
        elif loan_app.status == 'rejected':
            loan_app.save()
            messages.warning(
                self.request,
                f'Loan application {loan_app.application_number} rejected.'
            )
        
        return redirect(self.success_url)
