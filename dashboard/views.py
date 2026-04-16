from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta

from loans.models import Loan, LoanApprovalRequest, LoanType
from loans.models import SecurityTransaction
from payments.models import PaymentCollection, DefaultProvision, Payment
from clients.models import BorrowerGroup, Branch, AdminAuditLog, GroupMembership
from loans.views import VerifySecurityDepositView
from accounts.models import User


def _get_vault_balance(branch):
    try:
        from loans.models import BranchVault
        return BranchVault.objects.get(branch=branch).balance
    except Exception:
        return 0


def _group_loans_by_group(loans):
    """Group loans by their borrower's primary group, no duplicates."""
    from collections import OrderedDict
    groups = OrderedDict()
    for loan in loans:
        membership = loan.borrower.group_memberships.filter(is_active=True).select_related('group').first()
        group_name = membership.group.name if membership else 'No Group'
        group_obj = membership.group if membership else None
        key = group_obj.pk if group_obj else 0
        if key not in groups:
            groups[key] = {'group': group_obj, 'name': group_name, 'loans': []}
        groups[key]['loans'].append(loan)
    return list(groups.values())


def _group_collections_by_group(collections):
    """Group PaymentCollection records by borrower's primary group."""
    from collections import OrderedDict
    groups = OrderedDict()
    for coll in collections:
        membership = coll.loan.borrower.group_memberships.filter(is_active=True).select_related('group').first()
        group_name = membership.group.name if membership else 'No Group'
        group_obj = membership.group if membership else None
        key = group_obj.pk if group_obj else 0
        if key not in groups:
            groups[key] = {'group': group_obj, 'name': group_name, 'items': []}
        groups[key]['items'].append(coll)
    return list(groups.values())


@login_required
def dashboard(request):
    """Route to appropriate dashboard based on user role"""
    user = request.user
    
    # Debug: Check if user has role
    if not hasattr(user, 'role') or not user.role:
        # If role is missing, try to set default role
        if user.is_superuser:
            user.role = 'admin'
            user.save()
        else:
            return render(request, 'dashboard/access_denied.html', {
                'message': 'Your user account does not have a role assigned. Please contact your administrator.'
            })
    
    # Route based on role
    if user.role == 'loan_officer':
        return loan_officer_dashboard(request)
    elif user.role == 'manager':
        return manager_dashboard(request)
    elif user.role == 'admin':
        return admin_dashboard(request)
    elif user.role == 'borrower':
        # Redirect borrowers to loan officer's borrower management
        # Find their assigned loan officer
        if user.assigned_officer:
            from django.shortcuts import redirect
            return redirect('clients:officer_clients', officer_id=user.assigned_officer.id)
        else:
            # If no officer assigned, show a message
            return render(request, 'dashboard/access_denied.html', {
                'message': 'You have not been assigned to a loan officer. Please contact your administrator.'
            })
    else:
        return render(request, 'dashboard/access_denied.html', {
            'message': f'Unknown role: {user.role}. Please contact your administrator.'
        })


@login_required
def loan_officer_dashboard(request):
    """Loan Officer Dashboard"""
    officer = request.user
    
    # Get metrics
    groups = BorrowerGroup.objects.filter(assigned_officer=officer)
    
    # Get clients assigned to this officer - include both directly assigned and group members
    from django.db.models import Q
    clients = User.objects.filter(
        Q(assigned_officer=officer) | Q(group_memberships__group__assigned_officer=officer),
        role='borrower',
        is_active=True
    ).distinct()
    
    active_loans = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        status='active'
    ).distinct()
    
    # Today's collections
    today = date.today()
    today_collections = PaymentCollection.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        collection_date=today
    ).distinct()
    
    today_expected = sum(c.expected_amount for c in today_collections) or 0
    today_collected = sum(c.collected_amount for c in today_collections) or 0

    # Overdue: unpaid installments past their due date
    from payments.models import PaymentSchedule as PS
    today_defaults = PS.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        loan__status='active',
        is_paid=False,
        due_date__lt=today,
    ).values('loan').distinct().count()  # count distinct loans with overdue installments
    
    # Pending actions
    # Security deposits awaiting verification - loans with paid deposits but not verified
    pending_security = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        security_deposit__paid_amount__gt=0,
        security_deposit__is_verified=False
    ).distinct().count()
    
    # Ready to disburse - approved loans with verified deposits
    ready_to_disburse = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        status='approved',
        security_deposit__is_verified=True
    ).distinct().count()
    
    # Outstanding balance — use balance_remaining if set, else fall back to total_amount - amount_paid
    from django.db.models import F, ExpressionWrapper, DecimalField as DField
    outstanding_balance = active_loans.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('total_amount') - F('amount_paid'),
                output_field=DField(max_digits=14, decimal_places=2)
            )
        )
    )['total'] or 0
    
    # Workload percentage (assuming max capacity is 100 groups/clients)
    total_workload = groups.count() + clients.count()
    workload_percentage = (total_workload / 200 * 100) if total_workload > 0 else 0
    
    # Clients expected to pay today
    clients_expected_today = today_collections.select_related('loan__borrower').order_by('-expected_amount')
    
    # Recent transactions (from passbook/payment records)
    from payments.models import PaymentCollection as PC
    recent_transactions = PC.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer)
    ).select_related('loan__borrower').order_by('-collection_date').distinct()[:10]
    
    # Format recent transactions for display
    formatted_transactions = []
    for trans in recent_transactions:
        formatted_transactions.append({
            'type': 'payment',
            'description': f"Payment from {trans.loan.borrower.full_name}",
            'amount': trans.collected_amount,
            'created_at': trans.collection_date,
            'client_name': trans.loan.borrower.full_name,
        })
    
    # Passbook entries - get recent entries across all loans
    from payments.models import PassbookEntry
    passbook_entries = PassbookEntry.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer)
    ).select_related('loan__borrower').order_by('-entry_date').distinct()[:20]
    
    # Pending documents for review - get clients in officer's groups with pending documents
    from documents.models import ClientDocument
    
    pending_documents = []
    try:
        # Get all clients in officer's groups or directly assigned
        clients_in_groups = User.objects.filter(
            Q(group_memberships__group__assigned_officer=officer, group_memberships__is_active=True) |
            Q(assigned_officer=officer),
            role='borrower'
        ).values_list('id', flat=True).distinct()
        
        # Get pending documents from those clients
        pending_documents = ClientDocument.objects.filter(
            client_id__in=clients_in_groups,
            status='pending'
        ).select_related('client').distinct()[:10]
    except Exception as e:
        print(f"Error fetching pending documents: {e}")
        pending_documents = []
    
    # Document verification - get pending and verified verifications
    from documents.models import ClientVerification
    try:
        # Get all clients in officer's groups or directly assigned
        clients_in_groups = User.objects.filter(
            Q(group_memberships__group__assigned_officer=officer, group_memberships__is_active=True) |
            Q(assigned_officer=officer),
            role='borrower'
        ).values_list('id', flat=True).distinct()
        
        # Get pending verifications (documents submitted but not yet verified)
        pending_verifications = ClientVerification.objects.filter(
            client_id__in=clients_in_groups,
            status__in=['documents_submitted', 'documents_rejected']
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        # Get verified verifications (approved documents)
        verified_verifications = ClientVerification.objects.filter(
            client_id__in=clients_in_groups,
            status='verified'
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        pending_verification_count = pending_verifications.count()
        verified_client_count = verified_verifications.count()
    except Exception as e:
        print(f"Error fetching document verifications: {e}")
        pending_verifications = []
        verified_verifications = []
        pending_verification_count = 0
        verified_client_count = 0
    
    context = {
        'groups_count': groups.count(),
        'clients_count': clients.count(),
        'active_loans_count': active_loans.count(),
        'today_expected': today_expected,
        'today_collected': today_collected,
        'today_pending': today_expected - today_collected,
        'today_defaults': today_defaults,
        'groups': groups[:5],
        'pending_security': pending_security,
        'ready_to_disburse': ready_to_disburse,
        'defaults_to_follow': DefaultProvision.objects.filter(
            Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
            status='active'
        ).distinct().count(),
        'outstanding_balance': outstanding_balance,
        'workload_percentage': workload_percentage,
        'clients_expected_today': clients_expected_today,
        'collections_by_group': _group_collections_by_group(clients_expected_today),
        'recent_transactions': formatted_transactions,
        'passbook_entries': passbook_entries,
        'pending_documents': pending_documents,
        'pending_documents_count': pending_documents.count(),
        'pending_verifications': pending_verifications,
        'verified_verifications': verified_verifications,
        'pending_verification_count': pending_verification_count,
        'verified_client_count': verified_client_count,
        'pending_upfront_loans': Loan.objects.filter(
            Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
            status='approved',
            upfront_payment_verified=False,
            upfront_payment_paid=0,
        ).select_related('borrower').distinct(),
        'awaiting_verification_loans': Loan.objects.filter(
            Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
            status='approved',
            upfront_payment_paid__gt=0,
            upfront_payment_verified=False,
        ).select_related('borrower').distinct(),
        'ready_to_disburse_loans': Loan.objects.filter(
            Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
            status='approved',
            upfront_payment_verified=True,
        ).select_related('borrower').distinct(),
        'pending_security_transactions': SecurityTransaction.objects.filter(
            loan__loan_officer=officer,
            status='pending',
        ).select_related('loan', 'loan__borrower').order_by('-created_at'),
        'active_loans_with_security': Loan.objects.filter(
            Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
            status__in=['active', 'completed'],
            security_deposit__is_verified=True,
        ).select_related('borrower', 'security_deposit').distinct(),
        'security_by_group': _group_loans_by_group(
            Loan.objects.filter(
                Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
                status__in=['active', 'completed'],
                security_deposit__is_verified=True,
            ).select_related('borrower', 'security_deposit').distinct()
        ),
        # Security summary counts
        'sec_deposits_count': SecurityTransaction.objects.filter(
            loan__loan_officer=officer, transaction_type='adjustment', status='approved'
        ).count(),
        'sec_topups_count': SecurityTransaction.objects.filter(
            loan__loan_officer=officer, transaction_type='carry_forward'
        ).count(),
        'sec_returns_count': SecurityTransaction.objects.filter(
            loan__loan_officer=officer, transaction_type='return', status='approved'
        ).count(),
        'sec_withdrawals_count': SecurityTransaction.objects.filter(
            loan__loan_officer=officer, transaction_type='withdrawal', status='approved'
        ).count(),
        'sec_pending_count': SecurityTransaction.objects.filter(
            loan__loan_officer=officer, status='pending'
        ).count(),
    }

    # 1. Processing fees status
    from loans.models import LoanApplication
    officer_apps = LoanApplication.objects.filter(loan_officer=officer, processing_fee__gt=0)
    context['fees_pending_count'] = officer_apps.filter(processing_fee_verified=False).count()
    context['fees_verified_count'] = officer_apps.filter(processing_fee_verified=True).count()
    context['fees_pending_list'] = officer_apps.filter(
        processing_fee_verified=False
    ).select_related('borrower').order_by('-created_at')[:10]

    # 2. Overdue clients list
    from payments.models import PaymentSchedule as PS2
    overdue_schedules = PS2.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        loan__status='active', is_paid=False, due_date__lt=today,
    ).select_related('loan__borrower', 'loan').order_by('due_date').distinct()
    overdue_clients = {}
    for sched in overdue_schedules:
        lid = sched.loan_id
        if lid not in overdue_clients:
            overdue_clients[lid] = {
                'loan': sched.loan,
                'days_overdue': (today - sched.due_date).days,
                'overdue_amount': sched.total_amount - sched.amount_paid,
            }
    context['overdue_clients_list'] = sorted(overdue_clients.values(), key=lambda x: -x['days_overdue'])[:20]

    # 4. Loan applications status
    context['my_applications'] = LoanApplication.objects.filter(
        loan_officer=officer
    ).select_related('borrower').order_by('-created_at')[:15]
    context['apps_pending'] = LoanApplication.objects.filter(loan_officer=officer, status='pending').count()
    context['apps_approved'] = LoanApplication.objects.filter(loan_officer=officer, status='approved').count()
    context['apps_rejected'] = LoanApplication.objects.filter(loan_officer=officer, status='rejected').count()

    # 5. Default collections summary
    from payments.models import DefaultCollection, PaymentSchedule
    
    # Get loans with overdue payments (practical approach)
    # A loan is considered "defaulted" if it has unpaid schedules past their due date
    overdue_schedules = PaymentSchedule.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        loan__status='active',
        is_paid=False,
        due_date__lt=today
    ).select_related('loan').distinct()
    
    # Get unique defaulted loan IDs
    defaulted_loan_ids = overdue_schedules.values_list('loan_id', flat=True).distinct()
    default_loans = Loan.objects.filter(id__in=defaulted_loan_ids)
    
    context['default_loans_count'] = default_loans.count()
    context['default_total_outstanding'] = default_loans.aggregate(
        t=Sum('balance_remaining')
    )['t'] or 0
    context['default_collected_this_month'] = DefaultCollection.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        collection_date__gte=today.replace(day=1),
    ).distinct().aggregate(t=Sum('amount_paid'))['t'] or 0

    # 6. Securities amounts summary
    from loans.models import SecurityDeposit as SD
    sec_loans = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        security_deposit__is_verified=True,
    ).distinct()
    sec_agg = SD.objects.filter(loan__in=sec_loans).aggregate(
        total_paid=Sum('paid_amount'),
        total_used=Sum('security_used'),
        total_returned=Sum('security_returned'),
    )
    context['sec_total_held'] = sec_agg['total_paid'] or 0
    context['sec_total_used'] = sec_agg['total_used'] or 0
    context['sec_total_returned'] = sec_agg['total_returned'] or 0
    context['sec_total_available'] = max(0, (sec_agg['total_paid'] or 0) - (sec_agg['total_used'] or 0) - (sec_agg['total_returned'] or 0))

    # 7. This month's performance
    month_start = today.replace(day=1)
    context['month_disbursed'] = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        disbursement_date__date__gte=month_start,
    ).distinct().count()
    context['month_collected'] = PaymentCollection.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        collection_date__gte=month_start,
        collected_amount__gt=0,
    ).distinct().aggregate(t=Sum('collected_amount'))['t'] or 0
    context['month_new_clients'] = User.objects.filter(
        Q(assigned_officer=officer) | Q(group_memberships__group__assigned_officer=officer),
        role='borrower',
        date_joined__date__gte=month_start,
    ).distinct().count()
    context['month_completed_loans'] = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        status='completed',
        updated_at__date__gte=month_start,
    ).distinct().count()

    # Get filter parameters for overdue loans
    officer_group_filter = request.GET.get('group', '')
    limit = request.GET.get('limit', '5')  # Default to 5 records
    
    # Convert limit to int, handle 'all' case
    try:
        if limit.lower() == 'all':
            limit_int = None
        else:
            limit_int = int(limit)
    except:
        limit_int = 5

    # Build overdue loans list
    officer_active_loans = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        status='active'
    ).select_related('borrower', 'loan_officer').distinct()
    
    # Apply group filter
    if officer_group_filter:
        officer_active_loans = officer_active_loans.filter(
            borrower__group_memberships__group_id=officer_group_filter,
            borrower__group_memberships__is_active=True
        )
    
    overdue_loans = []
    for loan in officer_active_loans:
        oldest = PS.objects.filter(loan=loan, is_paid=False, due_date__lt=today).order_by('due_date').first()
        if oldest:
            # Get borrower's group
            membership = loan.borrower.group_memberships.filter(is_active=True).first()
            group_name = membership.group.name if membership else 'No Group'
            
            overdue_loans.append({
                'loan': loan,
                'days_overdue': (today - oldest.due_date).days,
                'balance': loan.balance_remaining or 0,
                'group_name': group_name,
            })
    
    # Always sort by days overdue (descending) - most overdue first
    overdue_loans.sort(key=lambda x: -x['days_overdue'])
    
    # Store total count before limiting
    total_overdue_count = len(overdue_loans)
    
    # Apply limit
    if limit_int:
        overdue_loans_limited = overdue_loans[:limit_int]
    else:
        overdue_loans_limited = overdue_loans
    
    context['overdue_loans'] = overdue_loans_limited
    context['total_overdue_count'] = total_overdue_count
    context['overdue_filters'] = {
        'group': officer_group_filter,
        'limit': limit,
    }

    return render(request, 'dashboard/loan_officer_enhanced.html', context)


