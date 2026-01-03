from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Sum
from decimal import Decimal
from .models import Expense, ExpenseCategory, VaultTransaction
from .forms import ExpenseForm, VaultTransactionForm


class ExpenseListView(LoginRequiredMixin, ListView):
    """List all expenses with filtering options"""
    model = Expense
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Expense.objects.all()
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by branch
        branch = self.request.GET.get('branch')
        if branch:
            queryset = queryset.filter(branch=branch)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(expense_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(expense_date__lte=end_date)
        
        # Filter by approval status
        approval_status = self.request.GET.get('approval_status')
        if approval_status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif approval_status == 'pending':
            queryset = queryset.filter(is_approved=False)
        
        return queryset.order_by('-expense_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ExpenseCategory.objects.filter(is_active=True)
        
        # Calculate totals
        queryset = self.get_queryset()
        context['total_expenses'] = queryset.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        context['approved_total'] = queryset.filter(is_approved=True).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        context['pending_total'] = queryset.filter(is_approved=False).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    """Create a new expense"""
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:list')
    
    def dispatch(self, request, *args, **kwargs):
        # Check permission
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'You do not have permission to create expenses.')
            return redirect('expenses:list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        messages.success(self.request, 'Expense created successfully.')
        return super().form_valid(form)


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing expense"""
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:list')
    
    def dispatch(self, request, *args, **kwargs):
        # Check permission
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'You do not have permission to update expenses.')
            return redirect('expenses:list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Expense updated successfully.')
        return super().form_valid(form)


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an expense"""
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:list')
    
    def dispatch(self, request, *args, **kwargs):
        # Check permission
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'You do not have permission to delete expenses.')
            return redirect('expenses:list')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Expense deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ExpenseReportView(LoginRequiredMixin, TemplateView):
    """Generate expense reports with aggregation by category and time period"""
    template_name = 'expenses/expense_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        category_id = self.request.GET.get('category')
        branch = self.request.GET.get('branch')
        
        # Build queryset
        queryset = Expense.objects.filter(is_approved=True)
        
        if start_date:
            queryset = queryset.filter(expense_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(expense_date__lte=end_date)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if branch:
            queryset = queryset.filter(branch=branch)
        
        # Aggregate by category
        category_totals = {}
        for category in ExpenseCategory.objects.filter(is_active=True):
            total = queryset.filter(category=category).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            if total > 0:
                category_totals[category.name] = total
        
        context['category_totals'] = category_totals
        context['total_expenses'] = sum(category_totals.values()) if category_totals else Decimal('0')
        context['categories'] = ExpenseCategory.objects.filter(is_active=True)
        context['expenses'] = queryset
        
        # Calculate average expense
        expense_count = queryset.count()
        if expense_count > 0:
            context['average_expense'] = context['total_expenses'] / expense_count
        else:
            context['average_expense'] = Decimal('0')
        
        return context


class VaultTransactionListView(LoginRequiredMixin, ListView):
    """List all vault transactions"""
    model = VaultTransaction
    template_name = 'expenses/vault_transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = VaultTransaction.objects.all()
        
        # Filter by transaction type
        transaction_type = self.request.GET.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by branch
        branch = self.request.GET.get('branch')
        if branch:
            queryset = queryset.filter(branch=branch)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)
        
        return queryset.order_by('-transaction_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction_types'] = VaultTransaction.TRANSACTION_TYPE_CHOICES
        
        # Calculate totals
        queryset = self.get_queryset()
        context['total_transactions'] = queryset.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        return context


class VaultTransactionCreateView(LoginRequiredMixin, CreateView):
    """Create a new vault transaction"""
    model = VaultTransaction
    form_class = VaultTransactionForm
    template_name = 'expenses/vault_transaction_form.html'
    success_url = reverse_lazy('expenses:vault-transactions')
    
    def dispatch(self, request, *args, **kwargs):
        # Check permission
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'You do not have permission to create vault transactions.')
            return redirect('expenses:vault-transactions')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        messages.success(self.request, 'Vault transaction recorded successfully.')
        return super().form_valid(form)


class BranchBalanceView(LoginRequiredMixin, TemplateView):
    """Display current balance for each branch"""
    template_name = 'expenses/branch_balance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all unique branches
        branches = VaultTransaction.objects.values_list('branch', flat=True).distinct()
        
        branch_balances = {}
        for branch in branches:
            # Calculate inflows and outflows
            inflows = VaultTransaction.objects.filter(
                branch=branch,
                transaction_type__in=['deposit', 'payment_collection']
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            outflows = VaultTransaction.objects.filter(
                branch=branch,
                transaction_type__in=['withdrawal', 'loan_disbursement']
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            balance = inflows - outflows
            branch_balances[branch] = {
                'inflows': inflows,
                'outflows': outflows,
                'balance': balance
            }
        
        context['branch_balances'] = branch_balances
        context['total_balance'] = sum(b['balance'] for b in branch_balances.values())
        
        return context
