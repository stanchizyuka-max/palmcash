from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # List view
    path('', views.client_document_upload, name='list'),
    
    # Client document verification URLs
    path('client/upload/', views.client_document_upload, name='client_upload'),
    path('upload/', views.client_document_upload, name='upload'),  # Alias for borrower dashboard
    path('client/status/', views.client_verification_status, name='client_verification_status'),
    path('verification/dashboard/', views.document_verification_dashboard, name='verification_dashboard'),
    path('verification/approve/<int:client_id>/', views.approve_client_documents, name='approve_client_documents'),
    path('verification/reject/<int:client_id>/', views.reject_client_documents, name='reject_client_documents'),
    path('verification/approve-document/<int:document_id>/', views.approve_single_document, name='approve_single_document'),
    path('verification/reject-document/<int:document_id>/', views.reject_single_document, name='reject_single_document'),
]
