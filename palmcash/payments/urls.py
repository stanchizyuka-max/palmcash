from django.urls import path
from . import views
from .views_bulk_approval import (
    BulkCollectionApprovalView,
    QuickApproveTodayView,
    GroupCollectionApprovalView
)
from .views_multi_schedule import (
    MultiSchedulePaymentView,
    CreateMultiSchedulePaymentView,
    MultiSchedulePaymentDetailView,
    ApproveMultiSchedulePaymentView,
    MultiSchedulePaymentListView
)

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='list'),
    path('upfront/<int:loan_id>/', views.UpfrontPaymentView.as_view(), name='upfront_payment'),
    path('make/<int:loan_id>/', views.MakePaymentView.as_view(), name='make'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='detail'),
    path('<int:pk>/confirm/', views.ConfirmPaymentView.as_view(), name='confirm'),
    path('<int:pk>/reject/', views.RejectPaymentView.as_view(), name='reject'),
    path('schedule/<int:loan_id>/', views.PaymentScheduleView.as_view(), name='schedule'),
    
    # Multi-Schedule Payment URLs
    path('multi-schedule/<int:loan_id>/', MultiSchedulePaymentView.as_view(), name='multi_schedule_payment'),
    path('multi-schedule/create/<int:loan_id>/', CreateMultiSchedulePaymentView.as_view(), name='create_multi_payment'),
    path('multi-schedule/<int:pk>/', MultiSchedulePaymentDetailView.as_view(), name='multi_payment_detail'),
    path('multi-schedule/<int:pk>/approve/', ApproveMultiSchedulePaymentView.as_view(), name='approve_multi_payment'),
    path('multi-schedule/', MultiSchedulePaymentListView.as_view(), name='multi_payment_list'),
    
    # Bulk Approval URLs
    path('bulk-approve/', BulkCollectionApprovalView.as_view(), name='bulk_approval'),
    path('quick-approve-today/', QuickApproveTodayView.as_view(), name='quick_approve_today'),
    path('group-approve/', GroupCollectionApprovalView.as_view(), name='group_approval'),
]
