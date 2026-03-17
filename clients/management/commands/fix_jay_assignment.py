from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix Jay OfficerAssignment for branch visibility'

    def handle(self, *args, **options):
        self.stdout.write("Fixing Jay's OfficerAssignment...")

        jay = User.objects.filter(username='jay').first()
        if not jay:
            self.stdout.write(self.style.ERROR('Jay user not found'))
            return

        self.stdout.write(f"Found: {jay.get_full_name()} | role: {jay.role}")

        with connection.cursor() as cursor:
            # Check what columns exist on the table
            cursor.execute("DESCRIBE clients_officerassignment")
            columns = {row[0]: row for row in cursor.fetchall()}
            self.stdout.write(f"Table columns: {list(columns.keys())}")

            # Check if assignment already exists
            cursor.execute(
                "SELECT id, branch FROM clients_officerassignment WHERE officer_id = %s",
                [jay.pk]
            )
            row = cursor.fetchone()

            if row:
                self.stdout.write(f"OfficerAssignment exists (id={row[0]}) | branch: '{row[1]}'")
                if not row[1]:
                    cursor.execute(
                        "UPDATE clients_officerassignment SET branch = %s WHERE officer_id = %s",
                        ['Kamwala', jay.pk]
                    )
                    self.stdout.write(self.style.SUCCESS("Updated branch to 'Kamwala'"))
                return

            # Need to create — figure out which columns exist
            self.stdout.write("No assignment found — creating via raw SQL...")

            if 'branch_id' in columns:
                # Production DB has branch as FK — find or create the branch row
                cursor.execute("DESCRIBE clients_branch")
                self.stdout.write("Branch table exists")
                cursor.execute("SELECT id, name FROM clients_branch WHERE name LIKE %s", ['%amwala%'])
                branch_row = cursor.fetchone()
                if not branch_row:
                    cursor.execute(
                        "INSERT INTO clients_branch (name, code, location, is_active, created_at, updated_at) "
                        "VALUES (%s, %s, %s, 1, NOW(), NOW())",
                        ['Kamwala', 'KM', 'Kamwala, Lusaka']
                    )
                    branch_id = cursor.lastrowid
                    self.stdout.write(self.style.SUCCESS(f"Created branch id={branch_id}"))
                else:
                    branch_id = branch_row[0]
                    self.stdout.write(f"Found branch id={branch_id} name='{branch_row[1]}'")

                cursor.execute(
                    "INSERT INTO clients_officerassignment "
                    "(officer_id, branch_id, max_groups, max_clients, is_accepting_assignments, created_at, updated_at) "
                    "VALUES (%s, %s, 15, 50, 1, NOW(), NOW())",
                    [jay.pk, branch_id]
                )
                self.stdout.write(self.style.SUCCESS(f"Created OfficerAssignment with branch_id={branch_id}"))

            else:
                # branch is a CharField
                cursor.execute(
                    "INSERT INTO clients_officerassignment "
                    "(officer_id, branch, max_groups, max_clients, is_accepting_assignments, created_at, updated_at) "
                    "VALUES (%s, %s, 15, 50, 1, NOW(), NOW())",
                    [jay.pk, 'Kamwala']
                )
                self.stdout.write(self.style.SUCCESS("Created OfficerAssignment with branch='Kamwala'"))

        self.stdout.write(self.style.SUCCESS('\nDone.'))
