from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import ClientDocument, ClientVerification
from accounts.models import User


# ============================================================================
# CLIENT DOCUMENT VERIFICATION VIEWS
# ============================================================================

@login_required
def client_document_upload(request):
    """Handle client document uploads (NRC front, NRC back, selfie)"""
    if request.user.role != 'borrower':
        messages.error(request, 'Only borrowers can upload documents.')
        return redirect('dashboard:dashboard')
    
    # Get or create client verification record
    verification, created = ClientVerification.objects.get_or_create(client=request.user)
    
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        image_file = request.FILES.get('image')
        
        if not document_type or not image_file:
            messages.error(request, 'Please select a document type and upload an image.')
            return redirect('documents:client_upload')
        
        # Validate document type
        valid_types = ['nrc_front', 'nrc_back', 'selfie']
        if document_type not in valid_types:
            messages.error(request, 'Invalid document type.')
            return redirect('documents:client_upload')
        
        try:
            # Create or update document
            doc, created = ClientDocument.objects.update_or_create(
                client=request.user,
                document_type=document_type,
                defaults={'image': image_file, 'status': 'pending'}
            )
            
            # Update verification tracking
            if document_type == 'nrc_front':
                verification.nrc_front_uploaded = True
            elif document_type == 'nrc_back':
                verification.nrc_back_uploaded = True
            elif document_type == 'selfie':
                verification.selfie_uploaded = True
            
            verification.save()
            
            # Update verification status
            verification.update_status()
            
            doc_display = dict(ClientDocument.DOCUMENT_TYPE_CHOICES).get(document_type, document_type)
            messages.success(request, f'{doc_display} uploaded successfully! Awaiting review.')
            
            return redirect('documents:client_verification_status')
        
        except Exception as e:
            messages.error(request, f'Error uploading document: {str(e)}')
            return redirect('documents:client_upload')
    
    # Get current documents
    documents = ClientDocument.objects.filter(client=request.user)
    doc_dict = {doc.document_type: doc for doc in documents}
    
    context = {
        'verification': verification,
        'documents': doc_dict,
        'document_types': [
            ('nrc_front', 'NRC Card - Front'),
            ('nrc_back', 'NRC Card - Back'),
            ('selfie', 'Live Photo (Selfie)'),
        ],
    }
    
    return render(request, 'documents/client_upload.html', context)


@login_required
def client_verification_status(request):
    """Show client their verification status"""
    if request.user.role != 'borrower':
        messages.error(request, 'Only borrowers can view verification status.')
        return redirect('dashboard:dashboard')
    
    # Get or create verification record
    verification, created = ClientVerification.objects.get_or_create(client=request.user)
    
    # Get all documents
    documents = ClientDocument.objects.filter(client=request.user).order_by('document_type')
    
    context = {
        'verification': verification,
        'documents': documents,
        'can_apply_for_loan': verification.can_apply_for_loan(),
        'all_documents_uploaded': verification.all_documents_uploaded,
    }
    
    return render(request, 'documents/client_verification_status.html', context)


