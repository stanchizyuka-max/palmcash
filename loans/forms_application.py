from django import forms
from .models import LoanApplication


class LoanApplicationForm(forms.ModelForm):
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
