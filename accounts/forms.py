from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=20, required=True, label="Primary Phone Number")
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

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email', 'phone_number',
            'date_of_birth', 'gender', 'marital_status', 'national_id',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(),
            'marital_status': forms.Select(),
            'national_id': forms.TextInput(attrs={'placeholder': 'NRC Number e.g. 123456/78/9'}),
        }


class BorrowerDetailsForm(forms.ModelForm):
    """Step 2: Full borrower details"""

    class Meta:
        model = User
        fields = [
            'address', 'province', 'district', 'residential_area',
            'employment_status', 'employer_name', 'monthly_income',
            'business_name', 'business_address',
            'reference1_name', 'reference1_phone', 'reference1_relationship',
            'reference2_name', 'reference2_phone', 'reference2_relationship',
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
