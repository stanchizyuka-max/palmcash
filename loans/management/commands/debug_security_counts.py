from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from loans.models import Loan, SecurityTransaction
from django.db.models import Q

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug security transaction counts for managers'

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUGGING SECURITY TRANSACTION COUNTS ===\n")
        
        # Get all managers
        managers = User.objects.filter(role='manager')
        self.stdout.write(f"Found {managers.count()} manager(s):")
        for mgr in managers:
            self.stdout.write(f"  - {mgr.first_name} {mgr.last_name} (ID: {mgr.id})")
        
        if not managers.exists():
            self.stdout.write("❌ No managers found")
            return
        
        # Use first manager for testing
        manager = managers.first()
        self.stdout.write(f"\nTesting with manager: {manager.first_name} {manager.last_name}")
        
        # Try to get manager's branch
        try:
            branch = manager.managed_branch
            self.stdout.write(f"Manager's branch: {branch.name}")
        except Exception as e:
            self.stdout.write(f"❌ Manager has no branch: {e}")
            # For testing, let's check all loans
            branch = None
        
        # Get loans (same logic as manager_dashboard)
        if branch:
            # Get all officers in this branch
            branch_officers = User.objects.filter(
                role='loan_officer',
                officer_assignment__branch=branch.name
            ).values_list('id', flat=True)
            
            self.stdout.write(f"Branch officers: {list(branch_officers)}")
            
            # Get loans from officers in this branch
            loans = Loan.objects.filter(
                Q(loan_officer_id__in=branch_officers) | 
                Q(borrower__group_memberships__group__branch=branch.name) |
                Q(borrower__group_memberships__group__assigned_officer__officer_assignment__branch=branch.name)
            ).distinct()
        else:
            # Check all loans for debugging
            loans = Loan.objects.all()
        
        self.stdout.write(f"\nTotal loans found: {loans.count()}")
        
        # Check security transactions
        all_security_txns = SecurityTransaction.objects.all()
        self.stdout.write(f"Total security transactions: {all_security_txns.count()}")
        
        pending_security_txns = SecurityTransaction.objects.filter(status='pending')
        self.stdout.write(f"Total pending security transactions: {pending_security_txns.count()}")
        
        # Check by loan IDs
        loan_ids = list(loans.values_list('id', flat=True))
        self.stdout.write(f"Loan IDs: {loan_ids[:10]}...")  # Show first 10
        
        # Pending security transactions by type (same logic as manager_dashboard)
        pending_sec_qs = SecurityTransaction.objects.filter(
            loan_id__in=loan_ids,
            status='pending',
        )
        
        self.stdout.write(f"\nPending security transactions for manager's loans: {pending_sec_qs.count()}")
        
        # Break down by type
        pending_returns = pending_sec_qs.filter(transaction_type='return').count()
        pending_adjustments = pending_sec_qs.filter(transaction_type='adjustment').count()
        pending_withdrawals = pending_sec_qs.filter(transaction_type='withdrawal').count()
        pending_carry_forwards = pending_sec_qs.filter(transaction_type='carry_forward').count()
        
        self.stdout.write(f"\n📊 BREAKDOWN BY TYPE:")
        self.stdout.write(f"  - Returns: {pending_returns}")
        self.stdout.write(f"  - Adjustments: {pending_adjustments}")
        self.stdout.write(f"  - Withdrawals: {pending_withdrawals}")
        self.stdout.write(f"  - Carry Forwards: {pending_carry_forwards}")
        self.stdout.write(f"  - Total: {pending_returns + pending_adjustments + pending_withdrawals + pending_carry_forwards}")
        
        # Show actual pending transactions
        if pending_sec_qs.exists():
            self.stdout.write(f"\n🔍 ACTUAL PENDING TRANSACTIONS:")
            for txn in pending_sec_qs[:5]:  # Show first 5
                self.stdout.write(f"  - ID: {txn.id}, Type: {txn.transaction_type}, Amount: K{txn.amount}, Loan: {txn.loan.application_number}")
        else:
            self.stdout.write(f"\n❌ NO PENDING TRANSACTIONS FOUND")
            
            # Check if there are any security transactions at all for these loans
            all_txns_for_loans = SecurityTransaction.objects.filter(loan_id__in=loan_ids)
            self.stdout.write(f"Total security transactions for these loans: {all_txns_for_loans.count()}")
            
            if all_txns_for_loans.exists():
                self.stdout.write(f"Sample transactions:")
                for txn in all_txns_for_loans[:3]:
                    self.stdout.write(f"  - ID: {txn.id}, Type: {txn.transaction_type}, Status: {txn.status}, Amount: K{txn.amount}")
        
        # Check top-up requests separately
        from loans.models import SecurityTopUpRequest
        pending_topups = SecurityTopUpRequest.objects.filter(
            loan_id__in=loan_ids,
            status='pending'
        )
        self.stdout.write(f"\n📋 TOP-UP REQUESTS:")
        self.stdout.write(f"  - Pending top-ups: {pending_topups.count()}")
        
        if pending_topups.exists():
            for req in pending_topups:
                self.stdout.write(f"    - ID: {req.id}, Amount: K{req.requested_amount}, Loan: {req.loan.application_number}, Officer: {req.requested_by}")
        
        self.stdout.write("\n=== DEBUG COMPLETE ===")