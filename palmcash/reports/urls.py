from django.urls import path
from . import views
from .views_daily_transactions import DailyTransactionReportView
from .views_financial_reports import (
    FinancialReportsView,
    DisbursementReportView,
    CollectionReportView,
    DepositReportView,
    ReturnsReportView,
    export_financial_report
)

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
    path('daily-transactions/', DailyTransactionReportView.as_view(), name='daily_transactions'),
    
    # Financial Reports with Date Range Filtering
    path('financial-reports/', FinancialReportsView.as_view(), name='financial_reports'),
    path('disbursement-report/', DisbursementReportView.as_view(), name='disbursement_report'),
    path('collection-report/', CollectionReportView.as_view(), name='collection_report'),
    path('deposit-report/', DepositReportView.as_view(), name='deposit_report'),
    path('returns-report/', ReturnsReportView.as_view(), name='returns_report'),
    
    # Export Functions
    path('export/<str:report_type>/', export_financial_report, name='export_disbursement_csv'),
]
