"""
Management command to fix payment schedule dates for loan LV-000126
Schedule should start on May 28, not May 29
"""
from django.core.management.base import BaseCommand
from loans.models import Loan
from payments.models import PaymentSchedule
from datetime import timedelta


class Command(BaseCommand):
    help = 'Fix payment schedule dates for loan LV-000126 to start on May 28'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm adjustment of payment dates',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  This will adjust payment schedule dates for loan LV-000126"
            ))
            self.stdout.write("\nTo proceed, run:")
            self.stdout.write("  python manage.py fix_lv000126_schedule_dates --confirm")
            return

        self.stdout.write("=" * 60)
        self.stdout.write("Fixing Payment Schedule Dates for Loan LV-000126")
        self.stdout.write("=" * 60)
        
        try:
            # Get the loan
            loan = Loan.objects.get(application_number='LV-000126')
            self.stdout.write(f"\n✓ Found loan: {loan.application_number}")
            self.stdout.write(f"  Borrower: {loan.borrower.get_full_name()}")
            self.stdout.write(f"  Disbursement date: {loan.disbursement_date}")
            self.stdout.write(f"  Repayment frequency: {loan.repayment_frequency}")
            
            # Get payment schedule
            schedule = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
            self.stdout.write(f"\n📅 Found {schedule.count()} installments")
            
            if schedule.exists():
                first_payment = schedule.first()
                self.stdout.write(f"\nCurrent first payment due: {first_payment.due_date}")
                self.stdout.write(f"Should be: May 28, 2026")
                
                # Calculate the difference
                from datetime import date
                expected_first_date = date(2026, 5, 28)
                current_first_date = first_payment.due_date
                
                if current_first_date != expected_first_date:
                    days_diff = (current_first_date - expected_first_date).days
                    self.stdout.write(f"\n⚠️  Schedule is off by {days_diff} day(s)")
                    
                    self.stdout.write("\n" + "=" * 60)
                    self.stdout.write("🔧 ADJUSTING DATES")
                    self.stdout.write("=" * 60)
                    
                    # Adjust all dates by moving them back by days_diff
                    for installment in schedule:
                        old_date = installment.due_date
                        new_date = old_date - timedelta(days=days_diff)
                        installment.due_date = new_date
                        installment.save()
                        
                        if installment.installment_number <= 5:
                            self.stdout.write(
                                f"  #{installment.installment_number}: "
                                f"{old_date} → {new_date}"
                            )
                    
                    if schedule.count() > 5:
                        self.stdout.write(f"  ... and {schedule.count() - 5} more")
                    
                    self.stdout.write("\n" + "=" * 60)
                    self.stdout.write("✅ SUCCESS")
                    self.stdout.write("=" * 60)
                    
                    # Show updated schedule
                    schedule = PaymentSchedule.objects.filter(loan=loan).order_by('installment_number')
                    first = schedule.first()
                    last = schedule.last()
                    
                    self.stdout.write(f"\n📊 Updated schedule:")
                    self.stdout.write(f"  First payment: {first.due_date} (#{first.installment_number})")
                    self.stdout.write(f"  Last payment: {last.due_date} (#{last.installment_number})")
                    self.stdout.write(f"  Total installments: {schedule.count()}")
                    
                    self.stdout.write("\n✅ Payment schedule now starts on May 28, 2026")
                    
                else:
                    self.stdout.write(self.style.SUCCESS(
                        "\n✅ Schedule is already correct! First payment is on May 28, 2026"
                    ))
            else:
                self.stdout.write(self.style.ERROR(
                    "\n❌ No payment schedule found for this loan"
                ))
        
        except Loan.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                "\n❌ ERROR: Loan LV-000126 not found"
            ))
            return
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"\n❌ ERROR: {str(e)}"
            ))
            import traceback
            traceback.print_exc()
