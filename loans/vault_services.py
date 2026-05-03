"""
Dual-Vault Services - Updated vault operations for Daily/Weekly separation.

This module replaces vault_services.py with dual-vault support.
All operations now route to the correct vault based on loan type.
"""

from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone
import uuid


def _get_vault_for_loan(loan, branch=None):
    """
    Get the correct vault (Daily or Weekly) based on loan type.
    This is the core function that enforces vault separation.
    """
    from .models import DailyVault, WeeklyVault
    
    if not branch:
        branch = _get_branch_for_loan(loan)
    
    if not branch:
        raise ValueError(f"Cannot determine branch for loan {loan.application_number}")
    
    # Route to correct vault based on loan repayment frequency
    if loan.repayment_frequency == 'daily':
        vault, _ = DailyVault.objects.get_or_create(branch=branch)
        vault_type = 'daily'
    else:  # weekly
        vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
        vault_type = 'weekly'
    
    return vault, vault_type


def _get_vault_by_type(branch, vault_type):
    """Get vault by explicit type (for non-loan operations)"""
    from .models import DailyVault, WeeklyVault
    
    if vault_type == 'daily':
        vault, _ = DailyVault.objects.get_or_create(branch=branch)
    else:
        vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
    
    return vault


def _get_branch_for_loan(loan, fallback_user=None):
    """Get the branch for a loan - handles both Branch objects and strings"""
    try:
        from clients.models import Branch
        
        # Get branch reference from loan officer
        if loan.loan_officer and hasattr(loan.loan_officer, 'officer_assignment'):
            branch_ref = loan.loan_officer.officer_assignment.branch
            
            # Handle both Branch object and string cases
            if isinstance(branch_ref, Branch):
                return branch_ref
            elif isinstance(branch_ref, str) and branch_ref:
                branch = Branch.objects.filter(name__iexact=branch_ref).first()
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
    """Record security deposit - routes to correct vault based on loan type"""
    branch = _get_branch_for_loan(loan, fallback_user=initiated_by)
    if not branch:
        return None
    
    with db_transaction.atomic():
        vault, vault_type = _get_vault_for_loan(loan, branch)
        vault.balance += Decimal(str(amount))
        vault.last_transaction_date = timezone.now()
        vault.total_inflows += Decimal(str(amount))
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_inflows', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='security_deposit',
            direction='in',
            branch=branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=vault.balance,
            description=f'Security deposit for {loan.application_number} ({vault_type} vault)',
            reference_number=_ref(),
            loan=loan,
            recorded_by=initiated_by,
            transaction_date=timezone.now(),
        )


def record_loan_disbursement(loan, approved_by):
    """Record loan disbursement - routes to correct vault based on loan type"""
    branch = _get_branch_for_loan(loan, fallback_user=approved_by)
    if not branch:
        return None
    
    with db_transaction.atomic():
        vault, vault_type = _get_vault_for_loan(loan, branch)
        
        # Check sufficient balance
        if vault.balance < Decimal(str(loan.principal_amount)):
            raise ValueError(
                f'Insufficient balance in {vault_type} vault. '
                f'Available: K{vault.balance:,.2f}, Required: K{loan.principal_amount:,.2f}'
            )
        
        vault.balance -= Decimal(str(loan.principal_amount))
        vault.last_transaction_date = timezone.now()
        vault.total_outflows += Decimal(str(loan.principal_amount))
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_outflows', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='loan_disbursement',
            direction='out',
            branch=branch.name,
            vault_type=vault_type,
            amount=loan.principal_amount,
            balance_after=vault.balance,
            description=f'Disbursement for {loan.application_number} ({vault_type} vault)',
            reference_number=_ref(),
            loan=loan,
            recorded_by=loan.loan_officer,
            approved_by=approved_by,
            transaction_date=timezone.now(),
        )


def record_security_return(loan, amount, approved_by):
    """Record a full security return to client"""
    branch = _get_branch_for_loan(loan, fallback_user=approved_by)
    if not branch:
        return None
    
    with db_transaction.atomic():
        vault, vault_type = _get_vault_for_loan(loan, branch)
        vault.balance -= Decimal(str(amount))
        vault.last_transaction_date = timezone.now()
        vault.total_outflows += Decimal(str(amount))
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_outflows', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='security_return',
            direction='out',
            branch=branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=vault.balance,
            description=f'Security return for {loan.application_number} ({vault_type} vault)',
            reference_number=_ref(),
            loan=loan,
            recorded_by=loan.loan_officer,
            approved_by=approved_by,
            transaction_date=timezone.now(),
        )