@login_required
def admin_performance_report(request):
    """System-wide financial activity log for admins."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')

    from django.db.models import Q, Sum
    from loans.models import Loan, LoanApplication
    from payments.models import PaymentCollection, DefaultCollection
    from clients.models import Branch
    from datetime import date, datetime

    today = date.today()
    date_from_str = request.GET.get('date_from', today.replace(day=1).isoformat())
    date_to_str = request.GET.get('date_to', today.isoformat())
    activity_type = request.GET.get('activity_type', '')
    search = request.GET.get('search', '').strip()
    branch_filter = request.GET.get('branch', '')
    officer_filter = request.GET.get('officer', '')

    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except Exception:
        date_from = today.replace(day=1)
        date_to = today

    branches = Branch.objects.filter(is_active=True).order_by('name')
    all_officers = User.objects.filter(role='loan_officer', is_active=True).order_by('first_name')

    loan_q = Q()
    col_q = Q()
    if branch_filter:
        loan_q &= Q(loan_officer__officer_assignment__branch__iexact=branch_filter)
        col_q &= Q(loan__loan_officer__officer_assignment__branch__iexact=branch_filter)
    if officer_filter:
        loan_q &= Q(loan_officer_id=officer_filter)
        col_q &= Q(loan__loan_officer_id=officer_filter)

    def _sl(qs):
        if search:
            return qs.filter(
                Q(borrower__first_name__icontains=search) |
                Q(borrower__last_name__icontains=search) |
                Q(application_number__icontains=search)
            )
        return qs

    def _sc(qs):
        if search:
            return qs.filter(
                Q(loan__borrower__first_name__icontains=search) |
                Q(loan__borrower__last_name__icontains=search) |
                Q(loan__application_number__icontains=search)
            )
        return qs

    activities = []

    if not activity_type or activity_type == 'disbursement':
        for loan in _sl(Loan.objects.filter(loan_q, disbursement_date__date__gte=date_from, disbursement_date__date__lte=date_to).distinct().select_related('borrower', 'loan_officer')):
            activities.append({'date': loan.disbursement_date.date() if loan.disbursement_date else None, 'type': 'Disbursement', 'type_color': 'blue', 'reference': loan.application_number, 'reference_url': f'/loans/{loan.pk}/', 'client': loan.borrower.get_full_name(), 'officer': loan.loan_officer.get_full_name() if loan.loan_officer else '—', 'branch': getattr(getattr(loan.loan_officer, 'officer_assignment', None), 'branch', '—') if loan.loan_officer else '—', 'amount': loan.principal_amount, 'status': 'Disbursed', 'status_color': 'blue'})

    if not activity_type or activity_type == 'collection':
        for c in _sc(PaymentCollection.objects.filter(col_q, collection_date__gte=date_from, collection_date__lte=date_to, collected_amount__gt=0).distinct().select_related('loan__borrower', 'loan__loan_officer')):
            activities.append({'date': c.collection_date, 'type': 'Collection', 'type_color': 'green', 'reference': c.loan.application_number, 'reference_url': f'/loans/{c.loan.pk}/', 'client': c.loan.borrower.get_full_name(), 'officer': c.loan.loan_officer.get_full_name() if c.loan.loan_officer else '—', 'branch': getattr(getattr(c.loan.loan_officer, 'officer_assignment', None), 'branch', '—') if c.loan.loan_officer else '—', 'amount': c.collected_amount, 'status': 'Partial' if c.is_partial else 'Paid', 'status_color': 'yellow' if c.is_partial else 'green'})

    if not activity_type or activity_type == 'default':
        for dc in _sc(DefaultCollection.objects.filter(col_q, collection_date__gte=date_from, collection_date__lte=date_to).distinct().select_related('loan__borrower', 'loan__loan_officer')):
            activities.append({'date': dc.collection_date, 'type': 'Default Collection', 'type_color': 'red', 'reference': dc.loan.application_number, 'reference_url': f'/loans/{dc.loan.pk}/', 'client': dc.loan.borrower.get_full_name(), 'officer': dc.loan.loan_officer.get_full_name() if dc.loan.loan_officer else '—', 'branch': getattr(getattr(dc.loan.loan_officer, 'officer_assignment', None), 'branch', '—') if dc.loan.loan_officer else '—', 'amount': dc.amount_paid, 'status': 'Collected', 'status_color': 'red'})

    if not activity_type or activity_type == 'completion':
        for loan in _sl(Loan.objects.filter(loan_q, status='completed', updated_at__date__gte=date_from, updated_at__date__lte=date_to).distinct().select_related('borrower', 'loan_officer')):
            activities.append({'date': loan.updated_at.date() if loan.updated_at else loan.maturity_date, 'type': 'Loan Completion', 'type_color': 'teal', 'reference': loan.application_number, 'reference_url': f'/loans/{loan.pk}/', 'client': loan.borrower.get_full_name(), 'officer': loan.loan_officer.get_full_name() if loan.loan_officer else '—', 'branch': getattr(getattr(loan.loan_officer, 'officer_assignment', None), 'branch', '—') if loan.loan_officer else '—', 'amount': loan.total_amount or loan.principal_amount, 'status': 'Completed', 'status_color': 'teal'})

    if not activity_type or activity_type == 'fee':
        fee_q = Q(processing_fee__gt=0, created_at__date__gte=date_from, created_at__date__lte=date_to)
        if branch_filter:
            fee_q &= Q(loan_officer__officer_assignment__branch__iexact=branch_filter)
        if officer_filter:
            fee_q &= Q(loan_officer_id=officer_filter)
        fee_qs = LoanApplication.objects.filter(fee_q).select_related('borrower', 'loan_officer')
        if search:
            fee_qs = fee_qs.filter(Q(borrower__first_name__icontains=search) | Q(borrower__last_name__icontains=search) | Q(application_number__icontains=search))
        for app in fee_qs:
            activities.append({'date': app.created_at.date(), 'type': 'Processing Fee', 'type_color': 'violet', 'reference': app.application_number, 'reference_url': f'/loans/applications/{app.pk}/approve/', 'client': app.borrower.get_full_name(), 'officer': app.loan_officer.get_full_name() if app.loan_officer else '—', 'branch': getattr(getattr(app.loan_officer, 'officer_assignment', None), 'branch', '—') if app.loan_officer else '—', 'amount': app.processing_fee, 'status': 'Verified' if app.processing_fee_verified else 'Pending', 'status_color': 'green' if app.processing_fee_verified else 'amber'})

    activities.sort(key=lambda x: x['date'] or date.min, reverse=True)
    total_amount = sum(a['amount'] for a in activities if a['amount'])

    all_col = PaymentCollection.objects.filter(col_q, collection_date__gte=date_from, collection_date__lte=date_to, collected_amount__gt=0).distinct()
    all_def = DefaultCollection.objects.filter(col_q, collection_date__gte=date_from, collection_date__lte=date_to).distinct()
    all_dis = Loan.objects.filter(loan_q, disbursement_date__date__gte=date_from, disbursement_date__date__lte=date_to).distinct()
    all_comp = Loan.objects.filter(loan_q, status='completed', updated_at__date__gte=date_from, updated_at__date__lte=date_to).distinct()

    return render(request, 'dashboard/admin_performance_report.html', {
        'date_from': date_from, 'date_to': date_to,
        'activity_type': activity_type, 'search': search,
        'branch_filter': branch_filter, 'officer_filter': officer_filter,
        'branches': branches, 'all_officers': all_officers,
        'activities': activities, 'total_amount': total_amount,
        'activity_count': len(activities),
        'disbursed_count': all_dis.count(),
        'disbursed_amount': all_dis.aggregate(t=Sum('principal_amount'))['t'] or 0,
        'total_collected': all_col.aggregate(t=Sum('collected_amount'))['t'] or 0,
        'total_expected': all_col.aggregate(t=Sum('expected_amount'))['t'] or 0,
        'completed_count': all_comp.count(),
        'defaults_collected': all_def.aggregate(t=Sum('amount_paid'))['t'] or 0,
    })


@login_required
def manager_performance_report(request):
    """Branch-wide financial activity log for managers."""
    if request.user.role not in ['manager', 'admin'] and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')

    from django.db.models import Q, Sum
    from loans.models import Loan, LoanApplication
    from payments.models import PaymentCollection, DefaultCollection
    from datetime import date, datetime

    today = date.today()
    date_from_str = request.GET.get('date_from', today.replace(day=1).isoformat())
    date_to_str = request.GET.get('date_to', today.isoformat())
    activity_type = request.GET.get('activity_type', '')
    search = request.GET.get('search', '').strip()
    officer_filter = request.GET.get('officer', '')

    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except Exception:
        date_from = today.replace(day=1)
        date_to = today

    try:
        branch = request.user.managed_branch
    except Exception:
        branch = None

    if request.user.role == 'admin' or request.user.is_superuser:
        branch_officers = User.objects.filter(role='loan_officer', is_active=True).order_by('first_name')
        loan_q = Q()
        col_q = Q()
    elif branch:
        branch_officers = User.objects.filter(
            role='loan_officer', officer_assignment__branch__iexact=branch.name, is_active=True
        ).order_by('first_name')
        # Only show loans where the loan officer is from this branch
        loan_q = Q(loan_officer__officer_assignment__branch__iexact=branch.name)
        col_q = Q(loan__loan_officer__officer_assignment__branch__iexact=branch.name)
    else:
        return render(request, 'dashboard/access_denied.html')

    if officer_filter:
        loan_q &= Q(loan_officer_id=officer_filter)
        col_q &= Q(loan__loan_officer_id=officer_filter)

    def _search_loan(qs):
        if search:
            return qs.filter(
                Q(borrower__first_name__icontains=search) |
                Q(borrower__last_name__icontains=search) |
                Q(application_number__icontains=search)
            )
        return qs

    def _search_col(qs):
        if search:
            return qs.filter(
                Q(loan__borrower__first_name__icontains=search) |
                Q(loan__borrower__last_name__icontains=search) |
                Q(loan__application_number__icontains=search)
            )
        return qs

    activities = []

    if not activity_type or activity_type == 'disbursement':
        qs = _search_loan(Loan.objects.filter(
            loan_q, disbursement_date__date__gte=date_from, disbursement_date__date__lte=date_to
        ).distinct().select_related('borrower', 'loan_officer'))
        for loan in qs:
            activities.append({
                'date': loan.disbursement_date.date() if loan.disbursement_date else None,
                'type': 'Disbursement', 'type_color': 'blue',
                'reference': loan.application_number,
                'reference_url': f'/loans/{loan.pk}/',
                'client': loan.borrower.get_full_name(),
                'officer': loan.loan_officer.get_full_name() if loan.loan_officer else '—',
                'amount': loan.principal_amount,
                'status': 'Disbursed', 'status_color': 'blue',
            })

    if not activity_type or activity_type == 'collection':
        qs = _search_col(PaymentCollection.objects.filter(
            col_q, collection_date__gte=date_from, collection_date__lte=date_to, collected_amount__gt=0
        ).distinct().select_related('loan__borrower', 'loan__loan_officer'))
        for c in qs:
            activities.append({
                'date': c.collection_date,
                'type': 'Collection', 'type_color': 'green',
                'reference': c.loan.application_number,
                'reference_url': f'/loans/{c.loan.pk}/',
                'client': c.loan.borrower.get_full_name(),
                'officer': c.loan.loan_officer.get_full_name() if c.loan.loan_officer else '—',
                'amount': c.collected_amount,
                'status': 'Partial' if c.is_partial else 'Paid',
                'status_color': 'yellow' if c.is_partial else 'green',
            })

    if not activity_type or activity_type == 'default':
        qs = _search_col(DefaultCollection.objects.filter(
            col_q, collection_date__gte=date_from, collection_date__lte=date_to
        ).distinct().select_related('loan__borrower', 'loan__loan_officer'))
        for dc in qs:
            activities.append({
                'date': dc.collection_date,
                'type': 'Default Collection', 'type_color': 'red',
                'reference': dc.loan.application_number,
                'reference_url': f'/loans/{dc.loan.pk}/',
                'client': dc.loan.borrower.get_full_name(),
                'officer': dc.loan.loan_officer.get_full_name() if dc.loan.loan_officer else '—',
                'amount': dc.amount_paid,
                'status': 'Collected', 'status_color': 'red',
            })

    if not activity_type or activity_type == 'completion':
        qs = _search_loan(Loan.objects.filter(
            loan_q, status='completed',
            updated_at__date__gte=date_from,
            updated_at__date__lte=date_to,
        ).distinct().select_related('borrower', 'loan_officer'))
        for loan in qs:
            activities.append({
                'date': loan.updated_at.date() if loan.updated_at else loan.maturity_date,
                'type': 'Loan Completion', 'type_color': 'teal',
                'reference': loan.application_number,
                'reference_url': f'/loans/{loan.pk}/',
                'client': loan.borrower.get_full_name(),
                'officer': loan.loan_officer.get_full_name() if loan.loan_officer else '—',
                'amount': loan.total_amount or loan.principal_amount,
                'status': 'Completed', 'status_color': 'teal',
            })

    if not activity_type or activity_type == 'fee':
        fee_q = Q(loan_officer__officer_assignment__branch__iexact=branch.name) if branch else Q()
        if officer_filter:
            fee_q &= Q(loan_officer_id=officer_filter)
        qs = LoanApplication.objects.filter(
            fee_q, processing_fee__gt=0,
            created_at__date__gte=date_from, created_at__date__lte=date_to,
        ).select_related('borrower', 'loan_officer')
        if search:
            qs = qs.filter(
                Q(borrower__first_name__icontains=search) |
                Q(borrower__last_name__icontains=search) |
                Q(application_number__icontains=search)
            )
        for app in qs:
            activities.append({
                'date': app.created_at.date(),
                'type': 'Processing Fee', 'type_color': 'violet',
                'reference': app.application_number,
                'reference_url': f'/loans/applications/{app.pk}/approve/',
                'client': app.borrower.get_full_name(),
                'officer': app.loan_officer.get_full_name() if app.loan_officer else '—',
                'amount': app.processing_fee,
                'status': 'Verified' if app.processing_fee_verified else 'Pending',
                'status_color': 'green' if app.processing_fee_verified else 'amber',
            })

    activities.sort(key=lambda x: x['date'] or date.min, reverse=True)
    total_amount = sum(a['amount'] for a in activities if a['amount'])

    # Summary totals (full period, no type filter)
    all_col = PaymentCollection.objects.filter(col_q, collection_date__gte=date_from, collection_date__lte=date_to, collected_amount__gt=0).distinct()
    all_def = DefaultCollection.objects.filter(col_q, collection_date__gte=date_from, collection_date__lte=date_to).distinct()
    all_dis = Loan.objects.filter(loan_q, disbursement_date__date__gte=date_from, disbursement_date__date__lte=date_to).distinct()
    all_comp = Loan.objects.filter(loan_q, status='completed', updated_at__date__gte=date_from, updated_at__date__lte=date_to).distinct()

    return render(request, 'dashboard/manager_performance_report.html', {
        'date_from': date_from, 'date_to': date_to,
        'activity_type': activity_type, 'search': search,
        'officer_filter': officer_filter,
        'branch_officers': branch_officers,
        'branch': branch,
        'activities': activities,
        'total_amount': total_amount,
        'activity_count': len(activities),
        'disbursed_count': all_dis.count(),
        'disbursed_amount': all_dis.aggregate(t=Sum('principal_amount'))['t'] or 0,
        'total_collected': all_col.aggregate(t=Sum('collected_amount'))['t'] or 0,
        'total_expected': all_col.aggregate(t=Sum('expected_amount'))['t'] or 0,
        'completed_count': all_comp.count(),
        'defaults_collected': all_def.aggregate(t=Sum('amount_paid'))['t'] or 0,
    })


@login_required
def officer_applications(request):
    """Dedicated loan applications page for loan officers."""
    if request.user.role not in ['loan_officer', 'manager', 'admin']:
        return render(request, 'dashboard/access_denied.html')
    from loans.models import LoanApplication
    officer = request.user
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '').strip()
    apps = LoanApplication.objects.filter(loan_officer=officer).select_related('borrower', 'group').order_by('-created_at')
    if status_filter:
        apps = apps.filter(status=status_filter)
    if search:
        from django.db.models import Q
        apps = apps.filter(
            Q(borrower__first_name__icontains=search) |
            Q(borrower__last_name__icontains=search) |
            Q(application_number__icontains=search)
        )
    all_apps = LoanApplication.objects.filter(loan_officer=officer)
    return render(request, 'dashboard/officer_applications.html', {
        'apps': apps,
        'status_filter': status_filter,
        'search': search,
        'total': all_apps.count(),
        'pending': all_apps.filter(status='pending').count(),
        'approved': all_apps.filter(status='approved').count(),
        'rejected': all_apps.filter(status='rejected').count(),
    })


@login_required
def officer_performance_report(request):
    """Dedicated performance report for loan officers with date filtering."""
    if request.user.role not in ['loan_officer', 'manager', 'admin'] and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')

    from django.db.models import Q, Sum
    from loans.models import Loan, LoanApplication
    from payments.models import PaymentCollection, DefaultCollection
    from datetime import date, datetime

    officer = request.user
    today = date.today()

    date_from_str = request.GET.get('date_from', today.replace(day=1).isoformat())
    date_to_str = request.GET.get('date_to', today.isoformat())
    activity_type = request.GET.get('activity_type', '')
    search = request.GET.get('search', '').strip()

    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except Exception:
        date_from = today.replace(day=1)
        date_to = today

    loan_q = Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer)
    col_q = Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer)

    # Build unified activity log
    activities = []

    # 1. Disbursements
    if not activity_type or activity_type == 'disbursement':
        qs = Loan.objects.filter(
            loan_q,
            disbursement_date__date__gte=date_from,
            disbursement_date__date__lte=date_to,
        ).distinct().select_related('borrower', 'loan_officer')
        if search:
            qs = qs.filter(
                Q(borrower__first_name__icontains=search) |
                Q(borrower__last_name__icontains=search) |
                Q(application_number__icontains=search)
            )
        for loan in qs:
            activities.append({
                'date': loan.disbursement_date.date() if loan.disbursement_date else None,
                'type': 'Disbursement',
                'type_color': 'blue',
                'reference': loan.application_number,
                'reference_url': f'/loans/{loan.pk}/',
                'client': loan.borrower.get_full_name(),
                'amount': loan.principal_amount,
                'status': 'Disbursed',
                'status_color': 'blue',
                'performed_by': loan.loan_officer.get_full_name() if loan.loan_officer else '—',
                'pk': loan.pk,
                'model': 'loan',
            })

    # 2. Collections
    if not activity_type or activity_type == 'collection':
        qs = PaymentCollection.objects.filter(
            col_q,
            collection_date__gte=date_from,
            collection_date__lte=date_to,
            collected_amount__gt=0,
        ).distinct().select_related('loan__borrower', 'collected_by')
        if search:
            qs = qs.filter(
                Q(loan__borrower__first_name__icontains=search) |
                Q(loan__borrower__last_name__icontains=search) |
                Q(loan__application_number__icontains=search)
            )
        for c in qs:
            activities.append({
                'date': c.collection_date,
                'type': 'Collection',
                'type_color': 'green',
                'reference': c.loan.application_number,
                'reference_url': f'/loans/{c.loan.pk}/',
                'client': c.loan.borrower.get_full_name(),
                'amount': c.collected_amount,
                'status': 'Partial' if c.is_partial else 'Paid',
                'status_color': 'yellow' if c.is_partial else 'green',
                'performed_by': c.collected_by.get_full_name() if c.collected_by else '—',
                'pk': c.loan.pk,
                'model': 'loan',
            })

    # 3. Default Collections
    if not activity_type or activity_type == 'default':
        qs = DefaultCollection.objects.filter(
            col_q,
            collection_date__gte=date_from,
            collection_date__lte=date_to,
        ).distinct().select_related('loan__borrower', 'recorded_by')
        if search:
            qs = qs.filter(
                Q(loan__borrower__first_name__icontains=search) |
                Q(loan__borrower__last_name__icontains=search) |
                Q(loan__application_number__icontains=search)
            )
        for dc in qs:
            activities.append({
                'date': dc.collection_date,
                'type': 'Default Collection',
                'type_color': 'red',
                'reference': dc.loan.application_number,
                'reference_url': f'/loans/{dc.loan.pk}/',
                'client': dc.loan.borrower.get_full_name(),
                'amount': dc.amount_paid,
                'status': 'Collected',
                'status_color': 'red',
                'performed_by': dc.recorded_by.get_full_name() if dc.recorded_by else '—',
                'pk': dc.loan.pk,
                'model': 'loan',
            })

    # 4. Loan Completions
    if not activity_type or activity_type == 'completion':
        qs = Loan.objects.filter(
            loan_q,
            status='completed',
            updated_at__date__gte=date_from,
            updated_at__date__lte=date_to,
        ).distinct().select_related('borrower', 'loan_officer')
        if search:
            qs = qs.filter(
                Q(borrower__first_name__icontains=search) |
                Q(borrower__last_name__icontains=search) |
                Q(application_number__icontains=search)
            )
        for loan in qs:
            activities.append({
                'date': loan.updated_at.date() if loan.updated_at else loan.maturity_date,
                'type': 'Loan Completion',
                'type_color': 'teal',
                'reference': loan.application_number,
                'reference_url': f'/loans/{loan.pk}/',
                'client': loan.borrower.get_full_name(),
                'amount': loan.total_amount or loan.principal_amount,
                'status': 'Completed',
                'status_color': 'teal',
                'performed_by': loan.loan_officer.get_full_name() if loan.loan_officer else '—',
                'pk': loan.pk,
                'model': 'loan',
            })

    # 5. Processing Fees
    if not activity_type or activity_type == 'fee':
        qs = LoanApplication.objects.filter(
            loan_officer=officer,
            processing_fee__gt=0,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        ).select_related('borrower', 'processing_fee_verified_by')
        if search:
            qs = qs.filter(
                Q(borrower__first_name__icontains=search) |
                Q(borrower__last_name__icontains=search) |
                Q(application_number__icontains=search)
            )
        for app in qs:
            activities.append({
                'date': app.created_at.date(),
                'type': 'Processing Fee',
                'type_color': 'violet',
                'reference': app.application_number,
                'reference_url': f'/loans/applications/{app.pk}/approve/',
                'client': app.borrower.get_full_name(),
                'amount': app.processing_fee,
                'status': 'Verified' if app.processing_fee_verified else 'Pending',
                'status_color': 'green' if app.processing_fee_verified else 'amber',
                'performed_by': app.processing_fee_verified_by.get_full_name() if app.processing_fee_verified_by else officer.get_full_name(),
                'pk': app.pk,
                'model': 'application',
            })

    # Sort by date descending
    activities.sort(key=lambda x: x['date'] or date.min, reverse=True)

    # Totals
    total_amount = sum(a['amount'] for a in activities if a['amount'])

    # Summary counts (always full period, no type filter)
    all_col = PaymentCollection.objects.filter(col_q, collection_date__gte=date_from, collection_date__lte=date_to, collected_amount__gt=0).distinct()
    all_def = DefaultCollection.objects.filter(col_q, collection_date__gte=date_from, collection_date__lte=date_to).distinct()
    all_dis = Loan.objects.filter(loan_q, disbursement_date__date__gte=date_from, disbursement_date__date__lte=date_to).distinct()
    all_comp = Loan.objects.filter(loan_q, status='completed', updated_at__date__gte=date_from, updated_at__date__lte=date_to).distinct()
    all_fees = LoanApplication.objects.filter(loan_officer=officer, processing_fee__gt=0, created_at__date__gte=date_from, created_at__date__lte=date_to)

    return render(request, 'dashboard/officer_performance_report.html', {
        'date_from': date_from,
        'date_to': date_to,
        'activity_type': activity_type,
        'search': search,
        'activities': activities,
        'total_amount': total_amount,
        'activity_count': len(activities),
        # Summary cards
        'disbursed_count': all_dis.count(),
        'disbursed_amount': all_dis.aggregate(t=Sum('principal_amount'))['t'] or 0,
        'total_collected': all_col.aggregate(t=Sum('collected_amount'))['t'] or 0,
        'total_expected': all_col.aggregate(t=Sum('expected_amount'))['t'] or 0,
        'completed_count': all_comp.count(),
        'defaults_collected': all_def.aggregate(t=Sum('amount_paid'))['t'] or 0,
        'total_fees': all_fees.aggregate(t=Sum('processing_fee'))['t'] or 0,
        'new_clients_count': User.objects.filter(
            Q(assigned_officer=officer) | Q(group_memberships__group__assigned_officer=officer),
            role='borrower', date_joined__date__gte=date_from, date_joined__date__lte=date_to,
        ).distinct().count(),
    })


@login_required
def manager_dashboard(request):
    """Manager Dashboard"""
    manager = request.user
    
    # Check if user is actually a manager
    if manager.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    # Get branch - manager should have a managed_branch relationship
    try:
        branch = manager.managed_branch
        if not branch:
            # Manager doesn't have a branch assigned
            return render(request, 'dashboard/access_denied.html', {
                'message': 'You have not been assigned to a branch. Please contact your administrator.'
            })
    except:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'You have not been assigned to a branch. Please contact your administrator.'
        })
    
    # Branch metrics
    from django.db.models import Q
    officers = User.objects.filter(role='loan_officer', officer_assignment__branch=branch.name)
    groups = BorrowerGroup.objects.filter(
        Q(branch=branch.name) | Q(assigned_officer__officer_assignment__branch=branch.name)
    ).distinct()
    clients_count = User.objects.filter(
        Q(group_memberships__group__branch=branch.name) |
        Q(group_memberships__group__assigned_officer__officer_assignment__branch=branch.name) |
        Q(assigned_officer__officer_assignment__branch=branch.name),
        role='borrower',
    ).distinct().count()
    
    # Today's collections - only include loans where officer is from this branch
    today = date.today()
    today_collections = PaymentCollection.objects.filter(
        loan__loan_officer__officer_assignment__branch=branch.name,
        collection_date=today
    ).distinct()
    
    today_expected = sum(c.expected_amount for c in today_collections) or 0
    today_collected = sum(c.collected_amount for c in today_collections) or 0
    collection_rate = (today_collected / today_expected * 100) if today_expected > 0 else 0
    
    # Pending approvals
    pending_security = 0
    pending_topups = 0
    pending_returns = 0
    pending_loan_approvals = 0
    ready_for_disbursement = 0
    
    try:
        from loans.models import SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, ManagerLoanApproval
        
        # Fix: Get all pending security deposits that have been paid but not verified
        # Remove branch filter to see all pending deposits, or use proper branch filtering
        pending_security = SecurityDeposit.objects.filter(
            is_verified=False,
            paid_amount__gt=0  # Only show deposits that have actually been paid
        ).count()
        
        # Alternative: If you want branch-specific deposits, use this query:
        # pending_security = SecurityDeposit.objects.filter(
        #     is_verified=False,
        #     paid_amount__gt=0,
        #     loan__loan_officer__officer_assignment__branch=branch.name
        # ).count()
        
        pending_topups = SecurityTopUpRequest.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            status='pending'
        ).count()
        
        pending_returns = SecurityTransaction.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            transaction_type='return',
            status='pending',
        ).count()
        
        # Pending loan approvals (approved loans with verified deposits but not yet approved by manager)
        pending_loan_approvals = Loan.objects.filter(
            status='approved',
            loan_officer__officer_assignment__branch=branch.name,
            upfront_payment_verified=True
        ).exclude(
            manager_approval__status='approved'
        ).count()
        
        # Ready for disbursement (manager approved loans)
        ready_for_disbursement = ManagerLoanApproval.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            status='approved'
        ).count()
    except:
        pass
    
    # Expense summary
    total_expenses = 0
    try:
        from expenses.models import Expense
        expenses = Expense.objects.filter(branch=branch.name)
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    except:
        pass
    
    # Fund summary
    total_transfers = 0
    total_deposits = 0
    try:
        from expenses.models import FundsTransfer, BankDeposit
        transfers = FundsTransfer.objects.filter(source_branch=branch.name)
        deposits = BankDeposit.objects.filter(source_branch=branch.name)
        total_transfers = transfers.aggregate(Sum('amount'))['amount__sum'] or 0
        total_deposits = deposits.aggregate(Sum('amount'))['amount__sum'] or 0
    except:
        pass
    
    # Officer performance
    officer_stats = []
    for officer in officers:
        try:
            officer_groups = BorrowerGroup.objects.filter(assigned_officer=officer, is_active=True)
            officer_clients = User.objects.filter(
                Q(assigned_officer=officer) |
                Q(group_memberships__group__assigned_officer=officer, group_memberships__is_active=True),
                role='borrower',
            ).distinct().count()
            officer_loans = Loan.objects.filter(
                Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
                status='active'
            ).distinct()
            officer_collections = PaymentCollection.objects.filter(
                Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
                status='completed'
            ).distinct()

            if officer_collections.exists():
                collection_rate_officer = (
                    officer_collections.filter(is_partial=False).count() /
                    officer_collections.count() * 100
                )
            else:
                collection_rate_officer = 0

            officer_stats.append({
                'name': officer.full_name,
                'groups': officer_groups.count(),
                'clients': officer_clients,
                'collection_rate': round(collection_rate_officer, 1),
            })
        except:
            pass
    
    # Total disbursed for this branch
    # Get all officers in this branch
    branch_officers = User.objects.filter(
        role='loan_officer',
        officer_assignment__branch=branch.name
    ).values_list('id', flat=True)
    
    # Debug: Print branch info
    print(f"DEBUG: Branch name = {branch.name}")
    print(f"DEBUG: Branch officers count = {branch_officers.count()}")
    print(f"DEBUG: Branch officer IDs = {list(branch_officers)}")
    
    # Get loans from officers in this branch OR from borrowers in this branch's groups
    loans = Loan.objects.filter(
        Q(loan_officer_id__in=branch_officers) | 
        Q(borrower__group_memberships__group__branch=branch.name) |
        Q(borrower__group_memberships__group__assigned_officer__officer_assignment__branch=branch.name)
    ).distinct()
    
    # Debug: Check loan counts by status
    all_loans_count = loans.count()
    active_loans_count = loans.filter(status='active').count()
    completed_loans_count = loans.filter(status='completed').count()
    disbursed_loans_count = loans.filter(status='disbursed').count()
    
    print(f"DEBUG: Total loans = {all_loans_count}")
    print(f"DEBUG: Active loans = {active_loans_count}")
    print(f"DEBUG: Completed loans = {completed_loans_count}")
    print(f"DEBUG: Disbursed loans = {disbursed_loans_count}")
    
    # Check individual disbursed loans
    disbursed_loans = loans.filter(status='disbursed')
    for loan in disbursed_loans[:5]:  # Show first 5
        print(f"DEBUG: Disbursed loan - ID: {loan.id}, Amount: {loan.principal_amount}, Status: {loan.status}")
    
    total_disbursed = loans.filter(
        status__in=['pending', 'approved', 'active', 'completed', 'disbursed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    print(f"DEBUG: Total disbursed amount = {total_disbursed}")
    
    # Get document verification statistics
    pending_document_verifications = 0
    verified_document_clients = 0
    total_document_clients = 0
    
    try:
        from documents.models import ClientVerification, ClientDocument
        
        print(f"DEBUG: Branch name = {branch.name}")
        
        # For managers, get all clients in their branch
        branch_client_ids = User.objects.filter(
            Q(assigned_officer__officer_assignment__branch=branch.name) | 
            Q(group_memberships__group__assigned_officer__branch=branch.name),
            role='borrower'
        ).values_list('id', flat=True).distinct()
        
        print(f"DEBUG: Branch client IDs count = {branch_client_ids.count()}")
        print(f"DEBUG: Branch client IDs = {list(branch_client_ids[:10])}")  # Show first 10
        
        # Check if ClientVerification model exists and has data
        all_verifications = ClientVerification.objects.all()
        print(f"DEBUG: Total ClientVerification records = {all_verifications.count()}")
        
        # Check ClientDocument model
        all_documents = ClientDocument.objects.all()
        print(f"DEBUG: Total ClientDocument records = {all_documents.count()}")
        
        # Get verification statistics for branch clients
        total_document_clients = ClientVerification.objects.filter(
            client_id__in=branch_client_ids
        ).count()
        
        print(f"DEBUG: Total document clients for branch = {total_document_clients}")
        
        # Check all verification statuses
        all_statuses = ClientVerification.objects.values_list('status', flat=True).distinct()
        print(f"DEBUG: All verification statuses = {list(all_statuses)}")
        
        verified_document_clients = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status='verified'
        ).count()
        
        print(f"DEBUG: Verified document clients = {verified_document_clients}")
        
        pending_document_verifications = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status__in=['documents_submitted', 'documents_rejected']
        ).count()
        
        print(f"DEBUG: Pending document verifications = {pending_document_verifications}")
        
        # Also check individual documents
        individual_docs = ClientDocument.objects.filter(
            client_id__in=branch_client_ids
        ).count()
        print(f"DEBUG: Individual documents for branch = {individual_docs}")
        
    except Exception as e:
        print(f"Error getting document verification stats: {e}")
        import traceback
        traceback.print_exc()
        pass
    
    # Calculate verification rate
    verification_rate = 0
    if total_document_clients > 0:
        verification_rate = round((verified_document_clients / total_document_clients) * 100, 1)
    
    print(f"DEBUG: Document verification stats - Total: {total_document_clients}, Verified: {verified_document_clients}, Pending: {pending_document_verifications}, Rate: {verification_rate}%")
    
    # Get loan applications for this branch
    try:
        from loans.models import LoanApplication
        from django.db.models import Q
        
        print(f"DEBUG: Manager branch name = {branch.name}")
        
        # Simple approach: Show all applications for now to ensure visibility
        # In production, you might want to restrict this to actual branch filtering
        branch_applications = LoanApplication.objects.all().order_by('-created_at')[:5]
        pending_applications_count = LoanApplication.objects.filter(status='pending').count()
        
        print(f"DEBUG: Total applications: {branch_applications.count()}")
        print(f"DEBUG: Pending applications: {pending_applications_count}")
        
        # Show debug info for each application
        for app in branch_applications:
            officer_branch = None
            try:
                officer_branch = app.loan_officer.officer_assignment.branch if hasattr(app.loan_officer, 'officer_assignment') and app.loan_officer.officer_assignment else None
            except:
                officer_branch = "Error getting branch"
            print(f"  - App {app.application_number}: {app.borrower.username} by {app.loan_officer.username} (Branch: {officer_branch})")
        
    except Exception as e:
        print(f"DEBUG: Error getting loan applications: {e}")
        import traceback
        traceback.print_exc()
        branch_applications = []
        pending_applications_count = 0
    
    context = {
        'branch': branch,
        'today': today,
        'officers_count': officers.count(),
        'groups_count': groups.count(),
        'clients_count': clients_count,
        'today_expected': today_expected,
        'today_collected': today_collected,
        'collection_rate': round(collection_rate, 1),
        'pending_security': pending_security,
        'pending_topups': pending_topups,
        'pending_returns': pending_returns,
        'pending_loan_approvals': pending_loan_approvals,
        'ready_for_disbursement': ready_for_disbursement,
        'officer_stats': officer_stats,
        'total_expenses': total_expenses,
        'total_transfers': total_transfers,
        'total_deposits': total_deposits,
        'total_funds': total_transfers + total_deposits,
        'total_disbursed': total_disbursed,
        'pending_document_verifications': pending_document_verifications,
        'verified_document_clients': verified_document_clients,
        'total_document_clients': total_document_clients,
        'verification_rate': verification_rate,
        'recent_applications': branch_applications,
        'pending_applications_count': pending_applications_count,
        'pending_upfront_verifications': Loan.objects.filter(
            id__in=loans.filter(status='approved').filter(
                Q(upfront_payment_paid__gt=0, upfront_payment_verified=False) |
                Q(security_deposit__paid_amount__gt=0, security_deposit__is_verified=False)
            ).values_list('id', flat=True)
        ).select_related('borrower', 'loan_officer').distinct(),
        'ready_to_disburse': Loan.objects.filter(
            id__in=loans.filter(
                status='approved',
                upfront_payment_verified=True,
            ).values_list('id', flat=True)
        ).select_related('borrower', 'loan_officer'),
        'pending_payments_count': Payment.objects.filter(
            loan__in=loans,
            status='pending',
        ).count(),
        'branch_loans_active': loans.filter(status='active').count(),
        'branch_loans_completed': loans.filter(status='completed').count(),
        'branch_loans_pending': loans.filter(status='approved').count(),
        'branch_loans_total': loans.count(),
        'vault_balance': _get_vault_balance(branch),
    }

    # Get filter parameters
    officer_filter = request.GET.get('officer', '')
    group_filter = request.GET.get('group', '')
    limit = request.GET.get('limit', '5')  # Default to 5 records
    
    # Convert limit to int, handle 'all' case
    try:
        if limit.lower() == 'all':
            limit_int = None
        else:
            limit_int = int(limit)
    except:
        limit_int = 5

    # 1. Overdue loans for this branch
    from payments.models import PaymentSchedule as PS
    active_branch_loans = loans.filter(status='active').select_related('borrower', 'loan_officer')
    
    # Apply filters
    if officer_filter:
        active_branch_loans = active_branch_loans.filter(loan_officer_id=officer_filter)
    if group_filter:
        active_branch_loans = active_branch_loans.filter(
            borrower__group_memberships__group_id=group_filter,
            borrower__group_memberships__is_active=True
        )
    
    overdue_loans = []
    for loan in active_branch_loans:
        oldest = PS.objects.filter(loan=loan, is_paid=False, due_date__lt=today).order_by('due_date').first()
        if oldest:
            # Get borrower's group
            membership = loan.borrower.group_memberships.filter(is_active=True).first()
            group_name = membership.group.name if membership else 'No Group'
            
            overdue_loans.append({
                'loan': loan,
                'days_overdue': (today - oldest.due_date).days,
                'balance': loan.balance_remaining or 0,
                'group_name': group_name,
            })
    
    # Always sort by days overdue (descending) - most overdue first
    overdue_loans.sort(key=lambda x: -x['days_overdue'])
    
    # Store total count before limiting
    total_overdue_count = len(overdue_loans)
    
    # Apply limit
    if limit_int:
        overdue_loans_limited = overdue_loans[:limit_int]
    else:
        overdue_loans_limited = overdue_loans
    
    context['overdue_loans'] = overdue_loans_limited
    context['total_overdue_count'] = total_overdue_count
    context['overdue_filters'] = {
        'officer': officer_filter,
        'group': group_filter,
        'limit': limit,
    }

    # 2. Loans approaching maturity (next 30 days)
    from datetime import timedelta
    in_30 = today + timedelta(days=30)
    context['maturing_loans'] = loans.filter(
        status='active', maturity_date__gte=today, maturity_date__lte=in_30
    ).select_related('borrower').order_by('maturity_date')[:10]

    # 3. Processing fees
    from loans.models import LoanApplication
    from datetime import timedelta
    branch_apps = LoanApplication.objects.filter(
        loan_officer__officer_assignment__branch__iexact=branch.name,
        processing_fee__isnull=False,
        processing_fee__gt=0,
    )
    context['pending_processing_fees'] = branch_apps.filter(
        processing_fee_verified=False,
    ).select_related('borrower', 'loan_officer').order_by('-created_at')[:20]
    month_start = today.replace(day=1)
    context['fees_collected_this_month'] = branch_apps.filter(
        processing_fee_verified=True,
        processing_fee_verified_at__date__gte=month_start,
    ).aggregate(t=Sum('processing_fee'))['t'] or 0
    context['fees_total_verified'] = branch_apps.filter(
        processing_fee_verified=True,
    ).aggregate(t=Sum('processing_fee'))['t'] or 0
    context['fees_total_pending'] = branch_apps.filter(
        processing_fee_verified=False,
    ).aggregate(t=Sum('processing_fee'))['t'] or 0

    # Pending security transactions by type
    pending_sec_qs = SecurityTransaction.objects.filter(
        loan_id__in=loans.values_list('id', flat=True),
        status='pending',
    )
    context['pending_returns'] = pending_sec_qs.filter(transaction_type='return').count()
    context['pending_adjustments'] = pending_sec_qs.filter(transaction_type='adjustment').count()
    context['pending_withdrawals'] = pending_sec_qs.filter(transaction_type='withdrawal').count()
    context['pending_carry_forwards'] = pending_sec_qs.filter(transaction_type='carry_forward').count()
    context['pending_sec_txns_total'] = pending_sec_qs.count()

    return render(request, 'dashboard/manager_enhanced.html', context)


@login_required
def overdue_loans_full(request):
    """Full page view of all overdue loans with pagination and advanced filters"""
    user = request.user
    
    # Check if user is manager or admin
    if user.role not in ['manager', 'admin']:
        return render(request, 'dashboard/access_denied.html')
    
    from payments.models import PaymentSchedule as PS
    from django.core.paginator import Paginator
    from clients.models import BorrowerGroup
    
    # Get branch context for managers
    if user.role == 'manager':
        try:
            branch = user.managed_branch
            officers = User.objects.filter(
                role='loan_officer',
                officer_assignment__branch=branch.name,
                is_active=True
            ).order_by('first_name', 'last_name')
            
            # Get loans for this branch
            loans = Loan.objects.filter(
                status='active',
                loan_officer__officer_assignment__branch=branch.name
            ).select_related('borrower', 'loan_officer')
            
            groups = BorrowerGroup.objects.filter(
                assigned_officer__officer_assignment__branch=branch.name,
                is_active=True
            ).order_by('name')
        except:
            return render(request, 'dashboard/access_denied.html', {
                'message': 'You have not been assigned to a branch.'
            })
    else:  # admin
        officers = User.objects.filter(role='loan_officer', is_active=True).order_by('first_name', 'last_name')
        loans = Loan.objects.filter(status='active').select_related('borrower', 'loan_officer')
        groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')
    
    # Get filter parameters
    officer_filter = request.GET.get('officer', '')
    group_filter = request.GET.get('group', '')
    search = request.GET.get('search', '').strip()
    
    # Apply filters
    if officer_filter:
        loans = loans.filter(loan_officer_id=officer_filter)
        # Filter groups by selected officer
        groups = groups.filter(assigned_officer_id=officer_filter)
    if group_filter:
        loans = loans.filter(
            borrower__group_memberships__group_id=group_filter,
            borrower__group_memberships__is_active=True
        )
    if search:
        loans = loans.filter(
            Q(application_number__icontains=search) |
            Q(borrower__first_name__icontains=search) |
            Q(borrower__last_name__icontains=search)
        )
    
    # Build overdue loans list
    today = date.today()
    overdue_loans = []
    
    for loan in loans:
        oldest = PS.objects.filter(loan=loan, is_paid=False, due_date__lt=today).order_by('due_date').first()
        if oldest:
            # Get borrower's group
            membership = loan.borrower.group_memberships.filter(is_active=True).first()
            group_name = membership.group.name if membership else 'No Group'
            
            overdue_loans.append({
                'loan': loan,
                'days_overdue': (today - oldest.due_date).days,
                'balance': loan.balance_remaining or 0,
                'group_name': group_name,
            })
    
    # Always sort by days overdue (descending) - most overdue first
    overdue_loans.sort(key=lambda x: -x['days_overdue'])
    
    # Pagination
    paginator = Paginator(overdue_loans, 50)  # 50 per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/overdue_loans_full.html', {
        'page_obj': page_obj,
        'total_count': len(overdue_loans),
        'officers': officers,
        'groups': groups,
        'filters': {
            'officer': officer_filter,
            'group': group_filter,
            'search': search,
        },
    })


@login_required
def admin_dashboard(request):
    """Admin Dashboard"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')

    loans = Loan.objects.all()
    active_loans = loans.filter(status='active').count()
    total_loans = loans.count()
    total_disbursed = loans.filter(status__in=['active', 'completed', 'disbursed']).aggregate(total=Sum('principal_amount'))['total'] or 0
    total_repaid = PaymentCollection.objects.filter(status='completed').aggregate(total=Sum('collected_amount'))['total'] or 0

    from payments.models import PaymentSchedule as PS
    overdue_count = PS.objects.filter(is_paid=False, due_date__lt=date.today()).values('loan').distinct().count()

    pending_security = 0
    try:
        from loans.models import SecurityDeposit
        pending_security = SecurityDeposit.objects.filter(is_verified=False, paid_amount__gt=0).count()
    except Exception:
        pass

    from loans.models import LoanApplication
    recent_applications = LoanApplication.objects.all().order_by('-created_at')[:5]

    new_signups = User.objects.filter(
        date_joined__gte=date.today().replace(day=1)
    ).count()

    context = {
        'today': date.today(),
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'borrowers_count': User.objects.filter(role='borrower').count(),
        'total_loans': total_loans,
        'active_loans': active_loans,
        'pending_security': pending_security,
        'total_disbursed': total_disbursed,
        'total_repaid': total_repaid,
        'overdue_count': overdue_count,
        'new_signups': new_signups,
        'recent_users': User.objects.all().order_by('-date_joined')[:5],
        'recent_applications': recent_applications,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def borrower_dashboard(request):
    """Borrower Dashboard"""
    borrower = request.user
    
    # Get borrower's loans
    loans = Loan.objects.filter(borrower=borrower)
    active_loans = loans.filter(status='active').count()
    completed_loans = loans.filter(status='completed').count()
    pending_loans = active_loans  # Fix: Use active_loans instead of filtering for 'pending'
    
    # Get first active loan for quick payment action
    first_active_loan = loans.filter(status='active').first()
    
    # Get upcoming payments
    from payments.models import PaymentCollection
    upcoming_payments = PaymentCollection.objects.filter(
        loan__borrower=borrower,
        status='scheduled'
    ).order_by('collection_date')[:5]
    
    # Get total borrowed and repaid
    total_borrowed = loans.filter(
        status__in=['active', 'completed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    total_repaid = PaymentCollection.objects.filter(
        loan__borrower=borrower,
        status='completed'
    ).aggregate(total=Sum('collected_amount'))['total'] or 0
    
    # Get borrower's documents
    from documents.models import ClientDocument
    borrower_documents = ClientDocument.objects.filter(client=borrower)
    has_verified_documents = borrower_documents.filter(status='approved').exists()
    
    # Get borrower's security deposits for upfront payment tracking
    from loans.models import SecurityDeposit
    security_deposits = SecurityDeposit.objects.filter(loan__borrower=borrower).select_related('loan')
    pending_deposits = security_deposits.filter(is_verified=False, paid_amount__gt=0)
    verified_deposits = security_deposits.filter(is_verified=True)
    
    # Get rejected loans
    rejected_loans = loans.filter(status='rejected')
    
    # Get recent notifications
    from notifications.models import Notification
    recent_notifications = Notification.objects.filter(
        recipient=borrower
    ).order_by('-created_at')[:5]
    
    # Get repayment schedule
    from payments.models import PaymentSchedule
    repayment_schedule = PaymentSchedule.objects.filter(
        loan__borrower=borrower
    ).order_by('due_date')
    
    # Get pending applications
    pending_applications = loans.filter(status='pending').count()
    
    # Get approved loans awaiting upfront payment
    approved_loans = loans.filter(status='approved')
    loans_awaiting_upfront = []
    for loan in approved_loans:
        if not loan.upfront_payment_verified and loan.upfront_payment_paid == 0:
            loans_awaiting_upfront.append(loan)
    
    # Get overdue payments
    from payments.models import PaymentSchedule
    overdue_payments = PaymentSchedule.objects.filter(
        loan__borrower=borrower,
        is_paid=False,
        due_date__lt=timezone.now().date()
    )
    
    # Get next payment due
    next_payment = PaymentSchedule.objects.filter(
        loan__borrower=borrower,
        is_paid=False,
        due_date__gte=timezone.now().date()
    ).order_by('due_date').first()
    
    # Get loan status summary
    loan_status_summary = {
        'pending': loans.filter(status='pending').count(),
        'approved': loans.filter(status='approved').count(),
        'active': loans.filter(status='active').count(),
        'completed': loans.filter(status='completed').count(),
        'rejected': loans.filter(status='rejected').count(),
        'defaulted': loans.filter(status='defaulted').count(),
    }
    
    # Get total outstanding balance
    from django.db.models import F, ExpressionWrapper, DecimalField as DField
    outstanding_balance = loans.filter(status='active').aggregate(
        total=Sum(
            ExpressionWrapper(
                F('total_amount') - F('amount_paid'),
                output_field=DField(max_digits=14, decimal_places=2)
            )
        )
    )['total'] or 0
    
    # Get recent loan activity (actual loans, not approval requests)
    recent_approvals = loans.order_by('-application_date')[:5]
    
    # Get available loan types
    available_loan_types = LoanType.objects.filter(is_active=True)
    
    context = {
        'total_loans': loans.count(),
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'pending_loans': pending_loans,
        'upcoming_payments': upcoming_payments,
        'total_borrowed': total_borrowed,
        'total_repaid': total_repaid,
        'has_verified_documents': has_verified_documents,
        'rejected_loans': rejected_loans,
        'recent_notifications': recent_notifications,
        'borrower_documents': borrower_documents,
        'repayment_schedule': repayment_schedule,
        'pending_applications': pending_applications,
        'user_loans': loans,
        'loans_awaiting_upfront': loans_awaiting_upfront,
        'overdue_payments': overdue_payments,
        'next_payment': next_payment,
        'security_deposits': security_deposits,
        'pending_deposits': pending_deposits,
        'verified_deposits': verified_deposits,
        'loan_status_summary': loan_status_summary,
        'outstanding_balance': outstanding_balance,
        'recent_approvals': recent_approvals,
        'available_loan_types': available_loan_types,
        'first_active_loan': first_active_loan,
    }
    
    return render(request, 'dashboard/borrower_dashboard.html', context)


# Action Views for Dashboard Links

@login_required
def collection_details(request):
    """Collection Details View - Shows detailed collection information grouped by loan"""
    user = request.user
    
    if user.role == 'manager':
        # Manager sees collections for their branch
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
        
        collections = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name
        ).order_by('-collection_date')
    elif user.role == 'loan_officer':
        # Loan officer sees their collections
        collections = PaymentCollection.objects.filter(
            loan__loan_officer=user
        ).order_by('-collection_date')
    elif user.role == 'admin':
        # Admin sees all collections
        collections = PaymentCollection.objects.all().order_by('-collection_date')
    else:
        return render(request, 'dashboard/access_denied.html')
    
    # Group collections by loan
    from django.db.models import Sum
    loans_with_collections = {}
    
    for collection in collections:
        loan_id = collection.loan.id
        if loan_id not in loans_with_collections:
            loans_with_collections[loan_id] = {
                'loan': collection.loan,
                'collections': [],
                'total_expected': 0,
                'total_collected': 0,
                'completed_count': 0,
                'scheduled_count': 0
            }
        
        loans_with_collections[loan_id]['collections'].append(collection)
        loans_with_collections[loan_id]['total_expected'] += collection.expected_amount
        loans_with_collections[loan_id]['total_collected'] += collection.collected_amount
        
        if collection.status == 'completed':
            loans_with_collections[loan_id]['completed_count'] += 1
        else:
            loans_with_collections[loan_id]['scheduled_count'] += 1
    
    # Convert to list, sort collections by date, find next pending
    grouped_loans = list(loans_with_collections.values())
    for ld in grouped_loans:
        ld['collections'].sort(key=lambda c: c.collection_date)
        ld['next_collection'] = next(
            (c for c in ld['collections'] if c.status != 'completed'), None
        )
    grouped_loans.sort(key=lambda x: x['loan'].application_number)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(grouped_loans, 20)  # 20 loans per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'grouped_loans': page_obj.object_list,
        'total_collections': collections.count(),
        'total_collected': collections.aggregate(total=Sum('collected_amount'))['total'] or 0,
        'total_loans': len(grouped_loans),
    }
    
    return render(request, 'dashboard/collection_details.html', context)


