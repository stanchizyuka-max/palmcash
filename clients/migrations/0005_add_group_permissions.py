"""
Migration to add custom permissions for group management
"""
from django.db import migrations


def add_group_permissions(apps, schema_editor):
    """Add custom permissions for group management"""
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Group = apps.get_model('auth', 'Group')
    
    # Get the BorrowerGroup content type
    try:
        borrower_group_ct = ContentType.objects.get(app_label='clients', model='borrowergroup')
    except ContentType.DoesNotExist:
        # Content type doesn't exist yet, skip
        return
    
    # Create custom permission for group creation
    can_create_group, created = Permission.objects.get_or_create(
        codename='can_create_group',
        content_type=borrower_group_ct,
        defaults={
            'name': 'Can create borrower groups'
        }
    )
    
    # Create or get loan officer group
    loan_officer_group, created = Group.objects.get_or_create(name='Loan Officers')
    
    # Add permission to loan officer group
    loan_officer_group.permissions.add(can_create_group)
    
    # Also add standard permissions
    add_permission = Permission.objects.filter(
        codename='add_borrowergroup',
        content_type=borrower_group_ct
    ).first()
    if add_permission:
        loan_officer_group.permissions.add(add_permission)
    
    change_permission = Permission.objects.filter(
        codename='change_borrowergroup',
        content_type=borrower_group_ct
    ).first()
    if change_permission:
        loan_officer_group.permissions.add(change_permission)
    
    view_permission = Permission.objects.filter(
        codename='view_borrowergroup',
        content_type=borrower_group_ct
    ).first()
    if view_permission:
        loan_officer_group.permissions.add(view_permission)


def remove_group_permissions(apps, schema_editor):
    """Remove custom permissions (reverse migration)"""
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    
    try:
        borrower_group_ct = ContentType.objects.get(app_label='clients', model='borrowergroup')
        Permission.objects.filter(
            codename='can_create_group',
            content_type=borrower_group_ct
        ).delete()
    except ContentType.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_borrowergroup_branch_borrowergroup_payment_day_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(add_group_permissions, remove_group_permissions),
    ]
