# Generated migration for adding Branch model, AdminAuditLog, and updating relationships

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0001_initial'),
    ]

    operations = [
        # Create Branch model first
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('code', models.CharField(help_text='Branch code (e.g., MB, SB1)', max_length=20, unique=True)),
                ('location', models.CharField(help_text='Physical location/address', max_length=200)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('manager', models.OneToOneField(
                    blank=True,
                    help_text='Branch manager',
                    limit_choices_to={'role': 'manager'},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='managed_branch',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Branch',
                'verbose_name_plural': 'Branches',
                'ordering': ['name'],
            },
        ),
        
        # Create AdminAuditLog model
        migrations.CreateModel(
            name='AdminAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('branch_create', 'Create Branch'),
                        ('branch_update', 'Update Branch'),
                        ('branch_delete', 'Delete Branch'),
                        ('officer_transfer', 'Transfer Officer'),
                        ('officer_update', 'Update Officer'),
                        ('group_transfer', 'Transfer Group'),
                        ('client_transfer', 'Transfer Client'),
                        ('loan_approve', 'Approve Loan'),
                        ('loan_reject', 'Reject Loan'),
                        ('override_assignment', 'Override Assignment'),
                        ('other', 'Other'),
                    ],
                    help_text='Type of action performed',
                    max_length=50
                )),
                ('description', models.TextField(help_text='Description of the action')),
                ('old_value', models.TextField(blank=True, help_text='Previous value (if applicable)')),
                ('new_value', models.TextField(blank=True, help_text='New value (if applicable)')),
                ('timestamp', models.DateTimeField(auto_now_add=True, help_text='When this action occurred')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of the admin', null=True)),
                ('admin_user', models.ForeignKey(
                    help_text='Admin who performed the action',
                    limit_choices_to={'role': 'admin'},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='admin_actions',
                    to=settings.AUTH_USER_MODEL
                )),
                ('affected_branch', models.ForeignKey(
                    blank=True,
                    help_text='Branch affected by this action',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='admin_actions',
                    to='clients.branch'
                )),
                ('affected_group', models.ForeignKey(
                    blank=True,
                    help_text='Group affected by this action',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='admin_actions',
                    to='clients.borrowergroup'
                )),
                ('affected_user', models.ForeignKey(
                    blank=True,
                    help_text='User affected by this action',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='admin_affected_actions',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Admin Audit Log',
                'verbose_name_plural': 'Admin Audit Logs',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Add indexes to AdminAuditLog
        migrations.AddIndex(
            model_name='adminauditlog',
            index=models.Index(fields=['admin_user', '-timestamp'], name='clients_adm_admin_u_idx'),
        ),
        migrations.AddIndex(
            model_name='adminauditlog',
            index=models.Index(fields=['action', '-timestamp'], name='clients_adm_action_idx'),
        ),
        migrations.AddIndex(
            model_name='adminauditlog',
            index=models.Index(fields=['affected_user', '-timestamp'], name='clients_adm_affected_idx'),
        ),
    ]
