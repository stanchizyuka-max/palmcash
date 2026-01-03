from django import forms
from .models import Expense, ExpenseCategory, VaultTransaction


class ExpenseForm(forms.ModelForm):
    """Form for creating and updating expenses"""
    
    class Meta:
        model = Expense
        fields = ['category', 'expense_type', 'title', 'description', 'amount', 'branch', 'expense_date', 'receipt']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'expense_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Expense title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Expense description'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount', 'step': '0.01'}),
            'branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch name'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'receipt': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount


class VaultTransactionForm(forms.ModelForm):
    """Form for creating vault transactions"""
    
    class Meta:
        model = VaultTransaction
        fields = ['transaction_type', 'branch', 'amount', 'description', 'reference_number', 'transaction_date', 'loan', 'payment']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch name'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Transaction description'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reference number'}),
            'transaction_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'loan': forms.Select(attrs={'class': 'form-control'}),
            'payment': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
