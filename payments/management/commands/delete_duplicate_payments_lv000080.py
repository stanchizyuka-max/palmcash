"""
Management command to delete duplicate pending payments for loan LV-000080
"""
from django.core.management.base import BaseCommand
from loans.models import Loan
from payments.models import Payment


class Command(BaseCommand):
    help = 'Delete duplicate pending payments for loan LV-000080'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of duplicate payments',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  This will DELETE duplicate pending payments"
            ))
            self.stdout.write("\nTo proceed, run:")
            self.stdout.write("  python manage.py delete_duplicate_payments_lv000080 --confirm")
            return

        self.stdout.write("=" * 60)
        self.stdout.write("Deleting Duplicate Payments for Loan LV-000080")
        self.stdout.write("=" * 60)
        
        try:
            # Get the loan
            loan = Loan.objects.get(application_number='LV-000080')
            self.stdout.write(f"\n✓ Found loan: {loan.application_number}")
            self.stdout.write(f"  Borrower: {loan.borrower.get_full_name()}")
            
            # Get all payments for this loan
            payments = Payment.objects.filter(loan=loan).order_by('payment_date', 'id')
            self.stdout.write(f"\n📊 Found {payments.count()} payment record(s):")
            
            for payment in payments:
                status_icon = "✅" if payment.status == 'completed' else "⏳"
                self.stdout.write(
                    f"  {status_icon} {payment.payment_number}: K{payment.amount} "
                    f"on {payment.payment_date.strftime('%Y-%m-%d')} - {payment.status.upper()}"
                )
            
            # Identify duplicates
            completed_payments = payments.filter(status='completed')
            pending_payments = payments.filter(status='pending')
            
            self.stdout.write(f"\n📈 Breakdown:")
            self.stdout.write(f"  Completed: {completed_payments.count()}")
            self.stdout.write(f"  Pending: {pending_payments.count()}")
            
            if pending_payments.exists():
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("🗑️  DELETING DUPLICATE PENDING PAYMENTS")
                self.stdout.write("=" * 60)
                
                for payment in pending_payments:
                    self.stdout.write(
                        f"\n  Deleting: {payment.payment_number} - K{payment.amount} "
                        f"({payment.status})"
                    )
                    payment.delete()
                
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("✅ SUCCESS")
                self.stdout.write("=" * 60)
                self.stdout.write(f"\nDeleted {pending_payments.count()} duplicate payment(s)")
                
                # Show remaining payments
                remaining = Payment.objects.filter(loan=loan).order_by('payment_date')
                self.stdout.write(f"\n📊 Remaining payments: {remaining.count()}")
                for payment in remaining:
                    self.stdout.write(
                        f"  ✅ {payment.payment_number}: K{payment.amount} "
                        f"on {payment.payment_date.strftime('%Y-%m-%d')} - {payment.status.upper()}"
                    )
                
                # Calculate correct total
                total_paid = sum(p.amount for p in remaining)
                self.stdout.write(f"\n💰 Total paid: K{total_paid}")
                
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("📝 NEXT STEPS")
                self.stdout.write("=" * 60)
                self.stdout.write("\n1. Run the payment allocation fix:")
                self.stdout.write("   python manage.py fix_loan_lv000080_payments")
                self.stdout.write("\n2. Restart the server:")
                self.stdout.write("   touch palmcash/wsgi.py")
                
            else:
                self.stdout.write(self.style.SUCCESS(
                    "\n✅ No duplicate pending payments found!"
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
