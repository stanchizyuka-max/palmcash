from decimal import Decimal
from django.db import transaction as db_transaction


def _get_or_create_vault(branch):
    from .models import BranchVault
    vault, _ = BranchVault.objects.get_or_create(branch=branch)
    return vault


def _get_branch_for_loan(loan):
    try:
        return loan.loan_officer.officer_assignment.branch_obj()
    except Exception:
        pass
    try:
        from clients.models import Branch
        return Branch.objects.get(name=loan.loan_officer.officer_assignment.branch)
    except Exception:
        return None


def record_security_deposit(loan, amount, initiated_by):
    branch = _get_branch_for_loan(loan)
    if not branch:
        return None
    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        vault.balance += Decimal(str(amount))
        vault.save(update_fields=['balance', 'updated_at'])
        from .models import VaultTransaction
        return VaultTransaction.objects.create(
            vault=vault, loan=loan,
            direction='in', transaction_type='security_deposit',
            amount=amount, balance_after=vault.balance,
            initiated_by=initiated_by,
            notes=f'Security deposit for {loan.application_number}',
        )


def record_loan_disbursement(loan, approved_by):
    branch = _get_branch_for_loan(loan)
    if not branch:
        return None
    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        vault.balance -= Decimal(str(loan.principal_amount))
        vault.save(update_fields=['balance', 'updated_at'])
        from .models import VaultTransaction
        return VaultTransaction.objects.create(
            vault=vault, loan=loan,
            direction='out', transaction_type='loan_disbursement',
            amount=loan.principal_amount, balance_after=vault.balance,
            initiated_by=loan.loan_officer, approved_by=approved_by,
            notes=f'Disbursement for {loan.application_number}',
        )


def record_security_return(loan, amount, approved_by):
    branch = _get_branch_for_loan(loan)
    if not branch:
        return None
    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        vault.balance -= Decimal(str(amount))
        vault.save(update_fields=['balance', 'updated_at'])
        from .models import VaultTransaction
        return VaultTransaction.objects.create(
            vault=vault, loan=loan,
            direction='out', transaction_type='security_return',
            amount=amount, balance_after=vault.balance,
            initiated_by=loan.loan_officer, approved_by=approved_by,
            notes=f'Security return for {loan.application_number}',
        )
