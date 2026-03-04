"""
Property-based tests for Expense and VaultTransaction models
Feature: loan-officer-group-management
"""
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from hypothesis.extra.django import from_model
from decimal import Decimal
from datetime import date, datetime
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from expenses.models import Expense, VaultTransaction, ExpenseCategory
from accounts.models import User


# Hypothesis strategies for generating test data
@st.composite
def expense_data(draw):
    """Generate valid expense data"""
    return {
        'title': draw(st.text(min_size=1, max_size=200)),
        'description': draw(st.text(min_size=1, max_size=500)),
        'amount': draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('1000000'), places=2)),
        'branch': draw(st.text(min_size=1, max_size=100)),
        'expense_date': draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))),
    }


@st.composite
def vault_transaction_data(draw):
    """Generate valid vault transaction data"""
    return {
        'transaction_type': draw(st.sampled_from(['deposit', 'withdrawal', 'transfer', 'loan_disbursement', 'payment_collection'])),
        'branch': draw(st.text(min_size=1, max_size=100)),
        'amount': draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('1000000'), places=2)),
        'description': draw(st.text(min_size=1, max_size=500)),
        'reference_number': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'transaction_date': draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31))),
    }


@pytest.mark.django_db
@pytest.mark.property
class TestExpenseProperties:
    """Property-based tests for Expense model"""
    
    # Feature: loan-officer-group-management, Property 21: Expense required fields validation
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(data=expense_data())
    def test_expense_requires_all_mandatory_fields(self, data, manager_user):
        """
        For any expense creation attempt, if any required field 
        (category, amount, date, description) is missing, the creation should be rejected
        
        Validates: Requirements 7.1
        """
        # Create a category for the expense
        category, _ = ExpenseCategory.objects.get_or_create(name='Test Category')
        
        # Test with all fields present - should succeed
        expense = Expense(
            category=category,
            title=data['title'],
            description=data['description'],
            amount=data['amount'],
            branch=data['branch'],
            expense_date=data['expense_date'],
            recorded_by=manager_user
        )
        expense.full_clean()  # Should not raise
        expense.save()
        assert expense.pk is not None
        
        # Test missing amount - should fail
        with pytest.raises((ValidationError, IntegrityError)):
            expense_no_amount = Expense(
                category=category,
                title=data['title'],
                description=data['description'],
                amount=None,  # Missing required field
                branch=data['branch'],
                expense_date=data['expense_date'],
                recorded_by=manager_user
            )
            expense_no_amount.full_clean()
            expense_no_amount.save()
        
        # Test missing expense_date - should fail
        with pytest.raises((ValidationError, IntegrityError)):
            expense_no_date = Expense(
                category=category,
                title=data['title'],
                description=data['description'],
                amount=data['amount'],
                branch=data['branch'],
                expense_date=None,  # Missing required field
                recorded_by=manager_user
            )
            expense_no_date.full_clean()
            expense_no_date.save()
        
        # Test missing description - should fail
        with pytest.raises((ValidationError, IntegrityError)):
            expense_no_desc = Expense(
                category=category,
                title=data['title'],
                description='',  # Empty required field
                amount=data['amount'],
                branch=data['branch'],
                expense_date=data['expense_date'],
                recorded_by=manager_user
            )
            expense_no_desc.full_clean()
            expense_no_desc.save()


@pytest.mark.django_db
@pytest.mark.property
class TestVaultTransactionProperties:
    """Property-based tests for VaultTransaction model"""
    
    # Feature: loan-officer-group-management, Property 25: Vault transaction required fields validation
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(data=vault_transaction_data())
    def test_vault_transaction_requires_all_mandatory_fields(self, data, manager_user):
        """
        For any vault transaction creation attempt, if any required field 
        (transaction_type, amount, source_branch, date) is missing, the creation should be rejected
        
        Validates: Requirements 8.1
        """
        # Test with all fields present - should succeed
        transaction = VaultTransaction(
            transaction_type=data['transaction_type'],
            branch=data['branch'],
            amount=data['amount'],
            description=data['description'],
            reference_number=data['reference_number'],
            transaction_date=data['transaction_date'],
            recorded_by=manager_user
        )
        transaction.full_clean()  # Should not raise
        transaction.save()
        assert transaction.pk is not None
        
        # Test missing transaction_type - should fail
        with pytest.raises((ValidationError, IntegrityError)):
            trans_no_type = VaultTransaction(
                transaction_type='',  # Missing required field
                branch=data['branch'],
                amount=data['amount'],
                description=data['description'],
                reference_number=data['reference_number'] + '_2',
                transaction_date=data['transaction_date'],
                recorded_by=manager_user
            )
            trans_no_type.full_clean()
            trans_no_type.save()
        
        # Test missing amount - should fail
        with pytest.raises((ValidationError, IntegrityError)):
            trans_no_amount = VaultTransaction(
                transaction_type=data['transaction_type'],
                branch=data['branch'],
                amount=None,  # Missing required field
                description=data['description'],
                reference_number=data['reference_number'] + '_3',
                transaction_date=data['transaction_date'],
                recorded_by=manager_user
            )
            trans_no_amount.full_clean()
            trans_no_amount.save()
        
        # Test missing branch - should fail
        with pytest.raises((ValidationError, IntegrityError)):
            trans_no_branch = VaultTransaction(
                transaction_type=data['transaction_type'],
                branch='',  # Missing required field
                amount=data['amount'],
                description=data['description'],
                reference_number=data['reference_number'] + '_4',
                transaction_date=data['transaction_date'],
                recorded_by=manager_user
            )
            trans_no_branch.full_clean()
            trans_no_branch.save()
        
        # Test missing transaction_date - should fail
        with pytest.raises((ValidationError, IntegrityError)):
            trans_no_date = VaultTransaction(
                transaction_type=data['transaction_type'],
                branch=data['branch'],
                amount=data['amount'],
                description=data['description'],
                reference_number=data['reference_number'] + '_5',
                transaction_date=None,  # Missing required field
                recorded_by=manager_user
            )
            trans_no_date.full_clean()
            trans_no_date.save()
    
    # Feature: loan-officer-group-management, Property 26: Vault transaction amount validation
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        amount=st.decimals(min_value=Decimal('-1000000'), max_value=Decimal('-0.01'), places=2),
        data=vault_transaction_data()
    )
    def test_vault_transaction_amount_must_be_positive(self, amount, data, manager_user):
        """
        For any vault transaction, the amount must be positive (greater than zero)
        
        Validates: Requirements 8.2
        """
        # Test with negative amount - should fail
        with pytest.raises((ValidationError, IntegrityError)):
            transaction = VaultTransaction(
                transaction_type=data['transaction_type'],
                branch=data['branch'],
                amount=amount,  # Negative amount
                description=data['description'],
                reference_number=data['reference_number'],
                transaction_date=data['transaction_date'],
                recorded_by=manager_user
            )
            transaction.full_clean()
            transaction.save()
        
        # Test with zero amount - should fail
        with pytest.raises((ValidationError, IntegrityError)):
            transaction_zero = VaultTransaction(
                transaction_type=data['transaction_type'],
                branch=data['branch'],
                amount=Decimal('0.00'),  # Zero amount
                description=data['description'],
                reference_number=data['reference_number'] + '_zero',
                transaction_date=data['transaction_date'],
                recorded_by=manager_user
            )
            transaction_zero.full_clean()
            transaction_zero.save()
