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

    from clients.models import Branch
    all_branches = Branch.objects.filter(is_active=True).order_by('name')

    if request.user.role == 'manager':
        branch = _get_manager_branch(request.user)
        if not branch:
            return render(request, 'dashboard/vault.html', {'no_branch': True})
        vault, _ = BranchVault.objects.get_or_create(branch=branch)
        qs = VaultTransaction.objects.filter(branch=branch.name).select_related('loan__borrower', 'recorded_by', 'approved_by')
    else:
        # Admin — scope to a selected branch to avoid loading all transactions
        selected_branch_name = request.GET.get('branch', '')
        if selected_branch_name:
            branch = all_branches.filter(name=selected_branch_name).first()
        else:
            branch = all_branches.first()

        if branch:
            vault, _ = BranchVault.objects.get_or_create(branch=branch)
            qs = VaultTransaction.objects.filter(branch=branch.name).select_related('loan__borrower', 'recorded_by', 'approved_by')
        else:
            vault = None
            qs = VaultTransaction.objects.none()

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
        ('bank_withdrawal', 'Bank Withdrawal'),
        ('bank_charges', 'Bank Charges'),
        ('bank_deposit_out', 'Bank Deposit (to Bank)'),
        ('fund_deposit', 'Fund Received'),
        ('branch_transfer_in', 'Branch Transfer (In)'),
        ('branch_transfer_out', 'Branch Transfer (Out)'),
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
        'all_branches': all_branches,
        'selected_branch': branch,
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


@login_required
def bank_withdrawal(request):
    """Record a bank withdrawal — net goes into vault, charges go out."""
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard:dashboard')

    branch = _get_manager_branch(request.user) if request.user.role == 'manager' else None

    if request.method == 'POST':
        from clients.models import Branch
        from decimal import Decimal
        from django.contrib import messages
        try:
            if request.user.role == 'admin':
                branch = Branch.objects.get(pk=request.POST.get('branch'))
            amount = Decimal(request.POST.get('gross_amount', '0'))
            notes = request.POST.get('notes', '')
            if amount <= 0:
                raise ValueError('Amount must be greater than zero.')
            from loans.vault_services import record_bank_withdrawal
            record_bank_withdrawal(branch, amount, notes, request.user)
            messages.success(request, f'Bank withdrawal of K{amount:,.2f} added to {branch.name} vault.')
            return redirect('dashboard:vault')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    from clients.models import Branch
    branches = Branch.objects.filter(is_active=True).order_by('name') if request.user.role == 'admin' else None
    return render(request, 'dashboard/vault_bank_withdrawal.html', {'branch': branch, 'branches': branches})


@login_required
def fund_deposit(request):
    """Record an incoming fund deposit into the vault."""
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard:dashboard')

    branch = _get_manager_branch(request.user) if request.user.role == 'manager' else None

    if request.method == 'POST':
        from clients.models import Branch
        from decimal import Decimal
        from django.contrib import messages
        try:
            if request.user.role == 'admin':
                branch = Branch.objects.get(pk=request.POST.get('branch'))
            amount = Decimal(request.POST.get('amount', '0'))
            source = request.POST.get('source', '').strip()
            notes = request.POST.get('notes', '')
            if amount <= 0:
                raise ValueError('Amount must be greater than zero.')
            if not source:
                raise ValueError('Source/type is required.')
            from loans.vault_services import record_fund_deposit
            record_fund_deposit(branch, amount, source, notes, request.user)
            messages.success(request, f'K{amount:,.2f} deposited into {branch.name} vault.')
            return redirect('dashboard:vault')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    from clients.models import Branch
    branches = Branch.objects.filter(is_active=True).order_by('name') if request.user.role == 'admin' else None
    return render(request, 'dashboard/vault_fund_deposit.html', {'branch': branch, 'branches': branches})


@login_required
def branch_transfer(request):
    """Transfer funds between two branch vaults."""
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard:dashboard')

    from clients.models import Branch
    from_branch = _get_manager_branch(request.user) if request.user.role == 'manager' else None
    all_branches = Branch.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        from decimal import Decimal
        from django.contrib import messages
        try:
            if request.user.role == 'admin':
                from_branch = Branch.objects.get(pk=request.POST.get('from_branch'))
            to_branch = Branch.objects.get(pk=request.POST.get('to_branch'))
            amount = Decimal(request.POST.get('amount', '0'))
            notes = request.POST.get('notes', '')
            if amount <= 0:
                raise ValueError('Amount must be greater than zero.')
            if from_branch == to_branch:
                raise ValueError('Source and destination branches must be different.')
            from loans.vault_services import record_branch_transfer
            record_branch_transfer(from_branch, to_branch, amount, notes, request.user)
            messages.success(request, f'K{amount:,.2f} transferred from {from_branch.name} to {to_branch.name}.')
            return redirect('dashboard:vault')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    to_branches = all_branches.exclude(pk=from_branch.pk) if from_branch else all_branches
    return render(request, 'dashboard/vault_branch_transfer.html', {
        'from_branch': from_branch,
        'all_branches': all_branches,
        'to_branches': to_branches,
    })


@login_required
def bank_deposit_out(request):
    """Record cash deposited to bank (vault OUT) with optional mobile money charges."""
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard:dashboard')

    branch = _get_manager_branch(request.user) if request.user.role == 'manager' else None

    if request.method == 'POST':
        from clients.models import Branch
        from decimal import Decimal
        from django.contrib import messages
        try:
            if request.user.role == 'admin':
                branch = Branch.objects.get(pk=request.POST.get('branch'))
            gross = Decimal(request.POST.get('gross_amount', '0'))
            charges = Decimal(request.POST.get('charges', '0') or '0')
            notes = request.POST.get('notes', '')
            if gross <= 0:
                raise ValueError('Amount must be greater than zero.')
            from loans.vault_services import record_bank_deposit
            record_bank_deposit(branch, gross, charges, notes, request.user)
            messages.success(request, f'Bank deposit of K{gross:,.2f} recorded. Vault reduced by K{gross + charges:,.2f} (incl. K{charges:,.2f} charges).')
            return redirect('dashboard:vault')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    from clients.models import Branch
    branches = Branch.objects.filter(is_active=True).order_by('name') if request.user.role == 'admin' else None
    return render(request, 'dashboard/vault_bank_deposit_out.html', {'branch': branch, 'branches': branches})
