from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.db.models import Q
from .models import Loan, LoanType
from .forms_enhanced import EnhancedLoanApplicationForm
from documents.models import ClientVerification
from accounts.models import User
import uuid

class EnhancedLoanApplicationView(LoginRequiredMixin, CreateView):
    """
    Enhanced loan application view with comprehensive form
    """
    model = Loan
    form_class = EnhancedLoanApplicationForm
    template_name = 'loans/enhanced_apply.html'
    success_url = reverse_lazy('documents:upload')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user has outstanding loans
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
        
        # Allow users to fill in the form first, documents can be uploaded after
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Create and save the loan using the form's save_loan method
        loan = form.save_loan(self.request.user)
        
        # Store application data in session for document upload
        self.request.session['loan_application_data'] = {
            'application_number': loan.application_number,
            'principal_amount': str(loan.principal_amount),
            'loan_type': loan.loan_type.name if loan.loan_type else '',
            'purpose': form.cleaned_data.get('purpose', ''),
        }
        
        messages.success(
            self.request,
            f'Loan application submitted successfully! Application Number: {loan.application_number}. '
            'Please upload your required documents to complete the application process.'
        )
        
        return redirect('documents:upload')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.role == 'borrower':
            context['user_loans'] = Loan.objects.filter(borrower=self.request.user)
            context['completed_loans'] = context['user_loans'].filter(status='completed').count()
            context['can_apply'] = not context['user_loans'].filter(
                status__in=['pending', 'active', 'approved', 'disbursed']
            ).exists()
            
            # Check document verification status
            context['has_verified_documents'] = ClientVerification.objects.filter(
                client=self.request.user,
                status='verified'
            ).exists()
        
        # Get available loan types
        context['loan_types'] = LoanType.objects.filter(is_active=True)
        
        return context

@login_required
def enhanced_loan_application(request):
    """
    Function-based view for enhanced loan application
    """
    # Check if user has outstanding loans
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
    
    if request.method == 'POST':
        form = EnhancedLoanApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            # Create and save the loan using the form's save_loan method
            loan = form.save_loan(request.user)
            
            # Store application data in session
            request.session['loan_application_data'] = {
                'application_number': loan.application_number,
                'principal_amount': str(loan.principal_amount),
                'loan_type': loan.loan_type.name if loan.loan_type else '',
                'purpose': form.cleaned_data.get('purpose', ''),
            }
            
            messages.success(
                request,
                f'Loan application submitted successfully! Application Number: {loan.application_number}. '
                'Please upload your required documents to complete the application process.'
            )
            
            return redirect('documents:upload')
    else:
        form = EnhancedLoanApplicationForm(user=request.user)
    
    context = {
        'form': form,
        'loan_types': LoanType.objects.filter(is_active=True),
    }
    
    if request.user.role == 'borrower':
        user_loans = Loan.objects.filter(borrower=request.user)
        context['user_loans'] = user_loans
        context['completed_loans'] = user_loans.filter(status='completed').count()
        context['can_apply'] = not user_loans.filter(
            status__in=['pending', 'active', 'approved', 'disbursed']
        ).exists()
    
    return render(request, 'loans/enhanced_apply.html', context)
