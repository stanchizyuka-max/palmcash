# Generated migration for ClientDocument and ClientVerification models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import documents.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('nrc_front', 'NRC Card - Front'), ('nrc_back', 'NRC Card - Back'), ('selfie', 'Live Photo (Selfie)')], help_text='Type of document', max_length=20)),
                ('image', models.ImageField(help_text='Document image (JPG or PNG)', upload_to=documents.models.document_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', help_text='Document verification status', max_length=20)),
                ('verification_date', models.DateTimeField(blank=True, help_text='When document was verified', null=True)),
                ('verification_notes', models.TextField(blank=True, help_text='Notes from verification (e.g., reason for rejection)')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(limit_choices_to={'role': 'borrower'}, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(blank=True, help_text='User who verified this document', limit_choices_to={'role__in': ['manager', 'admin']}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_client_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Client Document',
                'verbose_name_plural': 'Client Documents',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='ClientVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending - Documents Required'), ('documents_submitted', 'Documents Submitted - Awaiting Review'), ('documents_rejected', 'Documents Rejected - Resubmission Required'), ('verified', 'Verified - Ready for Loans'), ('rejected', 'Rejected - Cannot Apply for Loans')], default='pending', help_text='Overall verification status', max_length=30)),
                ('nrc_front_uploaded', models.BooleanField(default=False)),
                ('nrc_back_uploaded', models.BooleanField(default=False)),
                ('selfie_uploaded', models.BooleanField(default=False)),
                ('all_documents_approved', models.BooleanField(default=False)),
                ('verification_date', models.DateTimeField(blank=True, help_text='When client was verified', null=True)),
                ('rejection_reason', models.TextField(blank=True, help_text='Reason for rejection (if applicable)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.OneToOneField(limit_choices_to={'role': 'borrower'}, on_delete=django.db.models.deletion.CASCADE, related_name='verification', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(blank=True, help_text='User who verified this client', limit_choices_to={'role__in': ['manager', 'admin']}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_clients', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Client Verification',
                'verbose_name_plural': 'Client Verifications',
            },
        ),
        migrations.AddIndex(
            model_name='clientdocument',
            index=models.Index(fields=['client', 'status'], name='documents_c_client_status_idx'),
        ),
        migrations.AddIndex(
            model_name='clientdocument',
            index=models.Index(fields=['status', '-uploaded_at'], name='documents_c_status_uploaded_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='clientdocument',
            unique_together={('client', 'document_type')},
        ),
    ]
