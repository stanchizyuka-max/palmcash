# Generated migration for dual-vault system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0098_auto_previous'),  # Update this to your latest migration
        ('clients', '0013_rename_clients_adm_admin_u_idx_clients_adm_admin_u_b673c4_idx_and_more'),
    ]

    operations = [
        # Step 1: Rename existing vault relationship to vault_legacy
        migrations.AlterField(
            model_name='branchvault',
            name='branch',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='vault_legacy',
                to='clients.branch'
            ),
        ),
        
        # Step 2: Add is_migrated flag to BranchVault
        migrations.AddField(
            model_name='branchvault',
            name='is_migrated',
            field=models.BooleanField(default=False, help_text='Has this vault been migrated to dual-vault system?'),
        ),
        
        # Step 3: Create DailyVault model
        migrations.CreateModel(
            name='DailyVault',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=0, help_text='Current balance for daily loan operations', max_digits=14)),
                ('total_inflows', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('total_outflows', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('last_transaction_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='daily_vault', to='clients.branch')),
            ],
            options={
                'verbose_name': 'Daily Vault',
                'verbose_name_plural': 'Daily Vaults',
                'ordering': ['branch__name'],
            },
        ),
        
        # Step 4: Create WeeklyVault model
        migrations.CreateModel(
            name='WeeklyVault',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=0, help_text='Current balance for weekly loan operations', max_digits=14)),
                ('total_inflows', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('total_outflows', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('last_transaction_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='weekly_vault', to='clients.branch')),
            ],
            options={
                'verbose_name': 'Weekly Vault',
                'verbose_name_plural': 'Weekly Vaults',
                'ordering': ['branch__name'],
            },
        ),
        
        # Step 5: Update Meta for BranchVault
        migrations.AlterModelOptions(
            name='branchvault',
            options={'verbose_name': 'Legacy Branch Vault', 'verbose_name_plural': 'Legacy Branch Vaults'},
        ),
    ]
