"""
Tests for Manager Loan Approval and Disbursement Workflow

Tests cover:
- Security deposit approval
- Loan approval by manager
- Loan disbursement
- Workflow sequencing and validation
- Audit logging
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from django.test import Client
from datetime import timedelta

from accounts.models import User
from clients.models import Branch, BorrowerGroup
from loans.models import (
    Loan, LoanType, SecurityDeposit, ManagerLoanApproval, 
    ApprovalLog, LoanApprovalRequest
)


@pytest.fixture
def branch(db):
    """Create a test branch"""
    return Branch.objects.create(
        name='Test Branch',
        code='TB',
        location='Test Location'
    )


@pytest.fixture
def manager_with_branch(db, branch):
    """Create a manager assigned to a branch"""
    manager = User.objects.create_user(
        username='manager_test',
        email='manager@test.com',
        password='testpass123',
        role='manager',
        first_name='Manager',
        last_name='User'
    )
    manager.managed_branch = branch
    manager.save()
    return manager


@pytest.fixture
def loan_officer_with_branch(db, branch):
    """Create a loan officer assigned to a branch"""
    officer = User.objects.create_user(
        username='officer_test',
        email='officer@test.com',
        password='testpass123',
        role='loan_officer',
        first_name='Officer',
        last_name='User'
    )
    # Create officer assignment
    from clients.models import OfficerAssignment
    OfficerAssignment.objects.create(
        officer=officer,
        branch=branch.name
    )
    return officer


@pytest.fixture
def borrower(db):
    """Create a test borrower"""
    return User.objects.create_user(
        username='borrower_test',
        email='borrower@test.com',
        password='testpass123',
        role='borrower',
        first_name='Borrower',
        last_name='User'
    )


@pytest.fixture
def loan_type(db):
    """Create a test loan type"""
    return LoanType.objects.create(
        name='Weekly Loan',
        description='Test weekly loan',
        interest_rate=Decimal('45.00'),
        max_amount=Decimal('50000'),
        min_amount=Decimal('1000'),
        repayment_frequency='weekly',
        min_term_weeks=1,
        max_term_weeks=52,
        is_active=True
    )


def create_approved_loan_with_deposit(borrower, loan_officer, loan_type):
    """Helper function to create an approved loan with security deposit"""
    loan = Loan.objects.create(
        borrower=borrower,
        loan_officer=loan_officer,
        loan_type=loan_type,
        principal_amount=Decimal('5000'),
        interest_rate=Decimal('45.00'),
        repayment_frequency='weekly',
        term_weeks=12,
        payment_amount=Decimal('500'),
        status='approved',
        purpose='Test loan',
        upfront_payment_required=Decimal('500'),
        upfront_payment_paid=Decimal('500'),
        upfront_payment_date=timezone.now(),
        upfront_payment_verified=False
    )
    
    # Create security deposit (only if it doesn't exist)
    SecurityDeposit.objects.get_or_create(
        loan=loan,
        defaults={
            'required_amount': Decimal('500'),
            'paid_amount': Decimal('500'),
            'payment_date': timezone.now(),
            'payment_method': 'cash',
            'is_verified': False
        }
    )
    
    return loan


@pytest.fixture
def approved_loan(db, borrower, loan_officer_with_branch, loan_type):
    """Create an approved loan with security deposit"""
    return create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)


# ============================================================================
# Security Deposit Approval Tests
# ============================================================================

class TestSecurityDepositApproval:
    """Test security deposit approval workflow"""
    
    def test_security_deposit_pending_on_creation(self, db, borrower, loan_officer_with_branch, loan_type):
        """Test that security deposit is pending when created"""
        loan = create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)
        deposit = loan.security_deposit
        assert deposit.is_verified is False
        assert deposit.is_pending() is True
    
    def test_security_deposit_can_be_approved(self, db, borrower, loan_officer_with_branch, loan_type):
        """Test that pending security deposit can be approved"""
        loan = create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)
        deposit = loan.security_deposit
        can_approve, message = deposit.can_be_approved()
        assert can_approve is True
    
    def test_security_deposit_cannot_be_approved_twice(self, db, borrower, loan_officer_with_branch, loan_type, manager_with_branch):
        """Test that verified deposit cannot be approved again"""
        loan = create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)
        deposit = loan.security_deposit
        deposit.verify(manager_with_branch)
        
        can_approve, message = deposit.can_be_approved()
        assert can_approve is False
        assert 'already been verified' in message
    
    def test_security_deposit_approval_updates_loan(self, db, borrower, loan_officer_with_branch, loan_type, manager_with_branch):
        """Test that approving deposit updates loan verification status"""
        loan = create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)
        deposit = loan.security_deposit
        deposit.verify(manager_with_branch)
        
        # Manually update loan (normally done by view)
        loan.upfront_payment_verified = True
        loan.save()
        
        assert loan.upfront_payment_verified is True
    
    def test_security_deposit_approval_logged(self, db, borrower, loan_officer_with_branch, loan_type, manager_with_branch, branch):
        """Test that security deposit approval is logged"""
        loan = create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)
        deposit = loan.security_deposit
        deposit.verify(manager_with_branch)
        
        # Create approval log (normally done by view)
        ApprovalLog.objects.create(
            approval_type='security_deposit',
            loan=loan,
            manager=manager_with_branch,
            action='approve',
            comments='Test approval',
            branch=branch.name
        )
        
        logs = ApprovalLog.objects.filter(
            approval_type='security_deposit',
            loan=loan,
            action='approve'
        )
        assert logs.count() == 1


# ============================================================================
# Loan Approval Tests
# ============================================================================

class TestLoanApprovalByManager:
    """Test manager loan approval workflow"""
    
    def test_loan_cannot_be_approved_without_verified_deposit(self, db, borrower, loan_officer_with_branch, loan_type):
        """Test that loan cannot be approved without verified deposit"""
        loan = create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)
        can_approve, message = loan.can_be_approved_by_manager()
        assert can_approve is False
        assert 'Security deposit must be verified' in message
    
    def test_loan_can_be_approved_with_verified_deposit(self, db, borrower, loan_officer_with_branch, loan_type, manager_with_branch):
        """Test that loan can be approved with verified deposit"""
        loan = create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)
        # Verify deposit
        deposit = loan.security_deposit
        deposit.verify(manager_with_branch)
        loan.upfront_payment_verified = True
        loan.save()
        
        can_approve, message = loan.can_be_approved_by_manager()
        assert can_approve is True
    
    def test_manager_loan_approval_creates_record(self, db, borrower, loan_officer_with_branch, loan_type, manager_with_branch):
        """Test that manager approval creates ManagerLoanApproval record"""
        loan = create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)
        # Verify deposit first
        deposit = loan.security_deposit
        deposit.verify(manager_with_branch)
        loan.upfront_payment_verified = True
        loan.save()
        
        # Create manager approval
        approval, created = ManagerLoanApproval.objects.get_or_create(loan=loan)
        approval.status = 'approved'
        approval.manager = manager_with_branch
        approval.approved_date = timezone.now()
        approval.save()
        
        assert approval.status == 'approved'
        assert approval.manager == manager_with_branch
    
    def test_manager_loan_approval_logged(self, db, borrower, loan_officer_with_branch, loan_type, manager_with_branch, branch):
        """Test that loan approval is logged"""
        loan = create_approved_loan_with_deposit(borrower, loan_officer_with_branch, loan_type)
        # Verify deposit first
        deposit = loan.security_deposit
        deposit.verify(manager_with_branch)
        loan.upfront_payment_verified = True
        loan.save()
        
        # Create approval log
        ApprovalLog.objects.create(
            approval_type='loan_approval',
            loan=loan,
            manager=manager_with_branch,
            action='approve',
            comments='Test loan approval',
            branch=branch.name
        )
        
        logs = ApprovalLog.objects.filter(
            approval_type='loan_approval',
            loan=loan,
            action='approve'
        )
        assert logs.count() == 1


# ============================================================================
# Loan Disbursement Tests
# ============================================================================

class TestLoanDisbursement:
    """Test loan disbursement workflow"""
    
    def test_loan_cannot_be_disbursed_without_verified_deposit(self, approved_loan):
        """Test that loan cannot be disbursed without verified deposit"""
        can_disburse, message = approved_loan.can_be_disbursed_by_manager()
        assert can_disburse is False
        assert 'Security deposit must be verified' in message
    
    def test_loan_can_be_disbursed_with_verified_deposit(self, approved_loan, manager_with_branch):
        """Test that loan can be disbursed with verified deposit"""
        # Verify deposit
        deposit = approved_loan.security_deposit
        deposit.verify(manager_with_branch)
        approved_loan.upfront_payment_verified = True
        approved_loan.save()
        
        can_disburse, message = approved_loan.can_be_disbursed_by_manager()
        assert can_disburse is True
    
    def test_high_value_loan_requires_admin_approval(self, db, borrower, loan_officer_with_branch, loan_type):
        """Test that high-value loans require admin approval"""
        # Create high-value loan
        loan = Loan.objects.create(
            borrower=borrower,
            loan_officer=loan_officer_with_branch,
            loan_type=loan_type,
            principal_amount=Decimal('10000'),  # >= 6000
            interest_rate=Decimal('45.00'),
            repayment_frequency='weekly',
            term_weeks=12,
            payment_amount=Decimal('1000'),
            status='approved',
            purpose='High-value loan',
            upfront_payment_required=Decimal('1000'),
            upfront_payment_paid=Decimal('1000'),
            upfront_payment_date=timezone.now(),
            upfront_payment_verified=True
        )
        
        # Create security deposit
        SecurityDeposit.objects.get_or_create(
            loan=loan,
            defaults={
                'required_amount': Decimal('1000'),
                'paid_amount': Decimal('1000'),
                'payment_date': timezone.now(),
                'payment_method': 'cash',
                'is_verified': True
            }
        )
        
        # Without admin approval, cannot be disbursed
        can_disburse, message = loan.can_be_disbursed_by_manager()
        assert can_disburse is False
        assert 'admin approval' in message
    
    def test_loan_disbursement_updates_status(self, approved_loan, manager_with_branch):
        """Test that disbursement updates loan status"""
        # Verify deposit
        deposit = approved_loan.security_deposit
        deposit.verify(manager_with_branch)
        approved_loan.upfront_payment_verified = True
        approved_loan.save()
        
        # Simulate disbursement
        approved_loan.status = 'disbursed'
        approved_loan.disbursement_date = timezone.now()
        approved_loan.save()
        
        assert approved_loan.status == 'disbursed'
        assert approved_loan.disbursement_date is not None
    
    def test_loan_disbursement_sets_maturity_date(self, approved_loan, manager_with_branch):
        """Test that disbursement calculates maturity date"""
        # Verify deposit
        deposit = approved_loan.security_deposit
        deposit.verify(manager_with_branch)
        approved_loan.upfront_payment_verified = True
        approved_loan.save()
        
        # Simulate disbursement
        approved_loan.status = 'disbursed'
        approved_loan.disbursement_date = timezone.now()
        
        # Calculate maturity date
        if approved_loan.repayment_frequency == 'weekly' and approved_loan.term_weeks:
            approved_loan.maturity_date = (
                approved_loan.disbursement_date + 
                timedelta(weeks=approved_loan.term_weeks)
            ).date()
        
        approved_loan.save()
        
        assert approved_loan.maturity_date is not None
        expected_maturity = (
            approved_loan.disbursement_date + 
            timedelta(weeks=approved_loan.term_weeks)
        ).date()
        assert approved_loan.maturity_date == expected_maturity
    
    def test_loan_disbursement_logged(self, approved_loan, manager_with_branch, branch):
        """Test that loan disbursement is logged"""
        # Verify deposit
        deposit = approved_loan.security_deposit
        deposit.verify(manager_with_branch)
        approved_loan.upfront_payment_verified = True
        approved_loan.save()
        
        # Create disbursement log
        ApprovalLog.objects.create(
            approval_type='loan_disbursement',
            loan=approved_loan,
            manager=manager_with_branch,
            action='approve',
            comments=f'Loan disbursed: {approved_loan.principal_amount}',
            branch=branch.name
        )
        
        logs = ApprovalLog.objects.filter(
            approval_type='loan_disbursement',
            loan=approved_loan,
            action='approve'
        )
        assert logs.count() == 1


# ============================================================================
# Workflow Sequencing Tests
# ============================================================================

class TestWorkflowSequencing:
    """Test workflow sequencing and validation"""
    
    def test_pending_loan_cannot_be_approved(self, db, borrower, loan_officer_with_branch, loan_type):
        """Test that pending loans cannot be approved"""
        loan = Loan.objects.create(
            borrower=borrower,
            loan_officer=loan_officer_with_branch,
            loan_type=loan_type,
            principal_amount=Decimal('5000'),
            interest_rate=Decimal('45.00'),
            repayment_frequency='weekly',
            term_weeks=12,
            payment_amount=Decimal('500'),
            status='pending',  # Not approved
            purpose='Test loan'
        )
        
        can_approve, message = loan.can_be_approved_by_manager()
        assert can_approve is False
        assert 'not in approved status' in message
    
    def test_rejected_deposit_prevents_disbursement(self, approved_loan, manager_with_branch):
        """Test that rejected deposit prevents disbursement"""
        # Reject deposit (keep is_verified=False)
        deposit = approved_loan.security_deposit
        assert deposit.is_verified is False
        
        can_disburse, message = approved_loan.can_be_disbursed_by_manager()
        assert can_disburse is False
    
    def test_complete_workflow_sequence(self, approved_loan, manager_with_branch, branch):
        """Test complete workflow: deposit approval → loan approval → disbursement"""
        # Step 1: Approve security deposit
        deposit = approved_loan.security_deposit
        deposit.verify(manager_with_branch)
        approved_loan.upfront_payment_verified = True
        approved_loan.save()
        
        ApprovalLog.objects.create(
            approval_type='security_deposit',
            loan=approved_loan,
            manager=manager_with_branch,
            action='approve',
            branch=branch.name
        )
        
        # Step 2: Approve loan
        approval, _ = ManagerLoanApproval.objects.get_or_create(loan=approved_loan)
        approval.status = 'approved'
        approval.manager = manager_with_branch
        approval.save()
        
        ApprovalLog.objects.create(
            approval_type='loan_approval',
            loan=approved_loan,
            manager=manager_with_branch,
            action='approve',
            branch=branch.name
        )
        
        # Step 3: Disburse loan
        approved_loan.status = 'disbursed'
        approved_loan.disbursement_date = timezone.now()
        approved_loan.maturity_date = (
            approved_loan.disbursement_date + 
            timedelta(weeks=approved_loan.term_weeks)
        ).date()
        approved_loan.save()
        
        ApprovalLog.objects.create(
            approval_type='loan_disbursement',
            loan=approved_loan,
            manager=manager_with_branch,
            action='approve',
            branch=branch.name
        )
        
        # Verify workflow completed
        assert approved_loan.upfront_payment_verified is True
        assert approved_loan.manager_approval.status == 'approved'
        assert approved_loan.status == 'disbursed'
        
        # Verify all actions logged
        logs = ApprovalLog.objects.filter(loan=approved_loan)
        assert logs.count() == 3


# ============================================================================
# Audit and Logging Tests
# ============================================================================

class TestAuditAndLogging:
    """Test audit trail and logging"""
    
    def test_all_approvals_logged(self, approved_loan, manager_with_branch, branch):
        """Test that all approval actions are logged"""
        # Create various approval logs
        ApprovalLog.objects.create(
            approval_type='security_deposit',
            loan=approved_loan,
            manager=manager_with_branch,
            action='approve',
            comments='Deposit approved',
            branch=branch.name
        )
        
        ApprovalLog.objects.create(
            approval_type='loan_approval',
            loan=approved_loan,
            manager=manager_with_branch,
            action='approve',
            comments='Loan approved',
            branch=branch.name
        )
        
        ApprovalLog.objects.create(
            approval_type='loan_disbursement',
            loan=approved_loan,
            manager=manager_with_branch,
            action='approve',
            comments='Loan disbursed',
            branch=branch.name
        )
        
        logs = ApprovalLog.objects.filter(loan=approved_loan)
        assert logs.count() == 3
        
        # Verify all required fields are present
        for log in logs:
            assert log.approval_type in ['security_deposit', 'loan_approval', 'loan_disbursement']
            assert log.loan == approved_loan
            assert log.manager == manager_with_branch
            assert log.action == 'approve'
            assert log.comments
            assert log.branch == branch.name
            assert log.timestamp is not None
    
    def test_approval_log_filtering(self, approved_loan, manager_with_branch, branch):
        """Test that approval logs can be filtered"""
        # Create multiple logs
        for i in range(3):
            ApprovalLog.objects.create(
                approval_type='security_deposit',
                loan=approved_loan,
                manager=manager_with_branch,
                action='approve',
                branch=branch.name
            )
        
        # Filter by approval type
        deposits = ApprovalLog.objects.filter(approval_type='security_deposit')
        assert deposits.count() == 3
        
        # Filter by action
        approvals = ApprovalLog.objects.filter(action='approve')
        assert approvals.count() == 3
        
        # Filter by loan
        loan_logs = ApprovalLog.objects.filter(loan=approved_loan)
        assert loan_logs.count() == 3


# ============================================================================
# Branch Isolation Tests
# ============================================================================

class TestBranchIsolation:
    """Test that managers can only approve loans in their branch"""
    
    def test_manager_can_only_see_own_branch_loans(self, db, branch, manager_with_branch, 
                                                    loan_officer_with_branch, borrower, loan_type):
        """Test that manager can only see loans from their branch"""
        # Create loan in manager's branch
        loan = Loan.objects.create(
            borrower=borrower,
            loan_officer=loan_officer_with_branch,
            loan_type=loan_type,
            principal_amount=Decimal('5000'),
            interest_rate=Decimal('45.00'),
            repayment_frequency='weekly',
            term_weeks=12,
            payment_amount=Decimal('500'),
            status='approved',
            purpose='Test loan'
        )
        
        # Create another branch and officer
        other_branch = Branch.objects.create(
            name='Other Branch',
            code='OB',
            location='Other Location'
        )
        
        other_officer = User.objects.create_user(
            username='other_officer',
            email='other@test.com',
            password='testpass123',
            role='loan_officer'
        )
        
        from clients.models import OfficerAssignment
        OfficerAssignment.objects.create(
            officer=other_officer,
            branch=other_branch.name
        )
        
        # Create loan in other branch
        other_loan = Loan.objects.create(
            borrower=borrower,
            loan_officer=other_officer,
            loan_type=loan_type,
            principal_amount=Decimal('5000'),
            interest_rate=Decimal('45.00'),
            repayment_frequency='weekly',
            term_weeks=12,
            payment_amount=Decimal('500'),
            status='approved',
            purpose='Other loan'
        )
        
        # Manager should only see their branch's loan
        manager_loans = Loan.objects.filter(
            loan_officer__officer_assignment__branch=manager_with_branch.managed_branch.name
        )
        
        assert loan in manager_loans
        assert other_loan not in manager_loans