@login_required
def document_verification_dashboard(request):
    """Dashboard for reviewing approved client documents - accessible to loan officers, managers, and admins"""
    user = request.user
    
    # Check permissions
    if user.role not in ['loan_officer', 'manager', 'admin']:
        messages.error(request, 'You do not have permission to access this dashboard.')
        return redirect('dashboard:dashboard')
    
    # Filter based on role
    if user.role == 'loan_officer':
        # Loan officers see documents from their clients
        from django.db.models import Q
        client_ids = User.objects.filter(
            Q(assigned_officer=user) | Q(group_memberships__group__assigned_officer=user),
            role='borrower'
        ).values_list('id', flat=True).distinct()
        
        # Get verified/approved documents (primary focus)
        verified_verifications = ClientVerification.objects.filter(
            client_id__in=client_ids,
            status='verified'
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        # Get pending verifications (secondary)
        pending_verifications = ClientVerification.objects.filter(
            client_id__in=client_ids,
            status__in=['documents_submitted', 'documents_rejected']
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        all_verifications = ClientVerification.objects.filter(
            client_id__in=client_ids
        ).select_related('client').prefetch_related('client__documents')
        
        total_clients = ClientVerification.objects.filter(client_id__in=client_ids).count()
        verified_clients = ClientVerification.objects.filter(
            client_id__in=client_ids,
            status='verified'
        ).count()
    else:
        # Managers and admins see all documents
        verified_verifications = ClientVerification.objects.filter(
            status='verified'
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        pending_verifications = ClientVerification.objects.filter(
            status__in=['documents_submitted', 'documents_rejected']
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        all_verifications = ClientVerification.objects.all().select_related('client').prefetch_related('client__documents')
        
        total_clients = ClientVerification.objects.count()
        verified_clients = ClientVerification.objects.filter(status='verified').count()
    
    pending_clients = pending_verifications.count()
    
    context = {
        'verified_verifications': verified_verifications,
        'pending_verifications': pending_verifications,
        'all_verifications': all_verifications,
        'total_clients': total_clients,
        'verified_clients': verified_clients,
        'pending_clients': pending_clients,
    }
    
    return render(request, 'dashboard/document_verification.html', context)


@login_required
def approve_client_documents(request, client_id):
    """Approve all documents for a client"""
    if request.user.role not in ['loan_officer', 'admin']:
        messages.error(request, 'You do not have permission to approve documents.')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    if request.method != 'POST':
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    try:
        from accounts.models import User
        client = get_object_or_404(User, id=client_id, role='borrower')
        
        # Check if loan officer has access to this client
        if request.user.role == 'loan_officer':
            from django.db.models import Q
            has_access = User.objects.filter(
                Q(assigned_officer=request.user) | Q(group_memberships__group__assigned_officer=request.user),
                id=client_id,
                role='borrower'
            ).exists()
            if not has_access:
                messages.error(request, 'You do not have permission to approve documents for this client.')
                return redirect('dashboard:loan_officer_document_verification')
        
        verification = get_object_or_404(ClientVerification, client=client)
        
        # Approve all documents
        verification.approve_all_documents(request.user)
        
        messages.success(request, f'All documents for {client.full_name} have been approved.')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    except Exception as e:
        messages.error(request, f'Error approving documents: {str(e)}')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')


@login_required
def reject_client_documents(request, client_id):
    """Reject all documents for a client"""
    if request.user.role not in ['loan_officer', 'admin']:
        messages.error(request, 'You do not have permission to reject documents.')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    if request.method != 'POST':
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    try:
        from accounts.models import User
        client = get_object_or_404(User, id=client_id, role='borrower')
        
        # Check if loan officer has access to this client
        if request.user.role == 'loan_officer':
            from django.db.models import Q
            has_access = User.objects.filter(
                Q(assigned_officer=request.user) | Q(group_memberships__group__assigned_officer=request.user),
                id=client_id,
                role='borrower'
            ).exists()
            if not has_access:
                messages.error(request, 'You do not have permission to reject documents for this client.')
                return redirect('dashboard:loan_officer_document_verification')
        
        verification = get_object_or_404(ClientVerification, client=client)
        
        reason = request.POST.get('reason', 'Documents do not meet requirements.')
        
        # Reject all documents
        verification.reject_all_documents(request.user, reason)
        
        messages.success(request, f'Documents for {client.full_name} have been rejected.')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    except Exception as e:
        messages.error(request, f'Error rejecting documents: {str(e)}')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')


@login_required
def approve_single_document(request, document_id):
    """Approve a single document"""
    if request.user.role not in ['loan_officer', 'admin']:
        messages.error(request, 'You do not have permission to approve documents.')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    if request.method != 'POST':
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    try:
        document = get_object_or_404(ClientDocument, id=document_id)
        
        # Check if loan officer has access to this client
        if request.user.role == 'loan_officer':
            from django.db.models import Q
            has_access = User.objects.filter(
                Q(assigned_officer=request.user) | Q(group_memberships__group__assigned_officer=request.user),
                id=document.client_id,
                role='borrower'
            ).exists()
            if not has_access:
                messages.error(request, 'You do not have permission to approve documents for this client.')
                return redirect('dashboard:loan_officer_document_verification')
        
        notes = request.POST.get('notes', '')
        
        document.approve(request.user, notes)
        
        # Update verification status
        verification = document.client.verification
        verification.update_status()
        
        messages.success(request, f'{document.get_document_type_display()} approved.')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    except Exception as e:
        messages.error(request, f'Error approving document: {str(e)}')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')


@login_required
def reject_single_document(request, document_id):
    """Reject a single document"""
    if request.user.role not in ['loan_officer', 'admin']:
        messages.error(request, 'You do not have permission to reject documents.')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    if request.method != 'POST':
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    try:
        document = get_object_or_404(ClientDocument, id=document_id)
        
        # Check if loan officer has access to this client
        if request.user.role == 'loan_officer':
            from django.db.models import Q
            has_access = User.objects.filter(
                Q(assigned_officer=request.user) | Q(group_memberships__group__assigned_officer=request.user),
                id=document.client_id,
                role='borrower'
            ).exists()
            if not has_access:
                messages.error(request, 'You do not have permission to reject documents for this client.')
                return redirect('dashboard:loan_officer_document_verification')
        
        reason = request.POST.get('reason', 'Document does not meet requirements.')
        
        document.reject(request.user, reason)
        
        # Update verification status
        verification = document.client.verification
        verification.update_status()
        
        messages.success(request, f'{document.get_document_type_display()} rejected.')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
    
    except Exception as e:
        messages.error(request, f'Error rejecting document: {str(e)}')
        if request.user.role == 'loan_officer':
            return redirect('dashboard:loan_officer_document_verification')
        return redirect('documents:verification_dashboard')
 
 
 @ l o g i n _ r e q u i r e d 
 d e f   c l i e n t _ d o c u m e n t _ r e v i e w ( r e q u e s t ,   c l i e n t _ i d ) : 
         \  
 \ \ R e v i e w  
 d o c u m e n t s  
 f o r  
 a  
 s p e c i f i c  
 c l i e n t \ \ \ 
         u s e r   =   r e q u e s t . u s e r 
         
         #   C h e c k   p e r m i s s i o n s 
         i f   u s e r . r o l e   n o t   i n   [ ' l o a n _ o f f i c e r ' ,   ' m a n a g e r ' ,   ' a d m i n ' ] : 
                 m e s s a g e s . e r r o r ( r e q u e s t ,   ' Y o u   d o   n o t   h a v e   p e r m i s s i o n   t o   r e v i e w   d o c u m e n t s . ' ) 
                 r e t u r n   r e d i r e c t ( ' d a s h b o a r d : d a s h b o a r d ' ) 
         
         t r y : 
                 f r o m   a c c o u n t s . m o d e l s   i m p o r t   U s e r 
                 c l i e n t   =   g e t _ o b j e c t _ o r _ 4 0 4 ( U s e r ,   i d = c l i e n t _ i d ,   r o l e = ' b o r r o w e r ' ) 
                 
                 #   C h e c k   i f   l o a n   o f f i c e r   h a s   a c c e s s   t o   t h i s   c l i e n t 
                 i f   u s e r . r o l e   = =   ' l o a n _ o f f i c e r ' : 
                         f r o m   d j a n g o . d b . m o d e l s   i m p o r t   Q 
                         h a s _ a c c e s s   =   U s e r . o b j e c t s . f i l t e r ( 
                                 Q ( a s s i g n e d _ o f f i c e r = u s e r )   |   Q ( g r o u p _ m e m b e r s h i p s _ _ g r o u p _ _ a s s i g n e d _ o f f i c e r = u s e r ) , 
                                 i d = c l i e n t _ i d , 
                                 r o l e = ' b o r r o w e r ' 
                         ) . e x i s t s ( ) 
                         i f   n o t   h a s _ a c c e s s : 
                                 m e s s a g e s . e r r o r ( r e q u e s t ,   ' Y o u   d o   n o t   h a v e   p e r m i s s i o n   t o   r e v i e w   d o c u m e n t s   f o r   t h i s   c l i e n t . ' ) 
                                 r e t u r n   r e d i r e c t ( ' d a s h b o a r d : d a s h b o a r d ' ) 
                 
                 #   G e t   a l l   d o c u m e n t s   f o r   t h i s   c l i e n t 
                 d o c u m e n t s   =   C l i e n t D o c u m e n t . o b j e c t s . f i l t e r ( 
                         c l i e n t = c l i e n t 
                 ) . s e l e c t _ r e l a t e d ( ' c l i e n t ' ,   ' v e r i f i e d _ b y ' ) . o r d e r _ b y ( ' - u p l o a d e d _ a t ' ) 
                 
                 #   G e t   v e r i f i c a t i o n   s t a t u s 
                 t r y : 
                         v e r i f i c a t i o n   =   C l i e n t V e r i f i c a t i o n . o b j e c t s . g e t ( c l i e n t = c l i e n t ) 
                 e x c e p t   C l i e n t V e r i f i c a t i o n . D o e s N o t E x i s t : 
                         v e r i f i c a t i o n   =   N o n e 
                 
         e x c e p t   E x c e p t i o n   a s   e : 
                 m e s s a g e s . e r r o r ( r e q u e s t ,   f ' E r r o r   l o a d i n g   c l i e n t   d o c u m e n t s :   { s t r ( e ) } ' ) 
                 r e t u r n   r e d i r e c t ( ' d a s h b o a r d : d a s h b o a r d ' ) 
         
         c o n t e x t   =   { 
                 ' c l i e n t ' :   c l i e n t , 
                 ' d o c u m e n t s ' :   d o c u m e n t s , 
                 ' v e r i f i c a t i o n ' :   v e r i f i c a t i o n , 
                 ' u s e r _ r o l e ' :   u s e r . r o l e , 
         } 
         
         r e t u r n   r e n d e r ( r e q u e s t ,   ' d a s h b o a r d / c l i e n t _ d o c u m e n t _ r e v i e w . h t m l ' ,   c o n t e x t )  
 