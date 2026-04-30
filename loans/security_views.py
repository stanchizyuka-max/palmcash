from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Loan, SecurityTransaction
from .security_services import (
    initiate_security_adjustment,
    initiate_security_return,
    initiate_security_withdrawal,
    approve_security_transaction,
    reject_security_transaction,
)


@login_required
def security_action(request, loan_id, action):
    """Officer initiates a security adjustment, return, or withdrawal."""
    if request.user.role not in ['loan_officer', 'manager', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:dashboard')

    loan = get_object_or_404(Loan, pk=loan_id)
    
    # Daily loans don't have security deposits
    if loan.repayment_frequency == 'daily':
        messages.error(request, 'Daily loans do not have security deposits.')
        return redirect('loans:detail', pk=loan_id)
    
    # Validate action based on loan status
    if action == 'adjustment' and loan.status != 'active':
        messages.error(request, 'Balance adjustments can only be done on active loans.')
        return redirect('loans:detail', pk=loan_id)
    
    if action == 'withdrawal' and loan.status != 'completed':
        messages.error(request, 'Security withdrawals can only be done on completed loans.')
        return redirect('loans:detail', pk=loan_id)
    
    if action == 'return' and loan.status != 'completed':
        messages.error(request, 'Security returns can only be done on completed loans.')
        return redirect('loans:detail', pk=loan_id)

    if request.method == 'POST':
        try:
            amount = request.POST.get('amount', '0')
            notes = request.POST.get('notes', '')
            if action == 'adjustment':
                txn, err = initiate_security_adjustment(loan, amount, notes, request.user)
            elif action == 'return':
                txn, err = initiate_security_return(loan, amount, notes, request.user)
            elif action == 'withdrawal':
                # Officer enters the withdrawal amount - remaining can be used for new loan
                txn, err = initiate_security_withdrawal(loan, amount, notes, request.user)
            else:
                err = 'Invalid action.'
                txn = None

            if err:
                messages.error(request, err)
            else:
                if action == 'withdrawal':
                    messages.success(request, f'Security withdrawal of K{amount} submitted — awaiting manager approval. Remaining security can be used for a new loan.')
                else:
                    messages.success(request, f'Security {action} submitted — awaiting manager approval.')
                return redirect('loans:detail', pk=loan_id)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    try:
        deposit = loan.security_deposit
    except Exception:
        deposit = None

    return render(request, 'loans/security_action.html', {
        'loan': loan,
        'deposit': deposit,
        'action': action,
        'action_label': {
            'adjustment': 'Balance Adjustment',
            'return': 'Security Return',
            'withdrawal': 'Security Withdrawal',
        }.get(action, action.title()),
    })


@login_required
def security_transaction_approve(request, txn_id):
    """Manager approves or rejects a pending security transaction."""
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, 'Only managers can approve security transactions.')
        return redirect('dashboard:dashboard')

    txn = get_object_or_404(SecurityTransaction, pk=txn_id)

    if request.method == 'POST':
        decision = request.POST.get('decision')
        reason = request.POST.get('reason', '')

        if decision == 'approve':
            ok, err = approve_security_transaction(txn, request.user)
            if ok:
                messages.success(request, f'Security transaction approved — K{txn.amount} {txn.get_transaction_type_display()}.')
            else:
                messages.error(request, err)
        elif decision == 'reject':
            ok, err = reject_security_transaction(txn, request.user, reason)
            if ok:
                messages.warning(request, 'Security transaction rejected.')
            else:
                messages.error(request, err)

        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('loans:detail', pk=txn.loan_id)

    return render(request, 'loans/security_transaction_review.html', {'txn': txn})


@login_required
def security_transactions_list(request, loan_id):
    """View all security transactions for a loan."""
    loan = get_object_or_404(Loan, pk=loan_id)
    transactions = SecurityTransaction.objects.filter(loan=loan).select_related('initiated_by', 'approved_by')

    try:
        deposit = loan.security_deposit
    except Exception:
        deposit = None

    return render(request, 'loans/security_transactions.html', {
        'loan': loan,
        'deposit': deposit,
        'transactions': transactions,
    })


