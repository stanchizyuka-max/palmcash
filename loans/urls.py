from django.urls import path
from . import views
from . import views_application

app_name = 'loans'

urlpatterns = [
    path('', views.LoanListView.as_view(), name='list'),
    path('apply/', views.LoanApplicationView.as_view(), name='apply'),
    path('calculator/', views.LoanCalculatorView.as_view(), name='calculator'),
    path('history/', views.LoanHistoryView.as_view(), name='history'),
    path('status-dashboard/', views.LoanStatusDashboardView.as_view(), name='status_dashboard'),
    path('<int:pk>/', views.LoanDetailView.as_view(), name='detail'),
    path('<int:pk>/application/', views.LoanApplicationDetailView.as_view(), name='application_detail'),
    path('<int:pk>/edit/', views.LoanEditView.as_view(), name='edit'),
    path('<int:pk>/approve/', views.ApproveLoanView.as_view(), name='approve'),
    path('<int:pk>/reject/', views.RejectLoanView.as_view(), name='reject'),
    path('<int:pk>/disburse/', views.DisburseLoanView.as_view(), name='disburse'),
    path('<int:pk>/upfront-payment/', views.UpfrontPaymentView.as_view(), name='upfront_payment'),
    path('<int:pk>/verify-upfront/', views.VerifyUpfrontPaymentView.as_view(), name='verify_upfront'),
    
    path('documents/review-dashboard/', views.DocumentReviewDashboardView.as_view(), name='document_review_dashboard'),
    path('<int:loan_id>/documents/', views.LoanDocumentListView.as_view(), name='document_list'),
    path('<int:loan_id>/documents/upload/', views.LoanDocumentUploadView.as_view(), name='upload_document'),
    path('documents/<int:pk>/verify/', views.DocumentVerificationView.as_view(), name='verify_document'),
    path('documents/<int:pk>/download/', views.DocumentDownloadView.as_view(), name='download_document'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='delete_document'),
    path('documents/<int:pk>/admin-delete/', views.AdminDeleteLoanDocumentView.as_view(), name='admin_delete_document'),
    
    path('manage/loan-types/', views.LoanTypesManageView.as_view(), name='manage_loan_types'),
    path('manage/loan-documents/', views.LoanDocumentsManageView.as_view(), name='manage_loan_documents'),
    
    path('applications/submit/', views_application.SelectBorrowerView.as_view(), name='submit_application'),
    path('applications/submit/<int:pk>/', views_application.BorrowerDetailForApplicationView.as_view(), name='borrower_detail_for_application'),
    path('applications/submit/form/', views_application.SubmitLoanApplicationView.as_view(), name='submit_application_form'),
    path('applications/', views_application.LoanApplicationsListView.as_view(), name='applications_list'),
    path('applications/<int:pk>/approve/', views_application.ApproveLoanApplicationView.as_view(), name='approve_application'),
]
