# Generated migration to add residential_address field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_employment_business_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='residential_address',
            field=models.TextField(blank=True),
        ),
    ]