@login_required
def pending_approvals(request):
    """Pending Approvals View - Shows loan applications awaiting manager approval and security deposits"""
    user = request.user
    from loans.models import LoanApplication, SecurityDeposit, SecurityTopUpRequest

    if user.role == 'manager':
        try:
            branch = user.managed_branch
        except Exception:
            branch = None
        if not branch:
            return render(request, 'dashboard/access_denied.html')

        from django.db.models import Q
        branch_loan_ids = Loan.objects.filter(
            Q(loan_officer__officer_assignment__branch__iexact=branch.name) |
            Q(borrower__group_memberships__group__branch__iexact=branch.name) |
            Q(borrower__group_memberships__group__assigned_officer__officer_assignment__branch__iexact=branch.name)
        ).values_list('id', flat=True).distinct()

        pending_applications = LoanApplication.objects.filter(
            status='pending',
            loan_officer__officer_assignment__branch=branch.name
        ).select_related('borrower', 'loan_officer', 'group').order_by('-created_at')

        pending_deposits = SecurityDeposit.objects.filter(
            is_verified=False,
            paid_amount__gt=0,
            loan_id__in=branch_loan_ids,
        ).select_related('loan', 'loan__borrower', 'loan__loan_officer').order_by('-payment_date')

        pending_security_txns = SecurityTransaction.objects.filter(
            loan_id__in=branch_loan_ids,
            status='pending',
        ).select_related('loan', 'loan__borrower', 'initiated_by').order_by('-created_at')

        pending_topup_requests = SecurityTopUpRequest.objects.filter(
            loan_id__in=branch_loan_ids,
            status='pending',
        ).select_related('loan', 'loan__borrower', 'requested_by').order_by('-requested_date')

    elif user.role == 'admin':
        pending_applications = LoanApplication.objects.filter(
            status='pending'
        ).select_related('borrower', 'loan_officer', 'group').order_by('-created_at')

        pending_deposits = SecurityDeposit.objects.filter(
            is_verified=False,
            paid_amount__gt=0
        ).select_related('loan', 'loan__borrower').order_by('-payment_date')

        pending_security_txns = SecurityTransaction.objects.filter(
            status='pending',
        ).select_related('loan', 'loan__borrower', 'initiated_by').order_by('-created_at')

        pending_topup_requests = SecurityTopUpRequest.objects.filter(
            status='pending',
        ).select_related('loan', 'loan__borrower', 'requested_by').order_by('-requested_date')
    else:
        return render(request, 'dashboard/access_denied.html')

    from django.db.models import Sum
    deposit_totals = pending_deposits.aggregate(
        total_required=Sum('required_amount'),
        total_collected=Sum('paid_amount')
    )
    total_required = deposit_totals['total_required'] or 0
    total_collected = deposit_totals['total_collected'] or 0

    context = {
        'pending_applications': pending_applications,
        'pending_deposits': pending_deposits,
        'pending_security_txns': pending_security_txns,
        'pending_topup_requests': pending_topup_requests,
        'total_pending': pending_applications.count(),
        'total_deposits': pending_deposits.count(),
        'total_required': total_required,
        'total_collected': total_collected,
        'total_outstanding': total_required - total_collected,
    }

    return render(request, 'dashboard/pending_approvals.html', context)


@login_required
def security_topup_action(request, pk):
    """Approve or reject a SecurityTopUpRequest."""
    if request.user.role not in ['manager', 'admin'] and not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:pending_approvals')
    from loans.models import SecurityTopUpRequest
    from django.utils import timezone as tz
    req = get_object_or_404(SecurityTopUpRequest, pk=pk)
    if request.method == 'POST':
        decision = request.POST.get('decision')
        if decision == 'approve' and req.status == 'pending':
            req.status = 'approved'
            req.approved_by = request.user
            req.approval_date = tz.now()
            req.save(update_fields=['status', 'approved_by', 'approval_date'])
            try:
                dep = req.loan.security_deposit
                dep.paid_amount += req.requested_amount
                dep.save(update_fields=['paid_amount', 'updated_at'])
            except Exception:
                pass
            messages.success(request, f'Top-up of K{req.requested_amount} approved.')
        elif decision == 'reject' and req.status == 'pending':
            req.status = 'rejected'
            req.approved_by = request.user
            req.approval_date = tz.now()
            req.rejection_reason = request.POST.get('reason', '')
            req.save(update_fields=['status', 'approved_by', 'approval_date', 'rejection_reason'])
            messages.warning(request, 'Top-up request rejected.')
    return redirect(request.POST.get('next') or 'dashboard:pending_approvals')


