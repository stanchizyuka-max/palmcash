# Generated migration for adding assigned_officer field

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='assigned_officer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_clients',
                to=settings.AUTH_USER_MODEL,
                limit_choices_to={'role': 'loan_officer'},
                help_text='Loan officer assigned to this client'
            ),
        ),
    ]
