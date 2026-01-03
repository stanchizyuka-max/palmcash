from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib import messages as django_messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Max
from django.utils import timezone
from .models import Message, MessageThread, ThreadMessage
from accounts.models import User


class MessageInboxView(LoginRequiredMixin, ListView):
    """View inbox messages"""
    model = Message
    template_name = 'messages/inbox.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        # Only staff can access messaging
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            django_messages.error(request, 'Only staff members can access internal messaging.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Message.objects.filter(recipient=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.get_queryset().filter(is_read=False).count()
        context['total_count'] = self.get_queryset().count()
        return context


class MessageSentView(LoginRequiredMixin, ListView):
    """View sent messages"""
    model = Message
    template_name = 'messages/sent.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            django_messages.error(request, 'Only staff members can access internal messaging.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user)


class MessageDetailView(LoginRequiredMixin, DetailView):
    """View a single message"""
    model = Message
    template_name = 'messages/detail.html'
    context_object_name = 'message'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            django_messages.error(request, 'Only staff members can access internal messaging.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Users can only view messages they sent or received
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        )
    
    def get_object(self):
        obj = super().get_object()
        # Mark as read if recipient is viewing
        if obj.recipient == self.request.user:
            obj.mark_as_read()
        return obj


class MessageComposeView(LoginRequiredMixin, View):
    """Compose and send a new message"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            django_messages.error(request, 'Only staff members can access internal messaging.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        # Get staff members for recipient selection
        staff_members = User.objects.filter(
            role__in=['admin', 'manager', 'loan_officer']
        ).exclude(id=request.user.id)
        
        # Get loan_id if provided (for context)
        loan_id = request.GET.get('loan_id')
        loan = None
        if loan_id:
            from loans.models import Loan
            loan = get_object_or_404(Loan, id=loan_id)
        
        return render(request, 'messages/compose.html', {
            'staff_members': staff_members,
            'loan': loan
        })
    
    def post(self, request):
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        loan_id = request.POST.get('loan_id')
        
        if not recipient_id or not subject or not body:
            django_messages.error(request, 'Please fill in all required fields.')
            return redirect('messages:compose')
        
        recipient = get_object_or_404(User, id=recipient_id)
        
        # Create message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            subject=subject,
            body=body,
            loan_id=loan_id if loan_id else None
        )
        
        # Create notification for recipient
        self._create_notification(message)
        
        django_messages.success(request, f'Message sent to {recipient.full_name}!')
        return redirect('messages:inbox')
    
    def _create_notification(self, message):
        """Create notification for message recipient"""
        try:
            from notifications.models import Notification
            
            Notification.objects.create(
                recipient=message.recipient,
                subject=f'New message from {message.sender.full_name}',
                message=f'{message.sender.full_name} sent you a message: "{message.subject}"',
                channel='in_app',
                recipient_address=message.recipient.email or '',
                scheduled_at=timezone.now(),
                loan=message.loan,
                status='sent'
            )
        except Exception as e:
            print(f"Error creating message notification: {e}")


class MessageReplyView(LoginRequiredMixin, View):
    """Reply to a message"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            django_messages.error(request, 'Only staff members can access internal messaging.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        original_message = get_object_or_404(
            Message,
            Q(sender=request.user) | Q(recipient=request.user),
            pk=pk
        )
        
        return render(request, 'messages/reply.html', {
            'original_message': original_message
        })
    
    def post(self, request, pk):
        original_message = get_object_or_404(
            Message,
            Q(sender=request.user) | Q(recipient=request.user),
            pk=pk
        )
        
        body = request.POST.get('body')
        
        if not body:
            django_messages.error(request, 'Please enter a message.')
            return redirect('messages:reply', pk=pk)
        
        # Determine recipient (reply to sender)
        recipient = original_message.sender if original_message.recipient == request.user else original_message.recipient
        
        # Create reply message
        reply = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            subject=f"Re: {original_message.subject}",
            body=body,
            loan=original_message.loan
        )
        
        # Create notification
        self._create_notification(reply)
        
        django_messages.success(request, 'Reply sent!')
        return redirect('messages:detail', pk=reply.pk)
    
    def _create_notification(self, message):
        """Create notification for message recipient"""
        try:
            from notifications.models import Notification
            
            Notification.objects.create(
                recipient=message.recipient,
                subject=f'Reply from {message.sender.full_name}',
                message=f'{message.sender.full_name} replied to your message: "{message.subject}"',
                channel='in_app',
                recipient_address=message.recipient.email or '',
                scheduled_at=timezone.now(),
                loan=message.loan,
                status='sent'
            )
        except Exception as e:
            print(f"Error creating reply notification: {e}")


class ThreadListView(LoginRequiredMixin, ListView):
    """View message threads"""
    model = MessageThread
    template_name = 'messages/threads.html'
    context_object_name = 'threads'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            django_messages.error(request, 'Only staff members can access internal messaging.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return MessageThread.objects.filter(
            participants=self.request.user
        ).annotate(
            message_count=Count('thread_messages'),
            last_message_time=Max('thread_messages__created_at')
        ).order_by('-last_message_time')


class ThreadDetailView(LoginRequiredMixin, DetailView):
    """View a message thread"""
    model = MessageThread
    template_name = 'messages/thread_detail.html'
    context_object_name = 'thread'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            django_messages.error(request, 'Only staff members can access internal messaging.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return MessageThread.objects.filter(participants=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.get_object()
        
        # Get all messages in thread
        context['thread_messages'] = thread.thread_messages.all()
        
        # Mark messages as read
        for msg in context['thread_messages']:
            if self.request.user not in msg.read_by.all():
                msg.read_by.add(self.request.user)
        
        return context
    
    def post(self, request, pk):
        """Add message to thread"""
        thread = self.get_object()
        body = request.POST.get('body')
        
        if not body:
            django_messages.error(request, 'Please enter a message.')
            return redirect('messages:thread_detail', pk=pk)
        
        # Create thread message
        ThreadMessage.objects.create(
            thread=thread,
            sender=request.user,
            body=body
        )
        
        # Update thread timestamp
        thread.updated_at = timezone.now()
        thread.save()
        
        # Notify other participants
        self._notify_participants(thread, request.user)
        
        django_messages.success(request, 'Message added to thread!')
        return redirect('messages:thread_detail', pk=pk)
    
    def _notify_participants(self, thread, sender):
        """Notify thread participants about new message"""
        try:
            from notifications.models import Notification
            
            for participant in thread.participants.exclude(id=sender.id):
                Notification.objects.create(
                    recipient=participant,
                    subject=f'New message in: {thread.subject}',
                    message=f'{sender.full_name} posted in thread "{thread.subject}"',
                    channel='in_app',
                    recipient_address=participant.email or '',
                    scheduled_at=timezone.now(),
                    loan=thread.loan,
                    status='sent'
                )
        except Exception as e:
            print(f"Error notifying thread participants: {e}")
