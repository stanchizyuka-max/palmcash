# Generated migration for login tracking models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_add_guarantor_relationship'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLoginSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('login_time', models.DateTimeField(auto_now_add=True)),
                ('logout_time', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('session_key', models.CharField(blank=True, max_length=40)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='login_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-login_time'],
            },
        ),
        migrations.CreateModel(
            name='UserActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('login', 'Login'), ('logout', 'Logout'), ('password_change', 'Password Change'), ('user_create', 'Create User'), ('user_update', 'Update User'), ('user_delete', 'Delete User'), ('user_activate', 'Activate User'), ('user_deactivate', 'Deactivate User'), ('branch_create', 'Create Branch'), ('branch_update', 'Update Branch'), ('branch_delete', 'Delete Branch'), ('client_create', 'Create Client'), ('client_update', 'Update Client'), ('client_transfer', 'Transfer Client'), ('client_assign', 'Assign Client'), ('group_create', 'Create Group'), ('group_update', 'Update Group'), ('group_add_member', 'Add Group Member'), ('group_remove_member', 'Remove Group Member'), ('loan_apply', 'Apply for Loan'), ('loan_approve', 'Approve Loan'), ('loan_reject', 'Reject Loan'), ('loan_disburse', 'Disburse Loan'), ('loan_edit', 'Edit Loan'), ('loan_transfer', 'Transfer Loan'), ('payment_record', 'Record Payment'), ('payment_confirm', 'Confirm Payment'), ('payment_reject', 'Reject Payment'), ('collection_record', 'Record Collection'), ('default_collection', 'Default Collection'), ('security_create', 'Create Security Deposit'), ('security_verify', 'Verify Security Deposit'), ('security_topup', 'Security Top-up'), ('security_return', 'Security Return'), ('document_upload', 'Upload Document'), ('document_verify', 'Verify Document'), ('document_delete', 'Delete Document'), ('payroll_generate', 'Generate Payroll'), ('payroll_payment', 'Process Payroll Payment'), ('salary_update', 'Update Salary'), ('report_view', 'View Report'), ('report_export', 'Export Report'), ('dashboard_view', 'View Dashboard'), ('other', 'Other Action')], max_length=50)),
                ('target_type', models.CharField(blank=True, help_text='Type of target (client, loan, branch, etc.)', max_length=50)),
                ('target_id', models.CharField(blank=True, help_text='ID of the target object', max_length=100)),
                ('target_name', models.CharField(blank=True, help_text='Name/description of target', max_length=255)),
                ('description', models.TextField()),
                ('severity', models.CharField(choices=[('info', 'Info'), ('warning', 'Warning'), ('critical', 'Critical')], default='info', max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('old_value', models.TextField(blank=True)),
                ('new_value', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='userloginsession',
            index=models.Index(fields=['user', '-login_time'], name='accounts_us_user_id_login_t_idx'),
        ),
        migrations.AddIndex(
            model_name='userloginsession',
            index=models.Index(fields=['is_active', '-login_time'], name='accounts_us_is_acti_login_t_idx'),
        ),
        migrations.AddIndex(
            model_name='useractivitylog',
            index=models.Index(fields=['user', '-timestamp'], name='accounts_ua_user_id_timest_idx'),
        ),
        migrations.AddIndex(
            model_name='useractivitylog',
            index=models.Index(fields=['action', '-timestamp'], name='accounts_ua_action_timest_idx'),
        ),
        migrations.AddIndex(
            model_name='useractivitylog',
            index=models.Index(fields=['severity', '-timestamp'], name='accounts_ua_severit_timest_idx'),
        ),
        migrations.AddIndex(
            model_name='useractivitylog',
            index=models.Index(fields=['target_type', 'target_id'], name='accounts_ua_target__target__idx'),
        ),
    ]
