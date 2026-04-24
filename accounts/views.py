from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views.generic import CreateView, TemplateView, UpdateView
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy
from .models import User
from .forms import UserRegistrationForm, UserProfileForm, CustomPasswordResetForm, CustomSetPasswordForm

class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'loan_officer'
        user.is_active = False
        user.is_approved = False
        user.save()
        messages.success(self.request, 'Registration submitted. Your account is pending approval.')
        return redirect(self.success_url)

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
        if request.user.role not in ['admin', 'manager', 'loan_officer'] and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to manage users.')
            return redirect('dashboard:dashboard')
        
        # Redirect managers and loan officers to hierarchical view when viewing borrowers
        role_filter = request.GET.get('role', 'all')
        if request.user.role in ['manager', 'loan_officer'] and role_filter == 'borrower':
            return redirect('clients:hierarchical')
        
        # Store request for use in get_context_data
        self.request = request
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator
        from django.db.models import Q
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        role_filter = self.request.GET.get('role', 'all')

        if user.role == 'manager':
            try:
                branch_name = user.managed_branch.name if user.managed_branch else None
                if branch_name:
                    branch_users = User.objects.filter(
                        Q(role='loan_officer', officer_assignment__branch__iexact=branch_name) |
                        Q(role='loan_officer', officer_assignment__isnull=True) |
                        Q(role='borrower', group_memberships__group__branch__iexact=branch_name, group_memberships__is_active=True) |
                        Q(role='borrower', assigned_officer__officer_assignment__branch__iexact=branch_name)
                    ).distinct().order_by('-date_joined')
                else:
                    branch_users = User.objects.exclude(role__in=['admin']).order_by('-date_joined')
            except Exception:
                branch_users = User.objects.exclude(role__in=['admin']).order_by('-date_joined')
            users = branch_users
            all_users = branch_users
        elif user.role == 'loan_officer':
            users = User.objects.filter(
                Q(assigned_officer=user) |
                Q(group_memberships__group__assigned_officer=user, group_memberships__is_active=True),
                role='borrower'
            ).distinct().order_by('-date_joined')
            all_users = users
        else:
            users = User.objects.all().order_by('-date_joined')
            all_users = User.objects.all()

        if role_filter and role_filter != 'all':
            users = users.filter(role=role_filter)

        context['total_users'] = all_users.count()
        context['borrowers_count'] = all_users.filter(role='borrower').count()
        context['officers_count'] = all_users.filter(role='loan_officer').count()
        context['managers_count'] = all_users.filter(role='manager').count()
        context['admins_count'] = all_users.filter(role='admin').count()
        context['active_users'] = all_users.filter(is_active=True).count()
        context['current_filter'] = role_filter

        paginator = Paginator(users, 20)
        page_obj = paginator.get_page(self.request.GET.get('page'))
        context['users'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['page_obj'] = page_obj
        context['paginator'] = paginator

        return context



class UserEditView(LoginRequiredMixin, TemplateView):
    """View for editing a specific user"""
    template_name = 'accounts/user_edit.html'
    
    def dispatch(self, request, *args, **kwargs):
        user_id = self.kwargs.get('pk')
        user_to_edit = User.objects.get(pk=user_id)
        
        # Allow users to edit their own profile
        if request.user.id == int(user_id):
            return super().dispatch(request, *args, **kwargs)
        
        # Only admins can edit other users
        if request.user.role != 'admin' and not request.user.is_superuser:
            messages.error(request, 'Only administrators can edit other users.')
            return redirect('dashboard:dashboard')
        
        # Admins cannot edit other admins (only superusers can)
        if user_to_edit.role == 'admin' and not request.user.is_superuser:
            messages.error(request, 'Only superusers can edit administrator accounts.')
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
        
        # Loan officers can only view clients in their groups or assigned to them
        if request.user.role == 'loan_officer':
            user_id = kwargs.get('pk')
            try:
                user_to_view = User.objects.get(pk=user_id)
                from django.db.models import Q
                is_accessible = (
                    user_to_view.assigned_officer == request.user or
                    user_to_view.group_memberships.filter(
                        group__assigned_officer=request.user,
                        is_active=True
                    ).exists()
                )
                if not is_accessible:
                    messages.error(request, 'You can only view clients assigned to you or in your groups.')
                    return redirect('dashboard:dashboard')
            except User.DoesNotExist:
                pass
        
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


from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.contrib.auth import logout
from .audit_views import log_login, log_logout

class CustomLoginView(DjangoLoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Log the login activity"""
        user = form.get_user()
        if user.role == 'loan_officer' and not user.is_approved:
            from django.contrib import messages
            messages.error(self.request, 'Your account is pending approval.')
            return self.form_invalid(form)
        
        response = super().form_valid(form)
        # Track login
        log_login(self.request.user, self.request)
        return response

    def form_invalid(self, form):
        # Check if the credentials are valid but user is inactive/unapproved
        from django.contrib.auth import authenticate
        username = self.request.POST.get('username', '')
        password = self.request.POST.get('password', '')
        # Try authenticating without is_active check
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and not user.is_active and not user.is_approved:
                from django.contrib import messages
                messages.error(self.request, 'Your account is pending approval. Please wait for a manager to approve your account.')
                form.errors.clear()
        except User.DoesNotExist:
            pass
        return super().form_invalid(form)


class CustomLogoutView(DjangoLogoutView):
    """Custom logout view that tracks logout activity"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Track logout before actually logging out
            log_logout(request.user, request)
        return super().dispatch(request, *args, **kwargs)


class LoanOfficerRegisterView(CreateView):
    template_name = 'accounts/officer_register.html'
    success_url = reverse_lazy('accounts:login')

    def get_form_class(self):
        from .forms import LoanOfficerRegistrationForm
        return LoanOfficerRegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        from django.contrib import messages
        messages.success(self.request, 'Registration submitted. A manager will review and approve your account.')
        return redirect(self.success_url)


from django.contrib.auth.decorators import login_required as _login_required
from django.utils.decorators import method_decorator

@method_decorator(_login_required, name='dispatch')
class PromoteToManagerView(CreateView):
    """Admin promotes a loan officer to manager and assigns a branch."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            from django.contrib import messages
            messages.error(request, 'Only admins can promote users to manager.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        from clients.models import Branch
        user = get_object_or_404(User, pk=pk, role='loan_officer')
        branches = Branch.objects.filter(is_active=True).order_by('name')
        return render(request, 'accounts/promote_manager.html', {'officer': user, 'branches': branches})

    def post(self, request, pk):
        from clients.models import Branch
        from django.utils import timezone as tz
        user = get_object_or_404(User, pk=pk)
        branch_id = request.POST.get('branch')
        try:
            branch = Branch.objects.get(pk=branch_id)
            user.role = 'manager'
            user.is_active = True
            user.is_approved = True
            user.approved_by = request.user
            user.approved_at = tz.now()
            user.save()
            # Assign branch manager
            branch.manager = user
            branch.save(update_fields=['manager'])
            messages.success(request, f'{user.get_full_name()} promoted to manager of {branch.name}.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('dashboard:admin_officers_list')


@method_decorator(_login_required, name='dispatch')
class DeleteUserView(View):
    """Manager deletes a borrower."""

    def get(self, request, pk):
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'Permission denied.')
            return redirect('accounts:manage_users')
        user = get_object_or_404(User, pk=pk, role='borrower')
        user.delete()
        messages.success(request, f'Client deleted successfully.')
        return redirect('accounts:manage_users')


@method_decorator(_login_required, name='dispatch')
class EditClientProfileView(View):
    """Loan officer edits a borrower's basic profile info."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['loan_officer', 'manager', 'admin']:
            messages.error(request, 'Permission denied.')
            return redirect('accounts:manage_users')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        client = get_object_or_404(User, pk=pk, role='borrower')
        return render(request, 'accounts/edit_client_profile.html', {'client': client})

    def post(self, request, pk):
        client = get_object_or_404(User, pk=pk, role='borrower')
        client.first_name = request.POST.get('first_name', client.first_name)
        client.last_name = request.POST.get('last_name', client.last_name)
        client.phone_number = request.POST.get('phone_number', client.phone_number)
        client.address = request.POST.get('address', client.address)
        client.province = request.POST.get('province', client.province)
        client.district = request.POST.get('district', client.district)
        client.employment_status = request.POST.get('employment_status', client.employment_status)
        client.employer_name = request.POST.get('employer_name', client.employer_name)
        client.monthly_income = request.POST.get('monthly_income') or client.monthly_income
        client.save()
        messages.success(request, f'Client profile updated successfully.')
        return redirect('accounts:user_detail', pk=pk)
