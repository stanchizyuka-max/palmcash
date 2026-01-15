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
        try:
            # Get cleaned data
            cleaned_data = form.cleaned_data
            
            # Create loan directly without using save_loan method
            import uuid
            from decimal import Decimal
            
            loan_type = cleaned_data.get('loan_type')
            principal_amount = cleaned_data.get('principal_amount')
            term = cleaned_data.get('term')
            
            # Create loan
            loan = Loan(
                borrower=self.request.user,
                application_number=f"LA-{uuid.uuid4().hex[:8].upper()}",
                loan_type=loan_type,
                principal_amount=principal_amount,
                purpose=cleaned_data.get('purpose', 'Not specified'),
                status='pending',
                repayment_frequency=loan_type.repayment_frequency if loan_type else 'weekly',
                term_weeks=term if loan_type and loan_type.repayment_frequency == 'weekly' else None,
                term_days=term if loan_type and loan_type.repayment_frequency == 'daily' else None,
            )
            
            # Calculate payment amount
            if loan_type and principal_amount and term:
                interest_rate = loan_type.interest_rate / Decimal('100')
                total_interest = principal_amount * interest_rate
                total_repayment = principal_amount + total_interest
                loan.payment_amount = total_repayment / term
            else:
                loan.payment_amount = principal_amount if principal_amount else Decimal('0')
            
            loan.save()
            
            # Update user profile
            self.request.user.first_name = cleaned_data.get('first_name', '')
            self.request.user.last_name = cleaned_data.get('last_name', '')
            self.request.user.email = cleaned_data.get('email', '')
            self.request.user.residential_address = cleaned_data.get('residential_address', '')
            self.request.user.residential_duration = cleaned_data.get('residential_duration')
            self.request.user.employment_status = cleaned_data.get('employment_status', '')
            self.request.user.employer_name = cleaned_data.get('employer_name', '')
            self.request.user.employer_address = cleaned_data.get('employer_address', '')
            self.request.user.employment_duration = cleaned_data.get('employment_duration')
            self.request.user.monthly_income = cleaned_data.get('monthly_income')
            self.request.user.business_name = cleaned_data.get('business_name', '')
            self.request.user.business_address = cleaned_data.get('business_address', '')
            self.request.user.business_duration = cleaned_data.get('business_duration')
            self.request.user.reference1_name = cleaned_data.get('reference1_name', '')
            self.request.user.reference1_phone = cleaned_data.get('reference1_phone', '')
            self.request.user.reference1_relationship = cleaned_data.get('reference1_relationship', '')
            self.request.user.reference2_name = cleaned_data.get('reference2_name', '')
            self.request.user.reference2_phone = cleaned_data.get('reference2_phone', '')
            self.request.user.reference2_relationship = cleaned_data.get('reference2_relationship', '')
            self.request.user.save()
            
            messages.success(
                self.request,
                f'Loan application submitted successfully! Application Number: {loan.application_number}. '
                'Please upload your required documents to complete the application process.'
            )
            
            return redirect('documents:upload')
        except Exception as e:
            import traceback
            print(f"Error in form_valid: {e}")
            print(traceback.format_exc())
            messages.error(self.request, f'Error submitting application: {str(e)}')
            return self.form_invalid(form)
    
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
            try:
                # Get cleaned data
                cleaned_data = form.cleaned_data
                
                # Create loan directly
                import uuid
                from decimal import Decimal
                
                loan_type = cleaned_data.get('loan_type')
                principal_amount = cleaned_data.get('principal_amount')
                term = cleaned_data.get('term')
                
                # Create loan
                loan = Loan(
                    borrower=request.user,
                    application_number=f"LA-{uuid.uuid4().hex[:8].upper()}",
                    loan_type=loan_type,
                    principal_amount=principal_amount,
                    purpose=cleaned_data.get('purpose', 'Not specified'),
                    status='pending',
                    repayment_frequency=loan_type.repayment_frequency if loan_type else 'weekly',
                    term_weeks=term if loan_type and loan_type.repayment_frequency == 'weekly' else None,
                    term_days=term if loan_type and loan_type.repayment_frequency == 'daily' else None,
                )
                
                # Calculate payment amount
                if loan_type and principal_amount and term:
                    interest_rate = loan_type.interest_rate / Decimal('100')
                    total_interest = principal_amount * interest_rate
                    total_repayment = principal_amount + total_interest
                    loan.payment_amount = total_repayment / term
                else:
                    loan.payment_amount = principal_amount if principal_amount else Decimal('0')
                
                loan.save()
                
                # Update user profile
                request.user.first_name = cleaned_data.get('first_name', '')
                request.user.last_name = cleaned_data.get('last_name', '')
                request.user.email = cleaned_data.get('email', '')
                request.user.residential_address = cleaned_data.get('residential_address', '')
                request.user.residential_duration = cleaned_data.get('residential_duration')
                request.user.employment_status = cleaned_data.get('employment_status', '')
                request.user.employer_name = cleaned_data.get('employer_name', '')
                request.user.employer_address = cleaned_data.get('employer_address', '')
                request.user.employment_duration = cleaned_data.get('employment_duration')
                request.user.monthly_income = cleaned_data.get('monthly_income')
                request.user.business_name = cleaned_data.get('business_name', '')
                request.user.business_address = cleaned_data.get('business_address', '')
                request.user.business_duration = cleaned_data.get('business_duration')
                request.user.reference1_name = cleaned_data.get('reference1_name', '')
                request.user.reference1_phone = cleaned_data.get('reference1_phone', '')
                request.user.reference1_relationship = cleaned_data.get('reference1_relationship', '')
                request.user.reference2_name = cleaned_data.get('reference2_name', '')
                request.user.reference2_phone = cleaned_data.get('reference2_phone', '')
                request.user.reference2_relationship = cleaned_data.get('reference2_relationship', '')
                request.user.save()
                
                messages.success(
                    request,
                    f'Loan application submitted successfully! Application Number: {loan.application_number}. '
                    'Please upload your required documents to complete the application process.'
                )
                
                return redirect('documents:upload')
            except Exception as e:
                import traceback
                print(f"Error: {e}")
                print(traceback.format_exc())
                messages.error(request, f'Error submitting application: {str(e)}')
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
