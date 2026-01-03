from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.DocumentListView.as_view(), name='list'),
    path('upload/', views.DocumentUploadView.as_view(), name='upload'),
    path('review-dashboard/', views.DocumentReviewDashboardView.as_view(), name='review_dashboard'),
    path('bulk-delete/', views.BulkDeleteDocumentsView.as_view(), name='bulk_delete'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='detail'),
    path('<int:pk>/approve/', views.ApproveDocumentView.as_view(), name='approve'),
    path('<int:pk>/reject/', views.RejectDocumentView.as_view(), name='reject'),
    path('<int:pk>/delete/', views.DeleteDocumentView.as_view(), name='delete'),
    
    # Admin management URLs
    path('manage/documents/', views.DocumentsManageView.as_view(), name='manage_documents'),
    path('manage/document-types/', views.DocumentTypesManageView.as_view(), name='manage_document_types'),
]