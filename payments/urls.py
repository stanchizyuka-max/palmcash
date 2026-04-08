from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='list'),
    path('upfront/<int:loan_id>/', views.UpfrontPaymentView.as_view(), name='upfront_payment'),
    path('make/', views.MakePaymentView.as_view(), name='make'),
    path('make/<int:loan_id>/', views.MakePaymentView.as_view(), name='make'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='detail'),
    path('<int:pk>/confirm/', views.ConfirmPaymentView.as_view(), name='confirm'),
    path('<int:pk>/reject/', views.RejectPaymentView.as_view(), name='reject'),
    path('schedule/<int:loan_id>/', views.PaymentScheduleView.as_view(), name='schedule'),
    path('bulk-collection/', views.BulkCollectionView.as_view(), name='bulk_collection'),
    path('bulk-collection/group/<int:group_id>/', views.BulkCollectionGroupView.as_view(), name='bulk_collection_group'),
    path('default-collection/', views.DefaultCollectionView.as_view(), name='default_collection'),
    path('default-collection/group/<int:group_id>/', views.DefaultCollectionGroupView.as_view(), name='default_collection_group'),
    path('default-collection/history/', views.DefaultCollectionHistoryView.as_view(), name='default_collection_history'),
    path('collection-history/', views.CollectionHistoryView.as_view(), name='collection_history'),
    path('history/', views.HistoryHubView.as_view(), name='history'),
    path('collections-history/', views.CollectionsHistoryView.as_view(), name='collections_history'),
    path('securities-history/', views.SecuritiesHistoryView.as_view(), name='securities_history'),
]
