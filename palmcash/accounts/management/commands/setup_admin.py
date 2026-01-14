from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Create or update a superuser with admin role'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the admin user')
        parser.add_argument('email', type=str, help='Email for the admin user')
        parser.add_argument('password', type=str, help='Password for the admin user')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Create or update the superuser
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'role': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
            }
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created superuser: {username}'))
        else:
            # Update existing user
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.role = 'admin'
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated superuser: {username}'))

        self.stdout.write(self.style.SUCCESS(f'✓ Role set to: admin'))
        self.stdout.write(self.style.SUCCESS(f'✓ You can now log in with:'))
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Password: {password}')
