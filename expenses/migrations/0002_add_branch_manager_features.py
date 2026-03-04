# Generated migration for Branch Manager features

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('expenses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Unique expense code (e.g., EXP-001)', max_length=20, unique=True)),
                ('name', models.CharField(help_text='Expense category name', max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Expense Code',
                'verbose_name_plural': 'Expense Codes',
                'ordering': ['code'],
            },
        ),
        migrations.AddField(
            model_name='expense',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                default='pending',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='expense',
            name='approval_comments',
            field=models.TextField(blank=True, help_text='Comments from approver'),
        ),
        migrations.AddField(
            model_name='expense',
            name='rejection_reason',
            field=models.TextField(blank=True, help_text='Reason for rejection if rejected'),
        ),
        migrations.AlterField(
            model_name='expense',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'role__in': ['manager', 'admin']},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_expenses',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='expense',
            name='expense_code',
            field=models.ForeignKey(
                blank=True,
                help_text='Expense code for categorization',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='expenses',
                to='expenses.expensecode'
            ),
        ),
        migrations.CreateModel(
            name='ExpenseApprovalLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[('approved', 'Approved'), ('rejected', 'Rejected'), ('pending', 'Pending')],
                    max_length=20
                )),
                ('comments', models.TextField(blank=True, help_text='Approval or rejection comments')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('approved_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='expense_approvals',
                    to=settings.AUTH_USER_MODEL
                )),
                ('expense', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_logs', to='expenses.expense')),
            ],
            options={
                'verbose_name': 'Expense Approval Log',
                'verbose_name_plural': 'Expense Approval Logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='FundsTransfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(
                    decimal_places=2,
                    help_text='Amount to transfer',
                    max_digits=12,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]
                )),
                ('source_branch', models.CharField(help_text='Branch sending the funds', max_length=100)),
                ('destination_branch', models.CharField(help_text='Branch receiving the funds', max_length=100)),
                ('reference_number', models.CharField(help_text='Transfer reference number', max_length=50, unique=True)),
                ('description', models.TextField(blank=True, help_text='Description of the transfer')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed')],
                    default='pending',
                    max_length=20
                )),
                ('requested_date', models.DateTimeField(auto_now_add=True)),
                ('approval_date', models.DateTimeField(blank=True, null=True)),
                ('completion_date', models.DateTimeField(blank=True, null=True)),
                ('approval_comments', models.TextField(blank=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(
                    blank=True,
                    limit_choices_to={'role__in': ['manager', 'admin']},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approved_transfers',
                    to=settings.AUTH_USER_MODEL
                )),
                ('requested_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='requested_transfers',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Funds Transfer',
                'verbose_name_plural': 'Funds Transfers',
                'ordering': ['-requested_date'],
            },
        ),
        migrations.CreateModel(
            name='BankDeposit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(
                    decimal_places=2,
                    help_text='Amount deposited',
                    max_digits=12,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]
                )),
                ('source_branch', models.CharField(help_text='Branch depositing the funds', max_length=100)),
                ('bank_name', models.CharField(help_text='Name of the bank', max_length=100)),
                ('account_number', models.CharField(help_text='Bank account number', max_length=50)),
                ('reference_number', models.CharField(help_text='Deposit reference number', max_length=50, unique=True)),
                ('deposit_slip_number', models.CharField(blank=True, help_text='Bank deposit slip number', max_length=50)),
                ('description', models.TextField(blank=True, help_text='Description of the deposit')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed')],
                    default='pending',
                    max_length=20
                )),
                ('requested_date', models.DateTimeField(auto_now_add=True)),
                ('approval_date', models.DateTimeField(blank=True, null=True)),
                ('deposit_date', models.DateField(blank=True, help_text='Date of actual deposit', null=True)),
                ('completion_date', models.DateTimeField(blank=True, null=True)),
                ('approval_comments', models.TextField(blank=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(
                    blank=True,
                    limit_choices_to={'role__in': ['manager', 'admin']},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approved_deposits',
                    to=settings.AUTH_USER_MODEL
                )),
                ('requested_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='requested_deposits',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Bank Deposit',
                'verbose_name_plural': 'Bank Deposits',
                'ordering': ['-requested_date'],
            },
        ),
    ]