@login_required
def approved_security_deposits(request):
    """View approved security deposits and upfront payments"""
    user = request.user
    
    if user.role == 'manager':
        try:
            branch = user.managed_branch
            if not branch:
                return render(request, 'dashboard/access_denied.html')

            from loans.models import SecurityDeposit
            from django.db.models import Q
            # Only show deposits where the loan officer is from this branch
            approved_deposits = SecurityDeposit.objects.filter(
                is_verified=True,
                loan__loan_officer__officer_assignment__branch__iexact=branch.name
            ).select_related('loan', 'loan__borrower').distinct().order_by('-verification_date')

            branch_display_name = branch.name

        except Exception as e:
            return render(request, 'dashboard/access_denied.html')
        
    elif user.role == 'admin':
        # Admin sees all approved deposits
        from loans.models import SecurityDeposit
        approved_deposits = SecurityDeposit.objects.filter(
            is_verified=True
        ).select_related('loan', 'loan__borrower').order_by('-verification_date')
        
        branch_display_name = 'All Branches'
    else:
        return render(request, 'dashboard/access_denied.html')
    
    # Calculate totals
    from django.db.models import Sum
    if approved_deposits:
        total_required = sum(deposit.required_amount for deposit in approved_deposits)
        total_collected = sum(deposit.paid_amount for deposit in approved_deposits)
    else:
        total_required = 0
        total_collected = 0
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(approved_deposits, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'approved_deposits': page_obj.object_list,
        'total_deposits': len(approved_deposits),
        'total_required': total_required,
        'total_collected': total_collected,
        'branch': branch_display_name,
    }
    
    return render(request, 'dashboard/approved_security_deposits.html', context)


@login_required
def manage_officers(request):
    """Manage Officers View — pending approvals + active officers"""
    user = request.user

    if user.role == 'manager':
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html', {
                'message': 'You have not been assigned to a branch.'
            })

        # Handle approve action
        if request.method == 'POST':
            action = request.POST.get('action')
            officer_id = request.POST.get('officer_id')
            officer = get_object_or_404(User, pk=officer_id, role='loan_officer')

            if action == 'approve':
                from django.utils import timezone as tz
                officer.is_active = True
                officer.is_approved = True
                officer.approved_by = user
                officer.approved_at = tz.now()
                officer.save(update_fields=['is_active', 'is_approved', 'approved_by', 'approved_at'])
                # Create OfficerAssignment with branch
                from clients.models import OfficerAssignment
                from django.db import connection as _conn
                with _conn.cursor() as _cur:
                    _cur.execute('SELECT COUNT(*) FROM clients_officerassignment WHERE officer_id = %s', [officer.pk])
                    if _cur.fetchone()[0] == 0:
                        try:
                            _cur.execute(
                                'INSERT INTO clients_officerassignment (officer_id, branch_id, branch, max_groups, max_clients, is_accepting_assignments, created_at, updated_at) VALUES (%s, %s, %s, 15, 50, 1, NOW(), NOW())',
                                [officer.pk, branch.pk, branch.name]
                            )
                        except Exception:
                            _cur.execute(
                                'INSERT INTO clients_officerassignment (officer_id, branch, max_groups, max_clients, is_accepting_assignments, created_at, updated_at) VALUES (%s, %s, 15, 50, 1, NOW(), NOW())',
                                [officer.pk, branch.name]
                            )
                messages.success(request, f'{officer.get_full_name()} approved and assigned to {branch.name}.')

            elif action == 'reject':
                officer.is_active = False
                officer.save(update_fields=['is_active'])
                messages.warning(request, f'{officer.get_full_name()} rejected.')

            elif action == 'deactivate':
                officer.is_active = False
                officer.save(update_fields=['is_active'])
                messages.warning(request, f'{officer.get_full_name()} deactivated.')

            return redirect('dashboard:manage_officers')

        pending_officers = User.objects.filter(
            role='loan_officer', is_approved=False
        ).order_by('date_joined')

        active_officers = User.objects.filter(
            role='loan_officer',
            is_approved=True,
            officer_assignment__branch__iexact=branch.name,
        ).distinct().order_by('first_name', 'last_name')

    elif user.role == 'admin':
        if request.method == 'POST':
            return redirect('dashboard:manage_officers')
        pending_officers = User.objects.filter(role='loan_officer', is_approved=False).order_by('date_joined')
        active_officers = User.objects.filter(role='loan_officer', is_approved=True).order_by('first_name', 'last_name')
        branch = None
    else:
        return render(request, 'dashboard/access_denied.html')

    from clients.models import OfficerAssignment
    officer_assignments = {}
    for o in list(pending_officers) + list(active_officers):
        try:
            officer_assignments[o.id] = OfficerAssignment.objects.get(officer=o)
        except OfficerAssignment.DoesNotExist:
            officer_assignments[o.id] = None

    return render(request, 'dashboard/manage_officers.html', {
        'pending_officers': pending_officers,
        'active_officers': active_officers,
        'officer_assignments': officer_assignments,
        'branch': branch,
        'total_officers': active_officers.count(),
    })


@login_required
def manage_branches(request):
    """Manage Branches View - Shows all branches and their details"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    branches = Branch.objects.all().order_by('name')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(branches, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'branches': page_obj.object_list,
        'total_branches': branches.count(),
    }
    
    return render(request, 'dashboard/manage_branches.html', context)


@login_required
def audit_logs(request):
    """Audit Logs View - Shows admin audit logs"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    logs = AdminAuditLog.objects.all().order_by('-timestamp')
    
    # Calculate statistics
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    total_logs = logs.count()
    today_logs = logs.filter(timestamp__date=today).count()
    week_logs = logs.filter(timestamp__date__gte=week_ago).count()
    active_admins = logs.values('admin_user').distinct().count()
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'total_logs': total_logs,
        'today_logs': today_logs,
        'week_logs': week_logs,
        'active_admins': active_admins,
    }
    
    return render(request, 'dashboard/audit_logs.html', context)



# Approval Views

@login_required
def approval_detail(request, approval_id):
    """View approval details and allow approve/reject actions"""
    from loans.models import SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, ApprovalLog
    
    user = request.user
    
    # Get the approval item based on ID and type
    approval_type = request.GET.get('type', 'security_deposit')
    
    if approval_type == 'security_deposit':
        try:
            approval = SecurityDeposit.objects.get(id=approval_id, is_verified=False)
            approval_type_display = 'Security Deposit'
        except SecurityDeposit.DoesNotExist:
            return render(request, 'dashboard/access_denied.html', {'message': 'Approval not found'})
    elif approval_type == 'security_topup':
        try:
            approval = SecurityTopUpRequest.objects.get(id=approval_id, status='pending')
            approval_type_display = 'Security Top-Up'
        except SecurityTopUpRequest.DoesNotExist:
            return render(request, 'dashboard/access_denied.html', {'message': 'Approval not found'})
    elif approval_type == 'security_return':
        try:
            approval = SecurityReturnRequest.objects.get(id=approval_id, status='pending')
            approval_type_display = 'Security Return'
        except SecurityReturnRequest.DoesNotExist:
            return render(request, 'dashboard/access_denied.html', {'message': 'Approval not found'})
    else:
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid approval type'})
    
    # Check if user is manager of the branch
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    # Get loan details
    loan = approval.loan if hasattr(approval, 'loan') else None
    
    context = {
        'approval': approval,
        'approval_type': approval_type,
        'approval_type_display': approval_type_display,
        'loan': loan,
        'branch': branch,
    }
    
    return render(request, 'dashboard/approval_detail.html', context)


@login_required
def approval_approve(request, approval_id):
    """Approve a security-related request"""
    from loans.models import SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, ApprovalLog
    
    if request.method != 'POST':
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid request method'})
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    approval_type = request.POST.get('type', 'security_deposit')
    comments = request.POST.get('comments', '')
    
    try:
        if approval_type == 'security_deposit':
            approval = SecurityDeposit.objects.get(id=approval_id, is_verified=False)
            approval.is_verified = True
            approval.verified_by = user
            approval.verification_date = timezone.now()
            approval.save()
            
            # Update loan's upfront payment verified status
            loan = approval.loan
            loan.upfront_payment_verified = True
            loan.save()
            
            # Log the approval
            ApprovalLog.objects.create(
                approval_type='security_deposit',
                loan=approval.loan,
                manager=user,
                action='approve',
                comments=comments,
                branch=branch.name
            )
            
        elif approval_type == 'security_topup':
            approval = SecurityTopUpRequest.objects.get(id=approval_id, status='pending')
            approval.status = 'approved'
            approval.save()
            
            # Log the approval
            ApprovalLog.objects.create(
                approval_type='security_topup',
                loan=approval.loan,
                manager=user,
                action='approve',
                comments=comments,
                branch=branch.name
            )
            
        elif approval_type == 'security_return':
            approval = SecurityReturnRequest.objects.get(id=approval_id, status='pending')
            approval.status = 'approved'
            approval.save()
            
            # Log the approval
            ApprovalLog.objects.create(
                approval_type='security_return',
                loan=approval.loan,
                manager=user,
                action='approve',
                comments=comments,
                branch=branch.name
            )
        
        # Redirect to pending approvals
        from django.shortcuts import redirect
        return redirect('dashboard:pending_approvals')
        
    except Exception as e:
        return render(request, 'dashboard/access_denied.html', {'message': f'Error approving: {str(e)}'})


@login_required
def approval_reject(request, approval_id):
    """Reject a security-related request"""
    from loans.models import SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, ApprovalLog
    
    if request.method != 'POST':
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid request method'})
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    approval_type = request.POST.get('type', 'security_deposit')
    comments = request.POST.get('comments', '')
    
    if not comments:
        return render(request, 'dashboard/access_denied.html', {'message': 'Comments are required for rejection'})
    
    try:
        if approval_type == 'security_deposit':
            approval = SecurityDeposit.objects.get(id=approval_id, is_verified=False)
            approval.is_verified = False  # Keep as unverified
            approval.save()
            
            # Log the rejection
            ApprovalLog.objects.create(
                approval_type='security_deposit',
                loan=approval.loan,
                manager=user,
                action='reject',
                comments=comments,
                branch=branch.name
            )
            
        elif approval_type == 'security_topup':
            approval = SecurityTopUpRequest.objects.get(id=approval_id, status='pending')
            approval.status = 'rejected'
            approval.save()
            
            # Log the rejection
            ApprovalLog.objects.create(
                approval_type='security_topup',
                loan=approval.loan,
                manager=user,
                action='reject',
                comments=comments,
                branch=branch.name
            )
            
        elif approval_type == 'security_return':
            approval = SecurityReturnRequest.objects.get(id=approval_id, status='pending')
            approval.status = 'rejected'
            approval.save()
            
            # Log the rejection
            ApprovalLog.objects.create(
                approval_type='security_return',
                loan=approval.loan,
                manager=user,
                action='reject',
                comments=comments,
                branch=branch.name
            )
        
        # Redirect to pending approvals
        from django.shortcuts import redirect
        return redirect('dashboard:pending_approvals')
        
    except Exception as e:
        return render(request, 'dashboard/access_denied.html', {'message': f'Error rejecting: {str(e)}'})


@login_required
def approval_history(request):
    """View approval history and logs"""
    from loans.models import ApprovalLog
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    # Get approval logs for this branch
    logs = ApprovalLog.objects.filter(branch=branch.name).order_by('-timestamp')
    
    # Apply filters
    approval_type = request.GET.get('approval_type', '')
    action = request.GET.get('action', '')
    loan_id = request.GET.get('loan_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if approval_type:
        logs = logs.filter(approval_type=approval_type)
    
    if action:
        logs = logs.filter(action=action)
    
    if loan_id:
        logs = logs.filter(loan__id=loan_id)
    
    if date_from:
        from datetime import datetime
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        from datetime import datetime, timedelta
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire day
            date_to_obj = date_to_obj + timedelta(days=1)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except:
            pass
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'total_logs': logs.count(),
        'branch': branch,
        'approval_type': approval_type,
        'action': action,
        'loan_id': loan_id,
        'date_from': date_from,
        'date_to': date_to,
        'approval_types': ApprovalLog.APPROVAL_TYPES,
        'actions': ApprovalLog.ACTION_CHOICES,
    }
    
    return render(request, 'dashboard/approval_history.html', context)


@login_required
def manager_loan_approval_detail(request, loan_id):
    """Manager view: Display loan details for approval decision"""
    from loans.models import Loan, ManagerLoanApproval, SecurityDeposit
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        messages.error(request, 'You do not have permission to approve loans.')
        return redirect('dashboard:dashboard')
    
    try:
        branch = user.managed_branch
        if not branch:
            messages.error(request, 'You are not assigned to a branch.')
            return redirect('dashboard:dashboard')
    except:
        messages.error(request, 'Error accessing branch information.')
        return redirect('dashboard:dashboard')
    
    # Get the loan
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        messages.error(request, 'Loan not found.')
        return redirect('dashboard:pending_approvals')
    
    # Check if loan is in approved status
    if loan.status != 'approved':
        messages.error(request, 'Loan is not in approved status.')
        return redirect('dashboard:pending_approvals')
    
    # Check if manager's branch matches loan officer's branch
    try:
        if loan.loan_officer.officer_assignment.branch != branch.name:
            messages.error(request, 'You do not have permission to approve this loan.')
            return redirect('dashboard:pending_approvals')
    except:
        messages.error(request, 'Error verifying loan assignment.')
        return redirect('dashboard:pending_approvals')
    
    # Get security deposit status
    try:
        security_deposit = loan.security_deposit
        deposit_verified = security_deposit.is_verified
    except:
        deposit_verified = False
    
    # Get manager approval status
    try:
        manager_approval = loan.manager_approval
    except:
        manager_approval = None
    
    context = {
        'loan': loan,
        'security_deposit': security_deposit if 'security_deposit' in locals() else None,
        'deposit_verified': deposit_verified,
        'manager_approval': manager_approval,
        'branch': branch,
    }
    
    return render(request, 'dashboard/manager_loan_approval_detail.html', context)


@login_required
def manager_loan_approve(request, loan_id):
    """Manager view: Approve a loan for disbursement"""
    from loans.models import Loan, ManagerLoanApproval, ApprovalLog
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('dashboard:pending_approvals')
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        messages.error(request, 'You do not have permission to approve loans.')
        return redirect('dashboard:dashboard')
    
    try:
        branch = user.managed_branch
        if not branch:
            messages.error(request, 'You are not assigned to a branch.')
            return redirect('dashboard:dashboard')
    except:
        messages.error(request, 'Error accessing branch information.')
        return redirect('dashboard:dashboard')
    
    # Get the loan
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        messages.error(request, 'Loan not found.')
        return redirect('dashboard:pending_approvals')
    
    # Validate loan status
    if loan.status != 'approved':
        messages.error(request, 'Loan is not in approved status.')
        return redirect('dashboard:pending_approvals')
    
    # Check if manager's branch matches loan officer's branch
    try:
        if loan.loan_officer.officer_assignment.branch != branch.name:
            messages.error(request, 'You do not have permission to approve this loan.')
            return redirect('dashboard:pending_approvals')
    except:
        messages.error(request, 'Error verifying loan assignment.')
        return redirect('dashboard:pending_approvals')
    
    # Validate security deposit is verified
    try:
        security_deposit = loan.security_deposit
        if not security_deposit.is_verified:
            messages.error(request, 'Security deposit must be verified before loan approval.')
            return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)
    except:
        messages.error(request, 'Security deposit not found.')
        return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)
    
    # Get comments
    comments = request.POST.get('comments', '')
    
    try:
        # Create or update manager approval
        manager_approval, created = ManagerLoanApproval.objects.get_or_create(loan=loan)
        manager_approval.status = 'approved'
        manager_approval.manager = user
        manager_approval.approved_date = timezone.now()
        manager_approval.comments = comments
        manager_approval.save()
        
        # Log the approval
        ApprovalLog.objects.create(
            approval_type='loan_approval',
            loan=loan,
            manager=user,
            action='approve',
            comments=comments,
            branch=branch.name
        )
        
        messages.success(request, f'Loan {loan.application_number} has been approved for disbursement.')
        return redirect('dashboard:pending_approvals')
        
    except Exception as e:
        messages.error(request, f'Error approving loan: {str(e)}')
        return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)


@login_required
def manager_loan_reject(request, loan_id):
    """Manager view: Reject a loan approval"""
    from loans.models import Loan, ManagerLoanApproval, ApprovalLog
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('dashboard:pending_approvals')
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        messages.error(request, 'You do not have permission to reject loans.')
        return redirect('dashboard:dashboard')
    
    try:
        branch = user.managed_branch
        if not branch:
            messages.error(request, 'You are not assigned to a branch.')
            return redirect('dashboard:dashboard')
    except:
        messages.error(request, 'Error accessing branch information.')
        return redirect('dashboard:dashboard')
    
    # Get the loan
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        messages.error(request, 'Loan not found.')
        return redirect('dashboard:pending_approvals')
    
    # Validate loan status
    if loan.status != 'approved':
        messages.error(request, 'Loan is not in approved status.')
        return redirect('dashboard:pending_approvals')
    
    # Check if manager's branch matches loan officer's branch
    try:
        if loan.loan_officer.officer_assignment.branch != branch.name:
            messages.error(request, 'You do not have permission to reject this loan.')
            return redirect('dashboard:pending_approvals')
    except:
        messages.error(request, 'Error verifying loan assignment.')
        return redirect('dashboard:pending_approvals')
    
    # Get comments (required for rejection)
    comments = request.POST.get('comments', '')
    
    if not comments:
        messages.error(request, 'Comments are required for rejection.')
        return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)
    
    try:
        # Create or update manager approval
        manager_approval, created = ManagerLoanApproval.objects.get_or_create(loan=loan)
        manager_approval.status = 'rejected'
        manager_approval.manager = user
        manager_approval.comments = comments
        manager_approval.save()
        
        # Log the rejection
        ApprovalLog.objects.create(
            approval_type='loan_approval',
            loan=loan,
            manager=user,
            action='reject',
            comments=comments,
            branch=branch.name
        )
        
        messages.success(request, f'Loan {loan.application_number} has been rejected.')
        return redirect('dashboard:pending_approvals')
        
    except Exception as e:
        messages.error(request, f'Error rejecting loan: {str(e)}')
        return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)


# Expense Management Views

@login_required
def expense_list(request):
    """View and filter expenses — manager sees their branch, admin sees all"""
    from expenses.models import Expense, ExpenseCode

    user = request.user

    if user.role == 'admin' or user.is_superuser:
        branch_filter = request.GET.get('branch', '')
        if branch_filter:
            expenses = Expense.objects.filter(branch=branch_filter).order_by('-expense_date')
        else:
            expenses = Expense.objects.all().order_by('-expense_date')
        branch = None
    elif user.role == 'manager':
        try:
            branch = user.managed_branch
            if not branch:
                return render(request, 'dashboard/access_denied.html')
        except Exception:
            return render(request, 'dashboard/access_denied.html')
        expenses = Expense.objects.filter(branch=branch.name).order_by('-expense_date')
    else:
        return render(request, 'dashboard/access_denied.html')
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)
    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)
    
    # Filter by expense code
    expense_code = request.GET.get('expense_code')
    if expense_code:
        expenses = expenses.filter(expense_code_id=expense_code)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(expenses, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'page_obj': page_obj,
        'expenses': page_obj.object_list,
        'total_expenses': total_expenses,
        'expense_codes': ExpenseCode.objects.filter(is_active=True),
        'branch': branch,
    }
    
    return render(request, 'dashboard/expense_list.html', context)


@login_required
def expense_create(request):
    """Create a new expense"""
    from expenses.models import Expense, ExpenseCode
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            amount = request.POST.get('amount')
            expense_code_id = request.POST.get('expense_code')
            expense_date = request.POST.get('expense_date')
            description = request.POST.get('description')
            
            # Validate required fields
            if not amount or not expense_code_id or not expense_date:
                return render(request, 'dashboard/expense_form.html', {
                    'error': 'Amount, expense code, and date are required',
                    'expense_codes': ExpenseCode.objects.filter(is_active=True),
                    'branch': branch,
                })
            
            # Create expense
            if expense_code_id == 'other':
                expense_code, _ = ExpenseCode.objects.get_or_create(
                    code='OTHER',
                    defaults={'name': 'Other', 'description': 'Other expenses', 'is_active': True}
                )
            else:
                expense_code = ExpenseCode.objects.get(id=expense_code_id)
            expense = Expense.objects.create(
                amount=amount,
                expense_code=expense_code,
                expense_date=expense_date,
                description=description or '',
                branch=branch.name,
                recorded_by=user,
                title=f"{expense_code.name} - {expense_date}"
            )
            
            # Redirect to expense list
            from django.shortcuts import redirect
            return redirect('dashboard:expense_list')
            
        except Exception as e:
            return render(request, 'dashboard/expense_form.html', {
                'error': f'Error creating expense: {str(e)}',
                'expense_codes': ExpenseCode.objects.filter(is_active=True),
                'branch': branch,
            })
    
    context = {
        'expense_codes': ExpenseCode.objects.filter(is_active=True),
        'branch': branch,
    }
    
    return render(request, 'dashboard/expense_form.html', context)


@login_required
def expense_report(request):
    """Generate expense report by category and date"""
    from expenses.models import Expense, ExpenseCode
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    # Get expenses for this branch
    expenses = Expense.objects.filter(branch=branch.name)
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)
    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)
    
    # Aggregate by expense code
    category_totals = {}
    total_expenses = 0
    total_count = 0
    
    for code in ExpenseCode.objects.filter(is_active=True):
        code_expenses = expenses.filter(expense_code=code)
        total = code_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        if total > 0:
            count = code_expenses.count()
            total_count += count
            percentage = (total / expenses.aggregate(Sum('amount'))['amount__sum'] * 100) if expenses.aggregate(Sum('amount'))['amount__sum'] else 0
            category_totals[code.name] = {
                'total': total,
                'count': count,
                'percentage': round(percentage, 1)
            }
            total_expenses += total
    
    context = {
        'category_totals': category_totals,
        'total_expenses': total_expenses,
        'total_expenses_count': total_count,
        'expense_codes': ExpenseCode.objects.filter(is_active=True),
        'branch': branch,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'dashboard/expense_report.html', context)


# Funds Management Views

@login_required
def fund_transfer_create(request):
    """Create a new fund transfer between branches"""
    from expenses.models import FundsTransfer
    from clients.models import Branch
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            amount = request.POST.get('amount')
            destination_branch = request.POST.get('destination_branch')
            date_str = request.POST.get('date')
            reference = request.POST.get('reference')
            description = request.POST.get('description', '')
            
            # Validate required fields
            if not amount or not destination_branch or not date_str or not reference:
                return render(request, 'dashboard/fund_transfer_form.html', {
                    'error': 'Amount, destination branch, date, and reference are required',
                    'branches': Branch.objects.exclude(name=branch.name),
                    'branch': branch,
                })
            
            # Create fund transfer
            transfer = FundsTransfer.objects.create(
                amount=amount,
                source_branch=branch.name,
                destination_branch=destination_branch,
                reference_number=reference,
                description=description,
                requested_by=user,
                status='pending'
            )
            
            # Redirect to fund history
            from django.shortcuts import redirect
            return redirect('dashboard:fund_history')
            
        except Exception as e:
            return render(request, 'dashboard/fund_transfer_form.html', {
                'error': f'Error creating transfer: {str(e)}',
                'branches': Branch.objects.exclude(name=branch.name),
                'branch': branch,
            })
    
    context = {
        'branches': Branch.objects.exclude(name=branch.name),
        'branch': branch,
    }
    
    return render(request, 'dashboard/fund_transfer_form.html', context)


@login_required
def fund_deposit_create(request):
    """Create a new bank deposit"""
    from expenses.models import BankDeposit
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            amount = request.POST.get('amount')
            bank_name = request.POST.get('bank_name')
            account_number = request.POST.get('account_number')
            date_str = request.POST.get('date')
            reference = request.POST.get('reference')
            description = request.POST.get('description', '')
            
            # Validate required fields
            if not amount or not bank_name or not account_number or not date_str or not reference:
                return render(request, 'dashboard/fund_deposit_form.html', {
                    'error': 'Amount, bank name, account number, date, and reference are required',
                    'branch': branch,
                })
            
            # Create bank deposit
            deposit = BankDeposit.objects.create(
                amount=amount,
                source_branch=branch.name,
                bank_name=bank_name,
                account_number=account_number,
                reference_number=reference,
                description=description,
                requested_by=user,
                deposit_date=date_str,
                status='pending'
            )
            
            # Redirect to fund history
            from django.shortcuts import redirect
            return redirect('dashboard:fund_history')
            
        except Exception as e:
            return render(request, 'dashboard/fund_deposit_form.html', {
                'error': f'Error creating deposit: {str(e)}',
                'branch': branch,
            })
    
    context = {
        'branch': branch,
    }
    
    return render(request, 'dashboard/fund_deposit_form.html', context)


