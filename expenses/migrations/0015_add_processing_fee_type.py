# Generated migration to add processing_fee transaction type

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0008_add_vault_type_to_transactions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vaulttransaction',
            name='transaction_type',
            field=models.CharField(
                choices=[
                    ('deposit', 'Cash Deposit'),
                    ('withdrawal', 'Cash Withdrawal'),
                    ('transfer', 'Branch Transfer'),
                    ('loan_disbursement', 'Loan Disbursement'),
                    ('payment_collection', 'Payment Collection'),
                    ('security_deposit', 'Security Deposit'),
                    ('security_return', 'Security Return'),
                    ('security_withdrawal', 'Security Withdrawal'),
                    ('capital_injection', 'Capital Injection'),
                    ('bank_withdrawal', 'Bank Withdrawal'),
                    ('bank_charges', 'Bank Charges'),
                    ('fund_deposit', 'Fund Received'),
                    ('branch_transfer_out', 'Branch Transfer (Out)'),
                    ('branch_transfer_in', 'Branch Transfer (In)'),
                    ('bank_deposit_out', 'Bank Deposit (to Bank)'),
                    ('month_close', 'Month Closing'),
                    ('month_open', 'Month Opening'),
                    ('savings_deposit', 'Savings Deposit'),
                    ('savings_withdrawal', 'Savings Withdrawal'),
                    ('expense', 'Expense'),
                    ('processing_fee', 'Processing Fee'),
                ],
                max_length=30
            ),
        ),
    ]
