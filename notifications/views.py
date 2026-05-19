from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.contrib import messages
from django.http import JsonResponse
from .models import Notification, NotificationTemplate

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        from django.db.models import Q
        
        queryset = Notification.objects.filter(
            recipient=self.request.user
        )
        
        # Get filter parameters
        branch_filter = self.request.GET.get('branch', '').strip()
        status_filter = self.request.GET.get('status_filter', '')
        
        # Apply branch filter (for admins only)
        if branch_filter and self.request.user.role == 'admin':
            # Filter notifications by branch through loan or payment relationships
            queryset = queryset.filter(
                Q(loan__borrower__assigned_officer__officer_assignment__branch__iexact=branch_filter) |
                Q(loan__borrower__group_memberships__group__branch__iexact=branch_filter, loan__borrower__group_memberships__is_active=True) |
                Q(payment__loan__borrower__assigned_officer__officer_assignment__branch__iexact=branch_filter) |
                Q(payment__loan__borrower__group_memberships__group__branch__iexact=branch_filter, payment__loan__borrower__group_memberships__is_active=True)
            ).distinct()
        
        # Apply status filter
        if status_filter == 'unread':
            queryset = queryset.filter(status__in=['pending', 'sent', 'delivered'])
        elif status_filter == 'read':
            queryset = queryset.filter(status='read')
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        from django.db.models import Q
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        branch_filter = self.request.GET.get('branch', '').strip()
        status_filter = self.request.GET.get('status_filter', '')
        
        # Base queryset for counts (without filters)
        base_queryset = Notification.objects.filter(recipient=self.request.user)
        
        # Get unread count
        context['unread_count'] = base_queryset.filter(
            status__in=['pending', 'sent', 'delivered']
        ).count()
        
        # Get notifications by status (limited for display)
        context['unread_notifications'] = base_queryset.filter(
            status__in=['pending', 'sent', 'delivered']
        ).order_by('-created_at')[:10]
        
        context['read_notifications'] = base_queryset.filter(
            status='read'
        ).order_by('-created_at')[:10]
        
        # Add filter context
        context['branch_filter'] = branch_filter
        context['status_filter'] = status_filter
        
        # Get unique branches for filter dropdown (admin only)
        if self.request.user.role == 'admin':
            try:
                from clients.models import OfficerAssignment
                context['branches'] = OfficerAssignment.objects.values_list('branch', flat=True).distinct().order_by('branch')
            except Exception as e:
                # Fallback if OfficerAssignment doesn't exist or import fails
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error loading branches for notifications: {str(e)}")
                context['branches'] = []
        
        return context


class NotificationDetailView(LoginRequiredMixin, DetailView):
    model = Notification
    template_name = 'notifications/detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Mark as read when viewed
        if obj.status != 'read':
            obj.mark_as_read()
        return obj


class MarkAsReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification, 
            pk=pk, 
            recipient=request.user
        )
        
        notification.mark_as_read()
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Notification marked as read.')
        return redirect('notifications:list')


class MarkAllAsReadView(LoginRequiredMixin, View):
    def post(self, request):
        # Mark all unread notifications as read
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            status__in=['pending', 'sent', 'delivered']
        )
        
        from django.utils import timezone
        now = timezone.now()
        
        for notification in unread_notifications:
            notification.read_at = now
            notification.status = 'read'
            notification.save()
        
        count = unread_notifications.count()
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'count': count})
        
        messages.success(request, f'{count} notification(s) marked as read.')
        return redirect('notifications:list')


class TemplateListView(LoginRequiredMixin, ListView):
    model = NotificationTemplate
    template_name = 'notifications/templates.html'
    context_object_name = 'templates'
    
    def dispatch(self, request, *args, **kwargs):
        # Only admins can view templates
        if request.user.role not in ['admin']:
            messages.error(request, 'You do not have permission to view notification templates.')
            return redirect('notifications:list')
        return super().dispatch(request, *args, **kwargs)
