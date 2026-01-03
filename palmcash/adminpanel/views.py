from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from loans.models import LoanType, LoanDocument
from documents.models import DocumentType, Document

def is_manager_or_admin(user):
    """Check if user is manager or admin"""
    return user.is_authenticated and user.role in ['manager', 'admin']

# Loan Type Views
@login_required
@user_passes_test(is_manager_or_admin)
def loan_type_list(request):
    """List all loan types"""
    loan_types = LoanType.objects.all().order_by('-created_at')
    
    context = {
        'loan_types': loan_types,
    }
    return render(request, 'adminpanel/loan_type_list.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def loan_type_detail(request, pk):
    """View loan type details"""
    loan_type = get_object_or_404(LoanType, pk=pk)
    
    context = {
        'loan_type': loan_type,
    }
    return render(request, 'adminpanel/loan_type_detail.html', context)

# Loan Document Views
@login_required
@user_passes_test(is_manager_or_admin)
def loan_document_list(request):
    """List all loan documents"""
    loan_documents = LoanDocument.objects.select_related('loan', 'uploaded_by').all().order_by('-uploaded_at')
    
    # Filter by verification status
    status_filter = request.GET.get('status')
    if status_filter == 'verified':
        loan_documents = loan_documents.filter(is_verified=True)
    elif status_filter == 'unverified':
        loan_documents = loan_documents.filter(is_verified=False)
    
    context = {
        'loan_documents': loan_documents,
        'status_filter': status_filter,
    }
    return render(request, 'adminpanel/loan_document_list.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def loan_document_detail(request, pk):
    """View loan document details"""
    loan_document = get_object_or_404(LoanDocument, pk=pk)
    
    context = {
        'loan_document': loan_document,
    }
    return render(request, 'adminpanel/loan_document_detail.html', context)

# User Document Views
@login_required
@user_passes_test(is_manager_or_admin)
def user_document_list(request):
    """List all user documents"""
    user_documents = Document.objects.select_related('user', 'document_type').all().order_by('-uploaded_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        user_documents = user_documents.filter(status=status_filter)
    
    context = {
        'user_documents': user_documents,
        'status_filter': status_filter,
    }
    return render(request, 'adminpanel/user_document_list.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def user_document_detail(request, pk):
    """View user document details"""
    user_document = get_object_or_404(Document, pk=pk)
    
    context = {
        'user_document': user_document,
    }
    return render(request, 'adminpanel/user_document_detail.html', context)

# Document Type Views
@login_required
@user_passes_test(is_manager_or_admin)
def document_type_list(request):
    """List all document types"""
    document_types = DocumentType.objects.all().order_by('name')
    
    context = {
        'document_types': document_types,
    }
    return render(request, 'adminpanel/document_type_list.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def document_type_detail(request, pk):
    """View document type details"""
    document_type = get_object_or_404(DocumentType, pk=pk)
    
    context = {
        'document_type': document_type,
    }
    return render(request, 'adminpanel/document_type_detail.html', context)
