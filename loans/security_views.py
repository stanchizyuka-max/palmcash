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
    """Officer initiates a security adjustment or return."""
    if request.user.role not in ['loan_officer', 'manager', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:dashboard')

    loan = get_object_or_404(Loan, pk=loan_id)

    if request.method == 'POST':
        try:
            amount = request.POST.get('amount', '0')
            notes = request.POST.get('notes', '')
            if action == 'adjustment':
                txn, err = initiate_security_adjustment(loan, amount, notes, request.user)
            elif action == 'return':
                txn, err = initiate_security_return(loan, amount, notes, request.user)
            elif action == 'withdrawal':
                new_loan_amount = request.POST.get('new_loan_amount', '0')
                txn, err = initiate_security_withdrawal(loan, new_loan_amount, notes, request.user)
            else:
                err = 'Invalid action.'
                txn = None

            if err:
                messages.error(request, err)
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