@login_required
def fund_history(request):
    """View fund transfer and deposit history"""
    from expenses.models import FundsTransfer, BankDeposit
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            # If manager has no branch, show all records
            transfers = FundsTransfer.objects.all().order_by('-requested_date')
            deposits = BankDeposit.objects.all().order_by('-requested_date')
            branch_name = "All Branches"
        else:
            # Get transfers for this branch (as source or destination)
            transfers = FundsTransfer.objects.filter(
                Q(source_branch=branch.name) | Q(destination_branch=branch.name)
            ).order_by('-requested_date')
            
            # Get deposits for this branch
            deposits = BankDeposit.objects.filter(source_branch=branch.name).order_by('-requested_date')
            branch_name = branch.name
    except:
        return render(request, 'dashboard/access_denied.html')
    
    # Filter by type
    fund_type = request.GET.get('type')
    if fund_type == 'transfer':
        transfers = transfers
        deposits = BankDeposit.objects.none()
    elif fund_type == 'deposit':
        transfers = FundsTransfer.objects.none()
        deposits = deposits
    else:
        # Show all by default
        transfers = transfers
        deposits = deposits
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        transfers = transfers.filter(requested_date__gte=start_date)
        deposits = deposits.filter(requested_date__gte=start_date)
    if end_date:
        transfers = transfers.filter(requested_date__lte=end_date)
        deposits = deposits.filter(requested_date__lte=end_date)
    
    # Filter by amount range
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if min_amount:
        transfers = transfers.filter(amount__gte=min_amount)
        deposits = deposits.filter(amount__gte=min_amount)
    if max_amount:
        transfers = transfers.filter(amount__lte=max_amount)
        deposits = deposits.filter(amount__lte=max_amount)
    
    # Combine and paginate
    from django.core.paginator import Paginator
    from itertools import chain
    
    all_records = list(chain(transfers, deposits))
    all_records.sort(key=lambda x: x.requested_date, reverse=True)
    
    paginator = Paginator(all_records, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals
    total_transfers = transfers.aggregate(Sum('amount'))['amount__sum'] or 0
    total_deposits = deposits.aggregate(Sum('amount'))['amount__sum'] or 0
    total_funds = total_transfers + total_deposits
    
    context = {
        'page_obj': page_obj,
        'records': page_obj.object_list,
        'total_records': len(all_records),
        'total_transfers': total_transfers,
        'total_deposits': total_deposits,
        'total_funds': total_funds,
        'branch': branch_name,
    }
    
    return render(request, 'dashboard/fund_history.html', context)


# User Management Views

@login_required
def user_create(request):
    """Create a new user (officer or manager)"""
    user = request.user
    
    # Check if user is admin or manager
    if user.role not in ['admin', 'manager']:
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone_number = request.POST.get('phone_number')
            role = request.POST.get('role')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            # Managers can only create loan officers, not other managers or admins
            if user.role == 'manager' and role not in ['loan_officer']:
                return render(request, 'dashboard/user_form.html', {
                    'error': 'Managers can only create loan officers',
                })
            
            # Validate required fields
            if not all([username, email, first_name, last_name, role, password]):
                return render(request, 'dashboard/user_form.html', {
                    'error': 'All fields are required',
                })
            
            # Validate passwords match
            if password != password_confirm:
                return render(request, 'dashboard/user_form.html', {
                    'error': 'Passwords do not match',
                })
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                return render(request, 'dashboard/user_form.html', {
                    'error': 'Username already exists',
                })
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return render(request, 'dashboard/user_form.html', {
                    'error': 'Email already exists',
                })
            
            # Create user
            new_user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=role,
                phone_number=phone_number or '',
                is_active=True
            )
            
            # Log user creation in AdminAuditLog (only for admins - managers skip this)
            if request.user.role == 'admin':
                try:
                    AdminAuditLog.objects.create(
                        admin_user=request.user,
                        action='other',
                        affected_user=new_user,
                        description=f'Created user: {new_user.get_full_name()} ({role})'
                    )
                except Exception:
                    pass
            
            # If loan officer, create OfficerAssignment with correct branch
            if role == 'loan_officer':
                from clients.models import OfficerAssignment
                branch_name = ''
                branch_id = None
                if request.user.role == 'manager' and request.user.managed_branch:
                    branch_name = request.user.managed_branch.name
                    branch_id = request.user.managed_branch.pk
                # Use raw SQL to handle possible extra branch_id column on production DB
                from django.db import connection as _conn
                with _conn.cursor() as _cur:
                    _cur.execute(
                        'SELECT COUNT(*) FROM clients_officerassignment WHERE officer_id = %s',
                        [new_user.pk]
                    )
                    if _cur.fetchone()[0] == 0:
                        try:
                            _cur.execute(
                                'INSERT INTO clients_officerassignment '
                                '(officer_id, branch_id, branch, max_groups, max_clients, is_accepting_assignments, created_at, updated_at) '
                                'VALUES (%s, %s, %s, 15, 50, 1, NOW(), NOW())',
                                [new_user.pk, branch_id, branch_name]
                            )
                        except Exception:
                            _cur.execute(
                                'INSERT INTO clients_officerassignment '
                                '(officer_id, branch, max_groups, max_clients, is_accepting_assignments, created_at, updated_at) '
                                'VALUES (%s, %s, 15, 50, 1, NOW(), NOW())',
                                [new_user.pk, branch_name]
                            )

            # Redirect to manage officers
            from django.shortcuts import redirect
            return redirect('dashboard:manage_officers')

        except Exception as e:
            return render(request, 'dashboard/user_form.html', {
                'error': f'Error creating user: {str(e)}',
            })
    
    context = {}
    return render(request, 'dashboard/user_form.html', context)


@login_required
def branch_create(request):
    """Create a new branch"""
    user = request.user
    
    # Check if user is admin
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            location = request.POST.get('location')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            manager_id = request.POST.get('manager')
            
            # Validate required fields
            if not all([name, code, location]):
                return render(request, 'dashboard/branch_form.html', {
                    'error': 'Name, code, and location are required',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if branch name already exists
            if Branch.objects.filter(name=name).exists():
                return render(request, 'dashboard/branch_form.html', {
                    'error': 'Branch name already exists',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if branch code already exists
            if Branch.objects.filter(code=code).exists():
                return render(request, 'dashboard/branch_form.html', {
                    'error': 'Branch code already exists',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Get manager if provided
            manager = None
            if manager_id:
                try:
                    manager = User.objects.get(id=manager_id, role='manager')
                except User.DoesNotExist:
                    return render(request, 'dashboard/branch_form.html', {
                        'error': 'Invalid manager selected',
                        'managers': User.objects.filter(role='manager'),
                    })
            
            # Create branch
            branch = Branch.objects.create(
                name=name,
                code=code,
                location=location,
                phone=phone or '',
                email=email or '',
                manager=manager,
                is_active=True
            )
            
            # Redirect to manage branches
            from django.shortcuts import redirect
            return redirect('dashboard:manage_branches')
            
        except Exception as e:
            return render(request, 'dashboard/branch_form.html', {
                'error': f'Error creating branch: {str(e)}',
                'managers': User.objects.filter(role='manager'),
            })
    
    context = {
        'managers': User.objects.filter(role='manager'),
    }
    return render(request, 'dashboard/branch_form.html', context)


# Admin Branch Management Views

@login_required
def admin_branches_list(request):
    """Admin view: List all branches with filtering and pagination"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    branches = Branch.objects.all().order_by('name')
    
    # Search by name, code, or location
    search_query = request.GET.get('search', '')
    if search_query:
        branches = branches.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'active':
            branches = branches.filter(is_active=True)
        elif status_filter == 'inactive':
            branches = branches.filter(is_active=False)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(branches, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'branches': page_obj.object_list,
        'total_branches': branches.count(),
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/admin_branches_list.html', context)


@login_required
def admin_branch_detail(request, branch_id):
    """Admin view: Display branch details and statistics"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Branch not found'})
    
    # Get branch statistics
    officers = User.objects.filter(
        role='loan_officer',
        officer_assignment__branch=branch.name
    )
    
    groups = BorrowerGroup.objects.filter(branch=branch.name)
    
    # Calculate client count
    clients_count = sum(g.member_count for g in groups)
    
    # Get loans for this branch
    loans = Loan.objects.filter(
        loan_officer__officer_assignment__branch=branch.name
    )
    
    total_disbursed = loans.filter(
        status__in=['active', 'completed', 'disbursed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    active_loans = loans.filter(status='active').count()
    
    context = {
        'branch': branch,
        'officers_count': officers.count(),
        'officers': officers,
        'groups_count': groups.count(),
        'groups': groups,
        'clients_count': clients_count,
        'total_disbursed': total_disbursed,
        'active_loans': active_loans,
    }
    
    return render(request, 'dashboard/admin_branch_detail.html', context)


@login_required
def admin_branch_create(request):
    """Admin view: Create a new branch"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            location = request.POST.get('location')
            phone = request.POST.get('phone', '')
            email = request.POST.get('email', '')
            manager_id = request.POST.get('manager')
            
            # Validate required fields
            if not all([name, code, location]):
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Name, code, and location are required',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if branch name already exists
            if Branch.objects.filter(name=name).exists():
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Branch name already exists',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if branch code already exists
            if Branch.objects.filter(code=code).exists():
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Branch code already exists',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Get manager if provided
            manager = None
            if manager_id:
                try:
                    manager = User.objects.get(id=manager_id, role='manager')
                except User.DoesNotExist:
                    return render(request, 'dashboard/admin_branch_form.html', {
                        'error': 'Invalid manager selected',
                        'managers': User.objects.filter(role='manager'),
                    })
            
            # Create branch
            branch = Branch.objects.create(
                name=name,
                code=code,
                location=location,
                phone=phone,
                email=email,
                manager=manager,
                is_active=True
            )
            
            # Log creation in AdminAuditLog
            AdminAuditLog.objects.create(
                admin_user=user,
                action='branch_create',
                affected_branch=branch,
                description=f'Created branch: {name} ({code})',
                new_value=f'Branch: {name}, Code: {code}, Location: {location}'
            )
            
            # Redirect to branch detail
            from django.shortcuts import redirect
            return redirect('dashboard:admin_branch_detail', branch_id=branch.id)
            
        except Exception as e:
            return render(request, 'dashboard/admin_branch_form.html', {
                'error': f'Error creating branch: {str(e)}',
                'managers': User.objects.filter(role='manager'),
            })
    
    context = {
        'managers': User.objects.filter(role='manager'),
    }
    return render(request, 'dashboard/admin_branch_form.html', context)


@login_required
def admin_branch_edit(request, branch_id):
    """Admin view: Edit branch details"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Branch not found'})
    
    if request.method == 'POST':
        try:
            old_values = {
                'name': branch.name,
                'code': branch.code,
                'location': branch.location,
                'phone': branch.phone,
                'email': branch.email,
                'manager': str(branch.manager) if branch.manager else 'None',
            }
            
            name = request.POST.get('name')
            code = request.POST.get('code')
            location = request.POST.get('location')
            phone = request.POST.get('phone', '')
            email = request.POST.get('email', '')
            manager_id = request.POST.get('manager')
            
            # Validate required fields
            if not all([name, code, location]):
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Name, code, and location are required',
                    'branch': branch,
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if new name already exists (excluding current branch)
            if name != branch.name and Branch.objects.filter(name=name).exists():
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Branch name already exists',
                    'branch': branch,
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if new code already exists (excluding current branch)
            if code != branch.code and Branch.objects.filter(code=code).exists():
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Branch code already exists',
                    'branch': branch,
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Get manager if provided
            manager = None
            if manager_id:
                try:
                    manager = User.objects.get(id=manager_id, role='manager')
                except User.DoesNotExist:
                    return render(request, 'dashboard/admin_branch_form.html', {
                        'error': 'Invalid manager selected',
                        'branch': branch,
                        'managers': User.objects.filter(role='manager'),
                    })
            
            # Update branch
            branch.name = name
            branch.code = code
            branch.location = location
            branch.phone = phone
            branch.email = email
            branch.manager = manager
            branch.save()
            
            # Log changes in AdminAuditLog
            new_values = {
                'name': branch.name,
                'code': branch.code,
                'location': branch.location,
                'phone': branch.phone,
                'email': branch.email,
                'manager': str(branch.manager) if branch.manager else 'None',
            }
            
            changes = []
            for key in old_values:
                if old_values[key] != new_values[key]:
                    changes.append(f'{key}: {old_values[key]} → {new_values[key]}')
            
            if changes:
                AdminAuditLog.objects.create(
                    admin_user=user,
                    action='branch_update',
                    affected_branch=branch,
                    description=f'Updated branch: {branch.name}',
                    old_value=str(old_values),
                    new_value=str(new_values)
                )
            
            # Redirect to branch detail
            from django.shortcuts import redirect
            return redirect('dashboard:admin_branch_detail', branch_id=branch.id)
            
        except Exception as e:
            return render(request, 'dashboard/admin_branch_form.html', {
                'error': f'Error updating branch: {str(e)}',
                'branch': branch,
                'managers': User.objects.filter(role='manager'),
            })
    
    context = {
        'branch': branch,
        'managers': User.objects.filter(role='manager'),
        'is_edit': True,
    }
    return render(request, 'dashboard/admin_branch_form.html', context)


@login_required
def admin_branch_deactivate(request, branch_id):
    """Admin view: Deactivate a branch"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Branch not found'})
    
    if request.method == 'POST':
        try:
            # Get existing assignments
            officers = User.objects.filter(
                role='loan_officer',
                officer_assignment__branch=branch.name
            )
            
            groups = BorrowerGroup.objects.filter(branch=branch.name)
            
            # Deactivate branch
            branch.is_active = False
            branch.save()
            
            # Log deactivation
            AdminAuditLog.objects.create(
                admin_user=user,
                action='branch_delete',
                affected_branch=branch,
                description=f'Deactivated branch: {branch.name}',
                old_value=f'is_active: True',
                new_value=f'is_active: False'
            )
            
            # Redirect to branches list
            from django.shortcuts import redirect
            return redirect('dashboard:admin_branches_list')
            
        except Exception as e:
            return render(request, 'dashboard/admin_branch_deactivate_confirm.html', {
                'error': f'Error deactivating branch: {str(e)}',
                'branch': branch,
            })
    
    # Get existing assignments to warn admin
    officers = User.objects.filter(
        role='loan_officer',
        officer_assignment__branch=branch.name
    )
    
    groups = BorrowerGroup.objects.filter(branch=branch.name)
    
    context = {
        'branch': branch,
        'officers_count': officers.count(),
        'groups_count': groups.count(),
    }
    return render(request, 'dashboard/admin_branch_deactivate_confirm.html', context)


# Admin Officer Transfer Views

@login_required
def admin_officers_list(request):
    """Admin view: List all loan officers and managers with details"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    officers = User.objects.filter(role__in=['loan_officer', 'manager']).order_by('first_name', 'last_name')
    
    # Search by name, email, or username
    search_query = request.GET.get('search', '')
    if search_query:
        officers = officers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        officers = officers.filter(role=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'active':
            officers = officers.filter(is_active=True)
        elif status_filter == 'inactive':
            officers = officers.filter(is_active=False)
    
    # Filter by branch (for loan officers)
    branch_filter = request.GET.get('branch')
    if branch_filter:
        officers = officers.filter(officer_assignment__branch=branch_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(officers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get branches for filter dropdown
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'officers': page_obj.object_list,
        'total_officers': officers.count(),
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'branches': branches,
    }
    
    return render(request, 'dashboard/admin_officers_list.html', context)


@login_required
def admin_officer_transfer(request):
    """Admin view: Transfer a loan officer to a different branch"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    # Get officer_id from query string if provided
    selected_officer_id = request.GET.get('officer_id')
    selected_officer = None
    if selected_officer_id:
        try:
            selected_officer = User.objects.get(id=selected_officer_id, role='loan_officer')
        except User.DoesNotExist:
            pass
    
    if request.method == 'POST':
        officer_id = request.POST.get('officer_id')
        new_branch = request.POST.get('new_branch')
        reason = request.POST.get('reason')
        
        try:
            officer = User.objects.get(id=officer_id, role='loan_officer')
            # Update officer's branch assignment
            if hasattr(officer, 'officer_assignment'):
                officer.officer_assignment.branch = new_branch
                officer.officer_assignment.save()
            
            messages.success(request, f'{officer.full_name} has been transferred to {new_branch}')
        except User.DoesNotExist:
            messages.error(request, 'Officer not found')
        
        return redirect('dashboard:admin_officers_list')
    
    officers = User.objects.filter(role='loan_officer')
    branches = Branch.objects.all()
    
    context = {
        'officers': officers,
        'branches': branches,
        'selected_officer': selected_officer,
    }
    
    return render(request, 'dashboard/admin/officer_transfer.html', context)


@login_required
def admin_transfer_history(request):
    """Admin view: Display all officer transfers with dates, reasons, affected groups"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    from clients.models import OfficerTransferLog
    transfers = OfficerTransferLog.objects.all().order_by('-timestamp')
    
    # Search by officer name
    search_query = request.GET.get('search', '')
    if search_query:
        transfers = transfers.filter(
            Q(officer__first_name__icontains=search_query) |
            Q(officer__last_name__icontains=search_query)
        )
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        transfers = transfers.filter(timestamp__gte=start_date)
    if end_date:
        transfers = transfers.filter(timestamp__lte=end_date)
    
    # Filter by branch
    branch_filter = request.GET.get('branch')
    if branch_filter:
        transfers = transfers.filter(
            Q(previous_branch=branch_filter) | Q(new_branch=branch_filter)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transfers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'transfers': page_obj.object_list,
        'total_transfers': transfers.count(),
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'branch_filter': branch_filter,
        'branches': branches,
    }
    
    return render(request, 'dashboard/admin_transfer_history.html', context)


# Admin Client Transfer Views

def _branch_clients_groups(user):
    """Return (clients_qs, groups_qs) scoped to the user's branch for managers, or all for admins."""
    from django.db.models import Q
    if user.role == 'manager':
        try:
            branch_name = user.managed_branch.name
            clients = User.objects.filter(
                Q(group_memberships__group__branch__iexact=branch_name, group_memberships__is_active=True) |
                Q(assigned_officer__officer_assignment__branch__iexact=branch_name),
                role='borrower'
            ).distinct()
            groups = BorrowerGroup.objects.filter(branch__iexact=branch_name, is_active=True)
        except Exception:
            clients = User.objects.none()
            groups = BorrowerGroup.objects.none()
    else:
        clients = User.objects.filter(role='borrower')
        groups = BorrowerGroup.objects.filter(is_active=True)
    return clients, groups


@login_required
def admin_client_transfer(request):
    """Admin/Manager view: Transfer a client to a different group"""
    user = request.user
    
    if user.role not in ['admin', 'manager']:
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            client_id = request.POST.get('client_id')
            destination_group_id = request.POST.get('destination_group')
            reason = request.POST.get('reason')
            
            if not client_id or not destination_group_id or not reason:
                clients_query, groups_query = _branch_clients_groups(user)
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': 'Client, destination group, and reason are required',
                    'clients': clients_query,
                    'groups': groups_query,
                })
            
            try:
                client = User.objects.get(id=client_id, role='borrower')
                
                if user.role == 'manager':
                    try:
                        manager_branch = user.managed_branch.name
                        if not (client.group_memberships.filter(group__branch__iexact=manager_branch, is_active=True).exists() or
                                (client.assigned_officer and client.assigned_officer.officer_assignment.branch.lower() == manager_branch.lower())):
                            raise User.DoesNotExist
                    except User.DoesNotExist:
                        raise
                    except Exception:
                        raise User.DoesNotExist
            except User.DoesNotExist:
                clients_query = User.objects.filter(role='borrower')
                groups_query = BorrowerGroup.objects.filter(is_active=True)
                
                if user.role == 'manager':
                    try:
                        manager_branch = user.managed_branch.name
                        clients_query = clients_query.filter(
                            Q(group_memberships__group__branch=manager_branch, group_memberships__is_active=True) |
                            Q(assigned_officer__officerassignment__branch=manager_branch)
                        ).distinct()
                        groups_query = groups_query.filter(branch=manager_branch)
                    except:
                        clients_query = User.objects.none()
                        groups_query = BorrowerGroup.objects.none()
                
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': 'Client not found',
                    'clients': clients_query,
                    'groups': groups_query,
                })
            
            try:
                dest_group = BorrowerGroup.objects.get(id=destination_group_id)
                
                if user.role == 'manager':
                    try:
                        manager_branch = user.managed_branch.name
                        if dest_group.branch != manager_branch:
                            raise BorrowerGroup.DoesNotExist
                    except:
                        raise BorrowerGroup.DoesNotExist
            except BorrowerGroup.DoesNotExist:
                clients_query = User.objects.filter(role='borrower')
                groups_query = BorrowerGroup.objects.filter(is_active=True)
                
                if user.role == 'manager':
                    try:
                        manager_branch = user.managed_branch.name
                        clients_query = clients_query.filter(
                            Q(group_memberships__group__branch=manager_branch, group_memberships__is_active=True) |
                            Q(assigned_officer__officerassignment__branch=manager_branch)
                        ).distinct()
                        groups_query = groups_query.filter(branch=manager_branch)
                    except:
                        clients_query = User.objects.none()
                        groups_query = BorrowerGroup.objects.none()
                
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': 'Destination group not found',
                    'clients': clients_query,
                    'groups': groups_query,
                })
            
            if not dest_group.is_active:
                clients_query = User.objects.filter(role='borrower')
                groups_query = BorrowerGroup.objects.filter(is_active=True)
                
                if user.role == 'manager':
                    try:
                        manager_branch = user.managed_branch.name
                        clients_query = clients_query.filter(
                            Q(group_memberships__group__branch=manager_branch, group_memberships__is_active=True) |
                            Q(assigned_officer__officerassignment__branch=manager_branch)
                        ).distinct()
                        groups_query = groups_query.filter(branch=manager_branch)
                    except:
                        clients_query = User.objects.none()
                        groups_query = BorrowerGroup.objects.none()
                
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': 'Destination group is not active',
                    'clients': clients_query,
                    'groups': groups_query,
                })
            
            if dest_group.is_full:
                clients_query = User.objects.filter(role='borrower')
                groups_query = BorrowerGroup.objects.filter(is_active=True)
                
                if user.role == 'manager':
                    try:
                        manager_branch = user.managed_branch.name
                        clients_query = clients_query.filter(
                            Q(group_memberships__group__branch=manager_branch, group_memberships__is_active=True) |
                            Q(assigned_officer__officerassignment__branch=manager_branch)
                        ).distinct()
                        groups_query = groups_query.filter(branch=manager_branch)
                    except:
                        clients_query = User.objects.none()
                        groups_query = BorrowerGroup.objects.none()
                
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': f'Destination group is at capacity ({dest_group.member_count}/{dest_group.max_members})',
                    'clients': clients_query,
                    'groups': groups_query,
                })
            
            try:
                current_membership = GroupMembership.objects.get(borrower=client, is_active=True)
                previous_group = current_membership.group
            except GroupMembership.DoesNotExist:
                previous_group = None
            
            active_loans = Loan.objects.filter(borrower=client, status='active')
            pending_loans = Loan.objects.filter(borrower=client, status='pending')
            transferable_loans = Loan.objects.filter(borrower=client).exclude(status__in=['completed', 'rejected'])
            
            if transferable_loans.exists() and not request.POST.get('transfer_loans'):
                clients_query = User.objects.filter(role='borrower')
                groups_query = BorrowerGroup.objects.filter(is_active=True)
                
                if user.role == 'manager':
                    try:
                        manager_branch = user.managed_branch.name
                        clients_query = clients_query.filter(
                            Q(group_memberships__group__branch=manager_branch, group_memberships__is_active=True) |
                            Q(assigned_officer__officerassignment__branch=manager_branch)
                        ).distinct()
                        groups_query = groups_query.filter(branch=manager_branch)
                    except:
                        clients_query = User.objects.none()
                        groups_query = BorrowerGroup.objects.none()
                
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'show_loan_transfer_confirm': True,
                    'client': client,
                    'dest_group': dest_group,
                    'transferable_loans': transferable_loans,
                    'active_loans': active_loans,
                    'pending_loans': pending_loans,
                    'clients': clients_query,
                    'groups': groups_query,
                })
            
            if previous_group:
                current_membership.is_active = False
                current_membership.save()

            # Reactivate existing membership or create new one
            existing = GroupMembership.objects.filter(borrower=client, group=dest_group).first()
            if existing:
                existing.is_active = True
                existing.save(update_fields=['is_active', 'updated_at'])
                new_membership = existing
            else:
                new_membership = GroupMembership.objects.create(
                    borrower=client,
                    group=dest_group,
                    is_active=True,
                    added_by=user
                )
            
            # Transfer loans if requested
            transferred_loans = []
            if request.POST.get('transfer_loans') == 'yes':
                new_officer = dest_group.assigned_officer
                if new_officer:
                    # Transfer all transferable loans to new loan officer
                    for loan in transferable_loans:
                        old_officer = loan.loan_officer
                        loan.loan_officer = new_officer
                        loan.save()
                        transferred_loans.append(loan)
                        
                        # Create loan transfer audit log
                        AdminAuditLog.objects.create(
                            admin_user=user,
                            action='loan_transfer',
                            affected_user=client,
                            description=f'Transferred loan {loan.application_number} from {old_officer.get_full_name() if old_officer else "unassigned"} to {new_officer.get_full_name()}',
                            old_value=f'loan_officer: {old_officer.get_full_name() if old_officer else "none"}',
                            new_value=f'loan_officer: {new_officer.get_full_name()}'
                        )
            
            # Create ClientTransferLog
            from clients.models import ClientTransferLog
            ClientTransferLog.objects.create(
                client=client,
                previous_group=previous_group,
                new_group=dest_group,
                reason=reason,
                performed_by=user
            )
            
            # Create AdminAuditLog
            AdminAuditLog.objects.create(
                admin_user=user,
                action='client_transfer',
                affected_user=client,
                affected_group=dest_group,
                description=f'Transferred client {client.full_name} from {previous_group.name if previous_group else "no group"} to {dest_group.name}',
                old_value=f'group: {previous_group.name if previous_group else "none"}',
                new_value=f'group: {dest_group.name}'
            )
            
            # Add loan transfer info to description if loans were transferred
            if transferred_loans:
                AdminAuditLog.objects.create(
                    admin_user=user,
                    action='loan_transfer_batch',
                    affected_user=client,
                    description=f'Transferred {len(transferred_loans)} loan(s) with client {client.full_name} to {dest_group.assigned_officer.get_full_name() if dest_group.assigned_officer else "new officer"}',
                    old_value=f'loans: {[loan.application_number for loan in transferred_loans]}',
                    new_value=f'new_officer: {dest_group.assigned_officer.get_full_name() if dest_group.assigned_officer else "unassigned"}'
                )
            
            # Redirect to transfer history
            from django.shortcuts import redirect
            return redirect('dashboard:admin_client_transfer_history')
            
        except Exception as e:
            clients_query, groups_query = _branch_clients_groups(user)
            return render(request, 'dashboard/admin_client_transfer_form.html', {
                'error': f'Error transferring client: {str(e)}',
                'clients': clients_query,
                'groups': groups_query,
            })
    
    clients_query, groups_query = _branch_clients_groups(user)
    context = {
        'clients': clients_query,
        'groups': groups_query,
    }
    return render(request, 'dashboard/admin_client_transfer_form.html', context)


