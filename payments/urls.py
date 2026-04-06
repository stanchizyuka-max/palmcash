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
]
