import csv
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from loans.models import BranchVault
from expenses.models import VaultTransaction


def _get_manager_branch(user):
    try:
        return user.managed_branch
    except Exception:
        return None


@login_required
def vault_dashboard(request):
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard:dashboard')

    if request.user.role == 'manager':
        branch = _get_manager_branch(request.user)
        if not branch:
            return render(request, 'dashboard/vault.html', {'no_branch': True})
        vault, _ = BranchVault.objects.get_or_create(branch=branch)
        qs = VaultTransaction.objects.filter(branch=branch.name).select_related('loan__borrower', 'recorded_by', 'approved_by')
    else:
        vault = None
        qs = VaultTransaction.objects.select_related('loan__borrower', 'recorded_by', 'approved_by')

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    tx_type = request.GET.get('type')
    direction = request.GET.get('direction')

    if date_from:
        qs = qs.filter(transaction_date__date__gte=date_from)
    if date_to:
        qs = qs.filter(transaction_date__date__lte=date_to)
    if tx_type:
        qs = qs.filter(transaction_type=tx_type)
    if direction:
        qs = qs.filter(direction=direction)

    totals = qs.aggregate(
        total_in=Sum('amount', filter=Q(direction='in')),
        total_out=Sum('amount', filter=Q(direction='out')),
    )
    total_in = totals['total_in'] or 0
    total_out = totals['total_out'] or 0

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="vault_transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Type', 'Direction', 'Amount', 'Balance After', 'Loan', 'Recorded By', 'Approved By'])
        for tx in qs:
            writer.writerow([
                tx.transaction_date.date(),
                tx.get_transaction_type_display(),
                tx.get_direction_display(),
                tx.amount,
                tx.balance_after,
                tx.loan.application_number if tx.loan else '',
                tx.recorded_by.get_full_name() if tx.recorded_by else '',
                tx.approved_by.get_full_name() if tx.approved_by else '',
            ])
        writer.writerow(['', '', 'Total IN', total_in, '', '', '', ''])
        writer.writerow(['', '', 'Total OUT', total_out, '', '', '', ''])
        return response

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    tx_types = [
        ('security_deposit', 'Security Deposit'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('security_return', 'Security Return'),
        ('payment_collection', 'Loan Repayment'),
        ('capital_injection', 'Capital Injection'),
        ('deposit', 'Cash Deposit'),
        ('withdrawal', 'Cash Withdrawal'),
    ]

    return render(request, 'dashboard/vault.html', {
        'vault': vault,
        'page_obj': page,
        'total_in': total_in,
        'total_out': total_out,
        'tx_types': tx_types,
        'filters': request.GET,
    })


@login_required
def capital_injection(request):
    """Admin injects starting capital into a branch vault."""
    if request.user.role != 'admin':
        return redirect('dashboard:dashboard')

    from clients.models import Branch
    branches = Branch.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        branch_id = request.POST.get('branch')
        amount = request.POST.get('amount')
        notes = request.POST.get('notes', '')

        try:
            branch = Branch.objects.get(pk=branch_id)
            from decimal import Decimal
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError('Amount must be greater than zero.')
            from loans.vault_services import record_capital_injection
            record_capital_injection(branch, amount, notes, request.user)
            from django.contrib import messages
            messages.success(request, f'K{amount:,.2f} injected into {branch.name} vault.')
            return redirect('dashboard:vault')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error: {e}')

    return render(request, 'dashboard/capital_injection.html', {'branches': branches})