def record_security_withdrawal(loan, amount, approved_by):
    """Record a partial security withdrawal"""
    branch = _get_branch_for_loan(loan, fallback_user=approved_by)
    if not branch:
        return None
    
    with db_transaction.atomic():
        vault, vault_type = _get_vault_for_loan(loan, branch)
        vault.balance -= Decimal(str(amount))
        vault.last_transaction_date = timezone.now()
        vault.total_outflows += Decimal(str(amount))
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_outflows', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='security_withdrawal',
            direction='out',
            branch=branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=vault.balance,
            description=f'Security withdrawal for {loan.application_number} ({vault_type} vault)',
            reference_number=_ref(),
            loan=loan,
            recorded_by=loan.loan_officer,
            approved_by=approved_by,
            transaction_date=timezone.now(),
        )


def record_payment_collection(loan, amount, recorded_by):
    """Record payment collection - routes to correct vault based on loan type"""
    branch = _get_branch_for_loan(loan, fallback_user=recorded_by)
    if not branch:
        return None
    
    with db_transaction.atomic():
        vault, vault_type = _get_vault_for_loan(loan, branch)
        vault.balance += Decimal(str(amount))
        vault.last_transaction_date = timezone.now()
        vault.total_inflows += Decimal(str(amount))
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_inflows', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='payment_collection',
            direction='in',
            branch=branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=vault.balance,
            description=f'Loan repayment for {loan.application_number} ({vault_type} vault)',
            reference_number=_ref(),
            loan=loan,
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )


def record_capital_injection(branch, amount, notes, recorded_by, vault_type='weekly'):
    """Admin injects capital - must specify vault type"""
    with db_transaction.atomic():
        vault = _get_vault_by_type(branch, vault_type)
        vault.balance += Decimal(str(amount))
        vault.last_transaction_date = timezone.now()
        vault.total_inflows += Decimal(str(amount))
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_inflows', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='capital_injection',
            direction='in',
            branch=branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=vault.balance,
            description=notes or f'Capital injection by {recorded_by.get_full_name()} to {vault_type} vault',
            reference_number=_ref(),
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )


def get_vault_balance(branch, vault_type=None):
    """
    Return vault balance.
    If vault_type specified, return that vault's balance.
    If not specified, return total of both vaults.
    """
    try:
        from .models import DailyVault, WeeklyVault
        
        if vault_type == 'daily':
            return DailyVault.objects.get(branch=branch).balance
        elif vault_type == 'weekly':
            return WeeklyVault.objects.get(branch=branch).balance
        else:
            # Return total of both vaults
            daily = DailyVault.objects.filter(branch=branch).first()
            weekly = WeeklyVault.objects.filter(branch=branch).first()
            daily_balance = daily.balance if daily else Decimal('0')
            weekly_balance = weekly.balance if weekly else Decimal('0')
            return daily_balance + weekly_balance
    except Exception:
        return Decimal('0')


def get_vault_balances(branch):
    """Return both vault balances as a dict"""
    from .models import DailyVault, WeeklyVault
    
    daily = DailyVault.objects.filter(branch=branch).first()
    weekly = WeeklyVault.objects.filter(branch=branch).first()
    
    return {
        'daily': daily.balance if daily else Decimal('0'),
        'weekly': weekly.balance if weekly else Decimal('0'),
        'total': (daily.balance if daily else Decimal('0')) + (weekly.balance if weekly else Decimal('0')),
        'daily_vault': daily,
        'weekly_vault': weekly,
    }


def record_bank_withdrawal(branch, amount, notes, recorded_by, vault_type='weekly'):
    """Record bank withdrawal - must specify vault type"""
    amount = Decimal(str(amount))
    with db_transaction.atomic():
        vault = _get_vault_by_type(branch, vault_type)
        vault.balance += amount
        vault.last_transaction_date = timezone.now()
        vault.total_inflows += amount
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_inflows', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='bank_withdrawal',
            direction='in',
            branch=branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=vault.balance,
            description=notes or f'Bank withdrawal — K{amount:,.2f} to {vault_type} vault',
            reference_number=_ref(),
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )


def record_fund_deposit(branch, amount, source, notes, recorded_by, vault_type='weekly'):
    """Record fund deposit - must specify vault type"""
    amount = Decimal(str(amount))
    with db_transaction.atomic():
        vault = _get_vault_by_type(branch, vault_type)
        vault.balance += amount
        vault.last_transaction_date = timezone.now()
        vault.total_inflows += amount
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_inflows', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='fund_deposit',
            direction='in',
            branch=branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=vault.balance,
            description=f'Fund deposit — {source}. {notes} ({vault_type} vault)'.strip(),
            reference_number=_ref(),
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )


