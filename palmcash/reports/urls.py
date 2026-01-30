from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportListView.as_view(), name='list'),
    path('monthly-collections/', views.MonthlyCollectionTrendView.as_view(), name='monthly_collections'),
    path('system-statistics/', views.SystemStatisticsView.as_view(), name='system_statistics'),
    path('loans/', views.LoanReportView.as_view(), name='loans'),
    path('loans/export/', views.LoanExportView.as_view(), name='loans_export'),
    path('payments/', views.PaymentReportView.as_view(), name='payments'),
    path('payments/export/', views.PaymentExportView.as_view(), name='payments_export'),
    path('financial/', views.FinancialReportView.as_view(), name='financial'),
    path('financial/export/', views.FinancialExportView.as_view(), name='financial_export'),
]
