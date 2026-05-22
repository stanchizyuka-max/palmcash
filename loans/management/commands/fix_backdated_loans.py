"""
Management command to fix backdated loans by aligning loan dates with application dates.

This script:
1. Finds all loans created from backdated applications
2. Updates loan created_at, approval_date to match application date
3. Sets system timestamps (approval_recorded_at, disbursement_recorded_at)
4. Recalculates payment schedules based on backdated disbursement dates
5. Provides detailed report of changes

Usage:
    python manage.py fix_backdated_loans --dry-run  # Preview changes
    python manage.py fix_backdated_loans            # Apply changes
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from loans.models import Loan, LoanApplication
from payments.models import PaymentSchedule
from datetime import datetime, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix backdated loans by aligning dates with their applications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each loan',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be saved'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  LIVE MODE - Changes will be saved to database'))
        
        self.stdout.write('')
        
        # Find all loan applications with backdated dates
        applications = LoanApplication.objects.filter(
            status='approved'
        ).select_related('borrower', 'loan_officer')
        
        total_apps = applications.count()
        self.stdout.write(f'📋 Found {total_apps} approved loan applications')
        self.stdout.write('')
        
        fixed_count = 0
        skipped_count = 0
        error_count = 0
        
        for app in applications:
            try:
                # Find the loan created from this application
                # Match by borrower, loan officer, and amount
                loans = Loan.objects.filter(
                    borrower=app.borrower,
                    loan_officer=app.loan_officer,
                    principal_amount=app.loan_amount,
                    created_at__gte=app.created_at,  # Loan created on or after application
                ).order_by('created_at')
                
                if not loans.exists():
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️  No loan found for application {app.application_number}'
                            )
                        )
                    skipped_count += 1
                    continue
                
                loan = loans.first()
                
                # Check if loan needs fixing
                app_date = app.created_at
                loan_created = loan.created_at
                
                # If loan was created on same day as application, skip
                if app_date.date() == loan_created.date():
                    if verbose:
                        self.stdout.write(
                            f'✓ Loan {loan.application_number} already aligned with application date'
                        )
                    skipped_count += 1
                    continue
                
                # Calculate the difference
                days_diff = (loan_created.date() - app_date.date()).days
                
                if days_diff <= 0:
                    # Loan created before or same day as application - skip
                    skipped_count += 1
                    continue
                
                # This loan needs fixing
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(f'🔧 Fixing Loan {loan.application_number}'))
                self.stdout.write(f'   Borrower: {loan.borrower.get_full_name()}')
                self.stdout.write(f'   Application Date: {app_date.strftime("%Y-%m-%d")}')
                self.stdout.write(f'   Current Loan Created: {loan_created.strftime("%Y-%m-%d")}')
                self.stdout.write(f'   Difference: {days_diff} days')
                
                if not dry_run:
                    with transaction.atomic():
                        # Store original dates for audit
                        original_created = loan.created_at
                        original_approval = loan.approval_date
                        original_disbursement = loan.disbursement_date
                        
                        # Update loan dates to match application
                        loan.created_at = app_date
                        
                        # Set approval date to application date (business date)
                        loan.approval_date = app_date
                        
                        # Set system timestamp (when it was actually recorded)
                        loan.approval_recorded_at = original_approval or original_created
                        
                        # If loan is disbursed, backdate disbursement too
                        if loan.status in ['disbursed', 'active', 'completed', 'defaulted']:
                            if loan.disbursement_date:
                                # Calculate how many days after approval it was disbursed
                                if original_approval and original_disbursement:
                                    days_to_disburse = (original_disbursement.date() - original_approval.date()).days
                                else:
                                    days_to_disburse = 1  # Default to next day
                                
                                # Apply same delay to backdated date
                                new_disbursement = app_date + timedelta(days=days_to_disburse)
                                loan.disbursement_date = new_disbursement
                                loan.disbursement_recorded_at = original_disbursement
                                
                                # Recalculate maturity date
                                if loan.repayment_frequency == 'daily' and loan.term_days:
                                    loan.maturity_date = (new_disbursement + timedelta(days=loan.term_days)).date()
                                elif loan.repayment_frequency == 'weekly' and loan.term_weeks:
                                    loan.maturity_date = (new_disbursement + timedelta(weeks=loan.term_weeks)).date()
                                
                                self.stdout.write(f'   New Disbursement Date: {new_disbursement.strftime("%Y-%m-%d")}')
                                
                                # Regenerate payment schedule
                                if loan.status in ['active', 'completed', 'defaulted']:
                                    self.stdout.write('   Regenerating payment schedule...')
                                    
                                    # Delete old schedule
                                    old_schedules = PaymentSchedule.objects.filter(loan=loan)
                                    old_count = old_schedules.count()
                                    old_schedules.delete()
                                    
                                    # Generate new schedule
                                    from loans.utils import generate_payment_schedule
                                    generate_payment_schedule(loan)
                                    
                                    new_count = PaymentSchedule.objects.filter(loan=loan).count()
                                    self.stdout.write(f'   Payment schedule: {old_count} → {new_count} schedules')
                        
                        # Save the loan
                        loan.save()
                        
                        self.stdout.write(self.style.SUCCESS('   ✅ Fixed successfully'))
                        fixed_count += 1
                else:
                    self.stdout.write(self.style.WARNING('   [DRY RUN] Would fix this loan'))
                    fixed_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error fixing loan: {str(e)}')
                )
                error_count += 1
                continue
        
        # Summary
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Total Applications Checked: {total_apps}')
        self.stdout.write(self.style.SUCCESS(f'✅ Loans Fixed: {fixed_count}'))
        self.stdout.write(f'⏭️  Loans Skipped (already aligned): {skipped_count}')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errors: {error_count}'))
        
        if dry_run and fixed_count > 0:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠️  This was a DRY RUN. No changes were saved.'))
            self.stdout.write(self.style.WARNING('   Run without --dry-run to apply changes.'))
        elif fixed_count > 0:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ All changes have been saved to the database.'))
        
        self.stdout.write('')
