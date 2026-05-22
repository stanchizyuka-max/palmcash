"""
Management command to fix payment allocation for loan LV-000080
Client made one payment of K140 but system shows 2 complete payments
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.models import Loan
from payments.models import Payment, PaymentSchedule
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix payment allocation for loan LV-000080'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be saved\n"))
        
        self.stdout.write("=" * 60)
        self.stdout.write("Fixing Payment Allocation for Loan LV-000080")
        self.stdout.write("=" * 60)
        
        try:
            # Get the loan
            loan = Loan.objects.get(application_number='LV-000080')
            self.stdout.write(f"\n✓ Found loan: {loan.application_number}")
            self.stdout.write(f"  Borrower: {loan.borrower.get_full_name()}")
            self.stdout.write(f"  Loan amount: K{loan.principal_amount}")
            self.stdout.write(f"  Total with interest: K{loan.total_amount}")
            
            # Get all payments for this loan
            payments = Payment.objects.filter(loan=loan).order_by('payment_date')
            self.stdout.write(f"\n📊 Found {payments.count()} payment(s):")
            
            total_paid = Decimal('0')
            for payment in payments:
                self.stdout.write(f"  - K{payment.amount} on {payment.payment_date.strftime('%Y-%m-%d')}")
                total_paid += payment.amount
            
            self.stdout.write(f"\n💰 Total paid: K{total_paid}")
            
            # Get payment schedule
            schedule = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
            self.stdout.write(f"\n📅 Payment schedule ({schedule.count()} installments):")
            
            paid_count = 0
            partial_count = 0
            pending_count = 0
            
            for installment in schedule:
                # Determine status based on is_paid and amount_paid
                if installment.is_paid:
                    status = 'paid'
                    status_icon = "✅"
                    paid_count += 1
                elif installment.amount_paid > 0:
                    status = 'partial'
                    status_icon = "⚠️"
                    partial_count += 1
                else:
                    status = 'pending'
                    status_icon = "⏳"
                    pending_count += 1
                
                self.stdout.write(
                    f"  {status_icon} #{installment.installment_number}: "
                    f"K{installment.total_amount} - {status.upper()} "
                    f"(paid: K{installment.amount_paid})"
                )
            
            self.stdout.write(f"\n📈 Summary:")
            self.stdout.write(f"  Paid: {paid_count}")
            self.stdout.write(f"  Partial: {partial_count}")
            self.stdout.write(f"  Pending: {pending_count}")
            
            # Analyze the issue
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("🔍 ANALYSIS")
            self.stdout.write("=" * 60)
            
            # Expected: K420 should cover how many installments?
            expected_installment_amount = loan.payment_amount
            self.stdout.write(f"\nExpected installment amount: K{expected_installment_amount}")
            self.stdout.write(f"Total paid: K{total_paid}")
            
            # Calculate how many full installments can be paid
            full_installments = int(total_paid / expected_installment_amount)
            remainder = total_paid % expected_installment_amount
            
            self.stdout.write(f"\nWith K{total_paid}:")
            self.stdout.write(f"  Should cover: {full_installments} full installment(s)")
            self.stdout.write(f"  Remainder: K{remainder} (partial payment)")
            
            self.stdout.write(f"\nCurrent state:")
            self.stdout.write(f"  Showing: {paid_count} paid + {partial_count} partial")
            
            if paid_count != full_installments:
                self.stdout.write(self.style.ERROR(
                    f"\n❌ MISMATCH: Should show {full_installments} paid, but showing {paid_count}"
                ))
                
                # Propose fix
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("🔧 PROPOSED FIX")
                self.stdout.write("=" * 60)
                
                self.stdout.write(f"\nReset all installments and re-allocate K{total_paid}:")
                
                remaining_amount = total_paid
                for i, installment in enumerate(schedule, 1):
                    if remaining_amount >= installment.total_amount:
                        # Full payment
                        self.stdout.write(
                            f"  #{i}: K{installment.total_amount} → PAID (K{installment.total_amount})"
                        )
                        remaining_amount -= installment.total_amount
                    elif remaining_amount > 0:
                        # Partial payment
                        self.stdout.write(
                            f"  #{i}: K{installment.total_amount} → PARTIAL (K{remaining_amount} paid)"
                        )
                        remaining_amount = Decimal('0')
                    else:
                        # Pending
                        self.stdout.write(
                            f"  #{i}: K{installment.total_amount} → PENDING"
                        )
                
                # Apply fix if not dry run
                if not dry_run:
                    self.stdout.write("\n" + "=" * 60)
                    self.stdout.write("💾 APPLYING FIX")
                    self.stdout.write("=" * 60)
                    
                    remaining_amount = total_paid
                    for installment in schedule:
                        if remaining_amount >= installment.total_amount:
                            # Full payment
                            installment.amount_paid = installment.total_amount
                            installment.is_paid = True
                            installment.paid_date = payments.first().payment_date.date() if payments.exists() else timezone.now().date()
                            remaining_amount -= installment.total_amount
                        elif remaining_amount > 0:
                            # Partial payment
                            installment.amount_paid = remaining_amount
                            installment.is_paid = False
                            installment.paid_date = payments.first().payment_date.date() if payments.exists() else timezone.now().date()
                            remaining_amount = Decimal('0')
                        else:
                            # Pending
                            installment.amount_paid = Decimal('0')
                            installment.is_paid = False
                            installment.paid_date = None
                        
                        installment.save()
                    
                    self.stdout.write("\n✅ Fix applied successfully!")
                    
                    # Show updated state
                    self.stdout.write("\n" + "=" * 60)
                    self.stdout.write("📊 UPDATED STATE")
                    self.stdout.write("=" * 60)
                    
                    schedule = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
                    for installment in schedule[:5]:  # Show first 5
                        # Determine status
                        if installment.is_paid:
                            status = 'paid'
                            status_icon = "✅"
                        elif installment.amount_paid > 0:
                            status = 'partial'
                            status_icon = "⚠️"
                        else:
                            status = 'pending'
                            status_icon = "⏳"
                        
                        self.stdout.write(
                            f"  {status_icon} #{installment.installment_number}: "
                            f"K{installment.total_amount} - {status.upper()} "
                            f"(paid: K{installment.amount_paid})"
                        )
                    
                    if schedule.count() > 5:
                        self.stdout.write(f"  ... and {schedule.count() - 5} more")
                
                else:
                    self.stdout.write("\n" + "=" * 60)
                    self.stdout.write("ℹ️  DRY RUN - No changes made")
                    self.stdout.write("=" * 60)
                    self.stdout.write("\nTo apply the fix, run:")
                    self.stdout.write("  python manage.py fix_loan_lv000080_payments")
            
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"\n✅ Payment allocation is correct!"
                ))
        
        except Loan.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                "\n❌ ERROR: Loan LV-000080 not found"
            ))
            return
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"\n❌ ERROR: {str(e)}"
            ))
            import traceback
            traceback.print_exc()
