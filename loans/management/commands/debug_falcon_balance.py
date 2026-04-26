from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from loans.models import Loan, SecurityDeposit, SecurityTopUpRequest, SecurityTransaction
from clients.models import BorrowerGroup
from django.db.models import Sum

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug Falcon group balance calculation'

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUGGING FALCON GROUP BALANCE ===\n")
        
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
        
        self.stdout.write(f"✓ Falcon group has {falcon_loans.count()} loan(s):")
        for loan in falcon_loans:
            self.stdout.write(f"  - {loan.application_number}: {loan.borrower.full_name}")
        
        # Manual calculation using same logic as _security_stats_for_loans
        self.stdout.write(f"\n📊 DETAILED CALCULATION:")
        
        # 1. Upfront (SecurityDeposit)
        upfront = SecurityDeposit.objects.filter(
            loan__in=falcon_loans, is_verified=True
        ).aggregate(total=Sum('paid_amount'))['total'] or 0
        self.stdout.write(f"1. Upfront deposits: K{upfront}")
        
        # Show individual deposits
        deposits = SecurityDeposit.objects.filter(loan__in=falcon_loans, is_verified=True)
        for deposit in deposits:
            self.stdout.write(f"   - Loan {deposit.loan.application_number}: K{deposit.paid_amount}")
        
        # 2. Top-ups (SecurityTopUpRequest)
        topups = SecurityTopUpRequest.objects.filter(
            loan__in=falcon_loans, status='approved'
        ).aggregate(total=Sum('requested_amount'))['total'] or 0
        self.stdout.write(f"2. Approved top-ups: K{topups}")
        
        # Show individual top-ups
        topup_requests = SecurityTopUpRequest.objects.filter(loan__in=falcon_loans, status='approved')
        for req in topup_requests:
            self.stdout.write(f"   - Loan {req.loan.application_number}: K{req.requested_amount}")
        
        # 3. Carry forwards (SecurityTransaction)
        carry_forwards = SecurityTransaction.objects.filter(
            loan__in=falcon_loans,
            status='approved',
            transaction_type='carry_forward',
        ).aggregate(total=Sum('amount'))['total'] or 0
        self.stdout.write(f"3. Carry forwards: K{carry_forwards}")
        
        # 4. Adjustments (SecurityTransaction)
        adjustments = SecurityTransaction.objects.filter(
            loan__in=falcon_loans,
            status='approved',
            transaction_type='adjustment',
        ).aggregate(total=Sum('amount'))['total'] or 0
        self.stdout.write(f"4. Adjustments: K{adjustments}")
        
        # Show individual adjustments
        adjustment_txns = SecurityTransaction.objects.filter(
            loan__in=falcon_loans, status='approved', transaction_type='adjustment'
        )
        for txn in adjustment_txns:
            self.stdout.write(f"   - Loan {txn.loan.application_number}: K{txn.amount}")
        
        # 5. Returns (SecurityTransaction)
        returned = SecurityTransaction.objects.filter(
            loan__in=falcon_loans,
            status='approved',
            transaction_type='return',
        ).aggregate(total=Sum('amount'))['total'] or 0
        self.stdout.write(f"5. Returns: K{returned}")
        
        # 6. Withdrawals (SecurityTransaction)
        withdrawals = SecurityTransaction.objects.filter(
            loan__in=falcon_loans,
            status='approved',
            transaction_type='withdrawal',
        ).aggregate(total=Sum('amount'))['total'] or 0
        self.stdout.write(f"6. Withdrawals: K{withdrawals}")
        
        # Calculate balance using corrected formula
        increases = upfront + topups + carry_forwards
        decreases = adjustments + returned + withdrawals
        calculated_balance = increases - decreases
        
        self.stdout.write(f"\n🧮 BALANCE CALCULATION:")
        self.stdout.write(f"Increases: K{upfront} + K{topups} + K{carry_forwards} = K{increases}")
        self.stdout.write(f"Decreases: K{adjustments} + K{returned} + K{withdrawals} = K{decreases}")
        self.stdout.write(f"Balance: K{increases} - K{decreases} = K{calculated_balance}")
        
        # Compare with what's shown on screen
        self.stdout.write(f"\n📺 COMPARISON:")
        self.stdout.write(f"Calculated balance: K{calculated_balance}")
        self.stdout.write(f"Screen shows: K1,000")
        
        if calculated_balance == 1000:
            self.stdout.write("✅ MATCH: Calculation is correct")
        else:
            self.stdout.write("❌ MISMATCH: There's a calculation error")
            self.stdout.write(f"Difference: K{1000 - calculated_balance}")
        
        self.stdout.write("\n=== DEBUG COMPLETE ===")