from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncMonth, TruncDate
from datetime import datetime, date, timedelta
from loans.models import Loan
from payments.models import Payment, PaymentSchedule
from accounts.models import User
from common.utils import (
    get_system_launch_date, 
    get_monthly_periods_since_launch, 
    format_system_period,
    get_system_age_description
)

class ReportListView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/report_list.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins and managers can access system reports
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access system reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Available reports
        context['reports'] = [
            {
                'name': 'Monthly Collection Trends',
                'description': 'View monthly collection trends and performance metrics',
                'url': 'reports:monthly_collections',
                'icon': 'fas fa-chart-line'
            },
            {
                'name': 'System Statistics',
                'description': 'View comprehensive system statistics and user activity',
                'url': 'reports:system_statistics',
                'icon': 'fas fa-chart-bar'
            },
            {
                'name': 'Loan Reports',
                'description': 'Generate detailed loan reports and analytics',
                'url': 'reports:loans',
                'icon': 'fas fa-file-contract'
            },
            {
                'name': 'Payment Reports',
                'description': 'View payment history and transaction reports',
                'url': 'reports:payments',
                'icon': 'fas fa-credit-card'
            },
            {
                'name': 'Financial Reports',
                'description': 'Generate comprehensive financial statements',
                'url': 'reports:financial',
                'icon': 'fas fa-calculator'
            }
        ]
        
        # Quick statistics for overview
        system_launch = get_system_launch_date()
        
        # Total loans since system launch
        context['total_loans'] = Loan.objects.filter(
            application_date__date__gte=system_launch
        ).count()
        
        # Total disbursed amount
        context['total_disbursed'] = Loan.objects.filter(
            disbursement_date__date__gte=system_launch,
            status__in=['active', 'completed']
        ).aggregate(total=Sum('principal_amount'))['total'] or 0
        
        # Total collected amount
        context['total_collected'] = Payment.objects.filter(
            payment_date__date__gte=system_launch,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Active borrowers
        context['active_borrowers'] = Loan.objects.filter(
            status='active'
        ).values('borrower').distinct().count()
        
        return context

class MonthlyCollectionTrendView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/monthly_collection_trend.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins and managers can access system reports
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access system reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        system_launch = get_system_launch_date()
        current_date = date.today()
        
        # Basic system info
        context['system_launch_date'] = system_launch
        context['system_age'] = get_system_age_description()
        context['report_period'] = format_system_period()
        
        # Monthly collection data from system launch
        monthly_collections = Payment.objects.filter(
            payment_date__date__gte=system_launch,
            status='completed'
        ).annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total_amount=Sum('amount'),
            payment_count=Count('id'),
            avg_payment=Avg('amount')
        ).order_by('month')
        
        # Monthly loan disbursements from system launch
        monthly_disbursements = Loan.objects.filter(
            disbursement_date__date__gte=system_launch,
            status__in=['active', 'completed']
        ).annotate(
            month=TruncMonth('disbursement_date')
        ).values('month').annotate(
            total_amount=Sum('principal_amount'),
            loan_count=Count('id'),
            avg_loan=Avg('principal_amount')
        ).order_by('month')
        
        # Monthly loan applications from system launch
        monthly_applications = Loan.objects.filter(
            application_date__date__gte=system_launch
        ).annotate(
            month=TruncMonth('application_date')
        ).values('month').annotate(
            application_count=Count('id'),
            approved_count=Count('id', filter=Q(status__in=['approved', 'active', 'disbursed', 'completed'])),
            rejected_count=Count('id', filter=Q(status='rejected'))
        ).order_by('month')
        
        # Prepare monthly data for charts
        monthly_periods = get_monthly_periods_since_launch()
        chart_data = []
        
        for period in monthly_periods:
            period_date = date(period['year'], period['month'], 1)
            
            # Find matching data for this period
            collections = next((item for item in monthly_collections if item['month'].date() == period_date), None)
            disbursements = next((item for item in monthly_disbursements if item['month'].date() == period_date), None)
            applications = next((item for item in monthly_applications if item['month'].date() == period_date), None)
            
            collections_amount = float(collections['total_amount']) if collections and collections['total_amount'] else 0
            disbursements_amount = float(disbursements['total_amount']) if disbursements and disbursements['total_amount'] else 0
            net_flow = collections_amount - disbursements_amount
            
            chart_data.append({
                'period': period['period_label'],
                'month_year': f"{period['year']}-{period['month']:02d}",
                'collections': {
                    'amount': collections_amount,
                    'count': collections['payment_count'] if collections else 0,
                    'average': float(collections['avg_payment']) if collections and collections['avg_payment'] else 0
                },
                'disbursements': {
                    'amount': disbursements_amount,
                    'count': disbursements['loan_count'] if disbursements else 0,
                    'average': float(disbursements['avg_loan']) if disbursements and disbursements['avg_loan'] else 0
                },
                'applications': {
                    'total': applications['application_count'] if applications else 0,
                    'approved': applications['approved_count'] if applications else 0,
                    'rejected': applications['rejected_count'] if applications else 0,
                    'approval_rate': (applications['approved_count'] / applications['application_count'] * 100) if applications and applications['application_count'] > 0 else 0
                },
                'net_flow': net_flow
            })
        
        context['chart_data'] = chart_data
        context['monthly_periods'] = monthly_periods
        
        # Summary statistics from system launch
        total_collections = Payment.objects.filter(
            payment_date__date__gte=system_launch,
            status='completed'
        ).aggregate(
            total=Sum('amount'),
            count=Count('id'),
            average=Avg('amount')
        )
        
        total_disbursements = Loan.objects.filter(
            disbursement_date__date__gte=system_launch,
            status__in=['active', 'completed']
        ).aggregate(
            total=Sum('principal_amount'),
            count=Count('id'),
            average=Avg('principal_amount')
        )
        
        total_applications = Loan.objects.filter(
            application_date__date__gte=system_launch
        ).aggregate(
            total=Count('id'),
            approved=Count('id', filter=Q(status__in=['approved', 'active', 'disbursed', 'completed'])),
            rejected=Count('id', filter=Q(status='rejected')),
            pending=Count('id', filter=Q(status='pending'))
        )
        
        context['summary'] = {
            'collections': total_collections,
            'disbursements': total_disbursements,
            'applications': total_applications,
            'net_flow': (total_collections['total'] or 0) - (total_disbursements['total'] or 0)
        }
        
        # Recent performance (last 30 days or since launch)
        recent_date = max(current_date - timedelta(days=30), system_launch)
        
        recent_collections = Payment.objects.filter(
            payment_date__date__gte=recent_date,
            status='completed'
        ).aggregate(
            total=Sum('amount'),
            count=Count('id'),
            average=Avg('amount')
        )
        
        recent_applications = Loan.objects.filter(
            application_date__date__gte=recent_date
        ).count()
        
        context['recent_performance'] = {
            'collections': recent_collections,
            'applications': recent_applications,
            'period': format_system_period(recent_date)
        }
        
        return context


class SystemStatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/system_statistics_tailwind.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins and managers can access system reports
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access system reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        system_launch = get_system_launch_date()
        
        # System information
        context['system_launch_date'] = system_launch
        context['system_age'] = get_system_age_description()
        context['report_period'] = format_system_period()
        
        # User statistics from system launch
        context['user_stats'] = User.objects.filter(
            date_joined__date__gte=system_launch
        ).values('role').annotate(
            count=Count('id')
        ).order_by('role')
        
        # Document statistics from system launch
        context['document_stats'] = Document.objects.filter(
            uploaded_at__date__gte=system_launch
        ).values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Loan document statistics from system launch
        from loans.models import LoanDocument
        context['loan_document_stats'] = LoanDocument.objects.filter(
            uploaded_at__date__gte=system_launch
        ).values('is_verified').annotate(
            count=Count('id')
        )
        
        # Daily activity trends (last 30 days or since launch)
        recent_date = max(date.today() - timedelta(days=30), system_launch)
        
        daily_activity = []
        current = recent_date
        while current <= date.today():
            day_loans = Loan.objects.filter(application_date__date=current).count()
            day_payments = Payment.objects.filter(payment_date__date=current, status='completed').count()
            day_documents = Document.objects.filter(uploaded_at__date=current).count()
            
            daily_activity.append({
                'date': current.strftime('%Y-%m-%d'),
                'date_label': current.strftime('%b %d'),
                'loans': day_loans,
                'payments': day_payments,
                'documents': day_documents
            })
            current += timedelta(days=1)
        
        context['daily_activity'] = daily_activity
        
        return context


class LoanReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/loan_report.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins and managers can access system reports
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access system reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all loans
        all_loans = Loan.objects.all().select_related('borrower', 'loan_officer').order_by('-application_date')
        
        # Loan statistics
        context['total_loans'] = all_loans.count()
        context['total_disbursed'] = all_loans.filter(status__in=['active', 'completed']).aggregate(total=Sum('principal_amount'))['total'] or 0
        context['active_loans'] = all_loans.filter(status='active').count()
        context['completed_loans'] = all_loans.filter(status='completed').count()
        context['pending_loans'] = all_loans.filter(status='pending').count()
        context['rejected_loans'] = all_loans.filter(status='rejected').count()
        
        # Recent loans (last 50)
        context['recent_loans'] = all_loans[:50]
        
        # Monthly loan summary
        monthly_loans = all_loans.annotate(
            month=TruncMonth('application_date')
        ).values('month').annotate(
            loan_count=Count('id'),
            total_amount=Sum('principal_amount')
        ).order_by('-month')[:12]
        
        context['monthly_loans'] = monthly_loans
        
        # Loan status breakdown
        status_breakdown = all_loans.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('principal_amount')
        )
        context['status_breakdown'] = status_breakdown
        
        # Approval rate
        total_applications = all_loans.count()
        approved_loans = all_loans.filter(status__in=['approved', 'active', 'completed']).count()
        context['approval_rate'] = (approved_loans / total_applications * 100) if total_applications > 0 else 0
        
        return context


class LoanExportView(LoginRequiredMixin, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        # Only admins and managers can access system reports
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)


class PaymentReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/payment_report.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins and managers can access system reports
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access system reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all payments
        all_payments = Payment.objects.all().select_related('loan', 'loan__borrower').order_by('-payment_date')
        
        # Payment statistics
        context['total_payments'] = all_payments.count()
        context['total_amount'] = all_payments.aggregate(total=Sum('amount'))['total'] or 0
        context['completed_payments'] = all_payments.filter(status='completed').count()
        context['pending_payments'] = all_payments.filter(status='pending').count()
        
        # Recent payments (last 50)
        context['recent_payments'] = all_payments[:50]
        
        # Monthly payment summary
        monthly_payments = all_payments.filter(
            status='completed'
        ).annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total_amount=Sum('amount'),
            payment_count=Count('id')
        ).order_by('-month')[:12]
        
        context['monthly_payments'] = monthly_payments
        
        # Payment status breakdown
        status_breakdown = all_payments.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        context['status_breakdown'] = status_breakdown
        
        return context


class PaymentExportView(LoginRequiredMixin, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        # Only admins and managers can access system reports
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)


class FinancialReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/financial_report.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins and managers can access system reports
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Financial overview
        total_disbursed = Loan.objects.filter(status__in=['active', 'completed']).aggregate(total=Sum('principal_amount'))['total'] or 0
        total_collected = Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        outstanding_balance = total_disbursed - total_collected
        
        context['total_disbursed'] = total_disbursed
        context['total_collected'] = total_collected
        context['outstanding_balance'] = outstanding_balance
        context['collection_rate'] = (total_collected / total_disbursed * 100) if total_disbursed > 0 else 0
        
        # Monthly financial data
        monthly_financial = []
        for i in range(12):
            month_date = date.today().replace(day=1) - timedelta(days=30*i)
            month_disbursed = Loan.objects.filter(
                disbursement_date__year=month_date.year,
                disbursement_date__month=month_date.month,
                status__in=['active', 'completed']
            ).aggregate(total=Sum('principal_amount'))['total'] or 0
            
            month_collected = Payment.objects.filter(
                payment_date__year=month_date.year,
                payment_date__month=month_date.month,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_financial.append({
                'month': month_date.strftime('%B %Y'),
                'disbursed': month_disbursed,
                'collected': month_collected,
                'net_flow': month_collected - month_disbursed
            })
        
        context['monthly_financial'] = list(reversed(monthly_financial))
        
        # Overdue analysis
        overdue_schedules = PaymentSchedule.objects.filter(
            due_date__lt=date.today(),
            is_paid=False
        )
        context['overdue_amount'] = overdue_schedules.aggregate(total=Sum('total_amount'))['total'] or 0
        context['overdue_count'] = overdue_schedules.count()
        
        return context


class FinancialExportView(LoginRequiredMixin, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        # Only admins and managers can access system reports
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You do not have permission to access reports.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
