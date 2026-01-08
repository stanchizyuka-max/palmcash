from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .models import Loan, LoanType, LoanDocument
import re
from datetime import date

class EnhancedLoanApplicationForm(forms.ModelForm):
    """
    Comprehensive loan application form with all required fields
    """
    
    # Personal Information
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your last name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your email address'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your phone number (e.g., 0976123456)'
        })
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'date'
        })
    )
    
    # Address Information
    residential_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your residential address',
            'rows': 3
        })
    )
    
    residential_duration = forms.IntegerField(
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
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    employer_name = forms.CharField(
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
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your monthly income',
            'step': '0.01'
        })
    )
    
    # Business Information (if self-employed/business owner)
    business_name = forms.CharField(
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
        empty_label="Select loan type",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    principal_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter loan amount',
            'step': '0.01'
        })
    )
    
    purpose = forms.ChoiceField(
        choices=[
            ('', 'Select loan purpose'),
            ('personal', 'Personal'),
            ('business', 'Business'),
            ('education', 'Education'),
            ('medical', 'Medical'),
            ('emergency', 'Emergency'),
            ('home_improvement', 'Home Improvement'),
            ('debt_consolidation', 'Debt Consolidation'),
            ('other', 'Other'),
        ],
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
    
    # Dynamic term field - will be either days or weeks based on loan type
    term = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Loan term (days or weeks based on loan type)',
            'min': '1'
        })
    )
    
    # Collateral Information
    has_collateral = forms.ChoiceField(
        choices=[
            ('', 'Do you have collateral?'),
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    collateral_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Type of collateral (e.g., Vehicle, Property, etc.)'
        })
    )
    
    collateral_value = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Estimated collateral value',
            'step': '0.01'
        })
    )
    
    # References
    reference1_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 1 Full Name'
        })
    )
    
    reference1_phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 1 Phone Number'
        })
    )
    
    reference1_relationship = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 1 Relationship (e.g., Friend, Family, Colleague)'
        })
    )
    
    reference2_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 2 Full Name (Optional)'
        })
    )
    
    reference2_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Reference 2 Phone Number (Optional)'
        })
    )
    
    reference2_relationship = forms.CharField(
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
    
    class Meta:
        model = Loan
        fields = [
            'loan_type', 'principal_amount', 'purpose'
        ]
    
    def __init__(self, *args, **kwargs):
        # Extract user from kwargs before calling super().__init__
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill user information if available
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
        
        # Make certain fields required based on employment status
        self.fields['employer_name'].required = False
        self.fields['employer_address'].required = False
        self.fields['employment_duration'].required = False
        self.fields['business_name'].required = False
        self.fields['business_address'].required = False
        self.fields['business_duration'].required = False
        self.fields['collateral_type'].required = False
        self.fields['collateral_value'].required = False
        self.fields['reference2_name'].required = False
        self.fields['reference2_phone'].required = False
        self.fields['reference2_relationship'].required = False
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove any non-digit characters
            phone_digits = re.sub(r'\D', '', phone)
            
            # Validate Zambian phone number format
            if not (phone_digits.startswith('09') and len(phone_digits) == 10):
                raise ValidationError(
                    'Please enter a valid Zambian phone number (e.g., 0976123456)'
                )
            
            return phone_digits
    
    def clean_reference1_phone(self):
        phone = self.cleaned_data.get('reference1_phone')
        if phone:
            phone_digits = re.sub(r'\D', '', phone)
            if not (phone_digits.startswith('09') and len(phone_digits) == 10):
                raise ValidationError(
                    'Please enter a valid Zambian phone number for reference 1'
                )
            return phone_digits
    
    def clean_reference2_phone(self):
        phone = self.cleaned_data.get('reference2_phone')
        if phone:
            phone_digits = re.sub(r'\D', '', phone)
            if not (phone_digits.startswith('09') and len(phone_digits) == 10):
                raise ValidationError(
                    'Please enter a valid Zambian phone number for reference 2'
                )
            return phone_digits
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if age < 18:
                raise ValidationError('You must be at least 18 years old to apply for a loan')
            
            if age > 70:
                raise ValidationError('Applicants must be 70 years old or younger')
        
        return dob
    
    def clean(self):
        cleaned_data = super().clean()
        loan_type = cleaned_data.get('loan_type')
        principal_amount = cleaned_data.get('principal_amount')
        term = cleaned_data.get('term')
        employment_status = cleaned_data.get('employment_status')
        has_collateral = cleaned_data.get('has_collateral')
        
        # Validate loan amount against loan type limits
        if loan_type and principal_amount:
            if principal_amount < loan_type.min_amount:
                raise ValidationError(
                    f'Minimum loan amount for {loan_type.name} is K{loan_type.min_amount:,.0f}'
                )
            if principal_amount > loan_type.max_amount:
                raise ValidationError(
                    f'Maximum loan amount for {loan_type.name} is K{loan_type.max_amount:,.0f}'
                )
        
        # Validate term based on loan type frequency
        if loan_type and term:
            if loan_type.repayment_frequency == 'daily':
                if loan_type.min_term_days and term < loan_type.min_term_days:
                    raise ValidationError(
                        f'Minimum term for {loan_type.name} is {loan_type.min_term_days} days'
                    )
                if loan_type.max_term_days and term > loan_type.max_term_days:
                    raise ValidationError(
                        f'Maximum term for {loan_type.name} is {loan_type.max_term_days} days'
                    )
            else:  # weekly
                if loan_type.min_term_weeks and term < loan_type.min_term_weeks:
                    raise ValidationError(
                        f'Minimum term for {loan_type.name} is {loan_type.min_term_weeks} weeks'
                    )
                if loan_type.max_term_weeks and term > loan_type.max_term_weeks:
                    raise ValidationError(
                        f'Maximum term for {loan_type.name} is {loan_type.max_term_weeks} weeks'
                    )
        
        # Require employment details if employed
        if employment_status == 'employed':
            if not cleaned_data.get('employer_name'):
                raise ValidationError('Employer name is required when employed')
            if not cleaned_data.get('employment_duration'):
                raise ValidationError('Employment duration is required when employed')
        
        # Require business details if self-employed or business owner
        if employment_status in ['self_employed', 'business_owner']:
            if not cleaned_data.get('business_name'):
                raise ValidationError('Business name is required when self-employed or business owner')
            if not cleaned_data.get('business_duration'):
                raise ValidationError('Business duration is required when self-employed or business owner')
        
        # Require collateral details if has collateral
        if has_collateral == 'yes':
            if not cleaned_data.get('collateral_type'):
                raise ValidationError('Collateral type is required when you have collateral')
            if not cleaned_data.get('collateral_value'):
                raise ValidationError('Collateral value is required when you have collateral')
        
        return cleaned_data
