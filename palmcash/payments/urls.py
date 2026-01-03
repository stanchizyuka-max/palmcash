from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='list'),
    path('upfront/<int:loan_id>/', views.UpfrontPaymentView.as_view(), name='upfront_payment'),
    path('make/<int:loan_id>/', views.MakePaymentView.as_view(), name='make'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='detail'),
    path('<int:pk>/confirm/', views.ConfirmPaymentView.as_view(), name='confirm'),
    path('<int:pk>/reject/', views.RejectPaymentView.as_view(), name='reject'),
    path('schedule/<int:loan_id>/', views.PaymentScheduleView.as_view(), name='schedule'),
]