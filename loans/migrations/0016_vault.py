from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0015_security_tracking'),
        ('clients', '0013_rename_clients_adm_admin_u_idx_clients_adm_admin_u_b673c4_idx_and_more'),
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
    ]
