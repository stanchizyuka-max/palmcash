from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0004_populate_expense_codes'),
        ('clients', '0013_rename_clients_adm_admin_u_idx_clients_adm_admin_u_b673c4_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='vaulttransaction',
            name='direction',
            field=models.CharField(choices=[('in', 'Inflow'), ('out', 'Outflow')], default='in', max_length=3),
        ),
        migrations.AddField(
            model_name='vaulttransaction',
            name='balance_after',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='vaulttransaction',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_vault_tx', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='vaulttransaction',
            name='transaction_type',
            field=models.CharField(choices=[('deposit', 'Cash Deposit'), ('withdrawal', 'Cash Withdrawal'), ('transfer', 'Branch Transfer'), ('loan_disbursement', 'Loan Disbursement'), ('payment_collection', 'Payment Collection'), ('security_deposit', 'Security Deposit'), ('security_return', 'Security Return')], max_length=20),
        ),
    ]
