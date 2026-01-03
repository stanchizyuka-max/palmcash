from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.contrib.auth.decorators import login_required
from loans.models import Loan
from payments.models import Payment
from datetime import datetime, timedelta

@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard based on role"""
    user = request.user
    
    if user.is_superuser:
        return redirect('dashboard:admin')
    elif user.role == 'manager':
        return redirect('dashboard:manager')
    elif user.role == 'loan_officer':
        return redirect('dashboard:officer')
    elif user.role == 'borrower':
        return redirect('dashboard:borrower')
    else:
        return redirect('accounts:login')

class DashboardView(LoginRequiredMixin, TemplateView):
    """Legacy dashboard view - redirects to role-specific dashboard"""
    
    def get(self, request, *args, **kwargs):
        return dashboard_redirect(request)


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin Dashboard - System administration and full control"""
    template_name = 'dashboard/admin_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # System-wide statistics
        from accounts.models import User
        all_loans = Loan.objects.all()
        all_users = User.objects.all()
        
        context['total_loans'] = all_loans.count()
        context['active_loans'] = all_loans.filter(status='active').count()
        context['pending_loans'] = all_loans.filter(status='pending').count()
        context['rejected_loans'] = all_loans.filter(status='rejected').count()
        context['completed_loans'] = all_loans.filter(status='completed').count()
        
        # User statistics
        context['total_users'] = all_users.count()
        context['total_borrowers'] = all_users.filter(role='borrower').count()
        context['total_managers'] = all_users.filter(role='manager').count()
        context['total_officers'] = all_users.filter(role='loan_officer').count()
        context['active_users'] = all_users.filter(is_active=True).count()
        
        # Financial overview
        context['total_disbursed'] = all_loans.filter(
            status__in=['active', 'completed', 'disbursed']
        ).aggregate(total=Sum('principal_amount'))['total'] or 0
        
        context['total_repaid'] = Payment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # System activity
        context['recent_users'] = all_users.filter(
            date_joined__gte=thirty_days_ago
        ).order_by('-date_joined')[:10]
        
        context['recent_loans'] = all_loans.filter(
            application_date__gte=thirty_days_ago
        ).order_by('-application_date')[:10]
        
        # Performance metrics
        from payments.models import PaymentSchedule
        context['overdue_count'] = PaymentSchedule.objects.filter(
            due_date__lt=today,
            is_paid=False
        ).count()
        
        # Documents pending approval
        from documents.models import Document
        context['pending_documents'] = Document.objects.filter(status='pending').count()
        
        # Pending payments
        context['pending_payments'] = Payment.objects.filter(status='pending').count()
        
        # Monthly statistics
        context['monthly_signups'] = all_users.filter(
            date_joined__gte=thirty_days_ago
        ).count()
        
        context['monthly_applications'] = all_loans.filter(
            application_date__gte=thirty_days_ago
        ).count()
        
        # Role distribution
        context['role_distribution'] = [
            {'role': 'Borrowers', 'count': context['total_borrowers']},
            {'role': 'Managers', 'count': context['total_managers']},
            {'role': 'Officers', 'count': context['total_officers']},
        ]
        
        # Loan status distribution
        context['loan_status_data'] = all_loans.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return context


class ManagerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Manager Dashboard - High-level overview and controls"""
    template_name = 'dashboard/manager_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'manager' or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # Total statistics
        all_loans = Loan.objects.all()
        context['total_loans'] = all_loans.count()
        context['active_loans'] = all_loans.filter(status='active').count()
        context['pending_loans'] = all_loans.filter(status='pending').count()
        context['rejected_loans'] = all_loans.filter(status='rejected').count()
        context['completed_loans'] = all_loans.filter(status='completed').count()
        
        # Financial statistics
        context['total_disbursed'] = all_loans.filter(
            status__in=['active', 'completed', 'disbursed']
        ).aggregate(total=Sum('principal_amount'))['total'] or 0
        
        context['total_repaid'] = Payment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Customer statistics
        from accounts.models import User
        context['total_customers'] = User.objects.filter(role='borrower').count()
        context['active_loan_officers'] = User.objects.filter(role='loan_officer', is_active=True).count()
        
        # Recent activity
        context['recent_applications'] = all_loans.filter(
            application_date__gte=thirty_days_ago
        ).order_by('-application_date')[:10]
        
        # Overdue loans
        from payments.models import PaymentSchedule
        context['overdue_count'] = PaymentSchedule.objects.filter(
            due_date__lt=today,
            is_paid=False
        ).count()
        
        # Loan performance by status
        context['loan_status_data'] = all_loans.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Monthly repayment statistics
        context['monthly_repayments'] = Payment.objects.filter(
            payment_date__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Pending documents
        from documents.models import Document
        context['pending_documents'] = Document.objects.filter(status='pending').count()
        
        # Approved documents (for display on dashboard)
        context['approved_documents'] = Document.objects.filter(status='approved').order_by('-uploaded_at')[:10]
        context['total_approved_documents'] = Document.objects.filter(status='approved').count()
        
        # Pending payments
        context['pending_payments'] = Payment.objects.filter(status='pending').count()
        
        # Expenses data
        try:
            from expenses.models import Expense, VaultTransaction
            from decimal import Decimal
            
            all_expenses = Expense.objects.all()
            context['total_expenses'] = all_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
            context['approved_expenses'] = all_expenses.filter(is_approved=True).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            context['pending_expenses'] = all_expenses.filter(is_approved=False).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Recent expenses
            context['recent_expenses'] = all_expenses.order_by('-expense_date')[:5]
            
            # Category breakdown
            category_breakdown = {}
            for expense in all_expenses:
                category_name = expense.category.name if expense.category else 'Uncategorized'
                if category_name not in category_breakdown:
                    category_breakdown[category_name] = Decimal('0')
                category_breakdown[category_name] += expense.amount
            context['category_breakdown'] = category_breakdown
            
            # Vault balance
            deposits = VaultTransaction.objects.filter(
                transaction_type__in=['deposit', 'payment_collection']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            withdrawals = VaultTransaction.objects.filter(
                transaction_type__in=['withdrawal', 'loan_disbursement']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            context['vault_balance'] = deposits - withdrawals
            
            # Recent vault transactions
            context['recent_transactions'] = VaultTransaction.objects.order_by('-transaction_date')[:5]
            
            # Branch balances
            branch_balances = {}
            branches = VaultTransaction.objects.values_list('branch', flat=True).distinct()
            for branch in branches:
                inflows = VaultTransaction.objects.filter(
                    branch=branch,
                    transaction_type__in=['deposit', 'payment_collection']
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                outflows = VaultTransaction.objects.filter(
                    branch=branch,
                    transaction_type__in=['withdrawal', 'loan_disbursement']
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                branch_balances[branch] = {
                    'inflows': inflows,
                    'outflows': outflows,
                    'balance': inflows - outflows
                }
            context['branch_balances'] = branch_balances
            
        except ImportError:
            # Expenses app not available
            context['total_expenses'] = 0
            context['approved_expenses'] = 0
            context['pending_expenses'] = 0
            context['recent_expenses'] = []
            context['category_breakdown'] = {}
            context['vault_balance'] = 0
            context['recent_transactions'] = []
            context['branch_balances'] = {}
        
        # Recent messages
        from internal_messages.models import Message
        context['recent_messages'] = Message.objects.filter(recipient=self.request.user).order_by('-created_at')[:5]
        
        return context



class LoanOfficerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Loan Officer Dashboard - Assigned loans and clients"""
    template_name = 'dashboard/officer_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'loan_officer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = datetime.now().date()
        
        # Loans assigned to this officer
        assigned_loans = Loan.objects.filter(loan_officer=user)
        
        context['assigned_loans'] = assigned_loans.count()
        context['pending_approvals'] = assigned_loans.filter(status='pending').count()
        context['active_loans'] = assigned_loans.filter(status='active').count()
        context['overdue_loans'] = assigned_loans.filter(
            status='active',
            payment_schedule__due_date__lt=today,
            payment_schedule__is_paid=False
        ).distinct().count()
        
        # Recent loans
        context['recent_loans'] = assigned_loans.order_by('-application_date')[:10]
        
        # Clients assigned to this officer (using the new assigned_officer field)
        assigned_clients = user.assigned_clients.filter(role='borrower', is_active=True)
        context['my_clients'] = assigned_clients.count()
        context['recent_clients'] = assigned_clients.order_by('-date_joined')[:5]
        
        # Officer assignment settings
        try:
            from clients.models import OfficerAssignment
            context['officer_assignment'] = OfficerAssignment.objects.get(officer=user)
        except:
            context['officer_assignment'] = None
        
        # Repayments collected
        context['repayments_collected'] = Payment.objects.filter(
            loan__loan_officer=user,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Today's due payments
        from payments.models import PaymentSchedule
        context['due_today'] = PaymentSchedule.objects.filter(
            loan__loan_officer=user,
            due_date=today,
            is_paid=False
        ).count()
        
        # Pending payments to review
        context['pending_payments'] = Payment.objects.filter(
            loan__loan_officer=user,
            status='pending'
        ).count()
        
        # Documents for clients assigned to this officer
        from documents.models import Document
        context['pending_documents_for_review'] = Document.objects.filter(
            user__in=assigned_clients,
            status='pending'
        ).order_by('-uploaded_at')[:10]
        context['total_pending_documents'] = Document.objects.filter(
            user__in=assigned_clients,
            status='pending'
        ).count()
        
        # Recent messages
        from internal_messages.models import Message
        context['recent_messages'] = Message.objects.filter(recipient=user).order_by('-created_at')[:5]
        
        return context


class BorrowerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Borrower Dashboard - Personal loans and payments"""
    template_name = 'dashboard/borrower_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'borrower'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Borrower's loans
        user_loans = Loan.objects.filter(borrower=user)
        
        # Check for rejected loans with reasons
        rejected_loans = user_loans.filter(status='rejected').exclude(rejection_reason='')
        
        # Check document verification status
        from documents.models import Document
        has_verified_docs = Document.objects.filter(user=user, status='approved').exists()
        
        # Get borrower's documents
        borrower_documents = Document.objects.filter(user=user).order_by('-uploaded_at')
        
        # Get repayment schedule for active loans
        from payments.models import PaymentSchedule
        active_loans = user_loans.filter(status='active')
        repayment_schedule = PaymentSchedule.objects.filter(
            loan__in=active_loans
        ).order_by('due_date')[:10]  # Show next 10 payments
        
        # Recent notifications
        from notifications.models import Notification
        recent_notifications = Notification.objects.filter(
            recipient=user
        ).order_by('-created_at')[:5]
        
        context.update({
            'user_loans': user_loans,
            'active_loans': user_loans.filter(status='active').count(),
            'total_borrowed': user_loans.filter(status__in=['active', 'completed']).aggregate(
                total=Sum('principal_amount'))['total'] or 0,
            'pending_applications': user_loans.filter(status='pending').count(),
            'rejected_loans': rejected_loans,
            'has_verified_documents': has_verified_docs,
            'borrower_documents': borrower_documents,
            'repayment_schedule': repayment_schedule,
            'recent_notifications': recent_notifications,
        })
        
        return context


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Only show analytics to admin and loan officers
        if self.request.user.role in ['admin', 'loan_officer'] or self.request.user.is_superuser:
            context.update({
                'loan_status_data': self.get_loan_status_data(),
                'monthly_disbursements': self.get_monthly_disbursements(),
                'payment_performance': self.get_payment_performance(),
            })
        
        return context
    
    def get_loan_status_data(self):
        return Loan.objects.values('status').annotate(count=Count('id'))
    
    def get_monthly_disbursements(self):
        # Get disbursements for the last 12 months using Django's database-agnostic approach
        from django.db.models.functions import TruncMonth
        
        return Loan.objects.filter(
            disbursement_date__isnull=False,
            disbursement_date__gte=datetime.now().date() - timedelta(days=365)
        ).annotate(
            month=TruncMonth('disbursement_date')
        ).values('month').annotate(
            total=Sum('principal_amount'),
            count=Count('id')
        ).order_by('month')
    
    def get_payment_performance(self):
        from payments.models import PaymentSchedule
        total_due = PaymentSchedule.objects.aggregate(total=Sum('total_amount'))['total'] or 0
        paid = PaymentSchedule.objects.filter(is_paid=True).aggregate(total=Sum('total_amount'))['total'] or 0
        
        return {
            'total_due': total_due,
            'total_paid': paid,
            'collection_rate': (paid / total_due * 100) if total_due > 0 else 0
        }


class ManageUsersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin User Management"""
    template_name = 'dashboard/admin/manage_users.html'
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'manager'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.models import User
        from django.contrib.auth.models import Group
        
        context['users'] = User.objects.all().order_by('-date_joined')
        context['groups'] = Group.objects.all()
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['staff_users'] = User.objects.filter(is_staff=True).count()
        context['superusers'] = User.objects.filter(is_superuser=True).count()
        
        # Role distribution
        context['role_stats'] = {
            'borrowers': User.objects.filter(role='borrower').count(),
            'officers': User.objects.filter(role='loan_officer').count(),
            'managers': User.objects.filter(role='manager').count(),
            'admins': User.objects.filter(role='admin').count(),
        }
        
        return context


class ManageLoansView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin Loan Management"""
    template_name = 'dashboard/admin/manage_loans.html'
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'manager'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        all_loans = Loan.objects.all().select_related('borrower', 'loan_officer')
        
        context['loans'] = all_loans.order_by('-application_date')[:50]  # Latest 50
        context['total_loans'] = all_loans.count()
        
        # Status breakdown
        context['status_stats'] = {
            'pending': all_loans.filter(status='pending').count(),
            'approved': all_loans.filter(status='approved').count(),
            'active': all_loans.filter(status='active').count(),
            'completed': all_loans.filter(status='completed').count(),
            'rejected': all_loans.filter(status='rejected').count(),
        }
        
        # Financial stats
        context['financial_stats'] = {
            'total_disbursed': all_loans.filter(status__in=['active', 'completed']).aggregate(
                total=Sum('principal_amount'))['total'] or 0,
            'total_outstanding': all_loans.filter(status='active').aggregate(
                total=Sum('principal_amount'))['total'] or 0,
        }
        
        return context


class GroupsPermissionsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin Groups & Permissions Management"""
    template_name = 'dashboard/admin/groups_permissions.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        
        from accounts.models import User
        
        context['groups'] = Group.objects.all().prefetch_related('permissions')
        context['permissions'] = Permission.objects.all().select_related('content_type')
        context['content_types'] = ContentType.objects.all()
        
        # Group statistics
        context['group_stats'] = {}
        for group in context['groups']:
            context['group_stats'][group.name] = {
                'users': User.objects.filter(groups=group).count(),
                'permissions': group.permissions.count()
            }
        
        return context


class SystemReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin System Reports"""
    template_name = 'dashboard/admin/system_reports.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.models import User
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # User activity report
        context['user_activity'] = {
            'new_users_30d': User.objects.filter(date_joined__gte=thirty_days_ago).count(),
            'active_users_30d': User.objects.filter(last_login__gte=thirty_days_ago).count(),
            'total_logins': User.objects.exclude(last_login__isnull=True).count(),
        }
        
        # Loan performance report
        all_loans = Loan.objects.all()
        context['loan_performance'] = {
            'applications_30d': all_loans.filter(application_date__gte=thirty_days_ago).count(),
            'approvals_30d': all_loans.filter(
                application_date__gte=thirty_days_ago, 
                status__in=['approved', 'active', 'completed']
            ).count(),
            'approval_rate': 0,
        }
        
        if context['loan_performance']['applications_30d'] > 0:
            context['loan_performance']['approval_rate'] = (
                context['loan_performance']['approvals_30d'] / 
                context['loan_performance']['applications_30d'] * 100
            )
        
        # System health
        context['system_health'] = {
            'total_users': User.objects.count(),
            'total_loans': all_loans.count(),
            'pending_documents': 0,  # Will be calculated if documents app exists
        }
        
        try:
            from documents.models import Document
            context['system_health']['pending_documents'] = Document.objects.filter(
                status='pending'
            ).count()
        except ImportError:
            pass
        
        return context


class AddGroupView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin Add Group"""
    template_name = 'dashboard/admin/add_group.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.auth.models import Permission
        
        context['permissions'] = Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'codename')
        
        return context
    
    def post(self, request, *args, **kwargs):
        from django.contrib.auth.models import Group, Permission
        from django.contrib import messages
        from django.shortcuts import redirect
        
        name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        
        if not name:
            messages.error(request, 'Group name is required.')
            return self.get(request, *args, **kwargs)
        
        try:
            # Create the group
            group = Group.objects.create(name=name)
            
            # Add permissions if selected
            if permission_ids:
                permissions = Permission.objects.filter(id__in=permission_ids)
                group.permissions.set(permissions)
            
            messages.success(request, f'Group "{name}" created successfully!')
            return redirect('dashboard:manage_groups')
            
        except Exception as e:
            messages.error(request, f'Error creating group: {str(e)}')
            return self.get(request, *args, **kwargs)


class ManageGroupsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin Manage Groups"""
    template_name = 'dashboard/admin/manage_groups.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.auth.models import Group, Permission
        from accounts.models import User
        
        groups = Group.objects.all().prefetch_related('permissions')
        
        context['groups'] = groups
        context['total_permissions'] = Permission.objects.count()
        context['total_users_in_groups'] = User.objects.filter(groups__isnull=False).distinct().count()
        # Count groups that have users
        from accounts.models import User
        active_group_count = 0
        for group in groups:
            if User.objects.filter(groups=group).exists():
                active_group_count += 1
        context['active_groups'] = active_group_count
        
        return context
