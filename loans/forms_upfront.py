from django import forms
from .models import Loan
from decimal import Decimal

class UpfrontPaymentForm(forms.ModelForm):
    """Form for recording upfront payment"""
    
    payment_reference = forms.CharField(
        max_length=100,
        required=True,
        help_text="Enter your payment reference number or transaction ID",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., MTN-123456789 or Airtel-987654321'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=[
            ('mobile_money', 'Mobile Money (MTN/Airtel)'),
            ('bank_transfer', 'Bank Transfer'),
            ('cash', 'Cash Deposit'),
            ('other', 'Other'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_proof = forms.FileField(
        required=False,
        help_text="Upload payment receipt or proof (optional)",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf'
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional notes about the payment...'
        })
    )
    
    class Meta:
        model = Loan
        fields = []
    
    def __init__(self, *args, **kwargs):
        self.loan = kwargs.pop('loan', None)
        super().__init__(*args, **kwargs)
        
        if self.loan:
            self.fields['amount_paid'] = forms.DecimalField(
                max_digits=12,
                decimal_places=2,
                initial=self.loan.upfront_payment_required,
                min_value=self.loan.upfront_payment_required,
                help_text=f"Minimum payment: K{self.loan.upfront_payment_required:,.2f} (10% of K{self.loan.principal_amount:,.2f})",
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': str(self.loan.upfront_payment_required)
                })
            )
    
    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        if self.loan and amount < self.loan.upfront_payment_required:
            raise forms.ValidationError(
                f"Payment must be at least K{self.loan.upfront_payment_required:,.2f} (10% of loan amount)"
            )
        return amount
