"""
Pytest configuration and fixtures for PalmCash testing
"""
import pytest
from hypothesis import settings

# Configure Hypothesis settings
settings.register_profile("default", max_examples=100, deadline=None)
settings.load_profile("default")


@pytest.fixture
def api_client():
    """Fixture for Django test client"""
    from django.test import Client
    return Client()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing"""
    from accounts.models import User
    return User.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        password='testpass123',
        role='admin',
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def manager_user(db):
    """Create a manager user for testing"""
    from accounts.models import User
    return User.objects.create_user(
        username='manager_test',
        email='manager@test.com',
        password='testpass123',
        role='manager',
        first_name='Manager',
        last_name='User'
    )


@pytest.fixture
def loan_officer_user(db):
    """Create a loan officer user for testing"""
    from accounts.models import User
    return User.objects.create_user(
        username='officer_test',
        email='officer@test.com',
        password='testpass123',
        role='loan_officer',
        first_name='Officer',
        last_name='User'
    )


@pytest.fixture
def borrower_user(db):
    """Create a borrower user for testing"""
    from accounts.models import User
    return User.objects.create_user(
        username='borrower_test',
        email='borrower@test.com',
        password='testpass123',
        role='borrower',
        first_name='Borrower',
        last_name='User'
    )