@login_required
def admin_client_transfer_history(request):
    """Admin view: Display all client transfers with dates, reasons, affected groups"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    from clients.models import ClientTransferLog
    transfers = ClientTransferLog.objects.all().order_by('-timestamp')
    
    # Search by client name
    search_query = request.GET.get('search', '')
    if search_query:
        transfers = transfers.filter(
            Q(client__first_name__icontains=search_query) |
            Q(client__last_name__icontains=search_query)
        )
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        transfers = transfers.filter(timestamp__gte=start_date)
    if end_date:
        transfers = transfers.filter(timestamp__lte=end_date)
    
    # Filter by group
    group_filter = request.GET.get('group')
    if group_filter:
        transfers = transfers.filter(
            Q(previous_group_id=group_filter) | Q(new_group_id=group_filter)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transfers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get groups for filter
    groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'transfers': page_obj.object_list,
        'total_transfers': transfers.count(),
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'group_filter': group_filter,
        'groups': groups,
    }
    
    return render(request, 'dashboard/admin_client_transfer_history.html', context)


# Admin Group Assignment Override Views

@login_required
def admin_override_assignment(request):
    """Admin view: Override or correct group assignments for clients"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            client_id = request.POST.get('client_id')
            destination_group_id = request.POST.get('destination_group')
            override_reason = request.POST.get('override_reason')
            
            # Validate required fields
            if not client_id or not destination_group_id or not override_reason:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': 'Client, destination group, and reason are required',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Get client
            try:
                client = User.objects.get(id=client_id, role='borrower')
            except User.DoesNotExist:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': 'Client not found',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Get destination group
            try:
                dest_group = BorrowerGroup.objects.get(id=destination_group_id)
            except BorrowerGroup.DoesNotExist:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': 'Destination group not found',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Validate destination group is active
            if not dest_group.is_active:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': 'Destination group is not active',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Validate destination group is not at capacity
            if dest_group.is_full:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': f'Destination group is at capacity ({dest_group.member_count}/{dest_group.max_members})',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Get current group membership
            try:
                current_membership = GroupMembership.objects.get(borrower=client, is_active=True)
                previous_group = current_membership.group
            except GroupMembership.DoesNotExist:
                previous_group = None
            
            # Deactivate current membership if exists
            if previous_group:
                current_membership.is_active = False
                current_membership.save()
            
            # Create new membership
            new_membership = GroupMembership.objects.create(
                borrower=client,
                group=dest_group,
                is_active=True,
                added_by=user
            )
            
            # Create AdminAuditLog with override reason
            AdminAuditLog.objects.create(
                admin_user=user,
                action='override_assignment',
                affected_user=client,
                affected_group=dest_group,
                description=f'Overrode assignment for {client.full_name}: {previous_group.name if previous_group else "no group"} → {dest_group.name}',
                old_value=f'group: {previous_group.name if previous_group else "none"}',
                new_value=f'group: {dest_group.name}, reason: {override_reason}'
            )
            
            # Redirect to success page
            from django.shortcuts import redirect
            return redirect('dashboard:admin_branches_list')
            
        except Exception as e:
            return render(request, 'dashboard/admin_override_assignment_form.html', {
                'error': f'Error overriding assignment: {str(e)}',
                'clients': User.objects.filter(role='borrower'),
                'groups': BorrowerGroup.objects.filter(is_active=True),
            })
    
    context = {
        'clients': User.objects.filter(role='borrower'),
        'groups': BorrowerGroup.objects.filter(is_active=True),
    }
    return render(request, 'dashboard/admin_override_assignment_form.html', context)


# Admin High-Value Loan Approval Views

@login_required
def admin_pending_approvals(request):
    """Admin view: Display all pending high-value loans awaiting approval"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    from clients.models import LoanApprovalQueue
    pending_loans = LoanApprovalQueue.objects.filter(status='pending').order_by('-submitted_date')
    
    # Search by borrower name or loan ID
    search_query = request.GET.get('search', '')
    if search_query:
        pending_loans = pending_loans.filter(
            Q(loan__borrower__first_name__icontains=search_query) |
            Q(loan__borrower__last_name__icontains=search_query) |
            Q(loan__id__icontains=search_query)
        )
    
    # Filter by branch
    branch_filter = request.GET.get('branch')
    if branch_filter:
        pending_loans = pending_loans.filter(
            loan__loan_officer__officer_assignment__branch=branch_filter
        )
    
    # Filter by amount range
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if min_amount:
        pending_loans = pending_loans.filter(loan__principal_amount__gte=min_amount)
    if max_amount:
        pending_loans = pending_loans.filter(loan__principal_amount__lte=max_amount)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(pending_loans, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'pending_loans': page_obj.object_list,
        'total_pending': pending_loans.count(),
        'search_query': search_query,
        'branch_filter': branch_filter,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'branches': branches,
        'pending_security_txns': SecurityTransaction.objects.filter(
            status='pending'
        ).select_related('loan', 'loan__borrower', 'initiated_by').order_by('-created_at'),
        'pending_applications': __import__('loans.models', fromlist=['LoanApplication']).LoanApplication.objects.filter(
            status='pending'
        ).select_related('borrower', 'loan_officer', 'group').order_by('-created_at'),
    }
    
    return render(request, 'dashboard/admin_pending_approvals.html', context)


@login_required
def admin_loan_approval_detail(request, loan_id):
    """Admin view: Display complete loan information for approval decision"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Loan not found'})
    
    # Get approval queue entry
    try:
        from clients.models import LoanApprovalQueue
        approval_queue = LoanApprovalQueue.objects.get(loan=loan)
    except:
        approval_queue = None
    
    # Get borrower details
    borrower = loan.borrower
    
    # Get security deposit
    try:
        from loans.models import SecurityDeposit
        security_deposit = SecurityDeposit.objects.get(loan=loan)
    except:
        security_deposit = None
    
    # Get group membership
    try:
        group_membership = GroupMembership.objects.get(borrower=borrower, is_active=True)
        group = group_membership.group
    except:
        group = None
    
    context = {
        'loan': loan,
        'approval_queue': approval_queue,
        'borrower': borrower,
        'security_deposit': security_deposit,
        'group': group,
    }
    
    return render(request, 'dashboard/admin_loan_approval_detail.html', context)


@login_required
def admin_loan_approve(request, loan_id):
    """Admin view: Approve a high-value loan"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method != 'POST':
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid request method'})
    
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Loan not found'})
    
    try:
        from clients.models import LoanApprovalQueue, ApprovalAuditLog
        
        reason = request.POST.get('reason', '')
        
        # Get approval queue entry
        approval_queue = LoanApprovalQueue.objects.get(loan=loan, status='pending')
        
        # Update approval queue
        approval_queue.status = 'approved'
        approval_queue.decided_by = user
        approval_queue.decision_date = timezone.now()
        approval_queue.decision_reason = reason
        approval_queue.save()
        
        # Update loan status to allow disbursement
        loan.status = 'approved'
        loan.save()
        
        # Create ApprovalAuditLog
        ApprovalAuditLog.objects.create(
            loan=loan,
            action='approved',
            performed_by=user,
            reason=reason,
            ip_address=get_client_ip(request)
        )
        
        # Create AdminAuditLog
        AdminAuditLog.objects.create(
            admin_user=user,
            action='loan_approve',
            affected_user=loan.borrower,
            description=f'Approved high-value loan {loan.id} for K{loan.principal_amount}',
            new_value=f'status: approved, reason: {reason}'
        )
        
        # Redirect to pending approvals
        from django.shortcuts import redirect
        return redirect('dashboard:admin_pending_approvals')
        
    except Exception as e:
        return render(request, 'dashboard/access_denied.html', {'message': f'Error approving loan: {str(e)}'})


@login_required
def admin_loan_reject(request, loan_id):
    """Admin view: Reject a high-value loan"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method != 'POST':
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid request method'})
    
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Loan not found'})
    
    try:
        from clients.models import LoanApprovalQueue, ApprovalAuditLog
        
        reason = request.POST.get('reason', '')
        
        if not reason:
            return render(request, 'dashboard/admin_loan_approval_detail.html', {
                'error': 'Rejection reason is required',
                'loan': loan,
            })
        
        # Get approval queue entry
        approval_queue = LoanApprovalQueue.objects.get(loan=loan, status='pending')
        
        # Update approval queue
        approval_queue.status = 'rejected'
        approval_queue.decided_by = user
        approval_queue.decision_date = timezone.now()
        approval_queue.decision_reason = reason
        approval_queue.save()
        
        # Update loan status to rejected
        loan.status = 'rejected'
        loan.save()
        
        # Create ApprovalAuditLog
        ApprovalAuditLog.objects.create(
            loan=loan,
            action='rejected',
            performed_by=user,
            reason=reason,
            ip_address=get_client_ip(request)
        )
        
        # Create AdminAuditLog
        AdminAuditLog.objects.create(
            admin_user=user,
            action='loan_reject',
            affected_user=loan.borrower,
            description=f'Rejected high-value loan {loan.id} for K{loan.principal_amount}',
            new_value=f'status: rejected, reason: {reason}'
        )
        
        # Redirect to pending approvals
        from django.shortcuts import redirect
        return redirect('dashboard:admin_pending_approvals')
        
    except Exception as e:
        return render(request, 'dashboard/access_denied.html', {'message': f'Error rejecting loan: {str(e)}'})


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Admin Company-Wide Loan Viewing

@login_required
def admin_all_loans(request):
    """Admin view: Display all loans across all branches"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    from clients.models import GroupMembership
    
    loans = Loan.objects.all().select_related('borrower', 'loan_officer').order_by('-created_at')
    
    # Search by borrower name or loan ID
    search_query = request.GET.get('search', '')
    if search_query:
        loans = loans.filter(
            Q(borrower__first_name__icontains=search_query) |
            Q(borrower__last_name__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Filter by branch - include both officer-assigned loans and group-member loans
    branch_filter = request.GET.get('branch')
    if branch_filter:
        loans = loans.filter(
            Q(loan_officer__officer_assignment__branch=branch_filter) |
            Q(borrower__group_memberships__group__branch=branch_filter)
        ).distinct()
    
    # Filter by loan officer
    officer_filter = request.GET.get('officer')
    if officer_filter:
        loans = loans.filter(loan_officer_id=officer_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        loans = loans.filter(status=status_filter)
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        loans = loans.filter(created_at__gte=start_date)
    if end_date:
        loans = loans.filter(created_at__lte=end_date)
    
    # Filter by amount range
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if min_amount:
        loans = loans.filter(principal_amount__gte=min_amount)
    if max_amount:
        loans = loans.filter(principal_amount__lte=max_amount)
    
    # Calculate total amount for filtered loans
    from django.db.models import Sum
    total_amount = loans.aggregate(total=Sum('principal_amount'))['total'] or 0
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(loans, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Add group information to each loan in the current page
    loans_with_groups = []
    for loan in page_obj.object_list:
        membership = GroupMembership.objects.filter(
            borrower=loan.borrower,
            is_active=True
        ).select_related('group').first()
        
        loans_with_groups.append({
            'loan': loan,
            'group': membership.group if membership else None,
        })
    
    # Get branches, officers and statuses for filters
    branches = Branch.objects.filter(is_active=True).order_by('name')
    officers = User.objects.filter(role='loan_officer', is_active=True).order_by('first_name', 'last_name')
    statuses = Loan._meta.get_field('status').choices
    
    context = {
        'page_obj': page_obj,
        'loans': page_obj.object_list,
        'loans_with_groups': loans_with_groups,
        'total_loans': loans.count(),
        'total_amount': total_amount,
        'search_query': search_query,
        'branch_filter': branch_filter,
        'officer_filter': officer_filter,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'branches': branches,
        'officers': officers,
        'statuses': statuses,
    }
    
    return render(request, 'dashboard/admin_all_loans.html', context)


@login_required
def admin_loan_detail(request, loan_id):
    """Admin view: Display complete loan information"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Loan not found'})
    
    # Get borrower
    borrower = loan.borrower
    
    # Get group membership
    try:
        group_membership = GroupMembership.objects.get(borrower=borrower, is_active=True)
        group = group_membership.group
    except:
        group = None
    
    # Get collections
    from payments.models import PaymentCollection
    collections = PaymentCollection.objects.filter(loan=loan).order_by('-collection_date')
    
    total_collected = collections.aggregate(total=Sum('collected_amount'))['total'] or 0
    
    # Get security deposit
    try:
        from loans.models import SecurityDeposit
        security_deposit = SecurityDeposit.objects.get(loan=loan)
    except:
        security_deposit = None
    
    context = {
        'loan': loan,
        'borrower': borrower,
        'group': group,
        'collections': collections,
        'total_collected': total_collected,
        'security_deposit': security_deposit,
    }
    
    return render(request, 'dashboard/admin_loan_detail.html', context)


