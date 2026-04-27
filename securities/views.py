from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from decimal import Decimal

from accounts.models import User
from clients.models import BorrowerGroup, GroupMembership
from loans.models import Loan, SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, SecurityTransaction


def _zero():
    return Decimal('0')


def _security_stats_for_loans(loans_qs, date_from=None, date_to=None):
    """
    Given a queryset of Loans, compute the 4 security columns + balance.
    Returns a dict with upfront, topups, adjustments, returned, balance.
    Optionally filter transactions by date range (date objects).
    """
    deposit_qs = SecurityDeposit.objects.filter(loan__in=loans_qs, is_verified=True)
    if date_from and date_to:
        deposit_qs = deposit_qs.filter(created_at__date__range=[date_from, date_to])
    upfront = deposit_qs.aggregate(total=Sum('paid_amount'))['total'] or _zero()

    topup_qs = SecurityTopUpRequest.objects.filter(loan__in=loans_qs, status='approved')
    if date_from and date_to:
        topup_qs = topup_qs.filter(requested_date__date__range=[date_from, date_to])
    topups = topup_qs.aggregate(total=Sum('requested_amount'))['total'] or _zero()

    # Adjustments - used to apply security toward loan completion (decreases balance)
    adj_qs = SecurityTransaction.objects.filter(
        loan__in=loans_qs, status='approved', transaction_type='adjustment',
    )
    if date_from and date_to:
        adj_qs = adj_qs.filter(created_at__date__range=[date_from, date_to])
    adjustments = adj_qs.aggregate(total=Sum('amount'))['total'] or _zero()

    ret_qs = SecurityTransaction.objects.filter(
        loan__in=loans_qs, status='approved', transaction_type='return',
    )
    if date_from and date_to:
        ret_qs = ret_qs.filter(created_at__date__range=[date_from, date_to])
    returned = ret_qs.aggregate(total=Sum('amount'))['total'] or _zero()

    cf_qs = SecurityTransaction.objects.filter(
        loan__in=loans_qs, status='approved', transaction_type='carry_forward',
    )
    if date_from and date_to:
        cf_qs = cf_qs.filter(created_at__date__range=[date_from, date_to])
    carry_forwards = cf_qs.aggregate(total=Sum('amount'))['total'] or _zero()

    # Withdrawals should decrease the balance
    wd_qs = SecurityTransaction.objects.filter(
        loan__in=loans_qs, status='approved', transaction_type='withdrawal',
    )
    if date_from and date_to:
        wd_qs = wd_qs.filter(created_at__date__range=[date_from, date_to])
    withdrawals = wd_qs.aggregate(total=Sum('amount'))['total'] or _zero()

    # Correct balance calculation:
    # INCREASES: upfront + topups + carry_forwards
    # DECREASES: adjustments + returned + withdrawals
    balance = (upfront + topups + carry_forwards) - (adjustments + returned + withdrawals)

    return {
        'upfront': upfront,
        'topups': topups,
        'adjustments': adjustments,
        'returned': returned,
        'balance': balance,
    }


def _client_security_stats(client):
    """Security stats for a single borrower (all their loans)."""
    loans = Loan.objects.filter(borrower=client)
    stats = _security_stats_for_loans(loans)
    stats['loan_count'] = loans.count()
    # Latest loan for display
    latest = loans.order_by('-application_date').first()
    stats['loan_id'] = latest.application_number if latest else '—'
    stats['loan_status'] = latest.get_status_display() if latest else '—'
    return stats


@login_required
def securities_summary(request):
    """
    Hierarchical securities view.
    Admin: starts at branch level (BRANCHES > OFFICERS > GROUPS > CLIENTS)
    Manager: starts at officer level (OFFICERS > GROUPS > CLIENTS) - only their branch
    Loan Officer: starts at group level (GROUPS > CLIENTS) - only themselves
    """
    user = request.user

    # Admin sees branch-level view
    if user.role == 'admin' or user.is_superuser:
        return securities_branches(request)
    
    # Manager sees officer-level view for their branch
    elif user.role == 'manager':
        return securities_officers(request)
    
    # Loan officer sees their own groups
    elif user.role == 'loan_officer':
        return officer_groups(request, user.pk)
    
    else:
        return render(request, 'dashboard/access_denied.html')


