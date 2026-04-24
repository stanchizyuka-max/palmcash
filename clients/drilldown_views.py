"""
Hierarchical drill-down views for clients
- Managers: Officers > Groups > Clients
- Loan Officers: Groups > Clients
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from accounts.models import User
from clients.models import BorrowerGroup, GroupMembership


def _annotate_groups(groups):
    from loans.models import Loan
    from payments.models import PaymentSchedule
    for group in groups:
        borrower_ids = list(
            group.members.filter(is_active=True).values_list('borrower_id', flat=True)
        )
        group.active_loans_count = Loan.objects.filter(
            borrower_id__in=borrower_ids,
            status__in=['active', 'disbursed']
        ).count()
        group.pending_payments_count = PaymentSchedule.objects.filter(
            loan__borrower_id__in=borrower_ids,
            is_paid=False
        ).count()
    return groups


@login_required
def clients_drilldown_root(request):
    user = request.user

    if user.role == 'admin':
        return redirect('accounts:manage_users')

    elif user.role == 'loan_officer':
        return clients_drilldown_groups(request, officer_id=user.id)

    elif user.role == 'manager':
        try:
            branch = user.managed_branch
            branch_name = branch.name
        except Exception:
            messages.error(request, 'No branch assigned to your account.')
            return redirect('dashboard:dashboard')

        officers = User.objects.filter(
            role='loan_officer',
            is_active=True,
            officer_assignment__branch=branch_name
        ).annotate(
            group_count=Count('managed_groups', filter=Q(
                managed_groups__is_active=True,
                managed_groups__branch__iexact=branch_name
            )),
            client_count=Count('managed_groups__members', filter=Q(
                managed_groups__is_active=True,
                managed_groups__branch__iexact=branch_name,
                managed_groups__members__is_active=True
            ), distinct=True)
        ).order_by('first_name', 'last_name')

        context = {
            'view_level': 'officers',
            'officers': officers,
            'branch': branch,
            'breadcrumbs': [{'label': branch.name, 'url': None}],
        }
        return render(request, 'clients/drilldown.html', context)

    messages.error(request, 'Access denied.')
    return redirect('dashboard:dashboard')


@login_required
def clients_drilldown_groups(request, officer_id):
    user = request.user
    officer = get_object_or_404(User, pk=officer_id, role='loan_officer')

    if user.role == 'loan_officer' and user.id != officer.id:
        messages.error(request, 'You can only view your own groups.')
        return redirect('dashboard:dashboard')

    if user.role == 'manager':
        try:
            branch_name = user.managed_branch.name
            if not hasattr(officer, 'officer_assignment') or officer.officer_assignment.branch != branch_name:
                messages.error(request, 'This officer is not in your branch.')
                return redirect('dashboard:dashboard')
        except Exception:
            messages.error(request, 'No branch assigned.')
            return redirect('dashboard:dashboard')

    groups = list(BorrowerGroup.objects.filter(
        assigned_officer=officer,
        is_active=True
    ).annotate(
        member_count_db=Count('members', filter=Q(members__is_active=True))
    ).order_by('name'))

    groups = _annotate_groups(groups)

    direct_clients = User.objects.filter(
        role='borrower',
        is_active=True,
        assigned_officer=officer
    ).exclude(
        group_memberships__group__assigned_officer=officer,
        group_memberships__is_active=True
    ).distinct()

    breadcrumbs = []
    if user.role == 'manager':
        breadcrumbs.append({'label': user.managed_branch.name, 'url': '/clients/drilldown/'})
        breadcrumbs.append({'label': officer.get_full_name(), 'url': None})
    else:
        breadcrumbs.append({'label': 'My Groups', 'url': None})

    context = {
        'view_level': 'groups',
        'officer': officer,
        'groups': groups,
        'direct_clients': direct_clients,
        'breadcrumbs': breadcrumbs,
        'is_own_view': user.id == officer.id,
    }
    return render(request, 'clients/drilldown.html', context)


@login_required
def clients_drilldown_clients(request, group_id):
    user = request.user
    group = get_object_or_404(BorrowerGroup, pk=group_id, is_active=True)

    if user.role == 'loan_officer' and group.assigned_officer != user:
        messages.error(request, 'You can only view your own groups.')
        return redirect('dashboard:dashboard')

    if user.role == 'manager':
        try:
            branch_name = user.managed_branch.name
            if group.branch.lower() != branch_name.lower():
                messages.error(request, 'This group is not in your branch.')
                return redirect('dashboard:dashboard')
        except Exception:
            messages.error(request, 'No branch assigned.')
            return redirect('dashboard:dashboard')

    from loans.models import Loan
    from payments.models import PaymentSchedule

    memberships = GroupMembership.objects.filter(
        group=group,
        is_active=True
    ).select_related('borrower').order_by('borrower__first_name', 'borrower__last_name')

    # Annotate each membership with loan stats
    for m in memberships:
        m.active_loans_count = Loan.objects.filter(
            borrower=m.borrower,
            status__in=['active', 'disbursed']
        ).count()
        m.pending_payments_count = PaymentSchedule.objects.filter(
            loan__borrower=m.borrower,
            is_paid=False
        ).count()

    breadcrumbs = []
    if user.role == 'manager':
        breadcrumbs.append({'label': user.managed_branch.name, 'url': '/clients/drilldown/'})
        if group.assigned_officer:
            breadcrumbs.append({
                'label': group.assigned_officer.get_full_name(),
                'url': f'/clients/drilldown/officer/{group.assigned_officer.id}/groups/'
            })
        breadcrumbs.append({'label': group.name, 'url': None})
    else:
        breadcrumbs.append({'label': 'My Groups', 'url': '/clients/drilldown/'})
        breadcrumbs.append({'label': group.name, 'url': None})

    context = {
        'view_level': 'clients',
        'group': group,
        'memberships': memberships,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'clients/drilldown.html', context)
