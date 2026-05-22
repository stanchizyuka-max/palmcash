"""
Management command to add audit timestamp columns to loans_loan table.

This script adds the columns directly using raw SQL, bypassing Django migrations.
Use this when migration dependencies are broken.

Usage:
    python manage.py add_audit_columns
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Add audit timestamp columns to loans_loan table'

    def handle(self, *args, **options):
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('Adding Audit Timestamp Columns'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('')
        
        with connection.cursor() as cursor:
            # Check if columns already exist
            self.stdout.write('🔍 Checking if columns already exist...')
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'loans_loan' 
                AND COLUMN_NAME IN ('approval_recorded_at', 'disbursement_recorded_at')
            """)
            
            existing_count = cursor.fetchone()[0]
            
            if existing_count == 2:
                self.stdout.write(self.style.SUCCESS('✅ Both columns already exist!'))
                self.stdout.write('')
                self._show_columns(cursor)
                return
            elif existing_count == 1:
                self.stdout.write(self.style.WARNING('⚠️  One column exists, will add the missing one'))
            else:
                self.stdout.write('📝 No columns exist yet, will add both')
            
            self.stdout.write('')
            
            # Add approval_recorded_at if it doesn't exist
            try:
                self.stdout.write('Adding approval_recorded_at column...')
                cursor.execute("""
                    ALTER TABLE loans_loan 
                    ADD COLUMN approval_recorded_at DATETIME(6) NULL 
                    COMMENT 'System timestamp: when approval was recorded in the system'
                """)
                self.stdout.write(self.style.SUCCESS('  ✅ approval_recorded_at added'))
            except Exception as e:
                if 'Duplicate column name' in str(e):
                    self.stdout.write(self.style.WARNING('  ⏭️  approval_recorded_at already exists'))
                else:
                    self.stdout.write(self.style.ERROR(f'  ❌ Error: {e}'))
                    raise
            
            # Add disbursement_recorded_at if it doesn't exist
            try:
                self.stdout.write('Adding disbursement_recorded_at column...')
                cursor.execute("""
                    ALTER TABLE loans_loan 
                    ADD COLUMN disbursement_recorded_at DATETIME(6) NULL 
                    COMMENT 'System timestamp: when disbursement was recorded in the system'
                """)
                self.stdout.write(self.style.SUCCESS('  ✅ disbursement_recorded_at added'))
            except Exception as e:
                if 'Duplicate column name' in str(e):
                    self.stdout.write(self.style.WARNING('  ⏭️  disbursement_recorded_at already exists'))
                else:
                    self.stdout.write(self.style.ERROR(f'  ❌ Error: {e}'))
                    raise
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('✅ Columns Added Successfully'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write('')
            
            # Show the columns
            self._show_columns(cursor)
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 Done! You can now run:'))
            self.stdout.write(self.style.SUCCESS('   python manage.py fix_backdated_loans --dry-run'))
            self.stdout.write('')
    
    def _show_columns(self, cursor):
        """Show the newly added columns"""
        self.stdout.write('📋 Column Details:')
        self.stdout.write('')
        
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                COLUMN_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_COMMENT
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'loans_loan' 
            AND COLUMN_NAME IN ('approval_recorded_at', 'disbursement_recorded_at')
            ORDER BY COLUMN_NAME
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            for row in rows:
                col_name, col_type, nullable, default, comment = row
                self.stdout.write(f'  Column: {col_name}')
                self.stdout.write(f'    Type: {col_type}')
                self.stdout.write(f'    Nullable: {nullable}')
                self.stdout.write(f'    Default: {default or "NULL"}')
                self.stdout.write(f'    Comment: {comment or "None"}')
                self.stdout.write('')
        else:
            self.stdout.write(self.style.ERROR('  ❌ Columns not found!'))