@login_required
def securities_branches(request):
    """
    Branch-level summary for admins.
    Shows all branches with their security totals.
    """
    user = request.user
    
    if user.role not in ['admin'] and not user.is_superuser:
        return render(request, 'dashboard/access_denied.html')
    
    from clients.models import Branch
    
    # Get filter parameters
    branch_filter = request.GET.get('branch', '')
    officer_filter = request.GET.get('officer', '')
    group_filter = request.GET.get('group', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Set default date range (current month if not specified)
    if not date_from or not date_to:
        from datetime import date
        today = date.today()
        date_from = date_from or today.replace(day=1).strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')
    
    # Parse dates
    try:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    except:
        from datetime import date
        today = date.today()
        date_from_obj = today.replace(day=1)
        date_to_obj = today
        date_from = date_from_obj.strftime('%Y-%m-%d')
        date_to = date_to_obj.strftime('%Y-%m-%d')
    
    # Get all branches for filter
    all_branches = Branch.objects.filter(is_active=True).order_by('name')
    
    # Apply branch filter
    branches = all_branches
    if branch_filter:
        branches = branches.filter(id=branch_filter)
    
    # Get all officers for filter dropdown
    all_officers = User.objects.filter(
        role='loan_officer',
        is_active=True
    ).select_related('officer_assignment').order_by('first_name', 'last_name')
    
    # Get all groups for filter dropdown
    all_groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')
    
    rows = []
    totals = {'officer_count': 0, 'group_count': 0, 'client_count': 0,
              'upfront': _zero(), 'topups': _zero(), 'adjustments': _zero(),
              'returned': _zero(), 'balance': _zero()}
    
    for branch in branches:
        # Get officers in this branch
        officers = User.objects.filter(
            role='loan_officer',
            officer_assignment__branch__iexact=branch.name,
            is_active=True
        ).distinct()
        
        # Apply officer filter
        if officer_filter:
            officers = officers.filter(id=officer_filter)
        
        officer_count = officers.count()
        
        # Get all loans for officers in this branch
        loans_query = Q(loan_officer__in=officers) | Q(borrower__group_memberships__group__assigned_officer__in=officers)
        
        # Apply group filter
        if group_filter:
            loans_query = loans_query & Q(borrower__group_memberships__group_id=group_filter)
        
        loans = Loan.objects.filter(loans_query).distinct()
        
        stats = _security_stats_for_loans(loans, date_from_obj, date_to_obj)
        
        # Get groups count (apply group filter)
        groups_query = BorrowerGroup.objects.filter(
            assigned_officer__in=officers,
            is_active=True
        )
        if group_filter:
            groups_query = groups_query.filter(id=group_filter)
        group_count = groups_query.count()
        
        # Get clients count (apply group filter)
        clients_query = Q(group_memberships__group__assigned_officer__in=officers, group_memberships__is_active=True) | Q(assigned_officer__in=officers)
        if group_filter:
            clients_query = clients_query & Q(group_memberships__group_id=group_filter)
        
        client_count = User.objects.filter(
            clients_query,
            role='borrower'
        ).distinct().count()
        
        rows.append({
            'branch': branch,
            'officer_count': officer_count,
            'group_count': group_count,
            'client_count': client_count,
            **stats,
        })
        
        totals['officer_count'] += officer_count
        totals['group_count'] += group_count
        totals['client_count'] += client_count
        for k in ('upfront', 'topups', 'adjustments', 'returned', 'balance'):
            totals[k] += stats[k]
    
    return render(request, 'securities/branch_summary.html', {
        'rows': rows,
        'totals': totals,
        'page_title': 'Securities — Branch Summary',
        'filters': {
            'branch': branch_filter,
            'officer': officer_filter,
            'group': group_filter,
            'date_from': date_from,
            'date_to': date_to,
        },
        'all_branches': all_branches,
        'all_officers': all_officers,
        'all_groups': all_groups,
    })


@login_required
def securities_officers(request, branch_id=None):
    """
    Officer-level summary.
    Admin: all officers in selected branch (or all if no branch selected).
    Manager: all officers in their branch.
    """
    user = request.user

    # Get filter parameters
    officer_filter = request.GET.get('officer', '')
    group_filter = request.GET.get('group', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Set default date range (current month if not specified)
    if not date_from or not date_to:
        from datetime import date
        today = date.today()
        date_from = date_from or today.replace(day=1).strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')
    
    # Parse dates
    try:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    except:
        from datetime import date
        today = date.today()
        date_from_obj = today.replace(day=1)
        date_to_obj = today
        date_from = date_from_obj.strftime('%Y-%m-%d')
        date_to = date_to_obj.strftime('%Y-%m-%d')

    if user.role == 'admin' or user.is_superuser:
        if branch_id:
            from clients.models import Branch
            branch = get_object_or_404(Branch, pk=branch_id)
            officers = User.objects.filter(
                role='loan_officer',
                officer_assignment__branch__iexact=branch.name,
                is_active=True
            ).distinct()
            page_title = f'Securities — {branch.name} Officers'
        else:
            officers = User.objects.filter(role='loan_officer', is_active=True).distinct()
            branch = None
            page_title = 'Securities — All Officers'
    
    elif user.role == 'manager':
        try:
            branch = user.managed_branch
        except Exception:
            branch = None

        if branch:
            officers = User.objects.filter(
                role='loan_officer',
                officer_assignment__branch__iexact=branch.name,
                is_active=True
            ).distinct()
            page_title = f'Securities — {branch.name} Officers'
        else:
            officers = User.objects.none()
            page_title = 'Securities — Officers'

    else:
        return render(request, 'dashboard/access_denied.html')

    # Apply officer filter
    if officer_filter:
        officers = officers.filter(id=officer_filter)
    
    # Get all officers for filter dropdown (based on user role)
    if user.role == 'admin' or user.is_superuser:
        all_officers = User.objects.filter(role='loan_officer', is_active=True).order_by('first_name', 'last_name')
    elif user.role == 'manager' and branch:
        all_officers = User.objects.filter(
            role='loan_officer',
            officer_assignment__branch__iexact=branch.name,
            is_active=True
        ).order_by('first_name', 'last_name')
    else:
        all_officers = User.objects.none()
    
    # Get all groups for filter dropdown
    all_groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')

    rows = []
    totals = {'group_count': 0, 'client_count': 0, 'upfront': _zero(), 'topups': _zero(),
              'adjustments': _zero(), 'returned': _zero(), 'balance': _zero()}

    for officer in officers:
        # Base loans query
        loans_query = Q(loan_officer=officer) | Q(borrower__group_memberships__group__assigned_officer=officer)
        
        # Apply group filter
        if group_filter:
            loans_query = loans_query & Q(borrower__group_memberships__group_id=group_filter)
        
        loans = Loan.objects.filter(loans_query).distinct()
        
        stats = _security_stats_for_loans(loans, date_from_obj, date_to_obj)
        
        # Get groups count (apply group filter)
        groups_query = BorrowerGroup.objects.filter(
            assigned_officer=officer,
            is_active=True
        )
        if group_filter:
            groups_query = groups_query.filter(id=group_filter)
        group_count = groups_query.count()
        
        # Get clients count (apply group filter)
        clients_query = Q(group_memberships__group__assigned_officer=officer, group_memberships__is_active=True) | Q(assigned_officer=officer)
        if group_filter:
            clients_query = clients_query & Q(group_memberships__group_id=group_filter)
        
        client_count = User.objects.filter(
            clients_query,
            role='borrower'
        ).distinct().count()
        
        rows.append({
            'officer': officer,
            'group_count': group_count,
            'client_count': client_count,
            **stats,
        })
        totals['group_count'] += group_count
        totals['client_count'] += client_count
        for k in ('upfront', 'topups', 'adjustments', 'returned', 'balance'):
            totals[k] += stats[k]

    return render(request, 'securities/officer_summary.html', {
        'rows': rows,
        'totals': totals,
        'page_title': page_title,
        'branch': branch,
        'filters': {
            'officer': officer_filter,
            'group': group_filter,
            'date_from': date_from,
            'date_to': date_to,
        },
        'all_officers': all_officers,
        'all_groups': all_groups,
    })


@login_required
def officer_groups(request, officer_id):
    """Groups managed by a specific officer."""
    user = request.user
    officer = get_object_or_404(User, pk=officer_id, role='loan_officer')

    # Access control
    if user.role == 'admin' or user.is_superuser:
        # Admins can view any officer
        pass
    elif user.role == 'loan_officer' and user.pk != officer.pk:
        return render(request, 'dashboard/access_denied.html')
    elif user.role == 'manager':
        try:
            branch = user.managed_branch
            if officer.officer_assignment.branch != branch.name:
                return render(request, 'dashboard/access_denied.html')
        except Exception:
            return render(request, 'dashboard/access_denied.html')

    # Get filter parameters
    group_filter = request.GET.get('group', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Set default date range (current month if not specified)
    if not date_from or not date_to:
        from datetime import date
        today = date.today()
        date_from = date_from or today.replace(day=1).strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')
    
    # Parse dates
    try:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    except:
        from datetime import date
        today = date.today()
        date_from_obj = today.replace(day=1)
        date_to_obj = today
        date_from = date_from_obj.strftime('%Y-%m-%d')
        date_to = date_to_obj.strftime('%Y-%m-%d')

    # Get groups for this officer
    groups = BorrowerGroup.objects.filter(assigned_officer=officer, is_active=True)
    
    # Apply group filter
    if group_filter:
        groups = groups.filter(id=group_filter)
    
    # Get all groups for filter dropdown
    all_groups = BorrowerGroup.objects.filter(assigned_officer=officer, is_active=True).order_by('name')

    rows = []
    totals = {'client_count': 0, 'upfront': _zero(), 'topups': _zero(),
              'adjustments': _zero(), 'returned': _zero(), 'balance': _zero()}

    for group in groups:
        borrower_ids = GroupMembership.objects.filter(
            group=group, is_active=True
        ).values_list('borrower_id', flat=True)
        
        loans = Loan.objects.filter(borrower_id__in=borrower_ids).distinct()
        
        stats = _security_stats_for_loans(loans, date_from_obj, date_to_obj)
        client_count = borrower_ids.count()
        
        rows.append({
            'group': group,
            'client_count': client_count,
            **stats,
        })
        totals['client_count'] += client_count
        for k in ('upfront', 'topups', 'adjustments', 'returned', 'balance'):
            totals[k] += stats[k]

    return render(request, 'securities/officer_groups.html', {
        'officer': officer,
        'rows': rows,
        'totals': totals,
        'page_title': f'Securities — {officer.full_name}\'s Groups',
        'filters': {
            'group': group_filter,
            'date_from': date_from,
            'date_to': date_to,
        },
        'all_groups': all_groups,
    })


@login_required
def group_clients(request, group_id):
    """Clients in a specific group."""
    user = request.user
    group = get_object_or_404(BorrowerGroup, pk=group_id)

    # Access control
    if user.role == 'admin' or user.is_superuser:
        # Admins can view any group
        pass
    elif user.role == 'loan_officer' and group.assigned_officer != user:
        return render(request, 'dashboard/access_denied.html')
    elif user.role == 'manager':
        try:
            branch = user.managed_branch
            if group.assigned_officer and group.assigned_officer.officer_assignment.branch != branch.name:
                return render(request, 'dashboard/access_denied.html')
        except Exception:
            pass

    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Set default date range (current month if not specified)
    if not date_from or not date_to:
        from datetime import date
        today = date.today()
        date_from = date_from or today.replace(day=1).strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')
    
    # Parse dates
    try:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    except:
        from datetime import date
        today = date.today()
        date_from_obj = today.replace(day=1)
        date_to_obj = today
        date_from = date_from_obj.strftime('%Y-%m-%d')
        date_to = date_to_obj.strftime('%Y-%m-%d')

    memberships = GroupMembership.objects.filter(
        group=group, is_active=True
    ).select_related('borrower')

    rows = []
    totals = {'upfront': _zero(), 'topups': _zero(),
              'adjustments': _zero(), 'returned': _zero(), 'balance': _zero()}

    for membership in memberships:
        client = membership.borrower
        
        # Get client's loans
        loans = Loan.objects.filter(borrower=client)
        
        # Calculate stats with date filter
        stats = _security_stats_for_loans(loans, date_from_obj, date_to_obj)
        stats['loan_count'] = loans.count()
        
        # Latest loan for display
        latest = loans.order_by('-application_date').first()
        stats['loan_id'] = latest.application_number if latest else '—'
        stats['loan_status'] = latest.get_status_display() if latest else '—'
        
        rows.append({
            'client': client,
            **stats,
        })
        for k in ('upfront', 'topups', 'adjustments', 'returned', 'balance'):
            totals[k] += stats[k]

    return render(request, 'securities/group_clients.html', {
        'group': group,
        'rows': rows,
        'totals': totals,
        'page_title': f'Securities — {group.name}',
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
        },
    })


@login_required
def client_detail(request, client_id):
    """Full transaction breakdown for a single client."""
    user = request.user
    client = get_object_or_404(User, pk=client_id, role='borrower')

    # Access control
    if user.role == 'admin' or user.is_superuser:
        # Admins can view any client
        pass
    elif user.role == 'loan_officer':
        is_mine = (
            client.assigned_officer == user or
            GroupMembership.objects.filter(
                borrower=client, group__assigned_officer=user, is_active=True
            ).exists()
        )
        if not is_mine:
            return render(request, 'dashboard/access_denied.html')

    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Set default date range (current month if not specified)
    if not date_from or not date_to:
        from datetime import date
        today = date.today()
        date_from = date_from or today.replace(day=1).strftime('%Y-%m-%d')
        date_to = date_to or today.strftime('%Y-%m-%d')
    
    # Parse dates
    try:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    except:
        from datetime import date
        today = date.today()
        date_from_obj = today.replace(day=1)
        date_to_obj = today
        date_from = date_from_obj.strftime('%Y-%m-%d')
        date_to = date_to_obj.strftime('%Y-%m-%d')

    loans = Loan.objects.filter(borrower=client).order_by('-application_date')

    loan_rows = []
    totals = {'upfront': _zero(), 'topups': _zero(),
              'adjustments': _zero(), 'returned': _zero(), 'balance': _zero()}

    for loan in loans:
        try:
            deposit = loan.security_deposit
            # Check if deposit is within date range
            if deposit.is_verified:
                dep_date = deposit.payment_date or deposit.created_at
                if dep_date and dep_date.date() >= date_from_obj and dep_date.date() <= date_to_obj:
                    upfront = deposit.paid_amount
                else:
                    upfront = _zero()
            else:
                upfront = _zero()
        except Exception:
            upfront = _zero()

        # Apply date filter to all security transactions
        topups = SecurityTopUpRequest.objects.filter(
            loan=loan, status='approved',
            requested_date__date__range=[date_from_obj, date_to_obj]
        ).aggregate(total=Sum('requested_amount'))['total'] or _zero()

        adjustments = SecurityTransaction.objects.filter(
            loan=loan, status='approved', transaction_type='adjustment',
            created_at__date__range=[date_from_obj, date_to_obj]
        ).aggregate(total=Sum('amount'))['total'] or _zero()

        returned = SecurityTransaction.objects.filter(
            loan=loan, status='approved', transaction_type='return',
            created_at__date__range=[date_from_obj, date_to_obj]
        ).aggregate(total=Sum('amount'))['total'] or _zero()

        carry_fwd = SecurityTransaction.objects.filter(
            loan=loan, status='approved', transaction_type='carry_forward',
            created_at__date__range=[date_from_obj, date_to_obj]
        ).aggregate(total=Sum('amount'))['total'] or _zero()

        withdrawals = SecurityTransaction.objects.filter(
            loan=loan, status='approved', transaction_type='withdrawal',
            created_at__date__range=[date_from_obj, date_to_obj]
        ).aggregate(total=Sum('amount'))['total'] or _zero()

        # Correct balance calculation:
        # INCREASES: upfront + topups + carry_forwards  
        # DECREASES: adjustments + returned + withdrawals
        balance = (upfront + topups + carry_fwd) - (adjustments + returned + withdrawals)

        # Transactions list for this loan (apply date filter)
        transactions = []

        try:
            dep = loan.security_deposit
            if dep.paid_amount > 0:
                # Check if deposit falls within date range
                dep_date = dep.payment_date or dep.created_at
                if not dep_date or (dep_date.date() >= date_from_obj and dep_date.date() <= date_to_obj):
                    transactions.append({
                        'date': dep_date,
                        'type': '10% Upfront',
                        'amount': dep.paid_amount,
                        'status': 'Verified' if dep.is_verified else 'Pending',
                        'notes': dep.notes,
                    })
        except Exception:
            pass

        for tu in SecurityTopUpRequest.objects.filter(loan=loan).order_by('-requested_date'):
            # Apply date filter
            if tu.requested_date and (tu.requested_date.date() >= date_from_obj and tu.requested_date.date() <= date_to_obj):
                transactions.append({
                    'date': tu.requested_date,
                    'type': 'Top-Up',
                    'amount': tu.requested_amount,
                    'status': tu.get_status_display(),
                    'notes': tu.reason,
                })

        for adj in SecurityTransaction.objects.filter(loan=loan).order_by('-created_at'):
            # Apply date filter
            if adj.created_at and (adj.created_at.date() >= date_from_obj and adj.created_at.date() <= date_to_obj):
                transactions.append({
                    'date': adj.created_at,
                    'type': adj.get_transaction_type_display(),
                    'amount': adj.amount,
                    'status': adj.get_status_display(),
                    'notes': adj.notes,
                })

        # SecurityReturnRequest is unused — returns go through SecurityTransaction

        transactions.sort(key=lambda x: x['date'] or '', reverse=True)

        loan_rows.append({
            'loan': loan,
            'upfront': upfront,
            'topups': topups,
            'adjustments': adjustments,
            'returned': returned,
            'balance': balance,
            'transactions': transactions,
        })

        totals['upfront'] += upfront
        totals['topups'] += topups
        totals['adjustments'] += adjustments
        totals['returned'] += returned
        totals['balance'] += balance

    return render(request, 'securities/client_detail.html', {
        'client': client,
        'loan_rows': loan_rows,
        'totals': totals,
        'page_title': f'Securities — {client.full_name}',
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
        },
    })
