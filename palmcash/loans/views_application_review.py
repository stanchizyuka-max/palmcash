"""
Views for reviewing and downloading client loan applications
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Loan
from accounts.models import User
import json
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors


class ClientApplicationListView(LoginRequiredMixin, ListView):
    """List all client loan applications for review"""
    model = Loan
    template_name = 'loans/application_review_list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter applications based on user role"""
        queryset = Loan.objects.select_related(
            'borrower', 'loan_type', 'loan_officer'
        ).order_by('-application_date')
        
        if self.request.user.role == 'loan_officer':
            # Loan officers see applications for their assigned clients
            queryset = queryset.filter(
                Q(loan_officer=self.request.user) |
                Q(borrower__group_memberships__group__assigned_officer=self.request.user)
            ).distinct()
        elif self.request.user.role == 'manager':
            # Managers see applications in their branch
            if hasattr(self.request.user, 'officer_assignment'):
                branch_name = self.request.user.officer_assignment.branch
                queryset = queryset.filter(
                    Q(loan_officer__officer_assignment__branch=branch_name) |
                    Q(borrower__group_memberships__group__assigned_officer__officer_assignment__branch=branch_name)
                ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Client Applications Review'
        context['total_applications'] = self.get_queryset().count()
        
        # Add status filters
        context['status_choices'] = [
            ('all', 'All Applications'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('active', 'Active'),
            ('disbursed', 'Disbursed'),
            ('completed', 'Completed'),
        ]
        
        # Add date range filters
        today = datetime.now().date()
        context['date_filters'] = [
            ('all', 'All Time'),
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('quarter', 'This Quarter'),
        ]
        
        return context


class ClientApplicationDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a client application"""
    model = Loan
    template_name = 'loans/application_review_detail.html'
    context_object_name = 'application'
    
    def get_queryset(self):
        """Filter applications based on user role"""
        queryset = Loan.objects.select_related(
            'borrower', 'loan_type', 'loan_officer'
        )
        
        if self.request.user.role == 'loan_officer':
            # Loan officers see applications for their assigned clients
            queryset = queryset.filter(
                Q(loan_officer=self.request.user) |
                Q(borrower__group_memberships__group__assigned_officer=self.request.user)
            ).distinct()
        elif self.request.user.role == 'manager':
            # Managers see applications in their branch
            if hasattr(self.request.user, 'officer_assignment'):
                branch_name = self.request.user.officer_assignment.branch
                queryset = queryset.filter(
                    Q(loan_officer__officer_assignment__branch=branch_name) |
                    Q(borrower__group_memberships__group__assigned_officer__officer_assignment__branch=branch_name)
                ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.get_object()
        
        # Parse application data from form submission (stored in loan metadata or separate model)
        context['application_data'] = self.get_application_data(application)
        context['title'] = f'Application Review - {application.application_number}'
        
        return context
    
    def get_application_data(self, loan):
        """
        Extract application data from loan and borrower
        This would typically come from a separate ApplicationData model
        For now, we'll extract from existing loan and borrower data
        """
        borrower = loan.borrower
        
        # This is a placeholder - in a real implementation, 
        # you'd store the full application form data in a separate model
        application_data = {
            'personal_info': {
                'first_name': borrower.first_name,
                'last_name': borrower.last_name,
                'email': borrower.email,
                'phone_number': getattr(borrower, 'phone_number', ''),
                'date_of_birth': getattr(borrower, 'date_of_birth', ''),
            },
            'address_info': {
                'residential_address': getattr(borrower, 'address', ''),
                'residential_duration': getattr(borrower, 'residential_duration', ''),
            },
            'employment_info': {
                'employment_status': getattr(borrower, 'employment_status', ''),
                'employer_name': getattr(borrower, 'employer_name', ''),
                'employer_address': getattr(borrower, 'employer_address', ''),
                'employment_duration': getattr(borrower, 'employment_duration', ''),
                'monthly_income': getattr(borrower, 'monthly_income', ''),
            },
            'business_info': {
                'business_name': getattr(borrower, 'business_name', ''),
                'business_address': getattr(borrower, 'business_address', ''),
                'business_duration': getattr(borrower, 'business_duration', ''),
            },
            'loan_details': {
                'loan_type': loan.loan_type.name if loan.loan_type else '',
                'principal_amount': loan.principal_amount,
                'purpose': loan.purpose,
                'purpose_description': getattr(loan, 'purpose_description', ''),
                'term_days': loan.term_days,
                'term_weeks': loan.term_weeks,
                'repayment_frequency': loan.repayment_frequency,
            },
            'collateral_info': {
                'has_collateral': getattr(loan, 'has_collateral', ''),
                'collateral_type': loan.collateral_description,
                'collateral_value': getattr(loan, 'collateral_value', ''),
            },
            'references': {
                'reference1_name': getattr(borrower, 'reference1_name', ''),
                'reference1_phone': getattr(borrower, 'reference1_phone', ''),
                'reference1_relationship': getattr(borrower, 'reference1_relationship', ''),
                'reference2_name': getattr(borrower, 'reference2_name', ''),
                'reference2_phone': getattr(borrower, 'reference2_phone', ''),
                'reference2_relationship': getattr(borrower, 'reference2_relationship', ''),
            },
            'application_info': {
                'application_number': loan.application_number,
                'submitted_date': loan.created_at,
                'status': loan.status,
                'loan_officer': loan.loan_officer.get_full_name() if loan.loan_officer else '',
            }
        }
        
        return application_data


def download_application_pdf(request, pk):
    """Download client application as PDF"""
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to download applications.')
        return redirect('accounts:login')
    
    if request.user.role not in ['admin', 'manager', 'loan_officer']:
        messages.error(request, 'You do not have permission to download applications.')
        return redirect('dashboard:dashboard')
    
    loan = get_object_or_404(Loan, pk=pk)
    
    # Check permissions
    if request.user.role == 'loan_officer':
        if not (loan.loan_officer == request.user or 
                loan.borrower.group_memberships.filter(group__assigned_officer=request.user).exists()):
            messages.error(request, 'You do not have permission to download this application.')
            return redirect('loans:application_review_list')
    
    # Get application data
    view = ClientApplicationDetailView()
    view.request = request
    application_data = view.get_application_data(loan)
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="application_{loan.application_number}.pdf"'
    
    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue,
    )
    
    # Title
    story.append(Paragraph(f"Loan Application - {loan.application_number}", title_style))
    story.append(Spacer(1, 20))
    
    # Application Info
    story.append(Paragraph("Application Information", heading_style))
    app_info_data = [
        ['Application Number:', application_data['application_info']['application_number']],
        ['Submitted Date:', application_data['application_info']['submitted_date'].strftime('%Y-%m-%d %H:%M')],
        ['Status:', application_data['application_info']['status'].title()],
        ['Loan Officer:', application_data['application_info']['loan_officer']],
    ]
    
    app_info_table = Table(app_info_data, colWidths=[2*inch, 3*inch])
    app_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(app_info_table)
    story.append(Spacer(1, 20))
    
    # Personal Information
    story.append(Paragraph("Personal Information", heading_style))
    personal_info = application_data['personal_info']
    personal_data = [
        ['Name:', f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}"],
        ['Email:', personal_info.get('email', '')],
        ['Phone:', personal_info.get('phone_number', '')],
        ['Date of Birth:', str(personal_info.get('date_of_birth', ''))],
    ]
    
    personal_table = Table(personal_data, colWidths=[2*inch, 3*inch])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(personal_table)
    story.append(Spacer(1, 20))
    
    # Loan Details
    story.append(Paragraph("Loan Details", heading_style))
    loan_info = application_data['loan_details']
    loan_data = [
        ['Loan Type:', loan_info.get('loan_type', '')],
        ['Principal Amount:', f"K{loan_info.get('principal_amount', 0):,.2f}"],
        ['Purpose:', loan_info.get('purpose', '').title()],
        ['Purpose Description:', loan_info.get('purpose_description', '')],
        ['Repayment Frequency:', loan_info.get('repayment_frequency', '').title()],
        ['Term:', f"{loan_info.get('term_days', loan_info.get('term_weeks', ''))} {'days' if loan_info.get('term_days') else 'weeks'}"],
    ]
    
    loan_table = Table(loan_data, colWidths=[2*inch, 3*inch])
    loan_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(loan_table)
    story.append(Spacer(1, 20))
    
    # Employment Information
    if any(application_data['employment_info'].values()):
        story.append(Paragraph("Employment Information", heading_style))
        emp_info = application_data['employment_info']
        emp_data = [
            ['Employment Status:', emp_info.get('employment_status', '').title()],
            ['Employer Name:', emp_info.get('employer_name', '')],
            ['Employer Address:', emp_info.get('employer_address', '')],
            ['Employment Duration:', f"{emp_info.get('employment_duration', '')} years"],
            ['Monthly Income:', f"K{emp_info.get('monthly_income', 0):,.2f}"],
        ]
        
        emp_table = Table(emp_data, colWidths=[2*inch, 3*inch])
        emp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(emp_table)
        story.append(Spacer(1, 20))
    
    # Collateral Information
    if any(application_data['collateral_info'].values()):
        story.append(Paragraph("Collateral Information", heading_style))
        coll_info = application_data['collateral_info']
        coll_data = [
            ['Has Collateral:', coll_info.get('has_collateral', '').title()],
            ['Collateral Type:', coll_info.get('collateral_type', '')],
            ['Collateral Value:', f"K{coll_info.get('collateral_value', 0):,.2f}"],
        ]
        
        coll_table = Table(coll_data, colWidths=[2*inch, 3*inch])
        coll_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightcoral),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(coll_table)
        story.append(Spacer(1, 20))
    
    # References
    if any(application_data['references'].values()):
        story.append(Paragraph("References", heading_style))
        ref_info = application_data['references']
        ref_data = [
            ['Reference 1 Name:', ref_info.get('reference1_name', '')],
            ['Reference 1 Phone:', ref_info.get('reference1_phone', '')],
            ['Reference 1 Relationship:', ref_info.get('reference1_relationship', '')],
            ['Reference 2 Name:', ref_info.get('reference2_name', '')],
            ['Reference 2 Phone:', ref_info.get('reference2_phone', '')],
            ['Reference 2 Relationship:', ref_info.get('reference2_relationship', '')],
        ]
        
        ref_table = Table(ref_data, colWidths=[2*inch, 3*inch])
        ref_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lavender),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(ref_table)
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                          styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    return response
