from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix OfficerAssignment schema mismatch and create missing assignments'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("DESCRIBE clients_officerassignment")
            columns = {row[0]: row for row in cursor.fetchall()}
            self.stdout.write(f"Current columns: {list(columns.keys())}")

            # Fix schema: replace branch_id FK with branch CharField
            if 'branch_id' in columns and 'branch' not in columns:
                self.stdout.write("Fixing schema: dropping branch_id, adding branch CharField...")
                cursor.execute("ALTER TABLE clients_officerassignment DROP FOREIGN KEY " +
                               self._get_fk_name(cursor, 'clients_officerassignment', 'branch_id'))
                cursor.execute("ALTER TABLE clients_officerassignment DROP COLUMN branch_id")
                cursor.execute("ALTER TABLE clients_officerassignment ADD COLUMN branch VARCHAR(100) NOT NULL DEFAULT ''")
                self.stdout.write(self.style.SUCCESS("Schema fixed."))
            elif 'branch' not in columns and 'branch_id' not in columns:
                cursor.execute("ALTER TABLE clients_officerassignment ADD COLUMN branch VARCHAR(100) NOT NULL DEFAULT ''")
                self.stdout.write(self.style.SUCCESS("Added branch column."))
            else:
                self.stdout.write("Schema looks correct.")

        # Now create missing OfficerAssignments for all loan officers
        from accounts.models import User
        from clients.models import OfficerAssignment

        officers = User.objects.filter(role='loan_officer')
        self.stdout.write(f"\nChecking {officers.count()} loan officers...")

        for officer in officers:
            assignment = OfficerAssignment.objects.filter(officer=officer).first()
            if assignment:
                self.stdout.write(f"  {officer.get_full_name()}: branch='{assignment.branch}'")
            else:
                branch_name = ''
                # Try to infer branch from their groups
                group = officer.managed_groups.filter(branch__gt='').first()
                if group:
                    branch_name = group.branch
                # Or from manager's branch if we can find who created them
                if not branch_name:
                    try:
                        branch_name = officer.created_by_manager_branch or ''
                    except Exception:
                        pass

                OfficerAssignment.objects.create(
                    officer=officer,
                    branch=branch_name,
                    max_groups=15,
                    max_clients=50,
                )
                self.stdout.write(self.style.SUCCESS(
                    f"  Created assignment for {officer.get_full_name()} | branch='{branch_name}'"
                ))

        self.stdout.write(self.style.SUCCESS('\nDone.'))

    def _get_fk_name(self, cursor, table, column):
        cursor.execute("""
            SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = %s AND COLUMN_NAME = %s
            AND CONSTRAINT_SCHEMA = DATABASE()
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """, [table, column])
        row = cursor.fetchone()
        return row[0] if row else f"{table}_{column}_fk"
