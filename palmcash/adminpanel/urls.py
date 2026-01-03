from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # Loan Type URLs
    path('loan-types/', views.loan_type_list, name='loan_type_list'),
    path('loan-types/<int:pk>/', views.loan_type_detail, name='loan_type_detail'),
    
    # Loan Document URLs
    path('loan-documents/', views.loan_document_list, name='loan_document_list'),
    path('loan-documents/<int:pk>/', views.loan_document_detail, name='loan_document_detail'),
    
    # User Document URLs
    path('user-documents/', views.user_document_list, name='user_document_list'),
    path('user-documents/<int:pk>/', views.user_document_detail, name='user_document_detail'),
    
    # Document Type URLs
    path('document-types/', views.document_type_list, name='document_type_list'),
    path('document-types/<int:pk>/', views.document_type_detail, name='document_type_detail'),
]
