from django import forms
from django.utils import timezone
from .models import Payment
from loans.models import Loan


class RecordPaymentForm(forms.Form):
    loan = forms.ModelChoiceField(
        queryset=Loan.objects.none(),
        label='Loan / Borrower',
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'})
    )
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2,
        label='Amount (K)',
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'step': '0.01', 'min': '0.01'})
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('cash', 'Cash'),
            ('mtn', 'MTN Mobile Money'),
            ('airtel', 'Airtel Money'),
            ('bank_transfer', 'Bank Transfer'),
        ],
        label='Payment Method',
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'})
    )
    reference_number = forms.CharField(
        max_length=100, required=False,
        label='Reference Number',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'placeholder': 'Transaction ID / Receipt number'})
    )
    payment_date = forms.DateField(
        label='Payment Date',
        widget=forms.DateInput(attrs={'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'type': 'date'})
    )
    notes = forms.CharField(
        required=False,
        label='Notes',
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'rows': 2, 'placeholder': 'Optional notes...'})
    )

    def __init__(self, *args, officer=None, loan_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        from django.db.models import Q

        if officer:
            qs = Loan.objects.filter(
                Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
                status='active'
            ).select_related('borrower').distinct()
        else:
            qs = Loan.objects.filter(status='active').select_related('borrower')

        self.fields['loan'].queryset = qs
        self.fields['loan'].label_from_instance = lambda obj: f"{obj.application_number} — {obj.borrower.get_full_name()} (K{obj.principal_amount:,.2f})"

        if loan_id:
            try:
                self.fields['loan'].initial = qs.get(pk=loan_id)
            except Loan.DoesNotExist:
                pass

        self.fields['payment_date'].initial = timezone.now().date()

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('payment_method')
        ref = cleaned.get('reference_number', '').strip()
        if method in ('mtn', 'airtel', 'bank_transfer') and not ref:
            self.add_error('reference_number', 'Reference number is required for mobile money and bank transfers.')
        return cleaned
