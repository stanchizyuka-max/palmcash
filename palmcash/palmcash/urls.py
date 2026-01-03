"""
URL configuration for palmcash project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render

def redirect_to_dashboard(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    else:
        return redirect('accounts:login')

def home_view(request):
    """Simple home page view"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'home_tailwind.html')

urlpatterns = [
    path("admin/", admin.site.urls),
    path('admin-auth/', include('palmcash.admin_urls')),
    path('', home_view, name='home'),
    path('home/', home_view, name='home_alt'),  # Handle /home/ requests
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('loans/', include('loans.urls')),
    path('clients/', include('clients.urls')),
    path('payments/', include('payments.urls')),
    path('documents/', include('documents.urls')),
    path('notifications/', include('notifications.urls')),
    path('messages/', include('internal_messages.urls')),
    path('reports/', include('reports.urls')),
    path('pages/', include('pages.urls')),
    path('adminpanel/', include('adminpanel.urls')),
    path('expenses/', include('expenses.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Fix static files serving
    try:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    except (IndexError, AttributeError):
        pass
