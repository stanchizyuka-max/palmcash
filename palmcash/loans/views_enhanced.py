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
        
        # Check if user has verified documents
        has_verified_documents = ClientVerification.objects.filter(
            client=request.user,
            status='verified'
        ).exists()
        
        if not has_verified_documents:
            messages.error(
                request,
                'You must upload and have at least one document verified by an administrator '
                'before you can apply for a loan. Please upload your documents first.'
            )
            return redirect('documents:list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Set the borrower
        form.instance.borrower = self.request.user
        
        # Generate application number
        form.instance.application_number = f"LA-{uuid.uuid4().hex[:8].upper()}"
        
        # Set repayment frequency and terms based on loan type
        loan_type = form.cleaned_data['loan_type']
        term = form.cleaned_data['term']
        
        form.instance.repayment_frequency = loan_type.repayment_frequency
        
        if loan_type.repayment_frequency == 'daily':
            form.instance.term_days = term
            form.instance.term_weeks = None
        else:  # weekly
            form.instance.term_weeks = term
            form.instance.term_days = None
        
        # Calculate payment amount (principal + interest) divided by term
        principal = form.cleaned_data['principal_amount']
        interest_rate = loan_type.interest_rate / 100
        total_interest = principal * interest_rate
        total_repayment = principal + total_interest
        
        if loan_type.repayment_frequency == 'daily':
            form.instance.payment_amount = total_repayment / term
        else:  # weekly
            form.instance.payment_amount = total_repayment / term
        
        # Save the loan application
        response = super().form_valid(form)
        
        # Store application data in session for document upload
        self.request.session['loan_application_data'] = {
            'application_number': form.instance.application_number,
            'principal_amount': str(form.instance.principal_amount),
            'loan_type': form.instance.loan_type.name,
            'purpose': form.cleaned_data.get('purpose', ''),
            'purpose_description': form.cleaned_data.get('purpose_description', ''),
        }
        
        messages.success(
            self.request,
            f'Loan application submitted successfully! Application Number: {form.instance.application_number}. '
            'Please upload your required documents to complete the application process.'
        )
        
        return response
    
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
    
    # Check if user has verified documents
    has_verified_documents = ClientVerification.objects.filter(
        client=request.user,
        status='verified'
    ).exists()
    
    if not has_verified_documents:
        messages.error(
            request,
            'You must upload and have at least one document verified by an administrator '
            'before you can apply for a loan. Please upload your documents first.'
        )
        return redirect('documents:list')
    
    if request.method == 'POST':
        form = EnhancedLoanApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            # Create loan application
            loan = form.save(commit=False)
            loan.borrower = request.user
            loan.application_number = f"LA-{uuid.uuid4().hex[:8].upper()}"
            
            # Set repayment frequency and terms
            loan_type = form.cleaned_data['loan_type']
            term = form.cleaned_data['term']
            
            loan.repayment_frequency = loan_type.repayment_frequency
            
            if loan_type.repayment_frequency == 'daily':
                loan.term_days = term
                loan.term_weeks = None
            else:  # weekly
                loan.term_weeks = term
                loan.term_days = None
            
            # Calculate payment amount
            principal = form.cleaned_data['principal_amount']
            interest_rate = loan_type.interest_rate / 100
            total_interest = principal * interest_rate
            total_repayment = principal + total_interest
            
            if loan_type.repayment_frequency == 'daily':
                loan.payment_amount = total_repayment / term
            else:  # weekly
                loan.payment_amount = total_repayment / term
            
            loan.save()
            
            # Store application data in session
            request.session['loan_application_data'] = {
                'application_number': loan.application_number,
                'principal_amount': str(loan.principal_amount),
                'loan_type': loan.loan_type.name,
                'purpose': form.cleaned_data.get('purpose', ''),
                'purpose_description': form.cleaned_data.get('purpose_description', ''),
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
        'has_verified_documents': has_verified_documents,
    }
    
    if request.user.role == 'borrower':
        user_loans = Loan.objects.filter(borrower=request.user)
        context['user_loans'] = user_loans
        context['completed_loans'] = user_loans.filter(status='completed').count()
        context['can_apply'] = not user_loans.filter(
            status__in=['pending', 'active', 'approved', 'disbursed']
        ).exists()
    
    return render(request, 'loans/enhanced_apply.html', context)
