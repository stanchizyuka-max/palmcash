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


def _get_security_balance(branch):
    """Calculate total available security deposits for a branch from vault transactions."""
    from django.db.models import Sum
    from decimal import Decimal

    branch_name = branch.name

    security_in = VaultTransaction.objects.filter(
        branch=branch_name,
        transaction_type='security_deposit',
        direction='in'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    security_out = VaultTransaction.objects.filter(
        branch=branch_name,
        transaction_type__in=['security_return', 'security_used'],
        direction='out'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    return security_in - security_out


def _vault_qs(branch_name):
    """Return an optimised VaultTransaction queryset for a branch."""
    return (
        VaultTransaction.objects
        .filter(branch=branch_name)
        .select_related('loan', 'recorded_by', 'approved_by')
        .defer(
            'recorded_by__password', 'recorded_by__address', 'recorded_by__national_id',
            'recorded_by__date_of_birth', 'recorded_by__profile_picture',
            'recorded_by__employment_status', 'recorded_by__employer_name',
            'recorded_by__monthly_income', 'recorded_by__province', 'recorded_by__district',
            'approved_by__password', 'approved_by__address', 'approved_by__national_id',
            'approved_by__date_of_birth', 'approved_by__profile_picture',
            'approved_by__employment_status', 'approved_by__employer_name',
            'approved_by__monthly_income', 'approved_by__province', 'approved_by__district',
        )
    )


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
        qs = _vault_qs(branch.name)
    else:
        # Admin — scope to a selected branch to avoid loading all transactions
        selected_branch_name = request.GET.get('branch', '')
        if selected_branch_name:
            branch = all_branches.filter(name=selected_branch_name).first()
        else:
            branch = all_branches.first()

        if branch:
            vault, _ = BranchVault.objects.get_or_create(branch=branch)
            qs = _vault_qs(branch.name)
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
        ('deposit', 'Cash Deposit'),
        ('withdrawal', 'Cash Withdrawal'),
        ('payment_collection', 'Payment Collection'),
        ('security_deposit', 'Security Deposit'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('security_return', 'Security Return'),
        ('capital_injection', 'Capital Injection'),
        ('bank_withdrawal', 'Bank Withdrawal'),
        ('bank_charges', 'Bank Charges'),
        ('bank_deposit_out', 'Bank Deposit (to Bank)'),
        ('fund_deposit', 'Fund Received'),
        ('branch_transfer_in', 'Branch Transfer (In)'),
        ('branch_transfer_out', 'Branch Transfer (Out)'),
        ('savings_deposit', 'Savings Deposit'),
        ('savings_withdrawal', 'Savings Withdrawal'),
        ('month_close', 'Month Closing'),
        ('month_open', 'Month Opening'),
        ('expense', 'Expense'),
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
        'savings': __import__('loans.models', fromlist=['BranchSavings']).BranchSavings.objects.filter(branch=branch).first() if branch else None,
        'security_balance': _get_security_balance(branch) if branch else 0,
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


@login_required
def vault_collection(request):
    """Record a manual cash collection into the vault."""
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
            collection_date_str = request.POST.get('collection_date', '')
            if amount <= 0:
                raise ValueError('Amount must be greater than zero.')
            if not source:
                raise ValueError('Source/description is required.')

            # Parse date
            from datetime import datetime as dt
            if collection_date_str:
                collection_dt = dt.strptime(collection_date_str, '%Y-%m-%d')
                from django.utils import timezone as tz
                collection_dt = tz.make_aware(collection_dt)
            else:
                collection_dt = timezone.now()

            from expenses.models import VaultTransaction
            from loans.models import BranchVault
            import uuid

            vault, _ = BranchVault.objects.get_or_create(branch=branch)
            vault.balance += amount
            vault.save()

            VaultTransaction.objects.create(
                branch=branch.name,
                transaction_type='payment_collection',
                direction='in',
                amount=amount,
                balance_after=vault.balance,
                description=f'Manual collection — {source}. {notes}'.strip(),
                reference_number=f'COL-{uuid.uuid4().hex[:8].upper()}',
                recorded_by=request.user,
                transaction_date=collection_dt,
            )
            
            messages.success(request, f'K{amount:,.2f} collection recorded into {branch.name} vault.')
            return redirect('dashboard:vault')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    from clients.models import Branch
    branches = Branch.objects.filter(is_active=True).order_by('name') if request.user.role == 'admin' else None
    return render(request, 'dashboard/vault_collection.html', {'branch': branch, 'branches': branches})


@login_required
def vault_month_close(request):
    """Close the current month — record closing balance and reset vault to zero."""
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard:dashboard')

    branch = _get_manager_branch(request.user) if request.user.role == 'manager' else None

    if request.user.role == 'admin':
        from clients.models import Branch
        branch_name = request.GET.get('branch') or request.POST.get('branch')
        if branch_name:
            branch = Branch.objects.filter(name=branch_name).first()
        if not branch:
            branch = Branch.objects.filter(is_active=True).first()

    vault = None
    if branch:
        vault, _ = BranchVault.objects.get_or_create(branch=branch)

    from datetime import date
    current_month = date.today().strftime('%Y-%m')

    if request.method == 'POST':
        from django.contrib import messages
        from expenses.models import VaultTransaction
        import uuid

        try:
            closing_month = request.POST.get('closing_month', current_month)
            notes = request.POST.get('notes', '')
            closing_balance = vault.balance

            # 1. Record closing balance entry (OUT — removes balance from running total)
            VaultTransaction.objects.create(
                branch=branch.name,
                transaction_type='month_close',
                direction='out',
                amount=closing_balance,
                balance_after=0,
                description=f'Month closing — {closing_month}. Balance carried forward: K{closing_balance:,.2f}. {notes}'.strip(),
                reference_number=f'CLOSE-{closing_month}-{uuid.uuid4().hex[:4].upper()}',
                recorded_by=request.user,
                transaction_date=timezone.now(),
            )

            # 2. Reset vault balance to zero
            vault.balance = 0
            vault.save()

            # 3. Record opening balance for new month (IN — restores balance)
            VaultTransaction.objects.create(
                branch=branch.name,
                transaction_type='month_open',
                direction='in',
                amount=closing_balance,
                balance_after=closing_balance,
                description=f'Opening balance — carried forward from {closing_month}.',
                reference_number=f'OPEN-{closing_month}-{uuid.uuid4().hex[:4].upper()}',
                recorded_by=request.user,
                transaction_date=timezone.now(),
            )

            # 4. Restore vault balance to closing balance (it's the opening of new month)
            vault.balance = closing_balance
            vault.save()

            messages.success(request, f'Month {closing_month} closed. Vault reset with opening balance of K{closing_balance:,.2f}.')
            return redirect('dashboard:vault')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error: {e}')

    return render(request, 'dashboard/vault_month_close.html', {
        'vault': vault,
        'branch': branch,
        'current_month': current_month,
    })


@login_required
def vault_savings_deposit(request):
    """Move money from vault to savings."""
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard:dashboard')

    branch = _get_manager_branch(request.user) if request.user.role == 'manager' else None

    if request.user.role == 'admin':
        from clients.models import Branch
        branch_name = request.GET.get('branch') or request.POST.get('branch')
        if branch_name:
            branch = Branch.objects.filter(name=branch_name).first()
        if not branch:
            branch = Branch.objects.filter(is_active=True).first()

    vault = None
    savings = None
    if branch:
        vault, _ = BranchVault.objects.get_or_create(branch=branch)
        from loans.models import BranchSavings
        savings, _ = BranchSavings.objects.get_or_create(branch=branch)

    if request.method == 'POST':
        from decimal import Decimal
        from django.contrib import messages
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            notes = request.POST.get('notes', '')
            if amount <= 0:
                raise ValueError('Amount must be greater than zero.')
            from loans.vault_services import record_savings_deposit
            record_savings_deposit(branch, amount, notes, request.user)
            messages.success(request, f'K{amount:,.2f} moved from vault to savings.')
            return redirect('dashboard:vault')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error: {e}')

    from clients.models import Branch
    branches = Branch.objects.filter(is_active=True).order_by('name') if request.user.role == 'admin' else None
    return render(request, 'dashboard/vault_savings_deposit.html', {
        'branch': branch,
        'branches': branches,
        'vault': vault,
        'savings': savings,
    })


@login_required
def vault_savings_withdrawal(request):
    """Move money from savings back to vault."""
    if request.user.role not in ['manager', 'admin']:
        return redirect('dashboard:dashboard')

    branch = _get_manager_branch(request.user) if request.user.role == 'manager' else None

    if request.user.role == 'admin':
        from clients.models import Branch
        branch_name = request.GET.get('branch') or request.POST.get('branch')
        if branch_name:
            branch = Branch.objects.filter(name=branch_name).first()
        if not branch:
            branch = Branch.objects.filter(is_active=True).first()

    vault = None
    savings = None
    if branch:
        vault, _ = BranchVault.objects.get_or_create(branch=branch)
        from loans.models import BranchSavings
        savings, _ = BranchSavings.objects.get_or_create(branch=branch)

    if request.method == 'POST':
        from decimal import Decimal
        from django.contrib import messages
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            notes = request.POST.get('notes', '')
            if amount <= 0:
                raise ValueError('Amount must be greater than zero.')
            from loans.vault_services import record_savings_withdrawal
            record_savings_withdrawal(branch, amount, notes, request.user)
            messages.success(request, f'K{amount:,.2f} withdrawn from savings to vault.')
            return redirect('dashboard:vault')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error: {e}')

    from clients.models import Branch
    branches = Branch.objects.filter(is_active=True).order_by('name') if request.user.role == 'admin' else None
    return render(request, 'dashboard/vault_savings_withdrawal.html', {
        'branch': branch,
        'branches': branches,
        'vault': vault,
        'savings': savings,
    })