def record_branch_transfer(from_branch, to_branch, amount, notes, recorded_by, vault_type='weekly'):
    """Transfer funds between branches - must specify vault type"""
    amount = Decimal(str(amount))
    with db_transaction.atomic():
        from_vault = _get_vault_by_type(from_branch, vault_type)
        if from_vault.balance < amount:
            raise ValueError(
                f'Insufficient {vault_type} vault balance in {from_branch.name}. '
                f'Available: K{from_vault.balance:,.2f}'
            )

        to_vault = _get_vault_by_type(to_branch, vault_type)
        ref = _ref()
        from expenses.models import VaultTransaction

        # Deduct from sender
        from_vault.balance -= amount
        from_vault.last_transaction_date = timezone.now()
        from_vault.total_outflows += amount
        from_vault.save(update_fields=['balance', 'last_transaction_date', 'total_outflows', 'updated_at'])
        
        out_tx = VaultTransaction.objects.create(
            transaction_type='branch_transfer_out',
            direction='out',
            branch=from_branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=from_vault.balance,
            description=f'Transfer to {to_branch.name} ({vault_type} vault). {notes}'.strip(),
            reference_number=f'{ref}-OUT',
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )

        # Add to receiver
        to_vault.balance += amount
        to_vault.last_transaction_date = timezone.now()
        to_vault.total_inflows += amount
        to_vault.save(update_fields=['balance', 'last_transaction_date', 'total_inflows', 'updated_at'])
        
        in_tx = VaultTransaction.objects.create(
            transaction_type='branch_transfer_in',
            direction='in',
            branch=to_branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=to_vault.balance,
            description=f'Transfer from {from_branch.name} ({vault_type} vault). {notes}'.strip(),
            reference_number=f'{ref}-IN',
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )

        return out_tx, in_tx


def record_bank_deposit(branch, gross_amount, charges, notes, recorded_by, vault_type='weekly'):
    """Record bank deposit - must specify vault type"""
    gross_amount = Decimal(str(gross_amount))
    charges = Decimal(str(charges or 0))

    with db_transaction.atomic():
        vault = _get_vault_by_type(branch, vault_type)
        from expenses.models import VaultTransaction
        txns = []

        # Gross outflow
        vault.balance -= gross_amount
        vault.last_transaction_date = timezone.now()
        vault.total_outflows += gross_amount
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_outflows', 'updated_at'])
        
        txns.append(VaultTransaction.objects.create(
            transaction_type='bank_deposit_out',
            direction='out',
            branch=branch.name,
            vault_type=vault_type,
            amount=gross_amount,
            balance_after=vault.balance,
            description=notes or f'Bank deposit — K{gross_amount:,.2f} sent to bank from {vault_type} vault',
            reference_number=_ref(),
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        ))

        # Charges outflow
        if charges > 0:
            vault.balance -= charges
            vault.total_outflows += charges
            vault.save(update_fields=['balance', 'total_outflows', 'updated_at'])
            
            txns.append(VaultTransaction.objects.create(
                transaction_type='bank_charges',
                direction='out',
                branch=branch.name,
                vault_type=vault_type,
                amount=charges,
                balance_after=vault.balance,
                description=f'Mobile money / bank deposit charges ({vault_type} vault)',
                reference_number=_ref(),
                recorded_by=recorded_by,
                transaction_date=timezone.now(),
            ))

        return txns


def record_savings_deposit(branch, amount, notes, recorded_by, vault_type='weekly'):
    """Move money from vault to savings - must specify vault type"""
    amount = Decimal(str(amount))
    with db_transaction.atomic():
        vault = _get_vault_by_type(branch, vault_type)
        if vault.balance < amount:
            raise ValueError(
                f'Insufficient {vault_type} vault balance. Available: K{vault.balance:,.2f}'
            )
        
        from loans.models import BranchSavings
        savings, _ = BranchSavings.objects.get_or_create(branch=branch)
        
        vault.balance -= amount
        vault.last_transaction_date = timezone.now()
        vault.total_outflows += amount
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_outflows', 'updated_at'])
        
        savings.balance += amount
        savings.save(update_fields=['balance', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='savings_deposit',
            direction='out',
            branch=branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=vault.balance,
            description=notes or f'Savings deposit — K{amount:,.2f} from {vault_type} vault',
            reference_number=_ref(),
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )


def record_savings_withdrawal(branch, amount, notes, recorded_by, vault_type='weekly'):
    """Move money from savings to vault - must specify vault type"""
    amount = Decimal(str(amount))
    with db_transaction.atomic():
        from loans.models import BranchSavings
        savings, _ = BranchSavings.objects.get_or_create(branch=branch)
        if savings.balance < amount:
            raise ValueError(f'Insufficient savings balance. Available: K{savings.balance:,.2f}')
        
        vault = _get_vault_by_type(branch, vault_type)
        
        savings.balance -= amount
        savings.save(update_fields=['balance', 'updated_at'])
        
        vault.balance += amount
        vault.last_transaction_date = timezone.now()
        vault.total_inflows += amount
        vault.save(update_fields=['balance', 'last_transaction_date', 'total_inflows', 'updated_at'])
        
        from expenses.models import VaultTransaction
        return VaultTransaction.objects.create(
            transaction_type='savings_withdrawal',
            direction='in',
            branch=branch.name,
            vault_type=vault_type,
            amount=amount,
            balance_after=vault.balance,
            description=notes or f'Savings withdrawal — K{amount:,.2f} to {vault_type} vault',
            reference_number=_ref(),
            recorded_by=recorded_by,
            transaction_date=timezone.now(),
        )
