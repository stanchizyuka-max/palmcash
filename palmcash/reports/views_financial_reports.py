"""
Comprehensive financial reporting views with date range filtering
"""
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q, Avg, F
from django.db.models.functions import TruncDate, TruncMonth
from django.http import HttpResponse
from datetime import datetime, date, timedelta
from decimal import Decimal
from loans.models import Loan
from payments.models import Payment, PaymentCollection, PaymentSchedule
from accounts.models import User
from loans.models import SecurityDeposit
import json


class FinancialReportsView(LoginRequiredMixin, TemplateView):
    """Main financial reports dashboard"""
    template_name = 'reports/financial_reports_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins, managers, and loan officers can access financial reports
        if request.user.role not in ['admin', 'manager', 'loan_officer'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access financial reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available loan officers for filtering
        if self.request.user.role in ['admin', 'manager']:
            loan_officers = User.objects.filter(role='loan_officer', is_active=True)
        else:
            # Loan officers can only see their own reports
            loan_officers = User.objects.filter(id=self.request.user.id)
        
        context['loan_officers'] = loan_officers
        context['title'] = 'Financial Reports'
        
        return context


class DisbursementReportView(LoginRequiredMixin, TemplateView):
    """Disbursement report with date range filtering"""
    template_name = 'reports/disbursement_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        officer_id = self.request.GET.get('officer_id')
        
        # Set default date range (last 30 days)
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = date.today().strftime('%Y-%m-%d')
        
        # Parse dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Base query for disbursements
        disbursements_query = Loan.objects.filter(
            disbursement_date__date__gte=start_date,
            disbursement_date__date__lte=end_date,
            status__in=['active', 'disbursed', 'completed']
        )
        
        # Filter by loan officer if specified
        if officer_id and officer_id != 'all':
            disbursements_query = disbursements_query.filter(loan_officer_id=officer_id)
        elif self.request.user.role == 'loan_officer':
            # Loan officers can only see their own disbursements
            disbursements_query = disbursements_query.filter(loan_officer=self.request.user)
        elif self.request.user.role == 'manager':
            # Managers see disbursements in their branch
            if hasattr(self.request.user, 'officer_assignment'):
                branch_name = self.request.user.officer_assignment.branch
                disbursements_query = disbursements_query.filter(
                    Q(loan_officer__officer_assignment__branch=branch_name) |
                    Q(borrower__group_memberships__group__assigned_officer__officer_assignment__branch=branch_name)
                ).distinct()
        
        # Get disbursements
        disbursements = disbursements_query.select_related(
            'borrower', 'loan_officer', 'loan_type'
        ).order_by('-disbursement_date')
        
        # Calculate totals
        total_amount = disbursements.aggregate(
            total=Sum('principal_amount')
        )['total'] or Decimal('0.00')
        
        total_count = disbursements.count()
        
        # Group by loan officer for summary
        officer_summary = disbursements.values(
            'loan_officer__first_name',
            'loan_officer__last_name'
        ).annotate(
            amount=Sum('principal_amount'),
            count=Count('id')
        ).order_by('-amount')
        
        # Group by date for daily summary
        daily_summary = disbursements.extra({
            'date': 'date(disbursement_date)'
        }).values('date').annotate(
            amount=Sum('principal_amount'),
            count=Count('id')
        ).order_by('date')
        
        context.update({
            'disbursements': disbursements,
            'total_amount': total_amount,
            'total_count': total_count,
            'officer_summary': officer_summary,
            'daily_summary': daily_summary,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'selected_officer_id': officer_id,
            'title': 'Disbursement Report'
        })
        
        return context


class CollectionReportView(LoginRequiredMixin, TemplateView):
    """Collection report with date range filtering"""
    template_name = 'reports/collection_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        officer_id = self.request.GET.get('officer_id')
        
        # Set default date range (last 30 days)
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = date.today().strftime('%Y-%m-%d')
        
        # Parse dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Base query for collections
        collections_query = PaymentCollection.objects.filter(
            collection_date__gte=start_date,
            collection_date__lte=end_date,
            status='completed'
        )
        
        # Filter by loan officer if specified
        if officer_id and officer_id != 'all':
            collections_query = collections_query.filter(
                loan__loan_officer_id=officer_id
            )
        elif self.request.user.role == 'loan_officer':
            # Loan officers can only see their own collections
            collections_query = collections_query.filter(loan__loan_officer=self.request.user)
        elif self.request.user.role == 'manager':
            # Managers see collections in their branch
            if hasattr(self.request.user, 'officer_assignment'):
                branch_name = self.request.user.officer_assignment.branch
                collections_query = collections_query.filter(
                    Q(loan__loan_officer__officer_assignment__branch=branch_name) |
                    Q(loan__borrower__group_memberships__group__assigned_officer__officer_assignment__branch=branch_name)
                ).distinct()
        
        # Get collections
        collections = collections_query.select_related(
            'loan', 'loan__borrower', 'loan__loan_officer'
        ).order_by('-collection_date')
        
        # Calculate totals
        total_amount = collections.aggregate(
            total=Sum('collected_amount')
        )['total'] or Decimal('0.00')
        
        total_count = collections.count()
        
        # Group by loan officer for summary
        officer_summary = collections.values(
            'loan__loan_officer__first_name',
            'loan__loan_officer__last_name'
        ).annotate(
            amount=Sum('collected_amount'),
            count=Count('id')
        ).order_by('-amount')
        
        # Group by date for daily summary
        daily_summary = collections.extra({
            'date': 'date(collection_date)'
        }).values('date').annotate(
            amount=Sum('collected_amount'),
            count=Count('id')
        ).order_by('date')
        
        context.update({
            'collections': collections,
            'total_amount': total_amount,
            'total_count': total_count,
            'officer_summary': officer_summary,
            'daily_summary': daily_summary,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'selected_officer_id': officer_id,
            'title': 'Collection Report'
        })
        
        return context


class DepositReportView(LoginRequiredMixin, TemplateView):
    """Security deposit report with date range filtering"""
    template_name = 'reports/deposit_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        officer_id = self.request.GET.get('officer_id')
        
        # Set default date range (last 30 days)
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = date.today().strftime('%Y-%m-%d')
        
        # Parse dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Base query for deposits
        deposits_query = SecurityDeposit.objects.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date,
            paid_amount__gt=0
        )
        
        # Filter by loan officer if specified
        if officer_id and officer_id != 'all':
            deposits_query = deposits_query.filter(
                loan__loan_officer_id=officer_id
            )
        elif self.request.user.role == 'loan_officer':
            # Loan officers can only see their own deposits
            deposits_query = deposits_query.filter(loan__loan_officer=self.request.user)
        elif self.request.user.role == 'manager':
            # Managers see deposits in their branch
            if hasattr(self.request.user, 'officer_assignment'):
                branch_name = self.request.user.officer_assignment.branch
                deposits_query = deposits_query.filter(
                    Q(loan__loan_officer__officer_assignment__branch=branch_name) |
                    Q(loan__borrower__group_memberships__group__assigned_officer__officer_assignment__branch=branch_name)
                ).distinct()
        
        # Get deposits
        deposits = deposits_query.select_related(
            'loan', 'loan__borrower', 'loan__loan_officer'
        ).order_by('-payment_date')
        
        # Calculate totals
        total_amount = deposits.aggregate(
            total=Sum('paid_amount')
        )['total'] or Decimal('0.00')
        
        total_count = deposits.count()
        
        # Calculate verification stats
        verified_count = deposits.filter(is_verified=True).count()
        pending_count = deposits.filter(is_verified=False).count()
        
        # Group by loan officer for summary
        officer_summary = deposits.values(
            'loan__loan_officer__first_name',
            'loan__loan_officer__last_name'
        ).annotate(
            amount=Sum('paid_amount'),
            count=Count('id'),
            verified=Count('id', filter=Q(is_verified=True)),
            pending=Count('id', filter=Q(is_verified=False))
        ).order_by('-amount')
        
        # Group by date for daily summary
        daily_summary = deposits.extra({
            'date': 'date(payment_date)'
        }).values('date').annotate(
            amount=Sum('paid_amount'),
            count=Count('id'),
            verified=Count('id', filter=Q(is_verified=True))
        ).order_by('date')
        
        context.update({
            'deposits': deposits,
            'total_amount': total_amount,
            'total_count': total_count,
            'verified_count': verified_count,
            'pending_count': pending_count,
            'officer_summary': officer_summary,
            'daily_summary': daily_summary,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'selected_officer_id': officer_id,
            'title': 'Security Deposit Report'
        })
        
        return context


