from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date
from loans.models import Loan
from payments.models import Payment
from expenses.models import Expense, VaultTransaction


class DailyTransactionReportView(LoginRequiredMixin, TemplateView):
    """Generate daily transaction reports with aggregation by transaction type"""
    template_name = 'reports/daily_transaction_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date from request or use today
        report_date_str = self.request.GET.get('date')
        if report_date_str:
            try:
                report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
            except ValueError:
                report_date = date.today()
        else:
            report_date = date.today()
        
        # Get all transactions for the date
        transactions = []
        totals = {
            'disbursements': Decimal('0'),
            'payments': Decimal('0'),
            'deposits': Decimal('0'),
            'expenses': Decimal('0'),
            'total_inflows': Decimal('0'),
            'total_outflows': Decimal('0'),
        }
        
        # Get loan disbursements
        disbursements = Loan.objects.filter(
            disbursement_date__date=report_date,
            status__in=['active', 'completed']
        )
        for loan in disbursements:
            transactions.append({
                'type': 'Loan Disbursement',
                'amount': loan.principal_amount,
                'borrower': loan.borrower.full_name,
                'officer': loan.loan_officer.full_name if loan.loan_officer else 'N/A',
                'timestamp': loan.disbursement_date,
                'description': f'Loan {loan.application_number}'
            })
            totals['disbursements'] += loan.principal_amount
            totals['total_outflows'] += loan.principal_amount
        
        # Get payments
        payments = Payment.objects.filter(
            payment_date__date=report_date
        )
        for payment in payments:
            transactions.append({
                'type': 'Payment',
                'amount': payment.amount,
                'borrower': payment.loan.borrower.full_name,
                'officer': payment.loan.loan_officer.full_name if payment.loan.loan_officer else 'N/A',
                'timestamp': payment.payment_date,
                'description': f'Payment for {payment.loan.application_number}'
            })
            totals['payments'] += payment.amount
            totals['total_inflows'] += payment.amount
        
        # Get security deposits
        from loans.models import SecurityDeposit
        deposits = SecurityDeposit.objects.filter(
            payment_date__date=report_date,
            is_verified=True
        )
        for deposit in deposits:
            transactions.append({
                'type': 'Security Deposit',
                'amount': deposit.paid_amount,
                'borrower': deposit.loan.borrower.full_name,
                'officer': deposit.loan.loan_officer.full_name if deposit.loan.loan_officer else 'N/A',
                'timestamp': deposit.payment_date,
                'description': f'Deposit for {deposit.loan.application_number}'
            })
            totals['deposits'] += deposit.paid_amount
            totals['total_inflows'] += deposit.paid_amount
        
        # Get expenses
        expenses = Expense.objects.filter(
            expense_date=report_date,
            is_approved=True
        )
        for expense in expenses:
            transactions.append({
                'type': 'Expense',
                'amount': expense.amount,
                'borrower': expense.category.name,
                'officer': expense.recorded_by.full_name if expense.recorded_by else 'N/A',
                'timestamp': expense.created_at,
                'description': expense.title
            })
            totals['expenses'] += expense.amount
            totals['total_outflows'] += expense.amount
        
        # Get vault transactions
        vault_trans = VaultTransaction.objects.filter(
            transaction_date__date=report_date
        )
        for trans in vault_trans:
            if trans.transaction_type in ['deposit', 'payment_collection']:
                totals['total_inflows'] += trans.amount
            else:
                totals['total_outflows'] += trans.amount
            
            transactions.append({
                'type': trans.get_transaction_type_display(),
                'amount': trans.amount,
                'borrower': trans.branch,
                'officer': trans.recorded_by.full_name if trans.recorded_by else 'N/A',
                'timestamp': trans.transaction_date,
                'description': trans.description
            })
        
        # Sort transactions by timestamp
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Calculate net
        totals['net'] = totals['total_inflows'] - totals['total_outflows']
        
        context['report_date'] = report_date
        context['transactions'] = transactions
        context['totals'] = totals
        context['transaction_count'] = len(transactions)
        
        return context
