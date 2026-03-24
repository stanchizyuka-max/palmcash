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
    loan_qs = _loan_qs(request.user).filter(
        status__in=['active', 'completed']
    ).select_related('borrower', 'loan_officer__officer_assignment')

    status_filter = request.GET.get('status')
    branch_filter = request.GET.get('branch')
    group_filter = request.GET.get('group')

    if status_filter:
        loan_qs = loan_qs.filter(status=status_filter)
    if branch_filter and request.user.role == 'admin':
        loan_qs = loan_qs.filter(loan_officer__officer_assignment__branch=branch_filter)
    if group_filter:
        loan_qs = loan_qs.filter(
            borrower__group_memberships__group_id=group_filter
        )

    from django.db.models import OuterRef, Subquery
    borrower_ids = loan_qs.values_list('borrower_id', flat=True).distinct()

    from accounts.models import User
    clients = User.objects.filter(id__in=borrower_ids).prefetch_related('loans')

    rows = []
    total_outstanding = 0
    for client in clients:
        client_loans = loan_qs.filter(borrower=client)
        active_count = client_loans.filter(status='active').count()
        outstanding = client_loans.filter(status='active').aggregate(
            bal=Sum('balance_remaining')
        )['bal'] or 0
        total_outstanding += outstanding
        rows.append({
            'client': client,
            'active_loans': active_count,
            'outstanding': outstanding,
        })

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="client_balances.csv"'
        writer = csv.writer(response)
        writer.writerow(['Client', 'Active Loans', 'Outstanding Balance'])
        for row in rows:
            writer.writerow([
                row['client'].get_full_name(),
                row['active_loans'],
                row['outstanding'],
            ])
        writer.writerow(['TOTAL', '', total_outstanding])
        return response

    paginator = Paginator(rows, 25)
    page = paginator.get_page(request.GET.get('page'))

    from clients.models import Branch, BorrowerGroup
    branches = Branch.objects.filter(is_active=True) if request.user.role == 'admin' else []
    groups = BorrowerGroup.objects.filter(is_active=True)
    if request.user.role == 'loan_officer':
        groups = groups.filter(assigned_officer=request.user)
    elif request.user.role == 'manager':
        branch = _get_branch(request.user)
        if branch:
            groups = groups.filter(branch=branch)

    return render(request, 'dashboard/reports_balances.html', {
        'page_obj': page,
        'total_outstanding': total_outstanding,
        'branches': branches,
        'groups': groups,
        'filters': request.GET,
    })