class ReturnsReportView(LoginRequiredMixin, TemplateView):
    """Returns report with date range filtering"""
    template_name = 'reports/returns_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        officer_id = self.request.GET.get('officer_id')
        
        # Set default date range (last 30 days)
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = date.today().strftime('%Y-%m-%d')
        
        # Parse dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Base query for returns (overdue payments, defaults, etc.)
        # For this example, we'll consider returns as overdue payments
        returns_query = PaymentSchedule.objects.filter(
            due_date__gte=start_date,
            due_date__lte=end_date,
            is_paid=False
        )
        
        # Filter by loan officer if specified
        if officer_id and officer_id != 'all':
            returns_query = returns_query.filter(
                loan__loan_officer_id=officer_id
            )
        elif self.request.user.role == 'loan_officer':
            # Loan officers can only see their own returns
            returns_query = returns_query.filter(loan__loan_officer=self.request.user)
        elif self.request.user.role == 'manager':
            # Managers see returns in their branch
            if hasattr(self.request.user, 'officer_assignment'):
                branch_name = self.request.user.officer_assignment.branch
                returns_query = returns_query.filter(
                    Q(loan__loan_officer__officer_assignment__branch=branch_name) |
                    Q(loan__borrower__group_memberships__group__assigned_officer__officer_assignment__branch=branch_name)
                ).distinct()
        
        # Get returns
        returns = returns_query.select_related(
            'loan', 'loan__borrower', 'loan__loan_officer'
        ).order_by('-due_date')
        
        # Calculate totals
        total_amount = returns.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        total_count = returns.count()
        
        # Group by loan officer for summary
        officer_summary = returns.values(
            'loan__loan_officer__first_name',
            'loan__loan_officer__last_name'
        ).annotate(
            amount=Sum('total_amount'),
            count=Count('id')
        ).order_by('-amount')
        
        # Group by date for daily summary
        daily_summary = returns.extra({
            'date': 'date(due_date)'
        }).values('date').annotate(
            amount=Sum('total_amount'),
            count=Count('id')
        ).order_by('date')
        
        context.update({
            'returns': returns,
            'total_amount': total_amount,
            'total_count': total_count,
            'officer_summary': officer_summary,
            'daily_summary': daily_summary,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'selected_officer_id': officer_id,
            'title': 'Returns Report'
        })
        
        return context


