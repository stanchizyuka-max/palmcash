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


def record_payment_collection(loan, amount, recorded_by):
    branch = _get_branch_for_loan(loan, fallback_user=recorded_by)
    if not branch:
        return None
    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        vault.balance += Decimal(str(amount))
        vault.save(update_fields=['balance', 'updated_at'])
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='payment_collection',
            direction='in',
            branch=branch.name,
            amount=amount,
            balance_after=vault.balance,
            description=f'Loan repayment for {loan.application_number}',
            reference_number=_ref(),
            loan=loan,
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )


def record_capital_injection(branch, amount, notes, recorded_by):
    """Admin injects starting capital into a branch vault."""
    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        vault.balance += Decimal(str(amount))
        vault.save(update_fields=['balance', 'updated_at'])
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='capital_injection',
            direction='in',
            branch=branch.name,
            amount=amount,
            balance_after=vault.balance,
            description=notes or f'Capital injection by {recorded_by.get_full_name()}',
            reference_number=_ref(),
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )


def get_vault_balance(branch):
    """Return current vault balance for a branch, 0 if no vault."""
    try:
        from .models import BranchVault
        return BranchVault.objects.get(branch=branch).balance
    except Exception:
        return Decimal('0')


def record_bank_withdrawal(branch, gross_amount, bank_charges, notes, recorded_by):
    """
    Record a bank withdrawal:
    - Net amount (gross - charges) added to vault as IN
    - Bank charges recorded as OUT
    """
    gross_amount = Decimal(str(gross_amount))
    bank_charges = Decimal(str(bank_charges or 0))
    net_amount = gross_amount - bank_charges

    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        from expenses.models import VaultTransaction
        txns = []

        # Net inflow
        vault.balance += net_amount
        vault.save(update_fields=['balance', 'updated_at'])
        txns.append(VaultTransaction.objects.create(
            transaction_type='bank_withdrawal',
            direction='in',
            branch=branch.name,
            amount=net_amount,
            balance_after=vault.balance,
            description=notes or f'Bank withdrawal — net K{net_amount:,.2f} (gross K{gross_amount:,.2f})',
            reference_number=_ref(),
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        ))

        # Bank charges outflow
        if bank_charges > 0:
            vault.balance -= bank_charges
            vault.save(update_fields=['balance', 'updated_at'])
            txns.append(VaultTransaction.objects.create(
                transaction_type='bank_charges',
                direction='out',
                branch=branch.name,
                amount=bank_charges,
                balance_after=vault.balance,
                description=f'Bank charges on withdrawal',
                reference_number=_ref(),
                recorded_by=recorded_by,
                transaction_date=timezone.now(),
            ))

        return txns


def record_fund_deposit(branch, amount, source, notes, recorded_by):
    """Record an incoming fund deposit into the vault."""
    amount = Decimal(str(amount))
    with db_transaction.atomic():
        vault = _get_or_create_vault(branch)
        vault.balance += amount
        vault.save(update_fields=['balance', 'updated_at'])
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='fund_deposit',
            direction='in',
            branch=branch.name,
            amount=amount,
            balance_after=vault.balance,
            description=f'Fund deposit — {source}. {notes}'.strip(),
            reference_number=_ref(),
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )


def record_branch_transfer(from_branch, to_branch, amount, notes, recorded_by):
    """Transfer funds between two branch vaults."""
    amount = Decimal(str(amount))
    with db_transaction.atomic():
        from_vault = _get_or_create_vault(from_branch)
        if from_vault.balance < amount:
            raise ValueError(f'Insufficient vault balance in {from_branch.name}. Available: K{from_vault.balance:,.2f}')

        to_vault = _get_or_create_vault(to_branch)
        ref = _ref()
        from expenses.models import VaultTransaction

        # Deduct from sender
        from_vault.balance -= amount
        from_vault.save(update_fields=['balance', 'updated_at'])
        out_tx = VaultTransaction.objects.create(
            transaction_type='branch_transfer_out',
            direction='out',
            branch=from_branch.name,
            amount=amount,
            balance_after=from_vault.balance,
            description=f'Transfer to {to_branch.name}. {notes}'.strip(),
            reference_number=f'{ref}-OUT',
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )

        # Add to receiver
        to_vault.balance += amount
        to_vault.save(update_fields=['balance', 'updated_at'])
        in_tx = VaultTransaction.objects.create(
            transaction_type='branch_transfer_in',
            direction='in',
            branch=to_branch.name,
            amount=amount,
            balance_after=to_vault.balance,
            description=f'Transfer from {from_branch.name}. {notes}'.strip(),
            reference_number=f'{ref}-IN',
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )

        return out_tx, in_tx
