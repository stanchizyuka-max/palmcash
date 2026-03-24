from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone
import uuid


def _get_or_create_vault(branch):
    from .models import BranchVault
    vault, _ = BranchVault.objects.get_or_create(branch=branch)
    return vault


def _get_branch_for_loan(loan, fallback_user=None):
    try:
        from clients.models import Branch
        branch_name = loan.loan_officer.officer_assignment.branch
        if branch_name:
            branch = Branch.objects.filter(name__iexact=branch_name).first()
            if branch:
                return branch
    except Exception:
        pass
    # Fallback: use the verifying manager's branch
    if fallback_user and hasattr(fallback_user, 'managed_branch') and fallback_user.managed_branch:
        return fallback_user.managed_branch
    return None


def _ref():
    return uuid.uuid4().hex[:12].upper()


def record_security_deposit(loan, amount, initiated_by):
    branch = _get_branch_for_loan(loan, fallback_user=initiated_by)
    if not branch:
        return None
    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        vault.balance += Decimal(str(amount))
        vault.save(update_fields=['balance', 'updated_at'])
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='security_deposit',
            direction='in',
            branch=branch.name,
            amount=amount,
            balance_after=vault.balance,
            description=f'Security deposit for {loan.application_number}',
            reference_number=_ref(),
            loan=loan,
            recorded_by=initiated_by,
            transaction_date=timezone.now(),
        )


def record_loan_disbursement(loan, approved_by):
    branch = _get_branch_for_loan(loan, fallback_user=approved_by)
    if not branch:
        return None
    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        vault.balance -= Decimal(str(loan.principal_amount))
        vault.save(update_fields=['balance', 'updated_at'])
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='loan_disbursement',
            direction='out',
            branch=branch.name,
            amount=loan.principal_amount,
            balance_after=vault.balance,
            description=f'Disbursement for {loan.application_number}',
            reference_number=_ref(),
            loan=loan,
            recorded_by=loan.loan_officer,
            approved_by=approved_by,
            transaction_date=timezone.now(),
        )


def record_security_return(loan, amount, approved_by):
    branch = _get_branch_for_loan(loan, fallback_user=approved_by)
    if not branch:
        return None
    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        vault.balance -= Decimal(str(amount))
        vault.save(update_fields=['balance', 'updated_at'])
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='security_return',
            direction='out',
            branch=branch.name,
            amount=amount,
            balance_after=vault.balance,
            description=f'Security return for {loan.application_number}',
            reference_number=_ref(),
            loan=loan,
            recorded_by=loan.loan_officer,
            approved_by=approved_by,
            transaction_date=timezone.now(),
        )
