from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0013_rename_clients_adm_admin_u_idx_clients_adm_admin_u_b673c4_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('loans', '0012_alter_approvallog_approval_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoanApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application_number', models.CharField(max_length=50, unique=True)),
                ('loan_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('duration_days', models.IntegerField()),
                ('purpose', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('pending', 'Pending Manager Approval'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approval_date', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_loan_applications', to=settings.AUTH_USER_MODEL)),
                ('borrower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loan_applications', to=settings.AUTH_USER_MODEL)),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='clients.borrowergroup')),
                ('loan_officer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_loan_applications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
