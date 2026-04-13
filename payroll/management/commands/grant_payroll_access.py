from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from accounts.models import User


class Command(BaseCommand):
    help = 'Grant or revoke payroll access to a specific user'
    
    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')
        parser.add_argument(
            '--revoke',
            action='store_true',
            help='Revoke payroll access instead of granting'
        )
    
    def handle(self, *args, **options):
        username = options['username']
        revoke = options.get('revoke', False)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        try:
            # Get payroll permissions
            view_perm = Permission.objects.get(codename='can_view_payroll')
            manage_perm = Permission.objects.get(codename='can_manage_payroll')
            
            if revoke:
                user.user_permissions.remove(view_perm, manage_perm)
                self.stdout.write(
                    self.style.SUCCESS(f'✗ Revoked payroll access from {user.get_full_name()}')
                )
            else:
                user.user_permissions.add(view_perm, manage_perm)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Granted payroll access to {user.get_full_name()}')
                )
                self.stdout.write(f'  - can_view_payroll: ✓')
                self.stdout.write(f'  - can_manage_payroll: ✓')
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Payroll permissions not found. Run migrations first: python manage.py migrate payroll')
            )
