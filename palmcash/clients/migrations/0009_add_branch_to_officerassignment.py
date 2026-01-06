# Generated migration to add branch CharField to OfficerAssignment

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0008_merge_20260105_2129"),
    ]

    operations = [
        # Add the branch CharField to OfficerAssignment
        migrations.AddField(
            model_name='officerassignment',
            name='branch',
            field=models.CharField(
                blank=True,
                help_text='Branch where this loan officer is assigned',
                max_length=100
            ),
        ),
    ]
