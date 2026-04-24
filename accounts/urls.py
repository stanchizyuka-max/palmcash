from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import audit_views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register/officer/', views.LoanOfficerRegisterView.as_view(), name='officer_register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.EditProfileView.as_view(), name='edit_profile'),
    
    # Password Reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Admin management URLs
    path('manage/users/', views.UsersManageView.as_view(), name='manage_users'),
    path('user/<int:pk>/edit/', views.UserEditView.as_view(), name='edit_user'),
    path('user/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('user/<int:pk>/promote/', views.PromoteToManagerView.as_view(), name='promote_manager'),
    path('user/<int:pk>/delete/', views.DeleteUserView.as_view(), name='delete_user'),
    path('user/<int:pk>/edit-client/', views.EditClientProfileView.as_view(), name='edit_client_profile'),
    
    # Audit and Activity Tracking URLs
    path('audit/', audit_views.user_audit_list, name='user_audit_list'),
    path('audit/user/<int:user_id>/', audit_views.user_activity_detail, name='user_activity_detail'),
]
