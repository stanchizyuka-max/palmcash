# Generated migration for adding collection and passbook models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payments', '0001_initial'),
        ('loans', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentCollection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collection_date', models.DateField(help_text='Date when collection is scheduled')),
                ('expected_amount', models.DecimalField(decimal_places=2, help_text='Amount expected to be collected', max_digits=10)),
                ('collected_amount', models.DecimalField(decimal_places=2, default=0, help_text='Actual amount collected', max_digits=10)),
                ('status', models.CharField(
                    choices=[('scheduled', 'Scheduled'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
                    default='scheduled',
                    max_length=20
                )),
                ('is_partial', models.BooleanField(default=False, help_text='Is this a partial payment?')),
                ('is_default', models.BooleanField(default=False, help_text='Is this a default collection (client missed payment)?')),
                ('is_late', models.BooleanField(default=False, help_text='Is this payment late?')),
                ('actual_collection_date', models.DateTimeField(blank=True, help_text='When the payment was actually collected', null=True)),
                ('notes', models.TextField(blank=True, help_text='Notes about this collection')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('collected_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='collections',
                    to=settings.AUTH_USER_MODEL
                )),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collections', to='loans.loan')),
            ],
            options={
                'verbose_name': 'Payment Collection',
                'verbose_name_plural': 'Payment Collections',
                'ordering': ['-collection_date'],
                'unique_together': {('loan', 'collection_date')},
            },
        ),
        migrations.CreateModel(
            name='PassbookEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_type', models.CharField(
                    choices=[('disbursement', 'Loan Disbursement'), ('security_deposit', 'Security Deposit'), ('payment', 'Payment'), ('penalty', 'Penalty'), ('interest', 'Interest'), ('other', 'Other')],
                    max_length=20
                )),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField(help_text='Description of the entry')),
                ('entry_date', models.DateField(help_text='Date of the entry')),
                ('recorded_date', models.DateTimeField(auto_now_add=True, help_text='When this entry was recorded')),
                ('reference_number', models.CharField(blank=True, help_text='Reference number (e.g., payment number, receipt)', max_length=100)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passbook_entries', to='loans.loan')),
                ('recorded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='passbook_entries',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Passbook Entry',
                'verbose_name_plural': 'Passbook Entries',
                'ordering': ['-entry_date'],
            },
        ),
        migrations.CreateModel(
            name='DefaultProvision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('missed_payment_date', models.DateField(help_text='Date when payment was missed')),
                ('expected_amount', models.DecimalField(decimal_places=2, help_text='Amount that was expected', max_digits=10)),
                ('status', models.CharField(
                    choices=[('active', 'Active'), ('resolved', 'Resolved'), ('waived', 'Waived')],
                    default='active',
                    max_length=20
                )),
                ('resolved_date', models.DateField(blank=True, help_text='Date when default was resolved', null=True)),
                ('resolution_notes', models.TextField(blank=True, help_text='How the default was resolved')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='default_provisions', to='loans.loan')),
            ],
            options={
                'verbose_name': 'Default Provision',
                'verbose_name_plural': 'Default Provisions',
                'ordering': ['-missed_payment_date'],
            },
        ),
    ]
