from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from loans.models import Loan, SecurityTransaction
from clients.models import BorrowerGroup
from django.db.models import Sum

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug the K200 carry forward transaction in Falcon group'

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUGGING K200 CARRY FORWARD ===\n")
        
        # Find Falcon group
        try:
            falcon_group = BorrowerGroup.objects.get(name__icontains='falcon')
            self.stdout.write(f"✓ Found group: {falcon_group.name}")
        except BorrowerGroup.DoesNotExist:
            self.stdout.write("❌ Falcon group not found")
            return
        
        # Get loans for Falcon group members
        falcon_loans = Loan.objects.filter(
            borrower__group_memberships__group=falcon_group,
            borrower__group_memberships__is_active=True
        ).distinct()
        
        self.stdout.write(f"✓ Falcon group loans:")
        for loan in falcon_loans:
            self.stdout.write(f"  - {loan.application_number}: {loan.borrower.full_name}")
        
        # Find ALL carry forward transactions for these loans
        carry_forward_txns = SecurityTransaction.objects.filter(
            loan__in=falcon_loans,
            transaction_type='carry_forward'
        ).order_by('created_at')
        
        self.stdout.write(f"\n🔍 ALL CARRY FORWARD TRANSACTIONS ({carry_forward_txns.count()}):")
        
        if not carry_forward_txns.exists():
            self.stdout.write("❌ No carry forward transactions found")
            return
        
        total_carry_forwards = 0
        for txn in carry_forward_txns:
            self.stdout.write(f"\n📋 Transaction ID: {txn.id}")
            self.stdout.write(f"  - Loan: {txn.loan.application_number} ({txn.loan.borrower.full_name})")
            self.stdout.write(f"  - Amount: K{txn.amount}")
            self.stdout.write(f"  - Status: {txn.status}")
            self.stdout.write(f"  - Created: {txn.created_at}")
            self.stdout.write(f"  - Initiated by: {txn.initiated_by}")
            self.stdout.write(f"  - Approved by: {txn.approved_by}")
            self.stdout.write(f"  - Notes: {txn.notes}")
            
            if txn.status == 'approved':
                total_carry_forwards += txn.amount
        
        self.stdout.write(f"\n💰 TOTAL APPROVED CARRY FORWARDS: K{total_carry_forwards}")
        
        # Check if there are any pending carry forwards
        pending_carry_forwards = carry_forward_txns.filter(status='pending')
        if pending_carry_forwards.exists():
            self.stdout.write(f"\n⏳ PENDING CARRY FORWARDS ({pending_carry_forwards.count()}):")
            for txn in pending_carry_forwards:
                self.stdout.write(f"  - ID {txn.id}: K{txn.amount} for {txn.loan.application_number}")
        
        # Check rejected carry forwards
        rejected_carry_forwards = carry_forward_txns.filter(status='rejected')
        if rejected_carry_forwards.exists():
            self.stdout.write(f"\n❌ REJECTED CARRY FORWARDS ({rejected_carry_forwards.count()}):")
            for txn in rejected_carry_forwards:
                self.stdout.write(f"  - ID {txn.id}: K{txn.amount} for {txn.loan.application_number}")
        
        # Show transaction history for context
        self.stdout.write(f"\n📚 TRANSACTION CONTEXT:")
        self.stdout.write("Carry forwards typically happen when:")
        self.stdout.write("  1. Client completes a loan and has excess security")
        self.stdout.write("  2. Security is transferred from one loan to another")
        self.stdout.write("  3. Previous loan security is applied to new loan")
        self.stdout.write("  4. Manual security adjustment by manager")
        
        # Check if this matches any specific loan completion
        for loan in falcon_loans:
            completed_loans = Loan.objects.filter(
                borrower=loan.borrower,
                status='completed'
            )
            if completed_loans.exists():
                self.stdout.write(f"\n🏁 {loan.borrower.full_name} has {completed_loans.count()} completed loan(s):")
                for completed in completed_loans:
                    self.stdout.write(f"  - {completed.application_number}: completed")
        
        self.stdout.write("\n=== DEBUG COMPLETE ===")