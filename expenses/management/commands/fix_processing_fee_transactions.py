"""
Management command to fix vault transactions that are processing fees but labeled as deposits.

This script:
1. Finds all vault transactions with 'deposit' type that mention "Processing fee" in description
2. Changes their transaction_type to 'processing_fee'
3. Provides detailed report of changes

Usage:
    python manage.py fix_processing_fee_transactions --dry-run  # Preview changes
    python manage.py fix_processing_fee_transactions            # Apply changes
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from expenses.models import VaultTransaction


class Command(BaseCommand):
    help = 'Fix vault transactions that are processing fees but labeled as deposits'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be saved'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  LIVE MODE - Changes will be saved to database'))
        
        self.stdout.write('')
        
        # Find all deposit transactions that mention "Processing fee" in description
        processing_fee_deposits = VaultTransaction.objects.filter(
            transaction_type='deposit',
            description__icontains='Processing fee'
        ).order_by('transaction_date')
        
        total_count = processing_fee_deposits.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No processing fee deposits found to fix!'))
            self.stdout.write('   All processing fees are already correctly labeled.')
            return
        
        self.stdout.write(f'📋 Found {total_count} processing fee transactions labeled as deposits')
        self.stdout.write('')
        
        fixed_count = 0
        
        for txn in processing_fee_deposits:
            self.stdout.write(f'🔧 Transaction #{txn.id}')
            self.stdout.write(f'   Date: {txn.transaction_date.strftime("%Y-%m-%d")}')
            self.stdout.write(f'   Branch: {txn.branch}')
            self.stdout.write(f'   Amount: K{txn.amount:,.2f}')
            self.stdout.write(f'   Description: {txn.description[:80]}...' if len(txn.description) > 80 else f'   Description: {txn.description}')
            self.stdout.write(f'   Current Type: {txn.get_transaction_type_display()}')
            
            if not dry_run:
                with transaction.atomic():
                    txn.transaction_type = 'processing_fee'
                    txn.save(update_fields=['transaction_type'])
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Changed to: Processing Fee'))
            else:
                self.stdout.write(self.style.WARNING(f'   [DRY RUN] Would change to: Processing Fee'))
            
            self.stdout.write('')
            fixed_count += 1
        
        # Summary
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Total Transactions Found: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'✅ Transactions Fixed: {fixed_count}'))
        
        if dry_run and fixed_count > 0:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠️  This was a DRY RUN. No changes were saved.'))
            self.stdout.write(self.style.WARNING('   Run without --dry-run to apply changes.'))
        elif fixed_count > 0:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ All changes have been saved to the database.'))
            self.stdout.write('')
            self.stdout.write('🎉 Processing fees now show correctly in vault reports!')
        
        self.stdout.write('')
