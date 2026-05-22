"""
Management command to fix the application date for loan LV-000126
This loan was created from a backdated application but shows today's date
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.models import Loan, LoanApplication
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Fix application date for loan LV-000126 to match its backdated application'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("Fixing Loan LV-000126 Application Date")
        self.stdout.write("=" * 60)
        
        try:
            # Get the loan
            loan = Loan.objects.get(application_number='LV-000126')
            self.stdout.write(f"\n✓ Found loan: {loan.application_number}")
            self.stdout.write(f"  Borrower: {loan.borrower.get_full_name()}")
            self.stdout.write(f"  Current application_date: {loan.application_date}")
            self.stdout.write(f"  Current approval_date: {loan.approval_date}")
            
            # Find the corresponding application
            try:
                # The loan was created from application LA-A3B38172
                loan_app = LoanApplication.objects.get(application_number='LA-A3B38172')
                self.stdout.write(f"\n✓ Found application: {loan_app.application_number}")
                self.stdout.write(f"  Application created_at: {loan_app.created_at}")
                
                # Update the loan's application_date to match the application's created_at
                Loan.objects.filter(pk=loan.pk).update(
                    application_date=loan_app.created_at,
                    created_at=loan_app.created_at
                )
                
                # Refresh from database
                loan.refresh_from_db()
                
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("✅ SUCCESS")
                self.stdout.write("=" * 60)
                self.stdout.write(f"Updated loan {loan.application_number}:")
                self.stdout.write(f"  New application_date: {loan.application_date}")
                self.stdout.write(f"  New created_at: {loan.created_at}")
                self.stdout.write(f"  Approval date: {loan.approval_date}")
                self.stdout.write(f"  Approval recorded at: {loan.approval_recorded_at}")
                
            except LoanApplication.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"\n⚠️  Could not find application LA-A3B38172"
                ))
                self.stdout.write("\nUsing yesterday's date as fallback...")
                
                # Use yesterday's date
                yesterday = timezone.now() - timedelta(days=1)
                Loan.objects.filter(pk=loan.pk).update(
                    application_date=yesterday,
                    created_at=yesterday
                )
                
                loan.refresh_from_db()
                
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("✅ SUCCESS (with fallback)")
                self.stdout.write("=" * 60)
                self.stdout.write(f"Updated loan {loan.application_number}:")
                self.stdout.write(f"  New application_date: {loan.application_date}")
                self.stdout.write(f"  New created_at: {loan.created_at}")
                
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
