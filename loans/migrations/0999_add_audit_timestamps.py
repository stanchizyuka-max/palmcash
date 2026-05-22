# Generated migration for adding audit timestamp fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0098_loanapplication_processing_fee_and_more'),  # Update this to your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='loan',
            name='approval_recorded_at',
            field=models.DateTimeField(blank=True, help_text='System timestamp: when approval was recorded in the system', null=True),
        ),
        migrations.AddField(
            model_name='loan',
            name='disbursement_recorded_at',
            field=models.DateTimeField(blank=True, help_text='System timestamp: when disbursement was recorded in the system', null=True),
        ),
    ]
