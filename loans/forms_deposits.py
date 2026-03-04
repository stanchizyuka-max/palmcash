"""
Forms for security deposit management
"""
from django import forms
from decimal import Decimal
from django.core.exceptions import ValidationError

from .models import SecurityDeposit


class SecurityDepositForm(forms.ModelForm):
    """Form for recording security deposit payments"""
    
    class Meta:
        model = SecurityDeposit
        fields = ['paid_amount', 'payment_method', 'receipt_number', 'notes']
        widgets = {
            'paid_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'required': True,
                'placeholder': 'Enter amount paid'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Receipt or transaction reference'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            })
        }
    
    def __init__(self, *args, loan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.loan = loan
        
        if loan:
            # Set the required amount as help text
            required_amount = loan.upfront_payment_required or (loan.principal_amount * Decimal('0.10'))
            self.fields['paid_amount'].help_text = f'Required: {required_amount}'
    
    def clean_paid_amount(self):
        """Validate paid amount is positive"""
        paid_amount = self.cleaned_data.get('paid_amount')
        if paid_amount is not None and paid_amount <= 0:
            raise ValidationError('Payment amount must be greater than zero.')
        return paid_amount
