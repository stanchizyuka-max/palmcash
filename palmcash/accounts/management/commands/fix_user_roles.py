from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix user roles - set superusers to admin and ensure all users have a role'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Fix all users with missing or invalid roles',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all users and their roles',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_users()
        elif options['fix_all']:
            self.fix_all_users()
        else:
            self.fix_superusers()

    def list_users(self):
        """List all users and their roles"""
        users = User.objects.all()
        self.stdout.write(self.style.SUCCESS(f'\nTotal users: {users.count()}\n'))
        self.stdout.write(f'{"ID":<5} {"Username":<20} {"Role":<15} {"Superuser":<10}')
        self.stdout.write('-' * 50)
        
        for user in users:
            role = user.role if hasattr(user, 'role') and user.role else 'NONE'
            is_super = 'Yes' if user.is_superuser else 'No'
            self.stdout.write(f'{user.id:<5} {user.username:<20} {role:<15} {is_super:<10}')

    def fix_superusers(self):
        """Set superusers to admin role"""
        superusers = User.objects.filter(is_superuser=True)
        count = 0
        
        for user in superusers:
            if not user.role or user.role != 'admin':
                user.role = 'admin'
                user.save()
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Set {user.username} to admin role')
                )
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No superusers needed role update'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Fixed {count} superuser(s)')
            )

    def fix_all_users(self):
        """Fix all users with missing or invalid roles"""
        users = User.objects.all()
        fixed_count = 0
        
        valid_roles = ['admin', 'manager', 'loan_officer', 'borrower']
        
        for user in users:
            needs_fix = False
            
            # Check if role is missing
            if not user.role:
                needs_fix = True
                if user.is_superuser:
                    user.role = 'admin'
                else:
                    user.role = 'borrower'
            
            # Check if role is invalid
            elif user.role not in valid_roles:
                needs_fix = True
                if user.is_superuser:
                    user.role = 'admin'
                else:
                    user.role = 'borrower'
            
            # Ensure superusers are admins
            if user.is_superuser and user.role != 'admin':
                needs_fix = True
                user.role = 'admin'
            
            if needs_fix:
                user.save()
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Fixed {user.username} - role set to {user.role}')
                )
        
        if fixed_count == 0:
            self.stdout.write(self.style.WARNING('All users have valid roles'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Fixed {fixed_count} user(s)')
            )
