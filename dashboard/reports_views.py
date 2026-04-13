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
    client_filter = request.GET.get('client')

    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    if tx_type:
        qs = qs.filter(transaction_type=tx_type)
    if branch_filter and request.user.role == 'admin':
        qs = qs.filter(loan__loan_officer__officer_assignment__branch=branch_filter)
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
        writer.writerow(['Client', 'Loan ID', 'Type', 'Amount', 'Date', 'Branch', 'Status'])
        for tx in qs:
            branch = ''
            try:
                branch = tx.loan.loan_officer.officer_assignment.branch
            except Exception:
                pass
            writer.writerow([
                tx.loan.borrower.get_full_name(),
                tx.loan.application_number,
                tx.get_transaction_type_display(),
                tx.amount,
                tx.created_at.date(),
                branch,
                tx.get_status_display(),
            ])
        writer.writerow(['', '', 'TOTAL', total, '', '', ''])
        return response

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    from clients.models import Branch
    branches = Branch.objects.filter(is_active=True) if request.user.role == 'admin' else []

    return render(request, 'dashboard/reports_security.html', {
        'page_obj': page,
        'total': total,
        'tx_types': SecurityTransaction.TRANSACTION_TYPES,
        'branches': branches,
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

    if date_from:
        qs = qs.filter(disbursement_date__date__gte=date_from)
    if date_to:
        qs = qs.filter(disbursement_date__date__lte=date_to)
    if branch_filter and request.user.role == 'admin':
        qs = qs.filter(loan_officer__officer_assignment__branch=branch_filter)

    total = qs.aggregate(total=Sum('principal_amount'))['total'] or 0

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="disbursements.csv"'
        writer = csv.writer(response)
        writer.writerow(['Loan ID', 'Client', 'Amount', 'Disbursement Date', 'Branch'])
        for loan in qs:
            branch = ''
            try:
                branch = loan.loan_officer.officer_assignment.branch
            except Exception:
                pass
            writer.writerow([
                loan.application_number,
                loan.borrower.get_full_name(),
                loan.principal_amount,
                loan.disbursement_date.date() if loan.disbursement_date else '',
                branch,
            ])
        writer.writerow(['', 'TOTAL', total, '', ''])
        return response

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    from clients.models import Branch
    branches = Branch.objects.filter(is_active=True) if request.user.role == 'admin' else []

    return render(request, 'dashboard/reports_disbursements.html', {
        'page_obj': page,
        'total': total,
        'branches': branches,
        'filters': request.GET,
    })


@login_required
def client_balances_report(request):
    """Client balances report with hierarchical structure: Officers → Branches → Groups → Clients"""
    
    loan_qs = _loan_qs(request.user).filter(
        status__in=['active', 'completed']
    ).select_related('borrower', 'loan_officer', 'loan_officer__officer_assignment')

    status_filter = request.GET.get('status')
    branch_filter = request.GET.get('branch')
    group_filter = request.GET.get('group')
    officer_filter = request.GET.get('officer')

    if status_filter:
        loan_qs = loan_qs.filter(status=status_filter)
    if branch_filter and request.user.role == 'admin':
        loan_qs = loan_qs.filter(loan_officer__officer_assignment__branch=branch_filter)
    if group_filter:
        loan_qs = loan_qs.filter(
            borrower__group_memberships__group_id=group_filter,
            borrower__group_memberships__is_active=True
        )
    if officer_filter and request.user.role in ['admin', 'manager']:
        loan_qs = loan_qs.filter(loan_officer_id=officer_filter)

    # Build hierarchical structure
    from collections import defaultdict
    from accounts.models import User
    
    # Get all loan officers with loans
    officer_data = defaultdict(lambda: {
        'officer': None,
        'branch': None,
        'groups': defaultdict(lambda: {
            'group': None,
            'clients': []
        }),
        'total_outstanding': 0,
        'total_active_loans': 0
    })
    
    # Process loans
    for loan in loan_qs:
        if not loan.loan_officer:
            continue
            
        officer = loan.loan_officer
        officer_id = officer.id
        
        # Get officer's branch
        try:
            branch_name = officer.officer_assignment.branch
        except:
            branch_name = 'No Branch'
        
        # Get borrower's group
        membership = loan.borrower.group_memberships.filter(is_active=True).first()
        group = membership.group if membership else None
        group_id = group.id if group else 0
        group_name = group.name if group else 'No Group'
        
        # Initialize officer data
        if officer_data[officer_id]['officer'] is None:
            officer_data[officer_id]['officer'] = officer
            officer_data[officer_id]['branch'] = branch_name
        
        # Initialize group data
        if officer_data[officer_id]['groups'][group_id]['group'] is None:
            officer_data[officer_id]['groups'][group_id]['group'] = group
            officer_data[officer_id]['groups'][group_id]['group_name'] = group_name
            officer_data[officer_id]['groups'][group_id]['total_outstanding'] = 0
            officer_data[officer_id]['groups'][group_id]['total_active_loans'] = 0
        
        # Find or create client entry
        client_found = False
        for client_data in officer_data[officer_id]['groups'][group_id]['clients']:
            if client_data['client'].id == loan.borrower.id:
                # Update existing client
                if loan.status == 'active':
                    client_data['active_loans'] += 1
                    client_data['outstanding'] += loan.balance_remaining or 0
                client_found = True
                break
        
        if not client_found:
            # Add new client
            active_loans = 1 if loan.status == 'active' else 0
            outstanding = loan.balance_remaining or 0 if loan.status == 'active' else 0
            officer_data[officer_id]['groups'][group_id]['clients'].append({
                'client': loan.borrower,
                'active_loans': active_loans,
                'outstanding': outstanding
            })
        
        # Update group totals
        if loan.status == 'active':
            officer_data[officer_id]['groups'][group_id]['total_active_loans'] += 1
            officer_data[officer_id]['groups'][group_id]['total_outstanding'] += loan.balance_remaining or 0
            
            # Update officer totals
            officer_data[officer_id]['total_active_loans'] += 1
            officer_data[officer_id]['total_outstanding'] += loan.balance_remaining or 0
    
    # Convert to list and sort
    officers_list = []
    grand_total_outstanding = 0
    grand_total_active_loans = 0
    
    for officer_id, data in officer_data.items():
        # Convert groups dict to list
        groups_list = []
        for group_id, group_data in data['groups'].items():
            groups_list.append(group_data)
        
        # Sort groups by name
        groups_list.sort(key=lambda x: x['group_name'])
        
        data['groups_list'] = groups_list
        officers_list.append(data)
        
        grand_total_outstanding += data['total_outstanding']
        grand_total_active_loans += data['total_active_loans']
    
    # Sort officers by name
    officers_list.sort(key=lambda x: x['officer'].get_full_name() if x['officer'] else '')
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="client_balances.csv"'
        writer = csv.writer(response)
        writer.writerow(['Loan Officer', 'Branch', 'Group', 'Client', 'Active Loans', 'Outstanding Balance'])
        
        for officer_data in officers_list:
            officer_name = officer_data['officer'].get_full_name()
            branch_name = officer_data['branch']
            
            for group_data in officer_data['groups_list']:
                group_name = group_data['group_name']
                
                for client_data in group_data['clients']:
                    writer.writerow([
                        officer_name,
                        branch_name,
                        group_name,
                        client_data['client'].get_full_name(),
                        client_data['active_loans'],
                        client_data['outstanding'],
                    ])
        
        writer.writerow(['', '', '', 'GRAND TOTAL', grand_total_active_loans, grand_total_outstanding])
        return response

    # Get filter options
    from clients.models import Branch, BorrowerGroup
    branches = Branch.objects.filter(is_active=True) if request.user.role == 'admin' else []
    groups = BorrowerGroup.objects.filter(is_active=True)
    
    # Get officers for filter
    officers = User.objects.filter(role='loan_officer', is_active=True)
    if request.user.role == 'loan_officer':
        groups = groups.filter(assigned_officer=request.user)
        officers = officers.filter(id=request.user.id)
    elif request.user.role == 'manager':
        branch = _get_branch(request.user)
        if branch:
            groups = groups.filter(branch=branch)
            officers = officers.filter(officer_assignment__branch=branch.name)

    return render(request, 'dashboard/reports_balances.html', {
        'officers_list': officers_list,
        'grand_total_outstanding': grand_total_outstanding,
        'grand_total_active_loans': grand_total_active_loans,
        'branches': branches,
        'groups': groups,
        'officers': officers,
        'filters': request.GET,
    })

