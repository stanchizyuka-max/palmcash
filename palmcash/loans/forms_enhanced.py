from django import forms
from django.core.exceptions import ValidationError
from .models import Loan, LoanType
import re
from datetime import date

class EnhancedLoanApplicationForm(forms.Form):
    """
    Comprehensive loan application form - NOT a ModelForm
    All fields are regular form fields, not model fields
    """
    
    # Personal Information
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your last name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your email address'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your phone number (e.g., 0976123456)'
        })
    )
    
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'date'
        })
    )
    
    # Address Information
    residential_address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your residential address',
            'rows': 3
        })
    )
    
    residential_duration = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Years at current address',
            'min': '0'
        })
    )
    
    # Employment Information
    employment_status = forms.ChoiceField(
        choices=[
            ('', 'Select employment status'),
            ('employed', 'Employed'),
            ('self_employed', 'Self Employed'),
            ('business_owner', 'Business Owner'),
            ('unemployed', 'Unemployed'),
            ('student', 'Student'),
            ('retired', 'Retired'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    employer_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter employer name'
        })
    )
    
    employer_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter employer address',
            'rows': 3
        })
    )
    
    employment_duration = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Years with current employer',
            'min': '0'
        })
    )
    
    monthly_income = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your monthly income',
            'step': '0.01'
        })
    )
    
    # Business Information
    business_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter business name'
        })
    )
    
    business_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter business address',
            'rows': 3
        })
    )
    
    business_duration = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Years in business',
            'min': '0'
        })
    )
    
    # Loan Details
    loan_type = forms.ModelChoiceField(
        queryset=LoanType.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    principal_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter loan amount',
            'step': '0.01'
        })
    )
    
    purpose = forms.ChoiceField(
        choices=[
            ('personal', 'Personal'),
            ('business', 'Business'),
            ('education', 'Education'),
            ('medical', 'Medical'),
            ('emergency', 'Emergency'),
            ('home_improvement', 'Home Improvement'),
            ('debt_consolidation', 'Debt Consolidation'),
            ('other', 'Other'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    purpose_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Describe the purpose of this loan',
            'rows': 4
        })
    )
    
    term = forms.IntegerField(
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Loan term (days or weeks based on loan type)',
            'min': '1'
        })
    )
    
    # Collateral Information
    has_collateral = forms.ChoiceField(
        choices=[
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    collateral_type = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Type of collateral (e.g., Vehicle, Property, etc.)'
        })
    )
    
    collateral_value = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Estimated collateral value',
            'step': '0.01'
        })
    )
    
    # References
    reference1_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 1 Full Name'
        })
    )
    
    reference1_phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 1 Phone Number'
        })
    )
    
    reference1_relationship = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 1 Relationship (e.g., Friend, Family, Colleague)'
        })
    )
    
    reference2_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 2 Full Name (Optional)'
        })
    )
    
    reference2_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 2 Phone Number (Optional)'
        })
    )
    
    reference2_relationship = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 2 Relationship (Optional)'
        })
    )
    
    # Declarations
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
        })
    )
    
    declare_true_info = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill user information if available
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        # Just return the phone as-is, don't validate format
        return phone
    
    def clean_reference1_phone(self):
        phone = self.cleaned_data.get('reference1_phone')
        # Just return the phone as-is, don't validate format
        return phone
    
    def clean_reference2_phone(self):
        phone = self.cleaned_data.get('reference2_phone')
        # Just return the phone as-is, don't validate format
        return phone
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise ValidationError('You must be at least 18 years old to apply for a loan')
        return dob
    
    def clean(self):
        cleaned_data = super().clean()
        # Don't validate anything - just return the data
        return cleaned_data
    
    def save_loan(self, borrower):
        """
        Create and save a Loan instance from the form data
        """
        import uuid
        from decimal import Decimal
        
        cleaned_data = self.cleaned_data
        loan_type = cleaned_data.get('loan_type')
        principal_amount = cleaned_data.get('principal_amount')
        term = cleaned_data.get('term')
        
        # Create loan instance
        loan = Loan()
        loan.borrower = borrower
        loan.application_number = f"LA-{uuid.uuid4().hex[:8].upper()}"
        loan.loan_type = loan_type
        loan.principal_amount = principal_amount
        loan.purpose = cleaned_data.get('purpose', 'Not specified')
        loan.status = 'pending'  # Set initial status
        
        # Set repayment frequency and terms
        if loan_type and term:
            loan.repayment_frequency = loan_type.repayment_frequency
            
            if loan_type.repayment_frequency == 'daily':
                loan.term_days = term
                loan.term_weeks = None
            else:  # weekly
                loan.term_weeks = term
                loan.term_days = None
            
            # Calculate payment amount
            interest_rate = loan_type.interest_rate / Decimal('100')
            total_interest = principal_amount * interest_rate
            total_repayment = principal_amount + total_interest
            
            if loan_type.repayment_frequency == 'daily':
                loan.payment_amount = total_repayment / term
            else:
                loan.payment_amount = total_repayment / term
        else:
            # Fallback values if loan_type or term is missing
            loan.repayment_frequency = 'weekly'
            loan.term_weeks = 1
            loan.payment_amount = principal_amount if principal_amount else Decimal('0')
        
        # Set collateral info
        if cleaned_data.get('has_collateral') == 'yes':
            loan.collateral_description = cleaned_data.get('collateral_type', '')
            loan.collateral_value = cleaned_data.get('collateral_value')
        
        try:
            loan.save()
        except Exception as e:
            print(f"Error saving loan: {e}")
            raise
        
        # Update user profile with all the information
        borrower.first_name = cleaned_data.get('first_name', '')
        borrower.last_name = cleaned_data.get('last_name', '')
        borrower.email = cleaned_data.get('email', '')
        borrower.residential_address = cleaned_data.get('residential_address', '')
        borrower.residential_duration = cleaned_data.get('residential_duration')
        
        borrower.employment_status = cleaned_data.get('employment_status', '')
        borrower.employer_name = cleaned_data.get('employer_name', '')
        borrower.employer_address = cleaned_data.get('employer_address', '')
        borrower.employment_duration = cleaned_data.get('employment_duration')
        borrower.monthly_income = cleaned_data.get('monthly_income')
        
        borrower.business_name = cleaned_data.get('business_name', '')
        borrower.business_address = cleaned_data.get('business_address', '')
        borrower.business_duration = cleaned_data.get('business_duration')
        
        borrower.reference1_name = cleaned_data.get('reference1_name', '')
        borrower.reference1_phone = cleaned_data.get('reference1_phone', '')
        borrower.reference1_relationship = cleaned_data.get('reference1_relationship', '')
        borrower.reference2_name = cleaned_data.get('reference2_name', '')
        borrower.reference2_phone = cleaned_data.get('reference2_phone', '')
        borrower.reference2_relationship = cleaned_data.get('reference2_relationship', '')
        
        try:
            borrower.save()
        except Exception as e:
            print(f"Error saving borrower: {e}")
            raise
        
        return loan