@login_required
def admin_loan_statistics(request):
    """Admin view: Display portfolio metrics and branch comparison"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    # Get all loans
    all_loans = Loan.objects.all()
    
    # Total metrics
    total_disbursed = all_loans.filter(
        status__in=['active', 'completed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    active_loans = all_loans.filter(status='active').count()
    completed_loans = all_loans.filter(status='completed').count()
    defaulted_loans = all_loans.filter(status='defaulted').count()
    total_loans = all_loans.count()
    
    # Collection metrics
    from payments.models import PaymentCollection
    all_collections = PaymentCollection.objects.filter(status='completed')
    total_collected = all_collections.aggregate(total=Sum('collected_amount'))['total'] or 0
    
    if all_collections.exists():
        collection_rate = (all_collections.filter(is_partial=False).count() / all_collections.count() * 100)
    else:
        collection_rate = 0
    
    # Branch performance
    branches = Branch.objects.filter(is_active=True)
    branch_stats = []
    
    for branch in branches:
        branch_loans = all_loans.filter(
            loan_officer__officer_assignment__branch=branch.name
        )
        
        branch_disbursed = branch_loans.filter(
            status__in=['active', 'completed']
        ).aggregate(total=Sum('principal_amount'))['total'] or 0
        
        branch_active = branch_loans.filter(status='active').count()
        branch_defaulted = branch_loans.filter(status='defaulted').count()
        
        branch_collections = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            status='completed'
        )
        
        if branch_collections.exists():
            branch_rate = (branch_collections.filter(is_partial=False).count() / branch_collections.count() * 100)
        else:
            branch_rate = 0
        
        stats = {
            'name': branch.name,
            'total_disbursed': branch_disbursed,
            'active_loans': branch_active,
            'defaulted_loans': branch_defaulted,
            'collection_rate': round(branch_rate, 1),
        }
        branch_stats.append(stats)
    
    context = {
        'total_disbursed': total_disbursed,
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'defaulted_loans': defaulted_loans,
        'total_loans': total_loans,
        'total_collected': total_collected,
        'collection_rate': round(collection_rate, 1),
        'branch_stats': branch_stats,
        'average_loan_amount': total_disbursed / total_loans if total_loans > 0 else 0,
        'default_rate': (defaulted_loans / total_loans * 100) if total_loans > 0 else 0,
        'completion_rate': (completed_loans / total_loans * 100) if total_loans > 0 else 0,
        'outstanding_amount': total_disbursed - total_collected,
        'collection_percentage': (total_collected / total_disbursed * 100) if total_disbursed > 0 else 0,
    }
    
    return render(request, 'dashboard/admin_loan_statistics.html', context)



@login_required
def groups_permissions(request):
    """Groups and Permissions Management"""
    if request.user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    from django.contrib.auth.models import Group, Permission
    
    groups = Group.objects.all()
    permissions = Permission.objects.all()
    
    context = {
        'groups': groups,
        'permissions': permissions,
    }
    
    return render(request, 'dashboard/admin/groups_permissions.html', context)


@login_required
def system_reports(request):
    """System Reports View"""
    if request.user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    from datetime import timedelta
    from django.db.models import Count, Sum
    from documents.models import ClientDocument
    
    # System health overview
    total_users = User.objects.count()
    total_loans = Loan.objects.count()
    pending_documents = ClientDocument.objects.filter(status='pending').count()
    
    system_health = {
        'total_users': total_users,
        'total_loans': total_loans,
        'pending_documents': pending_documents,
    }
    
    # User activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    active_users_30d = User.objects.filter(last_login__gte=thirty_days_ago).count()
    total_logins = User.objects.filter(last_login__isnull=False).count()
    
    user_activity = {
        'new_users_30d': new_users_30d,
        'active_users_30d': active_users_30d,
        'total_logins': total_logins,
    }
    
    # Loan performance (last 30 days)
    applications_30d = Loan.objects.filter(application_date__gte=thirty_days_ago).count()
    approvals_30d = Loan.objects.filter(
        approval_date__gte=thirty_days_ago,
        approval_date__isnull=False
    ).count()
    approval_rate = (approvals_30d / applications_30d * 100) if applications_30d > 0 else 0
    
    loan_performance = {
        'applications_30d': applications_30d,
        'approvals_30d': approvals_30d,
        'approval_rate': approval_rate,
    }
    
    context = {
        'system_health': system_health,
        'user_activity': user_activity,
        'loan_performance': loan_performance,
    }
    
    return render(request, 'dashboard/admin/system_reports.html', context)


@login_required
def analytics(request):
    """Analytics Dashboard"""
    if request.user.role not in ['admin', 'manager']:
        return render(request, 'dashboard/access_denied.html')
    
    # Get loan status distribution
    loan_status_data = []
    statuses = ['pending', 'approved', 'active', 'completed', 'rejected', 'disbursed']
    for status in statuses:
        count = Loan.objects.filter(status=status).count()
        if count > 0:
            loan_status_data.append({
                'status': status,
                'count': count
            })
    
    # Get payment performance
    from payments.models import PaymentCollection
    all_collections = PaymentCollection.objects.all()
    total_due = sum(c.expected_amount for c in all_collections) or 0
    total_paid = sum(c.collected_amount for c in all_collections) or 0
    collection_rate = (total_paid / total_due * 100) if total_due > 0 else 0
    
    payment_performance = {
        'total_due': total_due,
        'total_paid': total_paid,
        'collection_rate': collection_rate,
    }
    
    # Get monthly disbursements for last 12 months
    from datetime import datetime, timedelta
    from django.db.models import Count, Sum
    
    monthly_disbursements = []
    today = date.today()
    
    for i in range(11, -1, -1):
        # Calculate month start and end
        month_start = today.replace(day=1) - timedelta(days=i*30)
        month_start = month_start.replace(day=1)
        
        if i == 0:
            month_end = today
        else:
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Get loans created/applied in this month (use application_date since disbursement_date may be null)
        month_loans = Loan.objects.filter(
            status__in=['active', 'completed', 'disbursed', 'approved'],
            application_date__gte=month_start,
            application_date__lte=month_end
        )
        
        count = month_loans.count()
        total = month_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
        
        if count > 0:
            monthly_disbursements.append({
                'month': month_start.strftime('%B %Y'),
                'count': count,
                'total': total,
            })
    
    context = {
        'loan_status_data': loan_status_data,
        'payment_performance': payment_performance,
        'monthly_disbursements': monthly_disbursements,
    }
    
    return render(request, 'dashboard/analytics.html', context)


@login_required
def loan_officer_document_verification(request):
    """Document verification dashboard for loan officers only"""
    user = request.user
    
    if user.role != 'loan_officer':
        return render(request, 'dashboard/access_denied.html')
    
    # Get branch from officer assignment (optional now)
    branch = None
    try:
        from clients.models import OfficerAssignment
        officer_assignment = OfficerAssignment.objects.filter(officer=user).first()
        if officer_assignment and officer_assignment.branch:
            from collections import namedtuple
            Branch = namedtuple('Branch', ['name'])
            branch = Branch(name=officer_assignment.branch.name)
        else:
            from collections import namedtuple
            Branch = namedtuple('Branch', ['name'])
            branch = Branch(name='All Clients')
    except Exception as e:
        print(f"Error getting officer assignment: {e}")
        from collections import namedtuple
        Branch = namedtuple('Branch', ['name'])
        branch = Branch(name='All Clients')
    
    try:
        from documents.models import ClientVerification, ClientDocument
        from django.db.models import Q
        from accounts.models import User
        
        # Loan officer sees only their assigned clients
        branch_clients = User.objects.filter(
            Q(assigned_officer=user) | Q(group_memberships__group__assigned_officer=user),
            role='borrower'
        ).distinct()
        
        branch_client_ids = branch_clients.values_list('id', flat=True)
        
        print(f"DEBUG: Loan officer {user.full_name} has {branch_clients.count()} assigned clients")
        print(f"DEBUG: Client IDs: {list(branch_client_ids)}")
        
        # Get verified verifications (approved documents) - this is the main focus for loan officers
        verified_verifications = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status='verified'
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        # Get pending verifications for reference (documents submitted but not yet verified)
        pending_verifications = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status__in=['documents_submitted', 'documents_rejected']
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        print(f"DEBUG: Pending verifications from ClientVerification: {pending_verifications.count()}")
        
        # Also get clients with pending individual documents
        clients_with_pending_docs = ClientDocument.objects.filter(
            client_id__in=branch_client_ids,
            status='pending'
        ).values_list('client_id', flat=True).distinct()
        
        print(f"DEBUG: Clients with pending documents: {list(clients_with_pending_docs)}")
        
        # Add these clients to pending verifications if not already there
        pending_verification_client_ids = set(pending_verifications.values_list('client_id', flat=True))
        for client_id in clients_with_pending_docs:
            if client_id not in pending_verification_client_ids:
                try:
                    verification = ClientVerification.objects.get(client_id=client_id)
                    if verification not in pending_verifications:
                        pending_verifications = list(pending_verifications) + [verification]
                        print(f"DEBUG: Added verification for client {client_id}")
                except ClientVerification.DoesNotExist:
                    print(f"DEBUG: No verification record for client {client_id}")
        
        # Get statistics
        total_clients = ClientVerification.objects.filter(client_id__in=branch_client_ids).count()
        verified_clients = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status='verified'
        ).count()
        pending_count = pending_verifications.count() if isinstance(pending_verifications, list) else pending_verifications.count()
        
        print(f"DEBUG: Total clients: {total_clients}, Verified: {verified_clients}, Pending: {pending_count}")
        
        # Get documents needing review
        documents_needing_review = ClientDocument.objects.filter(
            client_id__in=branch_client_ids,
            status='pending'
        ).select_related('client').order_by('-uploaded_at')
        
    except Exception as e:
        print(f"Error in loan officer document verification: {e}")
        import traceback
        traceback.print_exc()
        pending_verifications = []
        verified_verifications = []
        documents_needing_review = []
        total_clients = 0
        verified_clients = 0
        pending_count = 0
    
    context = {
        'branch': branch,
        'pending_verifications': pending_verifications,
        'verified_verifications': verified_verifications,
        'documents_needing_review': documents_needing_review,
        'total_clients': total_clients,
        'verified_clients': verified_clients,
        'pending_count': pending_count,
        'verification_rate': round((verified_clients / total_clients * 100) if total_clients > 0 else 0, 1),
    }
    
    return render(request, 'dashboard/loan_officer_document_verification.html', context)


@login_required
def manager_document_verification(request):
    """Document verification dashboard for managers and loan officers"""
    user = request.user
    
    if user.role not in ['manager', 'loan_officer']:
        return render(request, 'dashboard/access_denied.html')
    
    branch = None
    try:
        if user.role == 'manager':
            branch = user.managed_branch
            if not branch:
                return render(request, 'dashboard/access_denied.html', {
                    'message': 'You have not been assigned to a branch. Please contact your administrator.'
                })
        else:
            branch = None
    except Exception as e:
        print(f"Error getting branch: {e}")
        return render(request, 'dashboard/access_denied.html', {
            'message': 'Error accessing document verification. Please contact your administrator.'
        })
    
    try:
        from documents.models import ClientVerification, ClientDocument
        from django.db.models import Q
        from accounts.models import User
        
        if user.role == 'manager':
            manager_branch = user.managed_branch.name
            branch_clients = User.objects.filter(
                Q(group_memberships__group__branch=manager_branch, group_memberships__is_active=True) |
                Q(assigned_officer__officer_assignment__branch=manager_branch),
                role='borrower'
            ).distinct()
        else:
            branch_clients = User.objects.filter(
                Q(assigned_officer=user) | Q(group_memberships__group__assigned_officer=user),
                role='borrower'
            ).distinct()

        branch_client_ids = branch_clients.values_list('id', flat=True)

        pending_verifications = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status__in=['documents_submitted', 'documents_rejected']
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')

        recent_verifications = ClientDocument.objects.filter(
            client_id__in=branch_client_ids,
            status='approved'
        ).select_related('client', 'verified_by').order_by('-verification_date')[:10]

        total_clients = branch_clients.count()
        verified_clients = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status='verified'
        ).count()
        pending_count = pending_verifications.count()

        documents_needing_review = ClientDocument.objects.filter(
            client_id__in=branch_client_ids,
            status='pending'
        ).select_related('client').order_by('-uploaded_at')
        
    except Exception as e:
        print(f"Error in document verification: {e}")
        pending_verifications = []
        recent_verifications = []
        documents_needing_review = []
        total_clients = 0
        verified_clients = 0
        pending_count = 0
    
    context = {
        'branch': branch,
        'user_role': user.role,
        'pending_verifications': pending_verifications,
        'recent_verifications': recent_verifications,
        'documents_needing_review': documents_needing_review,
        'total_clients': total_clients,
        'verified_clients': verified_clients,
        'pending_count': pending_count,
        'verification_rate': round((verified_clients / total_clients * 100) if total_clients > 0 else 0, 1),
    }
    
    return render(request, 'dashboard/manager_document_verification.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# Admin Report Views
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def financial_summary(request):
    """System-wide financial summary (admin only)."""
    if request.user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')

    from loans.models import BranchVault, SecurityDeposit
    from payments.models import DefaultCollection
    from expenses.models import VaultTransaction
    from clients.models import Branch
    from payments.models import PaymentSchedule
    from datetime import datetime

    # Get filter parameters
    branch_filter = request.GET.get('branch', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # System-wide totals
    total_capital = VaultTransaction.objects.filter(
        transaction_type='capital_injection'
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_disbursed = Loan.objects.filter(
        status__in=['active', 'completed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0

    total_repaid = PaymentCollection.objects.filter(
        status='completed'
    ).aggregate(total=Sum('collected_amount'))['total'] or 0

    total_outstanding = (total_disbursed or 0) - (total_repaid or 0)

    total_security = SecurityDeposit.objects.filter(
        is_verified=True
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    total_default_collections = DefaultCollection.objects.aggregate(
        total=Sum('amount_paid')
    )['total'] or 0

    # Per-branch breakdown
    branches = Branch.objects.filter(is_active=True)
    branch_rows = []
    for branch in branches:
        vault_balance = 0
        try:
            vault_balance = BranchVault.objects.get(branch=branch).balance
        except Exception:
            pass

        branch_loans = Loan.objects.filter(
            Q(loan_officer__officer_assignment__branch=branch.name) |
            Q(borrower__group_memberships__group__branch=branch.name)
        ).distinct()

        b_disbursed = branch_loans.filter(
            status__in=['active', 'completed']
        ).aggregate(total=Sum('principal_amount'))['total'] or 0

        b_repaid = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            status='completed'
        ).distinct().aggregate(total=Sum('collected_amount'))['total'] or 0

        b_outstanding = (b_disbursed or 0) - (b_repaid or 0)
        b_active = branch_loans.filter(status='active').count()

        b_capital = VaultTransaction.objects.filter(
            transaction_type='capital_injection',
            branch=branch.name
        ).aggregate(total=Sum('amount'))['total'] or 0

        branch_rows.append({
            'branch': branch,
            'vault_balance': vault_balance,
            'capital_injected': b_capital,
            'disbursed': b_disbursed,
            'repaid': b_repaid,
            'outstanding': b_outstanding,
            'active_loans': b_active,
        })

    # Capital injection history with filters
    capital_history = VaultTransaction.objects.filter(
        transaction_type='capital_injection'
    )
    
    if branch_filter:
        capital_history = capital_history.filter(branch=branch_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            capital_history = capital_history.filter(transaction_date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            capital_history = capital_history.filter(transaction_date__lte=date_to_obj)
        except ValueError:
            pass
    
    capital_history = capital_history.select_related('recorded_by').order_by('-transaction_date')[:100]

    context = {
        'total_capital': total_capital,
        'total_disbursed': total_disbursed,
        'total_repaid': total_repaid,
        'total_outstanding': total_outstanding,
        'total_security': total_security,
        'total_default_collections': total_default_collections,
        'branch_rows': branch_rows,
        'capital_history': capital_history,
        'branches': branches,
        'branch_filter': branch_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'dashboard/financial_summary.html', context)


@login_required
def branch_comparison(request):
    """Side-by-side branch comparison (admin only)."""
    if request.user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')

    from loans.models import BranchVault, SecurityDeposit
    from clients.models import Branch, OfficerAssignment
    from payments.models import PaymentSchedule

    branches = Branch.objects.filter(is_active=True)
    rows = []
    for branch in branches:
        manager_name = branch.manager.get_full_name() if branch.manager else '—'

        officers_count = OfficerAssignment.objects.filter(branch=branch.name).count()
        groups_count = BorrowerGroup.objects.filter(branch=branch.name, is_active=True).count()
        clients_count = User.objects.filter(
            Q(group_memberships__group__branch=branch.name) |
            Q(assigned_officer__officer_assignment__branch=branch.name),
            role='borrower',
        ).distinct().count()

        branch_loans = Loan.objects.filter(
            Q(loan_officer__officer_assignment__branch=branch.name) |
            Q(borrower__group_memberships__group__branch=branch.name)
        ).distinct()

        active_loans = branch_loans.filter(status='active').count()
        total_disbursed = branch_loans.filter(
            status__in=['active', 'completed']
        ).aggregate(total=Sum('principal_amount'))['total'] or 0
        
        # Calculate total outstanding balance for active loans
        total_outstanding = branch_loans.filter(
            status='active'
        ).aggregate(total=Sum('balance_remaining'))['total'] or 0

        completed_collections = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            status='completed'
        ).distinct()
        total_repaid = completed_collections.aggregate(total=Sum('collected_amount'))['total'] or 0

        all_collections = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name
        ).distinct()
        total_expected = all_collections.aggregate(total=Sum('expected_amount'))['total'] or 0
        collection_rate = round((total_repaid / total_expected * 100), 1) if total_expected > 0 else 0

        vault_balance = 0
        try:
            vault_balance = BranchVault.objects.get(branch=branch).balance
        except Exception:
            pass

        today = date.today()
        default_count = branch_loans.filter(
            status='active',
            payment_schedule__is_paid=False,
            payment_schedule__due_date__lt=today,
        ).distinct().count()

        rows.append({
            'branch': branch,
            'manager_name': manager_name,
            'officers_count': officers_count,
            'groups_count': groups_count,
            'clients_count': clients_count,
            'active_loans': active_loans,
            'total_disbursed': total_disbursed,
            'total_outstanding': total_outstanding,
            'total_repaid': total_repaid,
            'collection_rate': collection_rate,
            'vault_balance': vault_balance,
            'default_count': default_count,
        })

    # Sort by collection rate descending
    rows.sort(key=lambda r: r['collection_rate'], reverse=True)

    return render(request, 'dashboard/branch_comparison.html', {'rows': rows})


@login_required
def loan_aging(request):
    """Loan aging report grouped by days overdue (admin only)."""
    if request.user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')

    from payments.models import PaymentSchedule

    today = date.today()
    active_loans = Loan.objects.filter(status='active').select_related(
        'borrower', 'loan_officer'
    )

    buckets = {
        'current':   {'label': 'Current',          'days_min': None, 'days_max': 0,   'color': 'green',  'loans': []},
        '1_7':       {'label': '1–7 days overdue',  'days_min': 1,    'days_max': 7,   'color': 'yellow', 'loans': []},
        '8_30':      {'label': '8–30 days overdue', 'days_min': 8,    'days_max': 30,  'color': 'orange', 'loans': []},
        '31_60':     {'label': '31–60 days overdue','days_min': 31,   'days_max': 60,  'color': 'red',    'loans': []},
        '60_plus':   {'label': '60+ days overdue',  'days_min': 61,   'days_max': None,'color': 'red',    'loans': []},
    }

    for loan in active_loans:
        oldest = PaymentSchedule.objects.filter(
            loan=loan, is_paid=False, due_date__lt=today
        ).order_by('due_date').first()

        days = (today - oldest.due_date).days if oldest else 0
        balance = loan.balance_remaining or 0

        entry = {
            'loan': loan,
            'days_overdue': days,
            'balance': balance,
        }

        if days == 0:
            buckets['current']['loans'].append(entry)
        elif days <= 7:
            buckets['1_7']['loans'].append(entry)
        elif days <= 30:
            buckets['8_30']['loans'].append(entry)
        elif days <= 60:
            buckets['31_60']['loans'].append(entry)
        else:
            buckets['60_plus']['loans'].append(entry)

    # Compute totals per bucket
    for key, bucket in buckets.items():
        bucket['count'] = len(bucket['loans'])
        bucket['total_balance'] = sum(e['balance'] for e in bucket['loans'])

    return render(request, 'dashboard/loan_aging.html', {'buckets': buckets})


@login_required
def officer_performance(request):
    """Officer performance report (admin only)."""
    if request.user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')

    from clients.models import OfficerAssignment
    from payments.models import PaymentSchedule

    today = date.today()
    officers = User.objects.filter(role='loan_officer', is_active=True).select_related(
        'officer_assignment'
    )

    rows = []
    for officer in officers:
        branch = ''
        try:
            branch = officer.officer_assignment.branch
        except Exception:
            pass

        groups_count = BorrowerGroup.objects.filter(
            assigned_officer=officer, is_active=True
        ).count()

        clients_count = User.objects.filter(
            Q(assigned_officer=officer) |
            Q(group_memberships__group__assigned_officer=officer, group_memberships__is_active=True),
            role='borrower',
        ).distinct().count()

        active_loans = Loan.objects.filter(
            Q(loan_officer=officer) |
            Q(borrower__group_memberships__group__assigned_officer=officer),
            status='active'
        ).distinct()
        active_loans_count = active_loans.count()

        total_disbursed = Loan.objects.filter(
            Q(loan_officer=officer) |
            Q(borrower__group_memberships__group__assigned_officer=officer),
            status__in=['active', 'completed']
        ).distinct().aggregate(total=Sum('principal_amount'))['total'] or 0

        completed_collections = PaymentCollection.objects.filter(
            Q(loan__loan_officer=officer) |
            Q(loan__borrower__group_memberships__group__assigned_officer=officer),
            status='completed'
        ).distinct()
        total_collected = completed_collections.aggregate(total=Sum('collected_amount'))['total'] or 0

        all_collections = PaymentCollection.objects.filter(
            Q(loan__loan_officer=officer) |
            Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        ).distinct()
        total_expected = all_collections.aggregate(total=Sum('expected_amount'))['total'] or 0
        collection_rate = round((total_collected / total_expected * 100), 1) if total_expected > 0 else 0

        default_count = active_loans.filter(
            payment_schedule__is_paid=False,
            payment_schedule__due_date__lt=today,
        ).distinct().count()

        last_collection = PaymentCollection.objects.filter(
            Q(loan__loan_officer=officer) |
            Q(loan__borrower__group_memberships__group__assigned_officer=officer),
            status='completed'
        ).order_by('-collection_date').first()
        last_activity = last_collection.collection_date if last_collection else None

        rows.append({
            'officer': officer,
            'branch': branch,
            'groups_count': groups_count,
            'clients_count': clients_count,
            'active_loans_count': active_loans_count,
            'total_disbursed': total_disbursed,
            'total_collected': total_collected,
            'collection_rate': collection_rate,
            'default_count': default_count,
            'last_activity': last_activity,
        })

    # Sort by collection rate ascending (worst performers first)
    rows.sort(key=lambda r: r['collection_rate'])

    return render(request, 'dashboard/officer_performance.html', {'rows': rows})


@login_required
def admin_manager_view(request):
    """Admin selects a branch to view its manager dashboard."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')

    branch_id = request.GET.get('branch')
    if branch_id:
        try:
            branch = Branch.objects.get(pk=branch_id)
            manager = branch.manager
            if not manager:
                messages.warning(request, f'{branch.name} has no manager assigned.')
                return redirect('dashboard:admin_manager_view')
            # Temporarily impersonate: pass branch context to manager dashboard template
            return _render_manager_dashboard_for_branch(request, branch, manager)
        except Branch.DoesNotExist:
            messages.error(request, 'Branch not found.')

    branches = Branch.objects.filter(is_active=True).select_related('manager').order_by('name')
    return render(request, 'dashboard/admin_manager_view.html', {'branches': branches})


