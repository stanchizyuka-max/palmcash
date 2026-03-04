# Generated migration for adding approval and security models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('loans', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoanApprovalRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                    default='pending',
                    max_length=20
                )),
                ('requested_date', models.DateTimeField(auto_now_add=True)),
                ('approval_date', models.DateTimeField(blank=True, null=True)),
                ('approval_notes', models.TextField(blank=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(
                    blank=True,
                    limit_choices_to={'role': 'admin'},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approved_loans',
                    to=settings.AUTH_USER_MODEL
                )),
                ('loan', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='approval_request', to='loans.loan')),
                ('requested_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='requested_approvals',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Loan Approval Request',
                'verbose_name_plural': 'Loan Approval Requests',
                'ordering': ['-requested_date'],
            },
        ),
        migrations.CreateModel(
            name='SecurityTopUpRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_amount', models.DecimalField(decimal_places=2, help_text='Amount to add to security deposit', max_digits=12)),
                ('reason', models.TextField(help_text='Reason for security top-up request')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed')],
                    default='pending',
                    max_length=20
                )),
                ('requested_date', models.DateTimeField(auto_now_add=True)),
                ('approval_date', models.DateTimeField(blank=True, null=True)),
                ('completion_date', models.DateTimeField(blank=True, null=True)),
                ('approval_notes', models.TextField(blank=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(
                    blank=True,
                    limit_choices_to={'role__in': ['manager', 'admin']},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approved_topups',
                    to=settings.AUTH_USER_MODEL
                )),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='security_topup_requests', to='loans.loan')),
                ('requested_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='requested_topups',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Security Top-Up Request',
                'verbose_name_plural': 'Security Top-Up Requests',
                'ordering': ['-requested_date'],
            },
        ),
        migrations.CreateModel(
            name='SecurityReturnRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('return_amount', models.DecimalField(decimal_places=2, help_text='Amount to be returned', max_digits=12)),
                ('reason', models.TextField(help_text='Reason for security return request')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed')],
                    default='pending',
                    max_length=20
                )),
                ('requested_date', models.DateTimeField(auto_now_add=True)),
                ('approval_date', models.DateTimeField(blank=True, null=True)),
                ('completion_date', models.DateTimeField(blank=True, null=True)),
                ('approval_notes', models.TextField(blank=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(
                    blank=True,
                    limit_choices_to={'role__in': ['manager', 'admin']},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approved_returns',
                    to=settings.AUTH_USER_MODEL
                )),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='security_return_requests', to='loans.loan')),
                ('requested_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='requested_returns',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Security Return Request',
                'verbose_name_plural': 'Security Return Requests',
                'ordering': ['-requested_date'],
            },
        ),
    ]