@login_required
def security_topup(request, loan_id=None):
    """Officer initiates a security top-up on an existing loan."""
    if request.user.role not in ['loan_officer', 'admin']:
        messages.error(request, 'Only loan officers can submit top-up requests.')
        return redirect('dashboard:dashboard')

    from accounts.models import User
    from django.db.models import Q

    # Build borrower list scoped to this officer - exclude daily loans
    borrowers = User.objects.filter(
        Q(assigned_officer=request.user) |
        Q(group_memberships__group__assigned_officer=request.user),
        role='borrower',
        is_active=True,
    ).distinct().order_by('last_name', 'first_name')

    selected_borrower_id = request.GET.get('borrower_id') or request.POST.get('borrower_id')
    selected_loan_id = request.GET.get('loan_id') or request.POST.get('loan_id')

    loans_for_borrower = []
    if selected_borrower_id:
        # Only allow top-ups on completed loans (exclude daily loans)
        loans_for_borrower = Loan.objects.filter(
            borrower_id=selected_borrower_id,
            status='completed',
            security_deposit__is_verified=True,
        ).exclude(repayment_frequency='daily').select_related('borrower', 'security_deposit').order_by('-created_at')

    loan = None
    deposit = None
    if selected_loan_id:
        try:
            loan = Loan.objects.select_related('borrower', 'security_deposit').get(
                pk=selected_loan_id,
                status='completed',
                security_deposit__is_verified=True,
            )
            # Check if it's a daily loan
            if loan.repayment_frequency == 'daily':
                messages.error(request, 'Daily loans do not require security deposits or top-ups.')
                return redirect('loans:detail', pk=loan.pk)
            deposit = loan.security_deposit
        except Loan.DoesNotExist:
            messages.error(request, 'Loan not found, not completed, or has no verified security deposit. Top-ups are only allowed on completed loans.')

    if request.method == 'POST' and loan:
        new_loan_amount = request.POST.get('new_loan_amount', '0')
        notes = request.POST.get('notes', '')
        from .security_services import calculate_topup_security
        from decimal import Decimal
        from .models import SecurityTopUpRequest

        try:
            new_amount = Decimal(str(new_loan_amount))
            if new_amount <= 0:
                raise ValueError('New loan amount must be greater than zero.')

            info = calculate_topup_security(loan, new_amount)
            shortfall = info['shortfall']

            if shortfall <= 0:
                messages.info(request, f'No top-up needed — existing security (K{deposit.available_security}) already covers 10% of K{new_amount}.')
                return redirect('loans:detail', pk=loan.pk)

            SecurityTopUpRequest.objects.create(
                loan=loan,
                requested_amount=shortfall,
                reason=notes or f'Top-up for new loan amount K{new_amount}. Required: K{info["required"]}, Available: K{info["available_from_previous"]}, Shortfall: K{shortfall}',
                requested_by=request.user,
                status='pending',
            )
            messages.success(request, f'Top-up request of K{shortfall:.2f} submitted — awaiting manager approval.')
            return redirect('loans:detail', pk=loan.pk)

        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'loans/security_topup.html', {
        'borrowers': borrowers,
        'selected_borrower_id': selected_borrower_id,
        'selected_loan_id': selected_loan_id,
        'loans_for_borrower': loans_for_borrower,
        'loan': loan,
        'deposit': deposit,
    })


@login_required
def officer_security_overview(request):
    """Officer's overview of all their security transactions with type filter."""
    from django.db.models import Q
    officer = request.user

    qs = SecurityTransaction.objects.filter(
        Q(loan__loan_officer=officer) |
        Q(loan__borrower__group_memberships__group__assigned_officer=officer)
    ).select_related('loan', 'loan__borrower', 'initiated_by', 'approved_by').distinct().order_by('-created_at')

    tx_type = request.GET.get('type')
    if tx_type:
        qs = qs.filter(transaction_type=tx_type)

    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    return render(request, 'loans/security_overview.html', {
        'transactions': qs,
        'tx_type': tx_type,
        'status_filter': status_filter,
        'type_choices': SecurityTransaction.TRANSACTION_TYPES,
    })
