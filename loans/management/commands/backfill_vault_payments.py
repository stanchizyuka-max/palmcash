from django.core.management.base import BaseCommand
from payments.models import Payment
from loans.vault_services import record_payment_collection
from expenses.models import VaultTransaction


class Command(BaseCommand):
    help = 'Backfill vault transactions for already-confirmed loan repayments'

    def handle(self, *args, **options):
        confirmed = Payment.objects.filter(status='completed').select_related('loan')
        self.stdout.write(f'Found {confirmed.count()} confirmed payments')
        for payment in confirmed:
            already = VaultTransaction.objects.filter(
                loan=payment.loan,
                transaction_type='payment_collection',
                amount=payment.amount,
            ).exists()
            if already:
                self.stdout.write(f'SKIP: {payment.payment_number}')
                continue
            recorder = payment.processed_by or payment.loan.loan_officer
            result = record_payment_collection(payment.loan, payment.amount, recorder)
            if result:
                self.stdout.write(self.style.SUCCESS(f'OK: {payment.payment_number} K{payment.amount}'))
            else:
                self.stdout.write(self.style.ERROR(f'FAILED: {payment.payment_number} — branch not found'))
