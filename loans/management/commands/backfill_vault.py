from django.core.management.base import BaseCommand
from loans.models import SecurityDeposit
from loans.vault_services import record_security_deposit
from expenses.models import VaultTransaction


class Command(BaseCommand):
    help = 'Backfill vault transactions for already-verified security deposits'

    def handle(self, *args, **options):
        verified = SecurityDeposit.objects.filter(is_verified=True, paid_amount__gt=0)
        self.stdout.write(f'Found {verified.count()} verified deposits')
        for dep in verified:
            already = VaultTransaction.objects.filter(
                loan=dep.loan, transaction_type='security_deposit'
            ).exists()
            if already:
                self.stdout.write(f'SKIP (exists): {dep.loan.application_number}')
                continue
            verifier = dep.verified_by or dep.loan.loan_officer
            result = record_security_deposit(dep.loan, dep.paid_amount, verifier)
            if result:
                self.stdout.write(self.style.SUCCESS(f'OK: {dep.loan.application_number} K{dep.paid_amount}'))
            else:
                self.stdout.write(self.style.ERROR(f'FAILED: {dep.loan.application_number} — branch not found'))
