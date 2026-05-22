"""
Management command to manually backdate loan LV-000126 to yesterday (May 21, 2026)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.models import Loan, LoanApplication
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Manually backdate loan LV-000126 and its application to yesterday (May 21, 2026)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to backdate to yesterday',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  This will manually change the dates for loan LV-000126"
            ))
            self.stdout.write("\nTo proceed, run:")
            self.stdout.write("  python manage.py backdate_lv000126_to_yesterday --confirm")
            return

        self.stdout.write("=" * 60)
        self.stdout.write("Backdating Loan LV-000126 to Yesterday")
        self.stdout.write("=" * 60)
        
        try:
            # Get the loan
            loan = Loan.objects.get(application_number='LV-000126')
            self.stdout.write(f"\n✓ Found loan: {loan.application_number}")
            self.stdout.write(f"  Borrower: {loan.borrower.get_full_name()}")
            self.stdout.write(f"  Current application_date: {loan.application_date}")
            
            # Get the application
            try:
                loan_app = LoanApplication.objects.get(application_number='LA-A3B38172')
                self.stdout.write(f"\n✓ Found application: {loan_app.application_number}")
                self.stdout.write(f"  Current created_at: {loan_app.created_at}")
            except LoanApplication.DoesNotExist:
                loan_app = None
                self.stdout.write(self.style.WARNING(
                    "\n⚠️  Application LA-A3B38172 not found"
                ))
            
            # Calculate yesterday's date (May 21, 2026)
            # Use the same time as the current created_at, just change the date
            if loan_app:
                current_time = loan_app.created_at
            else:
                current_time = loan.application_date
            
            # Set to yesterday at the same time
            yesterday = current_time - timedelta(days=1)
            
            self.stdout.write(f"\n📅 Target date: {yesterday}")
            self.stdout.write(f"   (Yesterday at {yesterday.strftime('%H:%M:%S')})")
            
            # Update the application
            if loan_app:
                LoanApplication.objects.filter(pk=loan_app.pk).update(
                    created_at=yesterday
                )
                self.stdout.write(f"\n✅ Updated application LA-A3B38172")
                self.stdout.write(f"   New created_at: {yesterday}")
            
            # Update the loan
            Loan.objects.filter(pk=loan.pk).update(
                application_date=yesterday,
                created_at=yesterday,
                approval_date=yesterday
            )
            
            # Refresh from database
            loan.refresh_from_db()
            if loan_app:
                loan_app.refresh_from_db()
            
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("✅ SUCCESS - Backdated to Yesterday")
            self.stdout.write("=" * 60)
            
            if loan_app:
                self.stdout.write(f"\nApplication LA-A3B38172:")
                self.stdout.write(f"  created_at: {loan_app.created_at}")
                self.stdout.write(f"  Date: {loan_app.created_at.strftime('%B %d, %Y')}")
            
            self.stdout.write(f"\nLoan LV-000126:")
            self.stdout.write(f"  application_date: {loan.application_date}")
            self.stdout.write(f"  approval_date: {loan.approval_date}")
            self.stdout.write(f"  created_at: {loan.created_at}")
            self.stdout.write(f"  Date: {loan.application_date.strftime('%B %d, %Y')}")
            
            self.stdout.write(f"\n✅ Loan will now show: Applied {loan.application_date.strftime('%B %d, %Y')}")
            
            # Note about system timestamps
            if loan.approval_recorded_at:
                self.stdout.write(f"\n📝 Note: System timestamp preserved for audit:")
                self.stdout.write(f"   approval_recorded_at: {loan.approval_recorded_at}")
                self.stdout.write(f"   (Shows when approval was actually recorded in system)")
            
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
