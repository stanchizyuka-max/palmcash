from django.urls import path
from . import views

app_name = 'internal_messages'

urlpatterns = [
    # Direct messages
    path('inbox/', views.MessageInboxView.as_view(), name='inbox'),
    path('sent/', views.MessageSentView.as_view(), name='sent'),
    path('compose/', views.MessageComposeView.as_view(), name='compose'),
    path('<int:pk>/', views.MessageDetailView.as_view(), name='detail'),
    path('<int:pk>/reply/', views.MessageReplyView.as_view(), name='reply'),
    
    # Threaded conversations
    path('threads/', views.ThreadListView.as_view(), name='threads'),
    path('threads/<int:pk>/', views.ThreadDetailView.as_view(), name='thread_detail'),
]