def _render_manager_dashboard_for_branch(request, branch, manager):
    """Render manager dashboard context for a specific branch (admin view)."""
    from django.db.models import Q, Sum
    from datetime import date

    today = date.today()
    officers = User.objects.filter(role='loan_officer', officer_assignment__branch=branch.name)
    groups = BorrowerGroup.objects.filter(
        Q(branch=branch.name) | Q(assigned_officer__officer_assignment__branch=branch.name)
    ).distinct()
    clients_count = User.objects.filter(
        Q(group_memberships__group__branch=branch.name) |
        Q(assigned_officer__officer_assignment__branch=branch.name),
        role='borrower',
    ).distinct().count()

    branch_officers = User.objects.filter(
        role='loan_officer', officer_assignment__branch=branch.name
    ).values_list('id', flat=True)

    loans = Loan.objects.filter(
        Q(loan_officer_id__in=branch_officers) |
        Q(borrower__group_memberships__group__branch=branch.name)
    ).distinct()

    from loans.models import SecurityDeposit
    pending_security = SecurityDeposit.objects.filter(
        is_verified=False, paid_amount__gt=0,
        loan__loan_officer__officer_assignment__branch=branch.name
    ).count()

    context = {
        'branch': branch,
        'viewing_as_admin': True,
        'manager': manager,
        'today': today,
        'officers_count': officers.count(),
        'groups_count': groups.count(),
        'clients_count': clients_count,
        'today_expected': 0,
        'today_collected': 0,
        'collection_rate': 0,
        'pending_security': pending_security,
        'pending_topups': 0,
        'pending_returns': 0,
        'officer_stats': [],
        'total_disbursed': loans.filter(status__in=['active', 'completed']).aggregate(t=Sum('principal_amount'))['t'] or 0,
        'branch_loans_active': loans.filter(status='active').count(),
        'branch_loans_completed': loans.filter(status='completed').count(),
        'branch_loans_pending': loans.filter(status='approved').count(),
        'branch_loans_total': loans.count(),
        'vault_balance': _get_vault_balance(branch),
        'pending_payments_count': 0,
        'pending_upfront_verifications': Loan.objects.filter(
            id__in=loans.filter(status='approved', upfront_payment_paid__gt=0, upfront_payment_verified=False).values_list('id', flat=True)
        ).select_related('borrower', 'loan_officer'),
        'ready_to_disburse': Loan.objects.filter(
            id__in=loans.filter(status='approved', upfront_payment_verified=True).values_list('id', flat=True)
        ).select_related('borrower', 'loan_officer'),
        'recent_applications': [],
        'pending_applications_count': 0,
        'pending_document_verifications': 0,
        'verified_document_clients': 0,
        'total_document_clients': 0,
        'verification_rate': 0,
        'total_expenses': 0,
        'total_transfers': 0,
        'total_deposits': 0,
        'total_funds': 0,
        'pending_loan_approvals': 0,
        'ready_for_disbursement': 0,
    }
    return render(request, 'dashboard/manager_enhanced.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# Admin Tracking Views
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def pending_officer_approvals(request):
    """Officers who registered but haven't been approved yet."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')
    pending = User.objects.filter(role='loan_officer', is_approved=False).order_by('date_joined')
    return render(request, 'dashboard/pending_officer_approvals.html', {'officers': pending})


@login_required
def loans_approaching_maturity(request):
    """Active loans due to complete in the next 30 days."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')
    from datetime import timedelta
    today = date.today()
    in_30 = today + timedelta(days=30)
    loans = Loan.objects.filter(
        status='active',
        maturity_date__gte=today,
        maturity_date__lte=in_30,
    ).select_related('borrower', 'loan_officer').order_by('maturity_date')
    return render(request, 'dashboard/loans_approaching_maturity.html', {
        'loans': loans,
        'today': today,
        'in_30': in_30,
    })


@login_required
def collection_trend(request):
    """Enhanced weekly collection trend with analytics and filtering."""
    if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')
    
    from datetime import timedelta
    from django.db.models import Sum, Q
    from clients.models import Branch, BorrowerGroup
    from accounts.models import User
    
    today = date.today()
    
    # Get filters
    branch_filter = request.GET.get('branch', '')
    officer_filter = request.GET.get('officer', '')
    group_filter = request.GET.get('group', '')
    weeks_count = int(request.GET.get('weeks', 8))
    
    # Build base queryset
    collections_qs = PaymentCollection.objects.all()
    
    if branch_filter:
        collections_qs = collections_qs.filter(
            loan__loan_officer__officer_assignment__branch=branch_filter
        )
    
    if officer_filter:
        collections_qs = collections_qs.filter(loan__loan_officer_id=officer_filter)
    
    if group_filter:
        collections_qs = collections_qs.filter(
            loan__borrower__group_memberships__group_id=group_filter,
            loan__borrower__group_memberships__is_active=True
        )
    
    # Calculate weekly trends
    weeks = []
    for i in range(weeks_count - 1, -1, -1):
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        
        week_collections = collections_qs.filter(
            collection_date__gte=week_start,
            collection_date__lte=week_end
        )
        
        expected = week_collections.aggregate(t=Sum('expected_amount'))['t'] or 0
        collected = week_collections.filter(
            status='completed'
        ).aggregate(t=Sum('collected_amount'))['t'] or 0
        
        # Calculate rate and performance
        if expected > 0:
            rate = round((collected / expected * 100), 1)
            has_data = True
            
            # Performance classification
            if rate <= 40:
                performance = 'critical'
                performance_label = 'Critical'
                performance_color = 'red'
            elif rate <= 80:
                performance = 'average'
                performance_label = 'Average'
                performance_color = 'yellow'
            else:
                performance = 'good'
                performance_label = 'Good'
                performance_color = 'green'
        else:
            rate = 0
            has_data = False
            performance = 'no-data'
            performance_label = 'No Data'
            performance_color = 'gray'
        
        weeks.append({
            'label': f"W{weeks_count - i}",
            'date_range': f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b')}",
            'week_start': week_start,
            'week_end': week_end,
            'expected': expected,
            'collected': collected,
            'rate': rate,
            'has_data': has_data,
            'performance': performance,
            'performance_label': performance_label,
            'performance_color': performance_color,
        })
    
    # Calculate week-over-week changes
    for i in range(1, len(weeks)):
        prev_rate = weeks[i-1]['rate']
        curr_rate = weeks[i]['rate']
        change = curr_rate - prev_rate
        weeks[i]['rate_change'] = change
        weeks[i]['rate_change_direction'] = 'up' if change > 0 else 'down' if change < 0 else 'same'
    
    # Calculate summary statistics
    total_expected = sum(w['expected'] for w in weeks)
    total_collected = sum(w['collected'] for w in weeks)
    overall_rate = round((total_collected / total_expected * 100), 1) if total_expected > 0 else 0
    
    # Get filter options
    branches = Branch.objects.filter(is_active=True).order_by('name')
    officers = User.objects.filter(role='loan_officer', is_active=True).order_by('first_name', 'last_name')
    groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')
    
    # Prepare chart data
    chart_labels = [w['label'] for w in weeks]
    chart_expected = [float(w['expected']) for w in weeks]
    chart_collected = [float(w['collected']) for w in weeks]
    chart_rates = [w['rate'] for w in weeks]
    
    context = {
        'weeks': weeks,
        'total_expected': total_expected,
        'total_collected': total_collected,
        'overall_rate': overall_rate,
        'branches': branches,
        'officers': officers,
        'groups': groups,
        'filters': {
            'branch': branch_filter,
            'officer': officer_filter,
            'group': group_filter,
            'weeks': weeks_count,
        },
        'chart_labels': chart_labels,
        'chart_expected': chart_expected,
        'chart_collected': chart_collected,
        'chart_rates': chart_rates,
    }
    
    return render(request, 'dashboard/collection_trend.html', context)


@login_required
def chronic_defaulters(request):
    """Clients who have never paid or consistently miss payments."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')
    from payments.models import PaymentSchedule
    from clients.models import GroupMembership
    from django.db.models import Q
    
    # Get search parameter
    search = request.GET.get('search', '').strip()
    
    today = date.today()
    # Borrowers with active loans where ALL overdue installments are unpaid
    active_loans = Loan.objects.filter(status='active').select_related('borrower', 'loan_officer')
    
    defaulters = []
    for loan in active_loans:
        overdue = PaymentSchedule.objects.filter(
            loan=loan, is_paid=False, due_date__lt=today
        ).count()
        paid = PaymentSchedule.objects.filter(loan=loan, is_paid=True).count()
        if overdue > 0:
            # Get borrower's group
            membership = GroupMembership.objects.filter(
                borrower=loan.borrower,
                is_active=True
            ).select_related('group').first()
            
            group_name = membership.group.name if membership else 'No Group'
            
            # Apply search filter
            if search:
                if not (search.lower() in group_name.lower() or
                        search.lower() in loan.borrower.get_full_name().lower() or
                        search.lower() in loan.application_number.lower()):
                    continue
            
            defaulters.append({
                'loan': loan,
                'overdue_count': overdue,
                'paid_count': paid,
                'never_paid': paid == 0,
                'balance': loan.balance_remaining or 0,
                'group': group_name,
            })
    
    defaulters.sort(key=lambda x: (-x['overdue_count'], x['never_paid']))
    return render(request, 'dashboard/chronic_defaulters.html', {
        'defaulters': defaulters,
        'search': search,
    })


@login_required
def manager_processing_fees(request):
    """Branch-scoped processing fees report for managers."""
    if request.user.role not in ['manager', 'admin'] and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')
    from loans.models import LoanApplication
    from django.db.models import Sum, Q
    from datetime import date
    from clients.models import BorrowerGroup

    try:
        branch = request.user.managed_branch
        if not branch:
            branch = None
    except Exception:
        branch = None

    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    officer_filter = request.GET.get('officer', '')
    group_filter = request.GET.get('group', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if request.user.role == 'admin' or request.user.is_superuser:
        apps = LoanApplication.objects.filter(
            processing_fee__isnull=False, processing_fee__gt=0
        )
    elif branch:
        apps = LoanApplication.objects.filter(
            loan_officer__officer_assignment__branch__iexact=branch.name,
            processing_fee__isnull=False,
            processing_fee__gt=0,
        )
    else:
        apps = LoanApplication.objects.none()

    apps = apps.select_related('borrower', 'loan_officer', 'processing_fee_verified_by', 'group')

    # Apply filters
    if search_query:
        apps = apps.filter(
            Q(application_number__icontains=search_query) |
            Q(borrower__first_name__icontains=search_query) |
            Q(borrower__last_name__icontains=search_query) |
            Q(borrower__email__icontains=search_query)
        )
    
    if officer_filter:
        apps = apps.filter(loan_officer_id=officer_filter)
    
    if group_filter:
        apps = apps.filter(group_id=group_filter)
    
    if date_from:
        apps = apps.filter(created_at__date__gte=date_from)
    
    if date_to:
        apps = apps.filter(created_at__date__lte=date_to)

    # Get officers for filter dropdown
    from accounts.models import User as _User
    if branch:
        officers = _User.objects.filter(
            role='loan_officer',
            officer_assignment__branch__iexact=branch.name,
            is_active=True
        ).order_by('first_name', 'last_name')
    else:
        officers = _User.objects.filter(
            role='loan_officer',
            is_active=True
        ).order_by('first_name', 'last_name')

    # Get groups for filter dropdown
    if officer_filter:
        groups = BorrowerGroup.objects.filter(
            assigned_officer_id=officer_filter,
            is_active=True
        ).order_by('name')
    elif branch:
        groups = BorrowerGroup.objects.filter(
            assigned_officer__officer_assignment__branch__iexact=branch.name,
            is_active=True
        ).order_by('name')
    else:
        groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')

    total_fees = apps.aggregate(t=Sum('processing_fee'))['t'] or 0
    verified_fees = apps.filter(processing_fee_verified=True).aggregate(t=Sum('processing_fee'))['t'] or 0
    pending_fees = apps.filter(processing_fee_verified=False).aggregate(t=Sum('processing_fee'))['t'] or 0

    today = date.today()
    month_start = today.replace(day=1)
    this_month = apps.filter(
        processing_fee_verified=True,
        processing_fee_verified_at__date__gte=month_start,
    ).aggregate(t=Sum('processing_fee'))['t'] or 0

    officer_fees = []
    officers_with_apps = _User.objects.filter(
        submitted_loan_applications__in=apps
    ).distinct()
    for officer in officers_with_apps:
        oa = apps.filter(loan_officer=officer)
        officer_fees.append({
            'officer': officer,
            'count': oa.count(),
            'total': oa.aggregate(t=Sum('processing_fee'))['t'] or 0,
            'verified': oa.filter(processing_fee_verified=True).aggregate(t=Sum('processing_fee'))['t'] or 0,
            'pending': oa.filter(processing_fee_verified=False).aggregate(t=Sum('processing_fee'))['t'] or 0,
        })
    officer_fees.sort(key=lambda x: -x['total'])

    return render(request, 'dashboard/manager_processing_fees.html', {
        'branch': branch,
        'apps': apps.order_by('-created_at'),
        'total_fees': total_fees,
        'verified_fees': verified_fees,
        'pending_fees': pending_fees,
        'this_month': this_month,
        'officer_fees': officer_fees,
        'officers': officers,
        'groups': groups,
        'filters': {
            'search': search_query,
            'officer': officer_filter,
            'group': group_filter,
            'date_from': date_from,
            'date_to': date_to,
        },
    })


@login_required
def processing_fees_summary(request):
    """Processing fees collected per branch and officer."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')
    from loans.models import LoanApplication
    from clients.models import Branch, BorrowerGroup
    from django.db.models import Sum, Count, Q
    
    # Get filter parameters
    branch_filter = request.GET.get('branch', '')
    officer_filter = request.GET.get('officer', '')
    group_filter = request.GET.get('group', '')
    status_filter = request.GET.get('status', '')
    
    apps = LoanApplication.objects.filter(
        processing_fee__isnull=False, processing_fee__gt=0
    ).select_related('borrower', 'loan_officer')
    
    # Apply filters
    if branch_filter:
        apps = apps.filter(
            Q(loan_officer__officer_assignment__branch__iexact=branch_filter) |
            Q(borrower__group_memberships__group__branch__iexact=branch_filter)
        ).distinct()
    
    if officer_filter:
        apps = apps.filter(loan_officer_id=officer_filter)
    
    if group_filter:
        apps = apps.filter(borrower__group_memberships__group_id=group_filter).distinct()
    
    if status_filter == 'verified':
        apps = apps.filter(processing_fee_verified=True)
    elif status_filter == 'pending':
        apps = apps.filter(processing_fee_verified=False)

    total_fees = apps.aggregate(t=Sum('processing_fee'))['t'] or 0
    verified_fees = apps.filter(processing_fee_verified=True).aggregate(t=Sum('processing_fee'))['t'] or 0
    pending_fees = apps.filter(processing_fee_verified=False).aggregate(t=Sum('processing_fee'))['t'] or 0

    # Per officer
    officer_fees = []
    officers_with_fees = User.objects.filter(
        role='loan_officer',
        submitted_loan_applications__processing_fee__gt=0
    ).distinct()
    
    if branch_filter:
        officers_with_fees = officers_with_fees.filter(officer_assignment__branch__iexact=branch_filter)
    
    for officer in officers_with_fees:
        officer_apps = apps.filter(loan_officer=officer)
        if officer_apps.exists():
            officer_fees.append({
                'officer': officer,
                'count': officer_apps.count(),
                'total': officer_apps.aggregate(t=Sum('processing_fee'))['t'] or 0,
                'verified': officer_apps.filter(processing_fee_verified=True).aggregate(t=Sum('processing_fee'))['t'] or 0,
            })
    officer_fees.sort(key=lambda x: -x['total'])
    
    # Get filter options
    branches = Branch.objects.filter(is_active=True).order_by('name')
    all_officers = User.objects.filter(role='loan_officer', is_active=True).order_by('first_name')
    groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')

    return render(request, 'dashboard/processing_fees_summary.html', {
        'apps': apps.order_by('-created_at')[:100],
        'total_fees': total_fees,
        'verified_fees': verified_fees,
        'pending_fees': pending_fees,
        'officer_fees': officer_fees,
        'branches': branches,
        'all_officers': all_officers,
        'groups': groups,
        'branch_filter': branch_filter,
        'officer_filter': officer_filter,
        'group_filter': group_filter,
        'status_filter': status_filter,
    })


@login_required
def borrower_profile_completeness(request):
    """Borrowers missing key profile fields."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')
    from django.db.models import Q
    borrowers = User.objects.filter(role='borrower', is_active=True)
    incomplete = []
    for b in borrowers:
        missing = []
        if not b.phone_number: missing.append('Phone')
        if not b.national_id: missing.append('NRC')
        if not b.date_of_birth: missing.append('Date of Birth')
        if not b.address and not b.residential_address: missing.append('Address')
        if not b.guarantor1_name: missing.append('Guarantor 1')
        if missing:
            incomplete.append({'borrower': b, 'missing': missing, 'count': len(missing)})
    incomplete.sort(key=lambda x: -x['count'])
    return render(request, 'dashboard/borrower_profile_completeness.html', {
        'incomplete': incomplete,
        'total_borrowers': borrowers.count(),
        'incomplete_count': len(incomplete),
    })


@login_required
def officer_activity(request):
    """Officer last activity — last payment, disbursement, registration."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return render(request, 'dashboard/access_denied.html')
    officers = User.objects.filter(role='loan_officer', is_active=True).order_by('first_name')
    rows = []
    for officer in officers:
        last_payment = Payment.objects.filter(processed_by=officer).order_by('-created_at').first()
        last_loan = Loan.objects.filter(loan_officer=officer).order_by('-created_at').first()
        last_borrower = User.objects.filter(assigned_officer=officer, role='borrower').order_by('-date_joined').first()
        branch = ''
        try:
            branch = officer.officer_assignment.branch
        except Exception:
            pass
        rows.append({
            'officer': officer,
            'branch': branch,
            'last_payment_date': last_payment.created_at if last_payment else None,
            'last_loan_date': last_loan.created_at if last_loan else None,
            'last_borrower_date': last_borrower.date_joined if last_borrower else None,
            'last_login': officer.last_login,
        })
    return render(request, 'dashboard/officer_activity.html', {'rows': rows})


@login_required
def officer_processing_fees(request):
    """View for loan officers to review verified processing fees with search filters."""
    if request.user.role != 'loan_officer':
        messages.error(request, "Access denied. This page is for loan officers only.")
        return redirect('dashboard:dashboard')
    
    from loans.models import LoanApplication
    from django.core.paginator import Paginator
    
    officer = request.user
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    group_filter = request.GET.get('group', '')
    
    # Base queryset - all applications by this officer with processing fees
    applications = LoanApplication.objects.filter(
        loan_officer=officer,
        processing_fee__gt=0
    ).select_related('borrower', 'group', 'processing_fee_verified_by').order_by('-created_at')
    
    # Apply filters
    if search_query:
        applications = applications.filter(
            Q(application_number__icontains=search_query) |
            Q(borrower__first_name__icontains=search_query) |
            Q(borrower__last_name__icontains=search_query) |
            Q(borrower__email__icontains=search_query)
        )
    
    if status_filter == 'verified':
        applications = applications.filter(processing_fee_verified=True)
    elif status_filter == 'pending':
        applications = applications.filter(processing_fee_verified=False)
    
    if group_filter:
        applications = applications.filter(group_id=group_filter)
    
    # Get officer's groups for filter dropdown
    officer_groups = BorrowerGroup.objects.filter(
        assigned_officer=officer
    ).order_by('name')
    
    # Pagination
    paginator = Paginator(applications, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary counts
    total_count = applications.count()
    verified_count = applications.filter(processing_fee_verified=True).count()
    pending_count = applications.filter(processing_fee_verified=False).count()
    total_fees = applications.aggregate(t=Sum('processing_fee'))['t'] or 0
    verified_fees = applications.filter(processing_fee_verified=True).aggregate(t=Sum('processing_fee'))['t'] or 0
    
    context = {
        'page_obj': page_obj,
        'officer_groups': officer_groups,
        'total_count': total_count,
        'verified_count': verified_count,
        'pending_count': pending_count,
        'total_fees': total_fees,
        'verified_fees': verified_fees,
        # Preserve filters
        'search_query': search_query,
        'status_filter': status_filter,
        'group_filter': group_filter,
    }
    
    return render(request, 'dashboard/officer_processing_fees.html', context)


@login_required
def manager_collections_hierarchical(request):
    """Hierarchical collections view for managers: Officers > Groups > Clients"""
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, "Access denied.")
        return redirect('dashboard:dashboard')
    
    from collections import defaultdict
    from django.db.models import Sum, Count, Q
    from datetime import date
    
    today = date.today()
    user = request.user
    
    # Get level and filters from URL
    level = request.GET.get('level', 'officer')  # officer, group, or client
    selected_officer = request.GET.get('officer_id', '')
    selected_group = request.GET.get('group_id', '')
    
    # Determine branch scope
    if user.role == 'manager':
        try:
            branch = user.managed_branch
            if not branch:
                messages.error(request, "No branch assigned.")
                return redirect('dashboard:dashboard')
        except Exception:
            messages.error(request, "No branch assigned.")
            return redirect('dashboard:dashboard')
        
        # Get officers in this branch
        officers = User.objects.filter(
            role='loan_officer',
            officer_assignment__branch__iexact=branch.name,
            is_active=True
        ).order_by('first_name', 'last_name')
    else:  # admin
        officers = User.objects.filter(
            role='loan_officer',
            is_active=True
        ).order_by('first_name', 'last_name')
        branch = None
    
    context = {
        'level': level,
        'selected_officer': selected_officer,
        'selected_group': selected_group,
        'branch': branch,
    }
    
    # LEVEL 1: Officer View
    if level == 'officer':
        officer_data = []
        for officer in officers:
            # Get collections for this officer
            collections = PaymentCollection.objects.filter(
                loan__loan_officer=officer
            )
            
            # Get today's collections
            today_collections = collections.filter(collection_date=today)
            today_expected = today_collections.aggregate(t=Sum('expected_amount'))['t'] or 0
            today_collected = today_collections.filter(status='completed').aggregate(t=Sum('collected_amount'))['t'] or 0
            
            # Get groups count
            groups_count = BorrowerGroup.objects.filter(
                assigned_officer=officer,
                is_active=True
            ).count()
            
            # Get clients count
            clients_count = User.objects.filter(
                Q(group_memberships__group__assigned_officer=officer, group_memberships__is_active=True) |
                Q(assigned_officer=officer),
                role='borrower'
            ).distinct().count()
            
            officer_data.append({
                'officer': officer,
                'groups_count': groups_count,
                'clients_count': clients_count,
                'today_expected': today_expected,
                'today_collected': today_collected,
                'today_pending': today_expected - today_collected,
                'collection_rate': (today_collected / today_expected * 100) if today_expected > 0 else 0,
            })
        
        context['officers'] = officer_data
    
    # LEVEL 2: Group View (for selected officer)
    elif level == 'group' and selected_officer:
        try:
            officer = User.objects.get(pk=selected_officer, role='loan_officer')
            context['officer'] = officer
            
            groups = BorrowerGroup.objects.filter(
                assigned_officer=officer,
                is_active=True
            ).order_by('name')
            
            group_data = []
            for group in groups:
                # Get members
                members = group.members.filter(is_active=True)
                members_count = members.count()
                
                # Get collections for this group
                borrower_ids = [m.borrower_id for m in members]
                collections = PaymentCollection.objects.filter(
                    loan__borrower_id__in=borrower_ids
                )
                
                # Today's collections
                today_collections = collections.filter(collection_date=today)
                today_expected = today_collections.aggregate(t=Sum('expected_amount'))['t'] or 0
                today_collected = today_collections.filter(status='completed').aggregate(t=Sum('collected_amount'))['t'] or 0
                
                group_data.append({
                    'group': group,
                    'members_count': members_count,
                    'today_expected': today_expected,
                    'today_collected': today_collected,
                    'today_pending': today_expected - today_collected,
                    'collection_rate': (today_collected / today_expected * 100) if today_expected > 0 else 0,
                })
            
            context['groups'] = group_data
        except User.DoesNotExist:
            messages.error(request, "Officer not found.")
            return redirect('dashboard:manager_collections_hierarchical')
    
    # LEVEL 3: Client View (for selected group)
    elif level == 'client' and selected_group:
        try:
            group = BorrowerGroup.objects.get(pk=selected_group)
            context['group'] = group
            context['officer'] = group.assigned_officer
            
            # Get members
            members = group.members.filter(is_active=True).select_related('borrower')
            
            client_data = []
            for membership in members:
                client = membership.borrower
                
                # Get collections for this client
                collections = PaymentCollection.objects.filter(
                    loan__borrower=client
                )
                
                # Today's collections
                today_collections = collections.filter(collection_date=today)
                today_expected = today_collections.aggregate(t=Sum('expected_amount'))['t'] or 0
                today_collected = today_collections.filter(status='completed').aggregate(t=Sum('collected_amount'))['t'] or 0
                
                # Get active loans
                active_loans = Loan.objects.filter(
                    borrower=client,
                    status='active'
                ).count()
                
                # Get all collections with details
                all_collections = today_collections.select_related('loan').order_by('-collection_date')
                
                client_data.append({
                    'client': client,
                    'active_loans': active_loans,
                    'today_expected': today_expected,
                    'today_collected': today_collected,
                    'today_pending': today_expected - today_collected,
                    'collection_rate': (today_collected / today_expected * 100) if today_expected > 0 else 0,
                    'collections': all_collections,
                })
            
            context['clients'] = client_data
        except BorrowerGroup.DoesNotExist:
            messages.error(request, "Group not found.")
            return redirect('dashboard:manager_collections_hierarchical')
    
    return render(request, 'dashboard/manager_collections_hierarchical.html', context)


@login_required
def view_officer_dashboard(request, officer_id):
    """Allow managers to view a specific officer's dashboard."""
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, "Access denied.")
        return redirect('dashboard:dashboard')
    
    from datetime import date
    
    # Get the officer
    officer = get_object_or_404(User, pk=officer_id, role='loan_officer')
    
    # Access control for managers
    if request.user.role == 'manager':
        try:
            branch = request.user.managed_branch
            if officer.officer_assignment.branch != branch.name:
                messages.error(request, "You can only view officers from your branch.")
                return redirect('dashboard:manager_dashboard')
        except Exception:
            messages.error(request, "Access denied.")
            return redirect('dashboard:manager_dashboard')
    
    today = date.today()
    
    # Get officer's groups
    groups = BorrowerGroup.objects.filter(
        assigned_officer=officer,
        is_active=True
    ).order_by('-created_at')[:5]
    
    # Get officer's clients
    clients = User.objects.filter(
        Q(group_memberships__group__assigned_officer=officer, group_memberships__is_active=True) |
        Q(assigned_officer=officer),
        role='borrower'
    ).distinct()
    
    # Get active loans
    active_loans = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        status='active'
    ).distinct()
    
    # Today's collections
    today_collections = PaymentCollection.objects.filter(
        loan__loan_officer=officer,
        collection_date=today
    )
    today_expected = today_collections.aggregate(t=Sum('expected_amount'))['t'] or 0
    today_collected = today_collections.filter(status='completed').aggregate(t=Sum('collected_amount'))['t'] or 0
    
    # Overdue loans
    from payments.models import PaymentSchedule
    overdue_schedules = PaymentSchedule.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        loan__status='active',
        is_paid=False,
        due_date__lt=today
    ).select_related('loan__borrower', 'loan').order_by('due_date').distinct()
    
    overdue_clients = {}
    for sched in overdue_schedules:
        lid = sched.loan_id
        if lid not in overdue_clients:
            overdue_clients[lid] = {
                'loan': sched.loan,
                'days_overdue': (today - sched.due_date).days,
                'overdue_amount': sched.total_amount - sched.amount_paid,
            }
    overdue_loans_list = sorted(overdue_clients.values(), key=lambda x: -x['days_overdue'])[:10]
    
    # Outstanding balance
    outstanding_balance = active_loans.aggregate(t=Sum('balance_remaining'))['t'] or 0
    
    # Pending security deposits
    pending_security = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        status='approved',
        security_deposit__isnull=False,
        security_deposit__is_verified=False,
    ).select_related('borrower', 'security_deposit').distinct()
    
    # Ready to disburse
    ready_to_disburse = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        status='approved',
        upfront_payment_verified=True,
    ).select_related('borrower').distinct()
    
    # Default collections summary
    overdue_schedules_for_default = PaymentSchedule.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        loan__status='active',
        is_paid=False,
        due_date__lt=today
    ).select_related('loan').distinct()
    
    defaulted_loan_ids = overdue_schedules_for_default.values_list('loan_id', flat=True).distinct()
    default_loans = Loan.objects.filter(id__in=defaulted_loan_ids)
    
    from payments.models import DefaultCollection
    default_loans_count = default_loans.count()
    default_total_outstanding = default_loans.aggregate(t=Sum('balance_remaining'))['t'] or 0
    default_collected_this_month = DefaultCollection.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        collection_date__gte=today.replace(day=1),
    ).distinct().aggregate(t=Sum('amount_paid'))['t'] or 0
    
    # This month's performance
    month_start = today.replace(day=1)
    month_disbursed = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        disbursement_date__date__gte=month_start,
    ).distinct().count()
    
    month_collected = PaymentCollection.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        collection_date__gte=month_start,
        status='completed'
    ).distinct().aggregate(t=Sum('collected_amount'))['t'] or 0
    
    # Loans pending upfront payment (approved but no upfront paid yet)
    pending_upfront = Loan.objects.filter(
        Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer),
        status='approved',
        upfront_payment_paid=0,
    ).select_related('borrower').distinct()
    
    # Security management counts
    from loans.models import SecurityTransaction
    pending_sec_returns = SecurityTransaction.objects.filter(
        Q(security_deposit__loan__loan_officer=officer) | 
        Q(security_deposit__loan__borrower__group_memberships__group__assigned_officer=officer),
        transaction_type='return',
        is_approved=False
    ).distinct().count()
    
    pending_sec_adjustments = SecurityTransaction.objects.filter(
        Q(security_deposit__loan__loan_officer=officer) |
        Q(security_deposit__loan__borrower__group_memberships__group__assigned_officer=officer),
        transaction_type='adjustment',
        is_approved=False
    ).distinct().count()
    
    pending_sec_topups = SecurityTransaction.objects.filter(
        Q(security_deposit__loan__loan_officer=officer) |
        Q(security_deposit__loan__borrower__group_memberships__group__assigned_officer=officer),
        transaction_type='top_up',
        is_approved=False
    ).distinct().count()
    
    pending_sec_withdrawals = SecurityTransaction.objects.filter(
        Q(security_deposit__loan__loan_officer=officer) |
        Q(security_deposit__loan__borrower__group_memberships__group__assigned_officer=officer),
        transaction_type='withdrawal',
        is_approved=False
    ).distinct().count()
    
    # Clients expected to pay today
    clients_expected_today = PaymentCollection.objects.filter(
        Q(loan__loan_officer=officer) | Q(loan__borrower__group_memberships__group__assigned_officer=officer),
        collection_date=today,
        status__in=['pending', 'partial']
    ).select_related('loan__borrower').distinct()[:10]
    
    context = {
        'officer': officer,
        'viewing_as_manager': True,
        'groups_count': groups.count(),
        'clients_count': clients.count(),
        'active_loans_count': active_loans.count(),
        'today_expected': today_expected,
        'today_collected': today_collected,
        'today_pending': today_expected - today_collected,
        'today_defaults': len(overdue_clients),
        'groups': groups,
        'pending_security': pending_security,
        'ready_to_disburse': ready_to_disburse,
        'pending_upfront': pending_upfront,
        'outstanding_balance': outstanding_balance,
        'overdue_clients_list': overdue_loans_list,
        'default_loans_count': default_loans_count,
        'default_total_outstanding': default_total_outstanding,
        'default_collected_this_month': default_collected_this_month,
        'month_disbursed': month_disbursed,
        'month_collected': month_collected,
        'pending_sec_returns': pending_sec_returns,
        'pending_sec_adjustments': pending_sec_adjustments,
        'pending_sec_topups': pending_sec_topups,
        'pending_sec_withdrawals': pending_sec_withdrawals,
        'clients_expected_today': clients_expected_today,
        'today': today,
    }
    
    return render(request, 'dashboard/view_officer_dashboard.html', context)
