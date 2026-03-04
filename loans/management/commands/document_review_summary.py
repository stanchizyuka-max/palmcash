from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from datetime import date, timedelta
from loans.models import LoanDocument, Loan
from accounts.models import User
from common.utils import get_system_launch_date, format_system_period


class Command(BaseCommand):
    help = 'Generate document review summary for administrators'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back for statistics (default: 7)'
        )
        parser.add_argument(
            '--email-admins',
            action='store_true',
            help='Send email summary to administrators'
        )

    def handle(self, *args, **options):
        days_back = options['days']
        email_admins = options['email_admins']
        
        self.stdout.write(
            self.style.SUCCESS(f'📋 Document Review Summary (Last {days_back} days)')
        )
        self.stdout.write('=' * 60)
        
        # Calculate date range (but not before system launch)
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        system_launch = get_system_launch_date()
        
        # Don't go before system launch date
        if start_date < system_launch:
            start_date = system_launch
            self.stdout.write(
                self.style.WARNING(f'Note: Analysis limited to system launch date ({system_launch})')
            )
        
        # Overall statistics
        total_docs = LoanDocument.objects.count()
        pending_docs = LoanDocument.objects.filter(is_verified=False).count()
        verified_docs = LoanDocument.objects.filter(is_verified=True).count()
        
        # Recent statistics (from system launch or specified period)
        recent_uploads = LoanDocument.objects.filter(
            uploaded_at__date__gte=start_date
        ).count()
        
        recent_verifications = LoanDocument.objects.filter(
            verified_at__date__gte=start_date
        ).count()
        
        # System-wide statistics (from launch date)
        system_uploads = LoanDocument.objects.filter(
            uploaded_at__date__gte=system_launch
        ).count()
        
        system_verifications = LoanDocument.objects.filter(
            verified_at__date__gte=system_launch
        ).count()
        
        # Display overall stats
        self.stdout.write('\n📊 OVERALL STATISTICS:')
        self.stdout.write(f'   Total Documents: {total_docs}')
        self.stdout.write(f'   Pending Review: {pending_docs}')
        self.stdout.write(f'   Verified: {verified_docs}')
        
        if total_docs > 0:
            verification_rate = (verified_docs / total_docs) * 100
            self.stdout.write(f'   Verification Rate: {verification_rate:.1f}%')
        
        # Display recent activity
        period_desc = format_system_period(start_date, end_date)
        self.stdout.write(f'\n📈 RECENT ACTIVITY ({period_desc}):')
        self.stdout.write(f'   New Uploads: {recent_uploads}')
        self.stdout.write(f'   New Verifications: {recent_verifications}')
        
        # Display system-wide activity since launch
        system_period = format_system_period()
        self.stdout.write(f'\n🚀 SYSTEM-WIDE ACTIVITY ({system_period}):')
        self.stdout.write(f'   Total Uploads: {system_uploads}')
        self.stdout.write(f'   Total Verifications: {system_verifications}')
        
        # Pending documents by loan
        if pending_docs > 0:
            self.stdout.write('\n⏳ PENDING DOCUMENTS BY LOAN:')
            pending_by_loan = {}
            for doc in LoanDocument.objects.filter(is_verified=False).select_related('loan'):
                loan_id = doc.loan.application_number
                if loan_id not in pending_by_loan:
                    pending_by_loan[loan_id] = {
                        'loan': doc.loan,
                        'count': 0,
                        'types': []
                    }
                pending_by_loan[loan_id]['count'] += 1
                pending_by_loan[loan_id]['types'].append(doc.get_document_type_display())
            
            for loan_id, data in pending_by_loan.items():
                loan = data['loan']
                self.stdout.write(
                    f'   📄 {loan_id} ({loan.borrower.full_name}): '
                    f'{data["count"]} document(s) - {", ".join(data["types"])}'
                )
        
        # Document types breakdown
        self.stdout.write('\n📋 DOCUMENT TYPES BREAKDOWN:')
        from django.db.models import Count
        doc_type_stats = LoanDocument.objects.values('document_type').annotate(
            total=Count('id'),
            verified=Count('id', filter=models.Q(is_verified=True)),
            pending=Count('id', filter=models.Q(is_verified=False))
        ).order_by('-total')
        
        for stat in doc_type_stats:
            doc_type = dict(LoanDocument.DOCUMENT_TYPE_CHOICES)[stat['document_type']]
            self.stdout.write(
                f'   {doc_type}: {stat["total"]} total '
                f'({stat["verified"]} verified, {stat["pending"]} pending)'
            )
        
        # Top verifiers
        self.stdout.write('\n👥 TOP VERIFIERS (Last 30 days):')
        recent_verifiers = LoanDocument.objects.filter(
            verified_at__date__gte=date.today() - timedelta(days=30),
            verified_by__isnull=False
        ).values('verified_by__username', 'verified_by__first_name', 'verified_by__last_name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        for verifier in recent_verifiers:
            name = f"{verifier['verified_by__first_name']} {verifier['verified_by__last_name']}".strip()
            if not name:
                name = verifier['verified_by__username']
            self.stdout.write(f'   {name}: {verifier["count"]} verifications')
        
        # Recommendations
        self.stdout.write('\n💡 RECOMMENDATIONS:')
        if pending_docs > 10:
            self.stdout.write('   ⚠️  High number of pending documents - consider additional review resources')
        
        if total_docs > 0 and (verified_docs / total_docs) < 0.8:
            self.stdout.write('   📈 Verification rate below 80% - prioritize document review')
        
        if recent_uploads > recent_verifications * 2:
            self.stdout.write('   🚀 Upload rate exceeding verification rate - review backlog building')
        
        # Admin access information
        self.stdout.write('\n🔗 ADMIN ACCESS LINKS:')
        self.stdout.write('   Django Admin: /admin/loans/loandocument/')
        self.stdout.write('   Review Dashboard: /loans/documents/review-dashboard/')
        self.stdout.write('   Loan Dashboard: /loans/status-dashboard/')
        
        # Email summary to admins if requested
        if email_admins:
            self._email_summary_to_admins(
                total_docs, pending_docs, verified_docs, 
                recent_uploads, recent_verifications, days_back
            )
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS('📋 Document Review Summary Complete!')
        )

    def _email_summary_to_admins(self, total_docs, pending_docs, verified_docs, 
                                recent_uploads, recent_verifications, days_back):
        """Send email summary to administrators"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            admins = User.objects.filter(
                role__in=['admin', 'loan_officer'],
                email__isnull=False
            ).exclude(email='')
            
            if not admins.exists():
                self.stdout.write(
                    self.style.WARNING('No administrators with email addresses found.')
                )
                return
            
            subject = f'Document Review Summary - {pending_docs} Pending'
            
            message = f"""
Document Review Summary Report

OVERALL STATISTICS:
- Total Documents: {total_docs}
- Pending Review: {pending_docs}
- Verified: {verified_docs}
- Verification Rate: {(verified_docs/total_docs*100):.1f}% if total_docs > 0 else 0

RECENT ACTIVITY (Last {days_back} days):
- New Uploads: {recent_uploads}
- New Verifications: {recent_verifications}

ACTION REQUIRED:
{'⚠️ Please review pending documents at: /admin/loans/loandocument/' if pending_docs > 0 else '✅ All documents are up to date!'}

Access the admin panel at: /admin/loans/loandocument/
Review dashboard at: /loans/documents/review-dashboard/

This is an automated summary from the LoanVista system.
            """
            
            admin_emails = [admin.email for admin in admins]
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'📧 Email summary sent to {len(admin_emails)} administrators')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send email summary: {e}')
            )
