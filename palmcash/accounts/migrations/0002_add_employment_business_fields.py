# Generated migration to add employment and business fields to User model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='employment_status',
            field=models.CharField(
                blank=True,
                choices=[('employed', 'Employed'), ('self_employed', 'Self Employed'), ('unemployed', 'Unemployed'), ('student', 'Student'), ('retired', 'Retired')],
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='employer_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='user',
            name='employer_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='employment_duration',
            field=models.IntegerField(blank=True, null=True, help_text='Employment duration in years'),
        ),
        migrations.AddField(
            model_name='user',
            name='monthly_income',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='business_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='user',
            name='business_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='business_duration',
            field=models.IntegerField(blank=True, null=True, help_text='Business duration in years'),
        ),
        migrations.AddField(
            model_name='user',
            name='residential_duration',
            field=models.IntegerField(blank=True, null=True, help_text='Residential duration in years'),
        ),
        migrations.AddField(
            model_name='user',
            name='reference1_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='user',
            name='reference1_phone',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='user',
            name='reference1_relationship',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='reference2_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='user',
            name='reference2_phone',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='user',
            name='reference2_relationship',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
