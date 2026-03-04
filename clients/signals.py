"""
Signal handlers for clients app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


@receiver(post_save, sender=User)
def assign_loan_officer_permissions(sender, instance, created, **kwargs):
    """
    Automatically assign group management permissions to loan officers
    """
    if instance.role == 'loan_officer':
        # Get or create Loan Officers group
        loan_officer_group, _ = Group.objects.get_or_create(name='Loan Officers')
        
        # Add user to the group
        instance.groups.add(loan_officer_group)
        
        # Get BorrowerGroup content type
        try:
            from .models import BorrowerGroup
            content_type = ContentType.objects.get_for_model(BorrowerGroup)
            
            # Get or create the custom permission
            can_create_group, _ = Permission.objects.get_or_create(
                codename='can_create_group',
                content_type=content_type,
                defaults={'name': 'Can create borrower groups'}
            )
            
            # Add permissions to the group
            loan_officer_group.permissions.add(can_create_group)
            
            # Also add standard permissions
            for codename in ['add_borrowergroup', 'change_borrowergroup', 'view_borrowergroup']:
                try:
                    perm = Permission.objects.get(
                        codename=codename,
                        content_type=content_type
                    )
                    loan_officer_group.permissions.add(perm)
                except Permission.DoesNotExist:
                    pass
        except Exception as e:
            # Don't fail user creation if permission assignment fails
            print(f"Error assigning permissions to loan officer: {e}")
