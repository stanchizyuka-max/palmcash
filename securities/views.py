from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from decimal import Decimal

from accounts.models import User
from clients.models import BorrowerGroup, GroupMembership
from loans.models import Loan, SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, SecurityTransaction


def _zero():
    return Decimal('0')


def _security_stats_for_loans(loans_qs):
    """
    Given a queryset of Loans, compute the 4 security columns + balance.
    Returns a dict with upfront, topups, adjustments, returned, balance.
    """
    upfront = SecurityDeposit.objects.filter(
        loan__in=loans_qs, is_verified=True
    ).aggregate(total=Sum('paid_amount'))['total'] or _zero()

    topups = SecurityTopUpRequest.objects.filter(
        loan__in=loans_qs, status='approved'
    ).aggregate(total=Sum('requested_amount'))['total'] or _zero()

    # Positive adjustments (carry_forward / withdrawal) from SecurityTransaction
    adjustments = SecurityTransaction.objects.filter(
        loan__in=loans_qs,
        status='approved',
        transaction_type='adjustment',
        amount__gt=0,
    ).aggregate(total=Sum('amount'))['total'] or _zero()

    returned = SecurityTransaction.objects.filter(
        loan__in=loans_qs,
        status='approved',
        transaction_type='return',
    ).aggregate(total=Sum('amount'))['total'] or _zero()

    carry_forwards = SecurityTransaction.objects.filter(
        loan__in=loans_qs,
        status='approved',
        transaction_type='carry_forward',
    ).aggregate(total=Sum('amount'))['total'] or _zero()

    balance = (upfront + topups + adjustments + carry_forwards) - returned

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
    Officer-level summary.
    Manager: all officers in their branch.
    Loan Officer: only themselves.
    """
    user = request.user

    if user.role == 'manager':
        try:
            branch = user.managed_branch
        except Exception:
            branch = None

        if branch:
            officers = User.objects.filter(
                role='loan_officer',
                officer_assignment__branch=branch.name
            ).distinct()
        else:
            officers = User.objects.none()

    elif user.role == 'loan_officer':
        officers = User.objects.filter(pk=user.pk)
    else:
        return render(request, 'dashboard/access_denied.html')

    rows = []
    totals = {'count': 0, 'upfront': _zero(), 'topups': _zero(),
              'adjustments': _zero(), 'returned': _zero(), 'balance': _zero()}

    for officer in officers:
        loans = Loan.objects.filter(
            Q(loan_officer=officer) |
            Q(borrower__group_memberships__group__assigned_officer=officer)
        ).distinct()
        stats = _security_stats_for_loans(loans)
        count = loans.count()
        rows.append({
            'officer': officer,
            'count': count,
            **stats,
        })
        totals['count'] += count
        for k in ('upfront', 'topups', 'adjustments', 'returned', 'balance'):
            totals[k] += stats[k]

    return render(request, 'securities/officer_summary.html', {
        'rows': rows,
        'totals': totals,
        'page_title': 'Securities — Officer Summary',
    })


@login_required
def officer_groups(request, officer_id):
    """Groups managed by a specific officer."""
    user = request.user
    officer = get_object_or_404(User, pk=officer_id, role='loan_officer')

    # Access control
    if user.role == 'loan_officer' and user.pk != officer.pk:
        return render(request, 'dashboard/access_denied.html')
    if user.role == 'manager':
        try:
            branch = user.managed_branch
            if officer.officer_assignment.branch != branch.name:
                return render(request, 'dashboard/access_denied.html')
        except Exception:
            return render(request, 'dashboard/access_denied.html')

    groups = BorrowerGroup.objects.filter(assigned_officer=officer, is_active=True)

    rows = []
    totals = {'client_count': 0, 'upfront': _zero(), 'topups': _zero(),
              'adjustments': _zero(), 'returned': _zero(), 'balance': _zero()}

    for group in groups:
        borrower_ids = GroupMembership.objects.filter(
            group=group, is_active=True
        ).values_list('borrower_id', flat=True)
        loans = Loan.objects.filter(borrower_id__in=borrower_ids).distinct()
        stats = _security_stats_for_loans(loans)
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
    })


@login_required
def group_clients(request, group_id):
    """Clients in a specific group."""
    user = request.user
    group = get_object_or_404(BorrowerGroup, pk=group_id)

    # Access control
    if user.role == 'loan_officer' and group.assigned_officer != user:
        return render(request, 'dashboard/access_denied.html')
    if user.role == 'manager':
        try:
            branch = user.managed_branch
            if group.assigned_officer and group.assigned_officer.officer_assignment.branch != branch.name:
                return render(request, 'dashboard/access_denied.html')
        except Exception:
            pass

    memberships = GroupMembership.objects.filter(
        group=group, is_active=True
    ).select_related('borrower')

    rows = []
    totals = {'upfront': _zero(), 'topups': _zero(),
              'adjustments': _zero(), 'returned': _zero(), 'balance': _zero()}

    for membership in memberships:
        client = membership.borrower
        stats = _client_security_stats(client)
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
    })


@login_required
def client_detail(request, client_id):
    """Full transaction breakdown for a single client."""
    user = request.user
    client = get_object_or_404(User, pk=client_id, role='borrower')

    # Access control
    if user.role == 'loan_officer':
        is_mine = (
            client.assigned_officer == user or
            GroupMembership.objects.filter(
                borrower=client, group__assigned_officer=user, is_active=True
            ).exists()
        )
        if not is_mine:
            return render(request, 'dashboard/access_denied.html')

    loans = Loan.objects.filter(borrower=client).order_by('-application_date')

    loan_rows = []
    totals = {'upfront': _zero(), 'topups': _zero(),
              'adjustments': _zero(), 'returned': _zero(), 'balance': _zero()}

    for loan in loans:
        try:
            deposit = loan.security_deposit
            upfront = deposit.paid_amount if deposit.is_verified else _zero()
        except Exception:
            upfront = _zero()

        topups = SecurityTopUpRequest.objects.filter(
            loan=loan, status='approved'
        ).aggregate(total=Sum('requested_amount'))['total'] or _zero()

        adjustments = SecurityTransaction.objects.filter(
            loan=loan, status='approved', transaction_type='adjustment', amount__gt=0
        ).aggregate(total=Sum('amount'))['total'] or _zero()

        returned = SecurityTransaction.objects.filter(
            loan=loan, status='approved', transaction_type='return'
        ).aggregate(total=Sum('amount'))['total'] or _zero()

        carry_fwd = SecurityTransaction.objects.filter(
            loan=loan, status='approved', transaction_type='carry_forward'
        ).aggregate(total=Sum('amount'))['total'] or _zero()

        balance = (upfront + topups + adjustments + carry_fwd) - returned

        # Transactions list for this loan        transactions = []

        try:
            dep = loan.security_deposit
            if dep.paid_amount > 0:
                transactions.append({
                    'date': dep.payment_date or dep.created_at,
                    'type': '10% Upfront',
                    'amount': dep.paid_amount,
                    'status': 'Verified' if dep.is_verified else 'Pending',
                    'notes': dep.notes,
                })
        except Exception:
            pass

        for tu in SecurityTopUpRequest.objects.filter(loan=loan).order_by('-requested_date'):
            transactions.append({
                'date': tu.requested_date,
                'type': 'Top-Up',
                'amount': tu.requested_amount,
                'status': tu.get_status_display(),
                'notes': tu.reason,
            })

        for adj in SecurityTransaction.objects.filter(loan=loan).order_by('-created_at'):
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
    })
