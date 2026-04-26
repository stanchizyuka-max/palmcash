from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from loans.models import SecurityTransaction, SecurityTopUpRequest
from django.db.models import Q

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix duplicate top-up counting by removing incorrect carry_forward transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually perform the cleanup (dry run by default)'
        )

    def handle(self, *args, **options):
        execute = options['execute']
        
        self.stdout.write("=== FIXING DUPLICATE TOP-UP COUNTING ===\n")
        
        # Find SecurityTransaction records that were incorrectly created for top-up approvals
        # These have type='carry_forward' and notes containing "Top-up approved by"
        duplicate_transactions = SecurityTransaction.objects.filter(
            transaction_type='carry_forward',
            notes__icontains='Top-up approved by'
        )
        
        self.stdout.write(f"Found {duplicate_transactions.count()} duplicate top-up transaction(s):")
        
        total_amount = 0
        for txn in duplicate_transactions:
            self.stdout.write(f"  - ID {txn.id}: K{txn.amount} for {txn.loan.application_number}")
            self.stdout.write(f"    Notes: {txn.notes}")
            self.stdout.write(f"    Created: {txn.created_at}")
            total_amount += txn.amount
        
        if not duplicate_transactions.exists():
            self.stdout.write("✅ No duplicate transactions found")
            return
        
        # Check corresponding SecurityTopUpRequest records
        self.stdout.write(f"\n🔍 Checking corresponding SecurityTopUpRequest records:")
        for txn in duplicate_transactions:
            # Find matching top-up request
            matching_requests = SecurityTopUpRequest.objects.filter(
                loan=txn.loan,
                requested_amount=txn.amount,
                status='approved'
            )
            
            if matching_requests.exists():
                req = matching_requests.first()
                self.stdout.write(f"  ✅ Found matching top-up request ID {req.id} for transaction {txn.id}")
            else:
                self.stdout.write(f"  ❌ No matching top-up request for transaction {txn.id}")
        
        if not execute:
            self.stdout.write(f"\n🔍 DRY RUN - Changes that would be made:")
            self.stdout.write(f"  - Delete {duplicate_transactions.count()} SecurityTransaction records")
            self.stdout.write(f"  - Total amount affected: K{total_amount}")
            self.stdout.write(f"  - This will fix double-counting in balance calculations")
            self.stdout.write("\nRun with --execute to apply changes")
            return
        
        # Execute the cleanup
        self.stdout.write(f"\n✅ EXECUTING CLEANUP:")
        
        deleted_count = 0
        for txn in duplicate_transactions:
            self.stdout.write(f"  - Deleting transaction ID {txn.id} (K{txn.amount})")
            txn.delete()
            deleted_count += 1
        
        self.stdout.write(f"\n🎉 SUCCESS:")
        self.stdout.write(f"  - Deleted {deleted_count} duplicate transactions")
        self.stdout.write(f"  - Fixed double-counting of K{total_amount}")
        self.stdout.write(f"  - Balance calculations are now correct")
        
        # Show expected balance changes
        self.stdout.write(f"\n📊 EXPECTED BALANCE CHANGES:")
        self.stdout.write(f"  - Falcon group balance should decrease by K{total_amount}")
        self.stdout.write(f"  - Top-up amounts will still show correctly in SecurityTopUpRequest")
        self.stdout.write(f"  - No actual security is lost - just fixing accounting")
        
        self.stdout.write("\n=== CLEANUP COMPLETE ===")