from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Loan, LoanType, LoanDocument
import os

class LoanApplicationForm(forms.ModelForm):
    # Dynamic term field - will be either days or weeks based on loan type
    term = forms.IntegerField(
        min_value=1,
        help_text="Loan term (days or weeks based on loan type)",
        widget=forms.NumberInput(attrs={'min': '1'})
    )
    
    class Meta:
        model = Loan
        fields = [
            'loan_type', 'principal_amount', 'purpose'
        ]
        widgets = {
            'purpose': forms.Textarea(attrs={'rows': 4}),
            'principal_amount': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['loan_type'].queryset = LoanType.objects.filter(is_active=True)
        
        # Add CSS classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        loan_type = cleaned_data.get('loan_type')
        principal_amount = cleaned_data.get('principal_amount')
        term = cleaned_data.get('term')
        
        if loan_type and principal_amount:
            if principal_amount < loan_type.min_amount:
                raise forms.ValidationError(
                    f'Minimum loan amount for {loan_type.name} is K{loan_type.min_amount:,.0f}'
                )
            if principal_amount > loan_type.max_amount:
                raise forms.ValidationError(
                    f'Maximum loan amount for {loan_type.name} is K{loan_type.max_amount:,.0f}'
                )
        
        # Validate term based on loan type frequency
        if loan_type and term:
            if loan_type.repayment_frequency == 'daily':
                min_term = loan_type.min_term_days or 1
                max_term = loan_type.max_term_days or 365
                unit = 'days'
            else:  # weekly
                min_term = loan_type.min_term_weeks or 1
                max_term = loan_type.max_term_weeks or 52
                unit = 'weeks'
            
            if term < min_term:
                raise forms.ValidationError(
                    f'Minimum term for {loan_type.name} is {min_term} {unit}'
                )
            if term > max_term:
                raise forms.ValidationError(
                    f'Maximum term for {loan_type.name} is {max_term} {unit}'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        loan = super().save(commit=False)
        
        # Set interest rate from loan type if not already set
        if loan.loan_type and not loan.interest_rate:
            loan.interest_rate = loan.loan_type.interest_rate
        
        # Set repayment frequency from loan type
        if loan.loan_type:
            loan.repayment_frequency = loan.loan_type.repayment_frequency
        
        # Set term based on frequency
        term = self.cleaned_data.get('term')
        if term:
            if loan.repayment_frequency == 'daily':
                loan.term_days = term
                loan.term_weeks = None
            else:  # weekly
                loan.term_weeks = term
                loan.term_days = None
        
        if commit:
            loan.save()
        return loan


class LoanDocumentForm(forms.ModelForm):
    class Meta:
        model = LoanDocument
        fields = ['document_type', 'document_file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional description of the document'}),
            'document_file': forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Add help text
        self.fields['document_file'].help_text = 'Accepted formats: PDF, JPG, PNG, DOC, DOCX (Max size: 10MB)'
    
    def clean_document_file(self):
        file = self.cleaned_data.get('document_file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 10MB')
            
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    f'File type not allowed. Accepted formats: {", ".join(allowed_extensions)}'
                )
        
        return file


class DocumentVerificationForm(forms.ModelForm):
    """Form for loan officers to verify documents"""
    class Meta:
        model = LoanDocument
        fields = ['is_verified', 'verification_notes']
        widgets = {
            'verification_notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['verification_notes'].widget.attrs.update({'class': 'form-control'})
        self.fields['is_verified'].widget.attrs.update({'class': 'form-check-input'})