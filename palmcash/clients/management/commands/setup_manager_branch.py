"""
Management command to set up a manager with a branch assignment.
Usage: python manage.py setup_manager_branch
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clients.models import Branch

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up a manager with a branch assignment'

    def handle(self, *args, **options):
        # Get all manager users
        managers = User.objects.filter(role='manager')
        
        if not managers.exists():
            self.stdout.write(self.style.ERROR('No manager users found in the system.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {managers.count()} manager(s):'))
        for i, manager in enumerate(managers, 1):
            self.stdout.write(f'{i}. {manager.full_name} ({manager.username})')
        
        # Get or create a default branch
        branch, created = Branch.objects.get_or_create(
            name='Main Branch',
            defaults={
                'code': 'MB',
                'location': 'Main Office',
                'phone': '+260-XXX-XXXX',
                'email': 'main@palmcash.com',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created new branch: {branch.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Using existing branch: {branch.name}'))
        
        # Assign the first manager to the branch
        manager = managers.first()
        branch.manager = manager
        branch.save()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Assigned {manager.full_name} to {branch.name}'))
        self.stdout.write(self.style.SUCCESS('Manager dashboard should now be accessible!'))
