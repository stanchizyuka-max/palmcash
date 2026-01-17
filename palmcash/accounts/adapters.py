from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .models import User

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter for Google OAuth login"""
    
    def pre_social_login(self, request, sociallogin):
        """
        This method is called when a user is about to login via social account.
        We can customize the user creation and login process here.
        """
        
        # If the user already exists, just continue
        if sociallogin.is_existing:
            return
        
        # Get user data from Google
        email = sociallogin.account.extra_data.get('email')
        first_name = sociallogin.account.extra_data.get('given_name', '')
        last_name = sociallogin.account.extra_data.get('family_name', '')
        
        # Check if a user with this email already exists
        try:
            existing_user = User.objects.get(email=email)
            # Link the social account to the existing user
            sociallogin.connect(request, existing_user)
            messages.success(request, f'Your Google account has been linked to your existing Palm Cash account!')
        except User.DoesNotExist:
            # Create a new user with the Google data
            user = User(
                email=email,
                username=email,  # Use email as username
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                # Set default role for new users
                role='borrower',
                # Google users are considered verified
                is_verified=True,
            )
            user.save()
            
            # Link the social account to the new user
            sociallogin.connect(request, user)
            messages.success(request, f'Welcome to Palm Cash, {first_name}! Your account has been created successfully.')
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Return the URL to redirect to after a successful social account connection.
        """
        return reverse('dashboard:dashboard')
    
    def get_disconnect_redirect_url(self, request, socialaccount):
        """
        Return the URL to redirect to after a successful social account disconnection.
        """
        return reverse('accounts:login')
