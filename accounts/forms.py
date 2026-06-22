from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()


def validate_zambian_phone(value):
    """
    Validate Zambian phone numbers.
    Accepts Zambian mobile formats:
    - 095, 096, 097 (Zamtel, MTN, Airtel)
    - 076, 077 (Zamtel, MTN)
    - 055, 057 (Zamtel, Airtel - new prefixes)
    Also accepts with country code: +260 or 260
    """
    # Remove spaces, dashes, and parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', str(value))
    
    # Zambian mobile prefixes: 095, 096, 097, 076, 077, 055, 057
    # Pattern explanation:
    # ^0(95|96|97|76|77|55|57)\d{7}$ - starts with 0, then valid prefix, then 7 more digits
    patterns = [
        r'^0(95|96|97|76|77|55|57)\d{7}$',        # 0955123456, 0965123456, 0975123456, 0765123456, 0775123456, 0555123456, 0575123456
        r'^(95|96|97|76|77|55|57)\d{7}$',         # 955123456 (without leading 0)
        r'^\+260(95|96|97|76|77|55|57)\d{7}$',    # +260955123456
        r'^260(95|96|97|76|77|55|57)\d{7}$',      # 260955123456
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return cleaned
    
    raise ValidationError(
        'Invalid phone number. Please enter a valid Zambian mobile number. '
        'Examples: 0955123456, 0965123456, 0975123456, 0765123456, 0775123456, 0555123456, 0575123456'
    )


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(
        max_length=20, 
        required=True, 
        label="Primary Phone Number",
        validators=[validate_zambian_phone],
        help_text="Enter phone number starting with 05, 07, or 09"
    )
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    national_id = forms.CharField(max_length=50, required=True, label="National ID Number")
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'national_id', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class BorrowerRegistrationForm(forms.ModelForm):
    """Step 1: Basic info for borrower registration"""
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        validators=[validate_zambian_phone],
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 0955123456, 0977123456', 
            'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500'
        }),
        help_text="Enter phone number starting with 05, 07, or 09"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max date dynamically for date_of_birth to prevent future dates
        from datetime import date
        if 'date_of_birth' in self.fields:
            self.fields['date_of_birth'].widget.attrs['max'] = date.today().isoformat()

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'gender', 'marital_status', 'national_id',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500'}),
            'gender': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 bg-white'}),
            'marital_status': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 bg-white'}),
            'national_id': forms.TextInput(attrs={'placeholder': 'NRC Number e.g. 123456/78/9', 'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500'}),
        }


class BorrowerDetailsForm(forms.ModelForm):
    """Step 2: Full borrower details"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max date dynamically for guarantor DOB fields to prevent future dates
        from datetime import date
        today = date.today().isoformat()
        if 'guarantor1_dob' in self.fields:
            self.fields['guarantor1_dob'].widget.attrs['max'] = today
        if 'guarantor2_dob' in self.fields:
            self.fields['guarantor2_dob'].widget.attrs['max'] = today

    class Meta:
        model = User
        fields = [
            'address', 'province', 'district', 'residential_area',
            'employment_status', 'employer_name', 'monthly_income',
            'business_name', 'business_address',
            'reference1_name', 'reference1_phone', 'reference1_relationship',
            'reference2_name', 'reference2_phone', 'reference2_relationship',
            'guarantor1_name', 'guarantor1_dob', 'guarantor1_nrc', 'guarantor1_phone', 'guarantor1_address', 'guarantor1_relationship',
            'guarantor2_name', 'guarantor2_dob', 'guarantor2_nrc', 'guarantor2_phone', 'guarantor2_address', 'guarantor2_relationship',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Physical address'}),
            'province': forms.TextInput(attrs={'placeholder': 'Province'}),
            'district': forms.TextInput(attrs={'placeholder': 'District'}),
            'residential_area': forms.TextInput(attrs={'placeholder': 'Residential area / compound'}),
            'employment_status': forms.Select(),
            'employer_name': forms.TextInput(attrs={'placeholder': 'Employer / Business name'}),
            'monthly_income': forms.NumberInput(attrs={'placeholder': 'Monthly income (K)', 'step': '0.01'}),
            'business_name': forms.TextInput(attrs={'placeholder': 'Business name (if self-employed)'}),
            'business_address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Business address'}),
            'reference1_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'reference1_phone': forms.TextInput(attrs={'placeholder': 'Phone number'}),
            'reference1_relationship': forms.TextInput(attrs={'placeholder': 'Relationship'}),
            'reference2_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'reference2_phone': forms.TextInput(attrs={'placeholder': 'Phone number'}),
            'reference2_relationship': forms.TextInput(attrs={'placeholder': 'Relationship'}),
            'guarantor1_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'guarantor1_dob': forms.DateInput(attrs={'type': 'date'}),
            'guarantor1_nrc': forms.TextInput(attrs={'placeholder': 'e.g. 123456/78/9'}),
            'guarantor1_phone': forms.TextInput(attrs={'placeholder': 'Phone number'}),
            'guarantor1_address': forms.TextInput(attrs={'placeholder': 'Current address'}),
            'guarantor1_relationship': forms.TextInput(attrs={'placeholder': 'e.g. Spouse, Sibling, Friend'}),
            'guarantor2_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'guarantor2_dob': forms.DateInput(attrs={'type': 'date'}),
            'guarantor2_nrc': forms.TextInput(attrs={'placeholder': 'e.g. 123456/78/9'}),
            'guarantor2_phone': forms.TextInput(attrs={'placeholder': 'Phone number'}),
            'guarantor2_address': forms.TextInput(attrs={'placeholder': 'Current address'}),
            'guarantor2_relationship': forms.TextInput(attrs={'placeholder': 'e.g. Spouse, Sibling, Friend'}),
        }


class BorrowerPhotoUploadForm(forms.Form):
    """Simple form for uploading borrower photos"""
    nrc_front = forms.ImageField(
        label='NRC Front',
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    nrc_back = forms.ImageField(
        label='NRC Back',
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    live_selfie = forms.ImageField(
        label='Live Selfie',
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with better styling"""
    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "No account found with this email address. Please check and try again."
            )
        return email


class CustomSetPasswordForm(SetPasswordForm):
    """Custom set password form with better styling"""
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text="Your password must contain at least 8 characters and cannot be entirely numeric."
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text="Enter the same password as before, for verification."
    )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'date_of_birth']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class LoanOfficerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}))
    phone_number = forms.CharField(
        max_length=20, 
        required=True, 
        validators=[validate_zambian_phone],
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 0955123456, 0977123456', 
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        help_text="Enter phone number starting with 05, 07, or 09"
    )
    national_id = forms.CharField(max_length=50, required=True, label='NRC Number', widget=forms.TextInput(attrs={'placeholder': 'e.g. 123456/78/9', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'phone_number', 'national_id', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ('password1', 'password2'):
            self.fields[f].widget.attrs.update({'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'loan_officer'
        user.is_active = False
        user.is_approved = False
        user.phone_number = self.cleaned_data['phone_number']
        user.national_id = self.cleaned_data['national_id']
        if commit:
            user.save()
        return user
