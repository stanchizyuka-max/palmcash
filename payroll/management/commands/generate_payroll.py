from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from calendar import monthrange
from payroll.models import Employee, PayrollPeriod, PayrollRecord


class Command(BaseCommand):
    help = 'Generate monthly payroll records for all active employees'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=int,
            help='Month (1-12). Defaults to current month'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Year (e.g., 2026). Defaults to current year'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if period already exists'
        )
    
    def handle(self, *args, **options):
        # Get month and year
        today = timezone.now().date()
        month = options.get('month') or today.month
        year = options.get('year') or today.year
        force = options.get('force', False)
        
        # Validate month
        if month < 1 or month > 12:
            self.stdout.write(self.style.ERROR('Month must be between 1 and 12'))
            return
        
        self.stdout.write(f'\nGenerating payroll for {date(year, month, 1).strftime("%B %Y")}...\n')
        
        # Check if period already exists
        period, created = PayrollPeriod.objects.get_or_create(
            month=month,
            year=year,
            defaults={'status': 'open'}
        )
        
        if not created and not force:
            self.stdout.write(
                self.style.WARNING(f'Payroll period already exists. Use --force to regenerate.')
            )
            self.stdout.write(f'Period ID: {period.id}')
            self.stdout.write(f'Status: {period.get_status_display()}')
            self.stdout.write(f'Total Expected: K{period.total_expected:,.2f}')
            self.stdout.write(f'Total Paid: K{period.total_paid:,.2f}')
            return
        
        if not created and force:
            # Delete existing records
            deleted_count = period.payroll_records.count()
            period.payroll_records.all().delete()
            self.stdout.write(f'Deleted {deleted_count} existing records')
        
        # Get all active employees
        employees = Employee.objects.filter(is_active=True, monthly_salary__gt=0)
        
        if not employees.exists():
            self.stdout.write(self.style.WARNING('No active employees with salary found'))
            return
        
        created_count = 0
        skipped_count = 0
        total_expected = 0
        
        for employee in employees:
            # Calculate due date based on employee's payment_day
            payment_day = employee.payment_day
            last_day = monthrange(year, month)[1]
            
            # If payment_day is greater than last day of month, use last day
            if payment_day > last_day:
                payment_day = last_day
            
            due_date = date(year, month, payment_day)
            
            # Create payroll record
            record, record_created = PayrollRecord.objects.get_or_create(
                period=period,
                employee=employee,
                defaults={
                    'expected_amount': employee.monthly_salary,
                    'due_date': due_date,
                    'status': 'pending',
                }
            )
            
            if record_created:
                created_count += 1
                total_expected += employee.monthly_salary
                self.stdout.write(
                    f'  ✓ {employee.employee_id} - {employee.user.get_full_name()}: '
                    f'K{employee.monthly_salary:,.2f} (Due: {due_date.strftime("%b %d")})'
                )
            else:
                skipped_count += 1
        
        # Update period totals
        period.update_totals()
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(f'✓ Payroll generation completed!'))
        self.stdout.write(f'\nPeriod: {period}')
        self.stdout.write(f'Status: {period.get_status_display()}')
        self.stdout.write(f'\nRecords created: {created_count}')
        self.stdout.write(f'Records skipped: {skipped_count}')
        self.stdout.write(f'\nTotal Expected: K{period.total_expected:,.2f}')
        self.stdout.write(f'Total Paid: K{period.total_paid:,.2f}')
        self.stdout.write(f'Outstanding: K{period.outstanding:,.2f}')
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ {created_count} employees ready for payment')
            )
