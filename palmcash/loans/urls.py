from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.LoanListView.as_view(), name='list'),
    path('apply/', views.LoanApplicationView.as_view(), name='apply'),
    path('calculator/', views.LoanCalculatorView.as_view(), name='calculator'),
    path('status-dashboard/', views.LoanStatusDashboardView.as_view(), name='status_dashboard'),
    path('<int:pk>/', views.LoanDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.LoanEditView.as_view(), name='edit'),
    path('<int:pk>/approve/', views.ApproveLoanView.as_view(), name='approve'),
    path('<int:pk>/reject/', views.RejectLoanView.as_view(), name='reject'),
    path('<int:pk>/disburse/', views.DisburseLoanView.as_view(), name='disburse'),
    path('<int:pk>/upfront-payment/', views.UpfrontPaymentView.as_view(), name='upfront_payment'),
    path('<int:pk>/verify-upfront/', views.VerifyUpfrontPaymentView.as_view(), name='verify_upfront'),
    
    # Document management URLs
    path('documents/review-dashboard/', views.DocumentReviewDashboardView.as_view(), name='document_review_dashboard'),
    path('<int:loan_id>/documents/', views.LoanDocumentListView.as_view(), name='document_list'),
    path('<int:loan_id>/documents/upload/', views.LoanDocumentUploadView.as_view(), name='upload_document'),
    path('documents/<int:pk>/verify/', views.DocumentVerificationView.as_view(), name='verify_document'),
    path('documents/<int:pk>/download/', views.DocumentDownloadView.as_view(), name='download_document'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='delete_document'),
    path('documents/<int:pk>/admin-delete/', views.AdminDeleteLoanDocumentView.as_view(), name='admin_delete_document'),
    
    # Admin management URLs
    path('manage/loan-types/', views.LoanTypesManageView.as_view(), name='manage_loan_types'),
    path('manage/loan-documents/', views.LoanDocumentsManageView.as_view(), name='manage_loan_documents'),
]