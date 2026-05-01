# Generated migration for adding vault_type to VaultTransaction

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0007_add_other_expense_code'),
    ]

    operations = [
        # Add vault_type field (nullable initially for migration)
        migrations.AddField(
            model_name='vaulttransaction',
            name='vault_type',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=10,
                choices=[('daily', 'Daily Vault'), ('weekly', 'Weekly Vault')],
                help_text='Which vault this transaction belongs to (Daily or Weekly)',
                db_index=True
            ),
        ),
    ]
