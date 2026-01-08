from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views.generic import CreateView, TemplateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import User
from .forms import UserRegistrationForm, UserProfileForm, CustomPasswordResetForm, CustomSetPasswordForm

class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard:dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Registration successful! Welcome to LoanVista.')
        
        # Create ClientVerification record for borrowers
        if self.object.role == 'borrower':
            try:
                from documents.models import ClientVerification
                ClientVerification.objects.get_or_create(client=self.object)
            except Exception as e:
                # Log error but don't fail registration
                print(f"Error creating ClientVerification: {str(e)}")
        
        # Notify admins about new user registration
        self._notify_admins_of_registration(self.object)
        
        return response
    
    def _notify_admins_of_registration(self, user):
        """Notify admins and managers about new user registration"""
        try:
            from notifications.models import Notification, NotificationTemplate
            from django.utils import timezone
            
            # Get the notification template
            try:
                template = NotificationTemplate.objects.get(
                    notification_type='user_registered',
                    is_active=True
                )
            except NotificationTemplate.DoesNotExist:
                return
            
            # Get all administrators, managers, and loan officers
            admins = User.objects.filter(role__in=['admin', 'manager', 'loan_officer'])
            
            for admin in admins:
                # Format the message using the template
                message = template.message_template.format(
                    user_name=user.full_name,
                    email=user.email,
                    role=user.get_role_display()
                )
                
                Notification.objects.create(
                    recipient=admin,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel=template.channel,
                    recipient_address=admin.email or '',
                    scheduled_at=timezone.now(),
                    status='sent'
                )
        except Exception as e:
            # Don't fail registration if notification fails
            print(f"Error creating registration notification: {e}")

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


# Password Reset Views
class CustomPasswordResetView(PasswordResetView):
    """Password reset request view"""
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            'Password reset email has been sent! Please check your inbox.'
        )
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Password reset email sent confirmation"""
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Password reset form view"""
    form_class = CustomSetPasswordForm
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            'Your password has been reset successfully! You can now log in with your new password.'
        )
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Password reset complete confirmation"""
    template_name = 'accounts/password_reset_complete.html'



class UsersManageView(LoginRequiredMixin, TemplateView):
    """View for managing all users"""
    template_name = 'accounts/users_manage.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated first
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Check if user has permission to manage users
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to manage users.')
            return redirect('dashboard:dashboard')
        
        # Store request for use in get_context_data
        self.request = request
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator
        context = super().get_context_data(**kwargs)
        
        # Get all users
        users = User.objects.all().order_by('-date_joined')
        
        # Filter by role if provided
        role_filter = self.request.GET.get('role', 'all')
        if role_filter and role_filter != 'all':
            users = users.filter(role=role_filter)
        
        # Statistics
        all_users = User.objects.all()
        context['total_users'] = all_users.count()
        context['borrowers_count'] = all_users.filter(role='borrower').count()
        context['officers_count'] = all_users.filter(role='loan_officer').count()
        context['managers_count'] = all_users.filter(role='manager').count()
        context['admins_count'] = all_users.filter(role='admin').count()
        context['active_users'] = all_users.filter(is_active=True).count()
        
        # Current filter
        context['current_filter'] = role_filter
        
        # Pagination
        paginator = Paginator(users, 20)  # Show 20 users per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['users'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        
        return context



class UserEditView(LoginRequiredMixin, TemplateView):
    """View for editing a specific user"""
    template_name = 'accounts/user_edit.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'manager'] and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to edit users.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('pk')
        user_to_edit = User.objects.get(pk=user_id)
        
        context['user_to_edit'] = user_to_edit
        
        # If borrower, get loan statistics
        if user_to_edit.role == 'borrower':
            from loans.models import Loan
            user_loans = Loan.objects.filter(borrower=user_to_edit)
            context['user_loans'] = user_loans
            context['active_loans'] = user_loans.filter(status='active').count()
            context['completed_loans'] = user_loans.filter(status='completed').count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle user update"""
        try:
            user_id = self.kwargs.get('pk')
            user_to_edit = User.objects.get(pk=user_id)
            
            # Update basic fields
            user_to_edit.username = request.POST.get('username')
            user_to_edit.email = request.POST.get('email')
            user_to_edit.first_name = request.POST.get('first_name')
            user_to_edit.last_name = request.POST.get('last_name')
            user_to_edit.phone_number = request.POST.get('phone_number')
            user_to_edit.national_id = request.POST.get('national_id')
            user_to_edit.address = request.POST.get('address')
            user_to_edit.role = request.POST.get('role')
            
            # Update date of birth if provided
            date_of_birth = request.POST.get('date_of_birth')
            if date_of_birth:
                user_to_edit.date_of_birth = date_of_birth
            
            # Update status fields
            user_to_edit.is_active = request.POST.get('is_active') == 'on'
            user_to_edit.is_verified = request.POST.get('is_verified') == 'on'
            user_to_edit.is_staff = request.POST.get('is_staff') == 'on'
            
            # Only allow superuser change if user is not already a superuser
            if not user_to_edit.is_superuser:
                user_to_edit.is_superuser = request.POST.get('is_superuser') == 'on'
            
            user_to_edit.save()
            
            messages.success(request, f'User "{user_to_edit.get_full_name()}" has been updated successfully!')
            return redirect('accounts:manage_users')
            
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('accounts:manage_users')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
            return redirect('accounts:edit_user', pk=user_id)



class UserDetailView(LoginRequiredMixin, TemplateView):
    """View for displaying user/client details"""
    template_name = 'clients/detail_tailwind.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'manager', 'loan_officer'] and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to view user details.')
            return redirect('dashboard:dashboard')
        
        # Loan officers can only view clients assigned to them
        if request.user.role == 'loan_officer':
            user_id = kwargs.get('pk')
            user_to_view = User.objects.get(pk=user_id)
            if user_to_view.assigned_officer != request.user:
                messages.error(request, 'You can only view clients assigned to you.')
                return redirect('dashboard:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('pk')
        client = User.objects.get(pk=user_id)
        
        context['client'] = client
        
        # Get loan statistics
        if client.role == 'borrower':
            from loans.models import Loan
            user_loans = Loan.objects.filter(borrower=client)
            context['total_loans_count'] = user_loans.count()
            context['active_loans_count'] = user_loans.filter(status__in=['active', 'approved', 'disbursed']).count()
            context['pending_loans_count'] = user_loans.filter(status='pending').count()
        
        # Get available loan officers for assignment
        context['loan_officers'] = User.objects.filter(role='loan_officer', is_active=True).order_by('last_name', 'first_name')
        
        return context