def export_financial_report(request, report_type):
    """Export financial report to CSV"""
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    
    if request.user.role not in ['admin', 'manager', 'loan_officer'] and not request.user.is_superuser:
        return HttpResponse('Forbidden', status=403)
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    officer_id = request.GET.get('officer_id')
    
    # Set default date range
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = date.today().strftime('%Y-%m-%d')
    
    # Parse dates
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Generate CSV based on report type
    if report_type == 'disbursement':
        return _export_disbursement_csv(request, start_date, end_date, officer_id)
    elif report_type == 'collection':
        return _export_collection_csv(request, start_date, end_date, officer_id)
    elif report_type == 'deposit':
        return _export_deposit_csv(request, start_date, end_date, officer_id)
    elif report_type == 'returns':
        return _export_returns_csv(request, start_date, end_date, officer_id)
    else:
        return HttpResponse('Invalid report type', status=400)


def _export_disbursement_csv(request, start_date, end_date, officer_id):
    """Export disbursement report to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="disbursement_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'Application Number', 'Borrower', 'Loan Officer', 'Amount', 
        'Disbursement Date', 'Loan Type', 'Status'
    ])
    
    # Get data (same logic as DisbursementReportView)
    disbursements_query = Loan.objects.filter(
        disbursement_date__date__gte=start_date,
        disbursement_date__date__lte=end_date,
        status__in=['active', 'disbursed', 'completed']
    )
    
    if officer_id and officer_id != 'all':
        disbursements_query = disbursements_query.filter(loan_officer_id=officer_id)
    elif request.user.role == 'loan_officer':
        disbursements_query = disbursements_query.filter(loan_officer=request.user)
    
    disbursements = disbursements_query.select_related(
        'borrower', 'loan_officer', 'loan_type'
    ).order_by('-disbursement_date')
    
    # Data rows
    for disbursement in disbursements:
        writer.writerow([
            disbursement.application_number,
            disbursement.borrower.get_full_name(),
            disbursement.loan_officer.get_full_name() if disbursement.loan_officer else '',
            disbursement.principal_amount,
            disbursement.disbursement_date.strftime('%Y-%m-%d'),
            disbursement.loan_type.name if disbursement.loan_type else '',
            disbursement.get_status_display()
        ])
    
    return response


def _export_collection_csv(request, start_date, end_date, officer_id):
    """Export collection report to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="collection_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'Loan Number', 'Borrower', 'Loan Officer', 'Amount', 
        'Collection Date', 'Payment Method', 'Status'
    ])
    
    # Get data (same logic as CollectionReportView)
    collections_query = PaymentCollection.objects.filter(
        collection_date__gte=start_date,
        collection_date__lte=end_date,
        status='completed'
    )
    
    if officer_id and officer_id != 'all':
        collections_query = collections_query.filter(loan__loan_officer_id=officer_id)
    elif request.user.role == 'loan_officer':
        collections_query = collections_query.filter(loan__loan_officer=request.user)
    
    collections = collections_query.select_related(
        'loan', 'loan__borrower', 'loan__loan_officer'
    ).order_by('-collection_date')
    
    # Data rows
    for collection in collections:
        writer.writerow([
            collection.loan.application_number,
            collection.loan.borrower.get_full_name(),
            collection.loan.loan_officer.get_full_name() if collection.loan.loan_officer else '',
            collection.collected_amount,
            collection.collection_date.strftime('%Y-%m-%d'),
            collection.payment_method,
            collection.status
        ])
    
    return response


