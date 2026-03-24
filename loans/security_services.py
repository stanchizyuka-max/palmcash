"""
Security deposit service functions.
All actions are initiated by loan officers and approved by managers.
"""
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction


def initiate_security_adjustment(loan, amount, notes, initiated_by):
    """
    Officer initiates: use part of security deposit to reduce loan balance.
    Returns (SecurityTransaction, error_message)
    """
    from .models import SecurityTransaction
    try:
        deposit = loan.security_deposit
    except Exception:
        return None, 'No security deposit found for this loan.'

    amount = Decimal(str(amount))
    if amount <= 0:
        return None, 'Amount must be greater than zero.'
    if amount > deposit.available_security:
        return None, f'Amount exceeds available security (K{deposit.available_security}).'
    if loan.balance_remaining and amount > loan.balance_remaining:
        return None, f'Amount exceeds remaining loan balance (K{loan.balance_remaining}).'

    txn = SecurityTransaction.objects.create(
        loan=loan,
        transaction_type='adjustment',
        amount=amount,
        notes=notes,
        initiated_by=initiated_by,
        status='pending',
    )
    return txn, None


def initiate_security_return(loan, amount, notes, initiated_by):
    """
    Officer initiates: refund unused security to borrower.
    Returns (SecurityTransaction, error_message)
    """
    from .models import SecurityTransaction
    try:
        deposit = loan.security_deposit
    except Exception:
        return None, 'No security deposit found for this loan.'

    amount = Decimal(str(amount))
    if amount <= 0:
        return None, 'Amount must be greater than zero.'
    if amount > deposit.available_security:
        return None, f'Amount exceeds available security (K{deposit.available_security}).'

    txn = SecurityTransaction.objects.create(
        loan=loan,
        transaction_type='return',
        amount=amount,
        notes=notes,
        initiated_by=initiated_by,
        status='pending',
    )
    return txn, None


def approve_security_transaction(txn, approved_by):
    """
    Manager approves a pending security transaction.
    Returns (success, error_message)
    """
    if txn.status != 'pending':
        return False, 'Transaction is not pending.'

    with db_transaction.atomic():
        deposit = txn.loan.security_deposit

        if txn.transaction_type == 'adjustment':
            if txn.amount > deposit.available_security:
                return False, 'Available security has changed — amount no longer valid.'
            if txn.loan.balance_remaining and txn.amount > txn.loan.balance_remaining:
                return False, 'Loan balance has changed — amount no longer valid.'
            deposit.security_used += txn.amount
            deposit.save(update_fields=['security_used', 'updated_at'])
            loan = txn.loan
            loan.balance_remaining = (loan.balance_remaining or Decimal('0')) - txn.amount
            loan.amount_paid += txn.amount
            loan.save(update_fields=['balance_remaining', 'amount_paid', 'updated_at'])

        elif txn.transaction_type == 'return':
            if txn.amount > deposit.available_security:
                return False, 'Available security has changed — amount no longer valid.'
            deposit.security_returned += txn.amount
            deposit.save(update_fields=['security_returned', 'updated_at'])

        txn.status = 'approved'
        txn.approved_by = approved_by
        txn.approved_at = timezone.now()
        txn.save(update_fields=['status', 'approved_by', 'approved_at'])

    return True, None


def reject_security_transaction(txn, rejected_by, reason=''):
    """Manager rejects a pending security transaction."""
    if txn.status != 'pending':
        return False, 'Transaction is not pending.'
    txn.status = 'rejected'
    txn.approved_by = rejected_by
    txn.approved_at = timezone.now()
    if reason:
        txn.notes = (txn.notes + f'\nRejected: {reason}').strip()
    txn.save(update_fields=['status', 'approved_by', 'approved_at', 'notes'])
    return True, None


def calculate_topup_security(previous_loan, new_amount):
    """
    For a top-up loan: calculate how much new security is needed.
    Returns dict with available, required, carry_forward, shortfall.
    """
    new_amount = Decimal(str(new_amount))
    required = new_amount * Decimal('0.10')
    available = Decimal('0')

    try:
        deposit = previous_loan.security_deposit
        if deposit.is_verified:
            available = deposit.available_security
    except Exception:
        pass

    carry_forward = min(available, required)
    shortfall = max(Decimal('0'), required - carry_forward)

    return {
        'required': required,
        'available_from_previous': available,
        'carry_forward': carry_forward,
        'shortfall': shortfall,
    }


def apply_carry_forward(previous_loan, new_loan, initiated_by):
    """
    Record carry-forward of security from previous loan to new top-up loan.
    Called after new loan is created and its security deposit is set up.
    Returns (SecurityTransaction, error_message)
    """
    from .models import SecurityTransaction
    info = calculate_topup_security(previous_loan, new_loan.principal_amount)
    carry = info['carry_forward']

    if carry <= 0:
        return None, 'No security available to carry forward.'

    txn = SecurityTransaction.objects.create(
        loan=previous_loan,
        transaction_type='carry_forward',
        amount=carry,
        notes=f'Carried forward to top-up loan {new_loan.application_number}',
        initiated_by=initiated_by,
        status='approved',
        approved_by=initiated_by,
        approved_at=timezone.now(),
    )

    deposit = previous_loan.security_deposit
    deposit.security_used += carry
    deposit.save(update_fields=['security_used', 'updated_at'])

    # Credit to new loan's deposit
    try:
        new_deposit = new_loan.security_deposit
        new_deposit.paid_amount += carry
        new_deposit.save(update_fields=['paid_amount', 'updated_at'])
    except Exception:
        pass

    return txn, None
