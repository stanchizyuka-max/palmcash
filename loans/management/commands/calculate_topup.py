from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from loans.models import Loan
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Calculate security top-up requirements for different loan amounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loan-amounts',
            nargs='+',
            type=float,
            default=[2000, 5000, 10000, 15000, 20000],
            help='Loan amounts to calculate top-up for (default: 2000 5000 10000 15000 20000)'
        )

    def handle(self, *args, **options):
        loan_amounts = [Decimal(str(amount)) for amount in options['loan_amounts']]
        
        # Get Shucco Zulu
        try:
            client = User.objects.get(
                first_name__icontains='shucco',
                last_name__icontains='zulu',
                role='borrower'
            )
            self.stdout.write(f"Client: {client.first_name} {client.last_name}")
        except User.DoesNotExist:
            self.stdout.write("❌ Shucco Zulu not found")
            return

        # Get the loan
        loan = Loan.objects.filter(borrower=client, status='active').first()
        if not loan:
            self.stdout.write("❌ No active loan found for client")
            return
        
        # Get current security
        try:
            deposit = loan.security_deposit
            current_security = deposit.paid_amount
            self.stdout.write(f"Current loan: {loan.application_number}")
            self.stdout.write(f"Current security: K{current_security}")
        except Exception:
            self.stdout.write("❌ No security deposit found")
            return

        self.stdout.write(f"\n📊 TOP-UP CALCULATIONS:")
        self.stdout.write("=" * 80)
        self.stdout.write(f"{'New Loan Amount':<15} {'Required (10%)':<15} {'Current':<12} {'Top-Up Needed':<15} {'Status'}")
        self.stdout.write("-" * 80)
        
        for new_amount in loan_amounts:
            required_security = new_amount * Decimal('0.10')  # 10%
            topup_needed = max(Decimal('0'), required_security - current_security)
            
            if topup_needed > 0:
                status = f"NEED K{topup_needed:.2f}"
            else:
                status = "✅ COVERED"
            
            self.stdout.write(
                f"K{new_amount:<14} K{required_security:<14.2f} K{current_security:<11} "
                f"K{topup_needed:<14.2f} {status}"
            )
        
        self.stdout.write("-" * 80)
        
        # Show what amount would need exactly K200 top-up
        target_topup = Decimal('200')
        required_for_200_topup = current_security + target_topup
        loan_amount_for_200 = required_for_200_topup / Decimal('0.10')
        
        self.stdout.write(f"\n💡 INSIGHT:")
        self.stdout.write(f"To need exactly K200 top-up, the new loan amount would be: K{loan_amount_for_200:.2f}")
        self.stdout.write(f"(Because K{loan_amount_for_200:.2f} × 10% = K{required_for_200_topup:.2f}, and K{required_for_200_topup:.2f} - K{current_security} = K{target_topup})")
        
        # Check recent attempts
        self.stdout.write(f"\n🔍 RECENT ACTIVITY CHECK:")
        self.stdout.write("If Precious entered K199.98, that explains why no request was created.")
        self.stdout.write("The system correctly determined that K400 already covers K199.98 × 10% = K19.998")
        
        # Suggest likely intended amounts
        self.stdout.write(f"\n🎯 LIKELY INTENDED AMOUNTS:")
        common_amounts = [2000, 3000, 5000, 6000, 10000, 15000, 20000]
        for amount in common_amounts:
            amount_decimal = Decimal(str(amount))
            required = amount_decimal * Decimal('0.10')
            needed = max(Decimal('0'), required - current_security)
            if needed > 0:
                self.stdout.write(f"  - K{amount}: needs K{needed:.2f} top-up")
            else:
                self.stdout.write(f"  - K{amount}: ✅ covered (no top-up needed)")