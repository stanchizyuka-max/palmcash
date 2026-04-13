import csv
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Q
from django.core.paginator import Paginator

from loans.models import Loan, SecurityTransaction
from payments.models import Payment
from clients.models import OfficerAssignment, BorrowerGroup


def _get_branch(user):
    try:
        return user.officer_assignment.branch
    except Exception:
        try:
            return user.managed_branch.name
        except Exception:
            return None


def _loan_qs(user):
    if user.role == 'loan_officer':
        return Loan.objects.filter(loan_officer=user)
    elif user.role == 'manager':
        branch = _get_branch(user)
        if branch:
            return Loan.objects.filter(loan_officer__officer_assignment__branch=branch)
        return Loan.objects.none()
    return Loan.objects.all()


@login_required
def security_transactions_report(request):
    qs = SecurityTransaction.objects.select_related(
        'loan__borrower', 'loan__loan_officer__officer_assignment'
    )

    if request.user.role == 'loan_officer':
        qs = qs.filter(loan__loan_officer=request.user)
    elif request.user.role == 'manager':
        branch = _get_branch(request.user)
        if branch:
            qs = qs.filter(loan__loan_officer__officer_assignment__branch=branch)
        else:
            qs = qs.none()

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    tx_type = request.GET.get('type')
    branch_filter = request.GET.get('branch')
    group_filter = request.GET.get('group')
    client_filter = request.GET.get('client')

    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    if tx_type:
        qs = qs.filter(transaction_type=tx_type)
    if branch_filter and request.user.role == 'admin':
        qs = qs.filter(loan__loan_officer__officer_assignment__branch=branch_filter)
    if group_filter:
        qs = qs.filter(
            loan__borrower__group_memberships__group_id=group_filter,
            loan__borrower__group_memberships__is_active=True
        )
    if client_filter:
        qs = qs.filter(
            Q(loan__borrower__first_name__icontains=client_filter) |
            Q(loan__borrower__last_name__icontains=client_filter) |
            Q(loan__application_number__icontains=client_filter)
        )

    total = qs.aggregate(total=Sum('amount'))['total'] or 0

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="security_transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(['Client', 'Loan ID', 'Group', 'Type', 'Amount', 'Date', 'Branch', 'Status'])
        for tx in qs:
            branch = ''
            try:
                branch = tx.loan.loan_officer.officer_assignment.branch
            except Exception:
                pass
            
            # Get borrower's group
            group_name = ''
            membership = tx.loan.borrower.group_memberships.filter(is_active=True).first()
            if membership:
                group_name = membership.group.name
            
            writer.writerow([
                tx.loan.borrower.get_full_name(),
                tx.loan.application_number,
                group_name,
                tx.get_transaction_type_display(),
                tx.amount,
                tx.created_at.date(),
                branch,
                tx.get_status_display(),
            ])
        writer.writerow(['', '', '', 'TOTAL', total, '', '', ''])
        return response

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    from clients.models import Branch, BorrowerGroup
    branches = Branch.objects.filter(is_active=True) if request.user.role == 'admin' else []
    groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')

    return render(request, 'dashboard/reports_security.html', {
        'page_obj': page,
        'total': total,
        'tx_types': SecurityTransaction.TRANSACTION_TYPES,
        'branches': branches,
        'groups': groups,
        'filters': request.GET,
    })


@login_required
def disbursement_report(request):
    qs = _loan_qs(request.user).filter(
        status__in=['active', 'completed', 'disbursed'],
        disbursement_date__isnull=False
    ).select_related('borrower', 'loan_officer__officer_assignment')

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    branch_filter = request.GET.get('branch')
    group_filter = request.GET.get('group')

    if date_from:
        qs = qs.filter(disbursement_date__date__gte=date_from)
    if date_to:
        qs = qs.filter(disbursement_date__date__lte=date_to)
    if branch_filter and request.user.role == 'admin':
        qs = qs.filter(loan_officer__officer_assignment__branch=branch_filter)
    if group_filter:
        qs = qs.filter(
            borrower__group_memberships__group_id=group_filter,
            borrower__group_memberships__is_active=True
        )

    total = qs.aggregate(total=Sum('principal_amount'))['total'] or 0

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="disbursements.csv"'
        writer = csv.writer(response)
        writer.writerow(['Loan ID', 'Client', 'Group', 'Amount', 'Disbursement Date', 'Branch'])
        for loan in qs:
            branch = ''
            try:
                branch = loan.loan_officer.officer_assignment.branch
            except Exception:
                pass
            
            # Get borrower's group
            group_name = ''
            membership = loan.borrower.group_memberships.filter(is_active=True).first()
            if membership:
                group_name = membership.group.name
            
            writer.writerow([
                loan.application_number,
                loan.borrower.get_full_name(),
                group_name,
                loan.principal_amount,
                loan.disbursement_date.date() if loan.disbursement_date else '',
                branch,
            ])
        writer.writerow(['', 'TOTAL', '', total, '', ''])
        return response

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    from clients.models import Branch, BorrowerGroup
    branches = Branch.objects.filter(is_active=True) if request.user.role == 'admin' else []
    groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')

    return render(request, 'dashboard/reports_disbursements.html', {
        'page_obj': page,
        'total': total,
        'branches': branches,
        'groups': groups,
        'filters': request.GET,
    })


