"""
Management command to reset all payroll data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from payroll.models import (
    Employee, PayrollPeriod, PayrollRecord, 
    SalaryRecord, PayrollPayment, PayrollAuditLog
)


class Command(BaseCommand):
    help = 'Reset all payroll data (employees, periods, records, payments)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all payroll data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL payroll data including:\n'
                    '  - Employees\n'
                    '  - Payroll Periods\n'
                    '  - Payroll Records\n'
                    '  - Salary Records\n'
                    '  - Payroll Payments\n'
                    '  - Audit Logs\n\n'
                    'Run with --confirm to proceed'
                )
            )
            return

        self.stdout.write('Resetting payroll data...')

        with transaction.atomic():
            # Count before deletion
            employee_count = Employee.objects.count()
            period_count = PayrollPeriod.objects.count()
            record_count = PayrollRecord.objects.count()
            salary_count = SalaryRecord.objects.count()
            payment_count = PayrollPayment.objects.count()
            audit_count = PayrollAuditLog.objects.count()

            # Delete all data
            PayrollAuditLog.objects.all().delete()
            PayrollPayment.objects.all().delete()
            SalaryRecord.objects.all().delete()
            PayrollRecord.objects.all().delete()
            PayrollPeriod.objects.all().delete()
            Employee.objects.all().delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully deleted:\n'
                    f'  - {employee_count} employees\n'
                    f'  - {period_count} payroll periods\n'
                    f'  - {record_count} payroll records\n'
                    f'  - {salary_count} salary records\n'
                    f'  - {payment_count} payments\n'
                    f'  - {audit_count} audit logs\n'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                '\n✓ Payroll data reset complete!\n'
                'You can now sync employees from User accounts.'
            )
        )
