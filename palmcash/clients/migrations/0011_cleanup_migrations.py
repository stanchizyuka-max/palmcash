# Cleanup migration to remove orphaned migration records

from django.db import migrations


def cleanup_migrations(apps, schema_editor):
    """Remove orphaned migration records from django_migrations table"""
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM django_migrations WHERE app='clients' AND name IN ('0011_add_missing_foreign_keys', '0012_rename_clients_adm_admin_u_idx_clients_adm_admin_u_b673c4_idx_and_more')"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0010_approvalauditlog_clienttransferlog_and_more"),
    ]

    operations = [
        migrations.RunPython(cleanup_migrations),
    ]