@login_required
def client_balances_report(request):
    """
    Hierarchical drill-down report: Branch → Officer → Group → Client
    Supports navigation through levels with breadcrumbs
    """
    from collections import defaultdict
    from accounts.models import User
    from clients.models import Branch, BorrowerGroup
    
    # Get drill-down level parameters
    view_level = request.GET.get('level', 'branch')  # branch, officer, group, client
    branch_id = request.GET.get('branch_id')
    officer_id = request.GET.get('officer_id')
    group_id = request.GET.get('group_id')
    
    # Get base loan queryset
    loan_qs = _loan_qs(request.user).filter(
        status='active'
    ).select_related('borrower', 'loan_officer', 'loan_officer__officer_assignment')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        loan_qs = loan_qs.filter(status=status_filter)
    
    # Build breadcrumb navigation
    breadcrumbs = [{'name': 'Branches', 'url': '?level=branch'}]
    selected_branch = None
    selected_officer = None
    selected_group = None
    
    # LEVEL 1: BRANCH VIEW
    if view_level == 'branch':
        branch_data = defaultdict(lambda: {
            'branch_name': None,
            'branch_id': None,
            'total_active_loans': 0,
            'total_outstanding': 0
        })
        
        for loan in loan_qs:
            if not loan.loan_officer:
                continue
            
            try:
                branch_name = loan.loan_officer.officer_assignment.branch
                branch_obj = Branch.objects.filter(name=branch_name).first()
                branch_key = branch_obj.id if branch_obj else 0
            except:
                branch_name = 'No Branch'
                branch_key = 0
            
            if branch_data[branch_key]['branch_name'] is None:
                branch_data[branch_key]['branch_name'] = branch_name
                branch_data[branch_key]['branch_id'] = branch_key
            
            branch_data[branch_key]['total_active_loans'] += 1
            branch_data[branch_key]['total_outstanding'] += loan.balance_remaining or 0
        
        data_list = sorted(branch_data.values(), key=lambda x: x['branch_name'])
        grand_total_loans = sum(b['total_active_loans'] for b in data_list)
        grand_total_outstanding = sum(b['total_outstanding'] for b in data_list)
        
        return render(request, 'dashboard/reports_balances_drilldown.html', {
            'view_level': 'branch',
            'data_list': data_list,
            'grand_total_loans': grand_total_loans,
            'grand_total_outstanding': grand_total_outstanding,
            'breadcrumbs': breadcrumbs,
        })
    
    # LEVEL 2: OFFICER VIEW (within a branch)
    elif view_level == 'officer' and branch_id:
        selected_branch = Branch.objects.filter(id=branch_id).first()
        if selected_branch:
            breadcrumbs.append({
                'name': selected_branch.name,
                'url': f'?level=officer&branch_id={branch_id}'
            })
            loan_qs = loan_qs.filter(loan_officer__officer_assignment__branch=selected_branch.name)
        
        officer_data = defaultdict(lambda: {
            'officer': None,
            'officer_id': None,
            'total_active_loans': 0,
            'total_outstanding': 0
        })
        
        for loan in loan_qs:
            if not loan.loan_officer:
                continue
            
            officer = loan.loan_officer
            officer_key = officer.id
            
            if officer_data[officer_key]['officer'] is None:
                officer_data[officer_key]['officer'] = officer
                officer_data[officer_key]['officer_id'] = officer.id
            
            officer_data[officer_key]['total_active_loans'] += 1
            officer_data[officer_key]['total_outstanding'] += loan.balance_remaining or 0
        
        data_list = sorted(officer_data.values(), key=lambda x: x['officer'].get_full_name() if x['officer'] else '')
        grand_total_loans = sum(o['total_active_loans'] for o in data_list)
        grand_total_outstanding = sum(o['total_outstanding'] for o in data_list)
        
        return render(request, 'dashboard/reports_balances_drilldown.html', {
            'view_level': 'officer',
            'data_list': data_list,
            'grand_total_loans': grand_total_loans,
            'grand_total_outstanding': grand_total_outstanding,
            'breadcrumbs': breadcrumbs,
            'branch_id': branch_id,
        })
    
    # LEVEL 3: GROUP VIEW (within an officer)
    elif view_level == 'group' and officer_id:
        selected_officer = User.objects.filter(id=officer_id).first()
        if selected_officer:
            # Rebuild breadcrumbs
            try:
                officer_branch = selected_officer.officer_assignment.branch
                officer_branch_obj = Branch.objects.filter(name=officer_branch).first()
                if officer_branch_obj:
                    breadcrumbs.append({
                        'name': officer_branch_obj.name,
                        'url': f'?level=officer&branch_id={officer_branch_obj.id}'
                    })
            except:
                pass
            
            breadcrumbs.append({
                'name': selected_officer.get_full_name(),
                'url': f'?level=group&officer_id={officer_id}'
            })
            loan_qs = loan_qs.filter(loan_officer=selected_officer)
        
        group_data = defaultdict(lambda: {
            'group': None,
            'group_id': None,
            'group_name': None,
            'total_active_loans': 0,
            'total_outstanding': 0
        })
        
        for loan in loan_qs:
            membership = loan.borrower.group_memberships.filter(is_active=True).first()
            group = membership.group if membership else None
            group_key = group.id if group else 0
            group_name = group.name if group else 'No Group'
            
            if group_data[group_key]['group'] is None:
                group_data[group_key]['group'] = group
                group_data[group_key]['group_id'] = group_key
                group_data[group_key]['group_name'] = group_name
            
            group_data[group_key]['total_active_loans'] += 1
            group_data[group_key]['total_outstanding'] += loan.balance_remaining or 0
        
        data_list = sorted(group_data.values(), key=lambda x: x['group_name'])
        grand_total_loans = sum(g['total_active_loans'] for g in data_list)
        grand_total_outstanding = sum(g['total_outstanding'] for g in data_list)
        
        return render(request, 'dashboard/reports_balances_drilldown.html', {
            'view_level': 'group',
            'data_list': data_list,
            'grand_total_loans': grand_total_loans,
            'grand_total_outstanding': grand_total_outstanding,
            'breadcrumbs': breadcrumbs,
            'officer_id': officer_id,
        })
    
    # LEVEL 4: CLIENT VIEW (within a group)
    elif view_level == 'client' and group_id:
        selected_group = BorrowerGroup.objects.filter(id=group_id).first()
        if selected_group:
            # Rebuild breadcrumbs
            if selected_group.assigned_officer:
                officer = selected_group.assigned_officer
                try:
                    officer_branch = officer.officer_assignment.branch
                    officer_branch_obj = Branch.objects.filter(name=officer_branch).first()
                    if officer_branch_obj:
                        breadcrumbs.append({
                            'name': officer_branch_obj.name,
                            'url': f'?level=officer&branch_id={officer_branch_obj.id}'
                        })
                except:
                    pass
                
                breadcrumbs.append({
                    'name': officer.get_full_name(),
                    'url': f'?level=group&officer_id={officer.id}'
                })
            
            breadcrumbs.append({
                'name': selected_group.name,
                'url': f'?level=client&group_id={group_id}'
            })
            
            loan_qs = loan_qs.filter(
                borrower__group_memberships__group=selected_group,
                borrower__group_memberships__is_active=True
            )
        
        client_data = defaultdict(lambda: {
            'client': None,
            'total_active_loans': 0,
            'total_outstanding': 0
        })
        
        for loan in loan_qs:
            client_key = loan.borrower.id
            
            if client_data[client_key]['client'] is None:
                client_data[client_key]['client'] = loan.borrower
            
            client_data[client_key]['total_active_loans'] += 1
            client_data[client_key]['total_outstanding'] += loan.balance_remaining or 0
        
        data_list = sorted(client_data.values(), key=lambda x: x['client'].get_full_name() if x['client'] else '')
        grand_total_loans = sum(c['total_active_loans'] for c in data_list)
        grand_total_outstanding = sum(c['total_outstanding'] for c in data_list)
        
        # Handle CSV export at client level
        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="client_balances.csv"'
            writer = csv.writer(response)
            writer.writerow(['Client Name', 'Active Loans', 'Outstanding Balance'])
            
            for client_data in data_list:
                writer.writerow([
                    client_data['client'].get_full_name(),
                    client_data['total_active_loans'],
                    client_data['total_outstanding'],
                ])
            
            writer.writerow(['GRAND TOTAL', grand_total_loans, grand_total_outstanding])
            return response
        
        return render(request, 'dashboard/reports_balances_drilldown.html', {
            'view_level': 'client',
            'data_list': data_list,
            'grand_total_loans': grand_total_loans,
            'grand_total_outstanding': grand_total_outstanding,
            'breadcrumbs': breadcrumbs,
            'group_id': group_id,
        })
    
    # Default: redirect to branch view
    return redirect('?level=branch')


