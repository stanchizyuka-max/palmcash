from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # Expense URLs
    path('', views.ExpenseListView.as_view(), name='list'),
    path('create/', views.ExpenseCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='delete'),
    path('report/', views.ExpenseReportView.as_view(), name='report'),
    
    # Vault Transaction URLs
    path('vault-transactions/', views.VaultTransactionListView.as_view(), name='vault-transactions'),
    path('vault-transactions/create/', views.VaultTransactionCreateView.as_view(), name='vault-create'),
    path('branch-balance/', views.BranchBalanceView.as_view(), name='branch-balance'),
]
