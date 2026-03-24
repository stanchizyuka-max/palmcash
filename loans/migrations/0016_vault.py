from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0015_security_tracking'),
        ('clients', '0013_rename_clients_adm_admin_u_idx_clients_adm_admin_u_b673c4_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BranchVault',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='vault', to='clients.branch')),
            ],
        ),
        migrations.CreateModel(
            name='VaultTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.CharField(choices=[('in', 'Inflow'), ('out', 'Outflow')], max_length=3)),
                ('transaction_type', models.CharField(choices=[('security_deposit', 'Security Deposit'), ('loan_disbursement', 'Loan Disbursement'), ('security_return', 'Security Return')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('balance_after', models.DecimalField(decimal_places=2, max_digits=14)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_vault_transactions', to=settings.AUTH_USER_MODEL)),
                ('initiated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='initiated_vault_transactions', to=settings.AUTH_USER_MODEL)),
                ('loan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vault_transactions', to='loans.loan')),
                ('vault', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='loans.branchvault')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