def _export_deposit_csv(request, start_date, end_date, officer_id):
    """Export deposit report to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="deposit_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'Loan Number', 'Borrower', 'Loan Officer', 'Amount', 
        'Paid Date', 'Verification Status', 'Status'
    ])
    
    # Get data (same logic as DepositReportView)
    deposits_query = SecurityDeposit.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        paid_amount__gt=0
    )
    
    if officer_id and officer_id != 'all':
        deposits_query = deposits_query.filter(loan__loan_officer_id=officer_id)
    elif request.user.role == 'loan_officer':
        deposits_query = deposits_query.filter(loan__loan_officer=request.user)
    
    deposits = deposits_query.select_related(
        'loan', 'loan__borrower', 'loan__loan_officer'
    ).order_by('-payment_date')
    
    # Data rows
    for deposit in deposits:
        writer.writerow([
            deposit.loan.application_number,
            deposit.loan.borrower.get_full_name(),
            deposit.loan.loan_officer.get_full_name() if deposit.loan.loan_officer else '',
            deposit.paid_amount,
            deposit.payment_date.strftime('%Y-%m-%d'),
            'Verified' if deposit.is_verified else 'Pending',
            deposit.get_status_display()
        ])
    
    return response


def _export_returns_csv(request, start_date, end_date, officer_id):
    """Export returns report to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="returns_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'Loan Number', 'Borrower', 'Loan Officer', 'Amount', 
        'Due Date', 'Days Overdue', 'Status'
    ])
    
    # Get data (same logic as ReturnsReportView)
    returns_query = Payment.objects.filter(
        due_date__date__gte=start_date,
        due_date__date__lte=end_date,
        status='overdue'
    )
    
    if officer_id and officer_id != 'all':
        returns_query = returns_query.filter(loan__loan_officer_id=officer_id)
    elif request.user.role == 'loan_officer':
        returns_query = returns_query.filter(loan__loan_officer=request.user)
    
    returns = returns_query.select_related(
        'loan', 'loan__borrower', 'loan__loan_officer'
    ).order_by('-due_date')
    
    # Data rows
    for return_item in returns:
        days_overdue = (date.today() - return_item.due_date.date()).days
        writer.writerow([
            return_item.loan.application_number,
            return_item.loan.borrower.get_full_name(),
            return_item.loan.loan_officer.get_full_name() if return_item.loan.loan_officer else '',
            return_item.amount,
            return_item.due_date.strftime('%Y-%m-%d'),
            days_overdue,
            return_item.status
        ])
    
    return response
