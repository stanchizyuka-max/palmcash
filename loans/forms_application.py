from django import forms
from .models import LoanApplication
from datetime import date


class LoanApplicationForm(forms.ModelForm):
    # Add application_date field for backdating
    application_date = forms.DateField(
        required=False,
        initial=date.today,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'max': date.today().isoformat(),  # Prevent future dates
        }),
        help_text='Date when the application was actually made (defaults to today)'
    )
    
    class Meta:
        model = LoanApplication
        fields = ['borrower', 'loan_amount', 'repayment_frequency', 'duration_days', 'purpose', 'group']
        widgets = {
            'borrower': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'loan_amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Loan amount',
                'step': '0.01'
            }),
            'repayment_frequency': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'onchange': 'updateInterestRate(this.value)',
            }),
            'duration_days': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Duration (days for daily, weeks for weekly)',
                'min': '1'
            }),
            'purpose': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Loan purpose'
            }),
            'group': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
        }
    
    def clean_application_date(self):
        application_date = self.cleaned_data.get('application_date')
        
        # If not provided, default to today
        if not application_date:
            application_date = date.today()
        
        # Prevent future dates
        if application_date > date.today():
            raise forms.ValidationError('Application date cannot be in the future.')
        
        return application_date
    
    def clean(self):
        cleaned_data = super().clean()
        repayment_frequency = cleaned_data.get('repayment_frequency')
        duration_days = cleaned_data.get('duration_days')
        
        # Convert weeks to days for weekly loans
        # User enters weeks, but we store as days internally
        if repayment_frequency == 'weekly' and duration_days:
            # User entered weeks, convert to days
            cleaned_data['duration_days'] = duration_days * 7
        
        return cleaned_data
