from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Payment, PaymentSchedule

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        if self.request.user.role == 'borrower':
            return Payment.objects.filter(loan__borrower=self.request.user)
        return Payment.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add pending payments count for staff
        if self.request.user.role in ['admin', 'loan_officer']:
            context['pending_count'] = Payment.objects.filter(status='pending').count()
        
        return context

class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/detail.html'
    context_object_name = 'payment'

class MakePaymentView(LoginRequiredMixin, CreateView):
    model = Payment
    template_name = 'payments/make.html'
    fields = ['amount', 'payment_method', 'reference_number', 'notes']
    
    def dispatch(self, request, *args, **kwargs):
        # Only borrowers can access the payment form
        if request.user.role != 'borrower':
            messages.error(request, 'Only borrowers can submit payments. Please contact the borrower to make their payment.')
            return redirect('payments:list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('payments:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        from django.shortcuts import get_object_or_404
        from loans.models import Loan
        from django.utils import timezone
        
        # Get the loan from URL parameter
        loan_id = self.kwargs.get('loan_id')
        loan = get_object_or_404(Loan, pk=loan_id)
        
        # Only borrowers can make payments, and only for their own loans
        if self.request.user.role != 'borrower':
            messages.error(self.request, 'Only borrowers can submit payments. Administrators can only process payments submitted by borrowers.')
            return redirect('loans:list')
        
        if loan.borrower != self.request.user:
            messages.error(self.request, 'You can only make payments for your own loans.')
            return redirect('loans:list')
        
        # Set payment details
        form.instance.loan = loan
        form.instance.payment_date = timezone.now()
        form.instance.processed_by = self.request.user
        
        # Check if this is for a specific payment schedule
        schedule_id = self.request.GET.get('schedule_id')
        if schedule_id:
            try:
                # Validate that schedule_id is a valid integer
                schedule_id = int(schedule_id)
                payment_schedule = PaymentSchedule.objects.get(id=schedule_id, loan=loan)
                form.instance.payment_schedule = payment_schedule
            except (ValueError, TypeError, PaymentSchedule.DoesNotExist):
                # Invalid schedule_id or schedule doesn't exist, just ignore it
                pass
        
        # Save the payment first
        response = super().form_valid(form)
        
        # Create notifications for staff (admins, loan officers, managers)
        self._notify_staff_of_new_payment(form.instance)
        
        # Create notification for borrower (payment under review)
        self._notify_borrower_payment_submitted(form.instance)
        
        messages.success(self.request, f'Payment of K{form.instance.amount} has been submitted successfully!')
        return response
    
    def _notify_staff_of_new_payment(self, payment):
        """Notify all staff members about new payment submission"""
        try:
            from notifications.models import Notification, NotificationTemplate
            from accounts.models import User
            
            # Get staff users (admins, loan officers, managers)
            staff_users = User.objects.filter(role__in=['admin', 'loan_officer', 'manager'])
            
            # Try to get the notification template
            try:
                template = NotificationTemplate.objects.get(
                    notification_type='payment_submitted',
                    is_active=True
                )
            except NotificationTemplate.DoesNotExist:
                # Create a default notification without template
                for staff_user in staff_users:
                    Notification.objects.create(
                        recipient=staff_user,
                        template=None,
                        subject=f'New Payment Submitted - {payment.payment_number}',
                        message=f'A new payment of K{payment.amount:,.2f} has been submitted by {payment.loan.borrower.get_full_name()} for loan {payment.loan.application_number}. Please review and process this payment.',
                        channel='in_app',
                        recipient_address=staff_user.email or '',
                        scheduled_at=timezone.now(),
                        loan=payment.loan,
                        payment=payment,
                        status='sent'
                    )
                return
            
            # Create notifications for each staff member
            for staff_user in staff_users:
                message = template.message_template.format(
                    borrower_name=payment.loan.borrower.get_full_name(),
                    amount=f"{payment.amount:,.2f}",
                    payment_number=payment.payment_number,
                    loan_number=payment.loan.application_number
                )
                
                Notification.objects.create(
                    recipient=staff_user,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel=template.channel,
                    recipient_address=staff_user.email or '',
                    scheduled_at=timezone.now(),
                    loan=payment.loan,
                    payment=payment,
                    status='sent'
                )
        except Exception as e:
            print(f"Error creating staff notifications: {e}")
    
    def _notify_borrower_payment_submitted(self, payment):
        """Notify borrower that payment is under review"""
        try:
            from notifications.models import Notification, NotificationTemplate
            
            try:
                template = NotificationTemplate.objects.get(
                    notification_type='payment_under_review',
                    is_active=True
                )
            except NotificationTemplate.DoesNotExist:
                # Create a default notification without template
                Notification.objects.create(
                    recipient=payment.loan.borrower,
                    template=None,
                    subject=f'Payment Submitted - Under Review',
                    message=f'Your payment of K{payment.amount:,.2f} for loan {payment.loan.application_number} has been received and is currently under review. You will be notified once it has been processed.',
                    channel='in_app',
                    recipient_address=payment.loan.borrower.email or '',
                    scheduled_at=timezone.now(),
                    loan=payment.loan,
                    payment=payment,
                    status='sent'
                )
                return
            
            message = template.message_template.format(
                borrower_name=payment.loan.borrower.get_full_name(),
                amount=f"{payment.amount:,.2f}",
                payment_number=payment.payment_number,
                loan_number=payment.loan.application_number
            )
            
            Notification.objects.create(
                recipient=payment.loan.borrower,
                template=template,
                subject=template.subject,
                message=message,
                channel=template.channel,
                recipient_address=payment.loan.borrower.email or '',
                scheduled_at=timezone.now(),
                loan=payment.loan,
                payment=payment,
                status='sent'
            )
        except Exception as e:
            print(f"Error creating borrower notification: {e}")

class ConfirmPaymentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # Check user permissions
        if request.user.role not in ['admin', 'loan_officer', 'manager']:
            messages.error(request, 'You do not have permission to confirm payments.')
            return redirect('payments:detail', pk=pk)
        
        # Get the payment
        payment = get_object_or_404(Payment, pk=pk)
        
        # Check if payment is pending
        if payment.status != 'pending':
            messages.warning(request, f'Payment {payment.payment_number} is not pending confirmation. Current status: {payment.get_status_display()}')
            return redirect('payments:detail', pk=pk)
        
        # Confirm the payment
        payment.status = 'completed'
        payment.processed_by = request.user
        payment.updated_at = timezone.now()
        payment.save()
        
        # Update payment schedule if linked
        if payment.payment_schedule:
            payment.payment_schedule.is_paid = True
            payment.payment_schedule.paid_date = payment.payment_date.date()
            payment.payment_schedule.save()
        
        # Update loan balance
        loan = payment.loan
        loan.amount_paid += payment.amount
        if loan.balance_remaining:
            loan.balance_remaining -= payment.amount
        
        # Check if loan is fully paid and update status
        self._update_loan_status_if_completed(loan)
        loan.save()
        
        # Send payment confirmation email
        from common.email_utils import send_payment_received_email
        try:
            send_payment_received_email(payment)
        except Exception as e:
            print(f"Error sending payment confirmation email: {e}")
        
        # Create notification for borrower (payment approved)
        self._create_payment_notification(payment, 'confirmed')
        
        # Notify staff about payment confirmation
        self._notify_staff_payment_confirmed(payment)
        
        messages.success(
            request, 
            f'Payment {payment.payment_number} of K{payment.amount:,.2f} has been confirmed successfully.'
        )
        return redirect('payments:detail', pk=pk)
    
    def _update_loan_status_if_completed(self, loan):
        """Check if loan is fully paid and update status to completed"""
        # Check if all payment schedules are paid
        unpaid_schedules = PaymentSchedule.objects.filter(loan=loan, is_paid=False).count()
        
        # Also check if balance is zero or negative
        balance_cleared = loan.balance_remaining is not None and loan.balance_remaining <= 0
        
        if unpaid_schedules == 0 or balance_cleared:
            loan.status = 'completed'
            # Create completion notification
            self._create_loan_completion_notification(loan)
    
    def _create_loan_completion_notification(self, loan):
        """Create notification for loan completion"""
        try:
            from notifications.models import Notification, NotificationTemplate
            
            try:
                template = NotificationTemplate.objects.get(notification_type='loan_completed')
                
                message = template.message_template.format(
                    borrower_name=loan.borrower.full_name,
                    loan_number=loan.application_number,
                    total_amount=f"{loan.total_amount:,.2f}" if loan.total_amount else "0.00"
                )
                
                Notification.objects.create(
                    recipient=loan.borrower,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel=template.channel,
                    recipient_address=loan.borrower.email or str(loan.borrower.phone_number),
                    scheduled_at=timezone.now(),
                    loan=loan
                )
            except NotificationTemplate.DoesNotExist:
                pass  # Template not configured
        except ImportError:
            pass  # Notifications app not available
    
    def _create_payment_notification(self, payment, action):
        """Create notification for payment confirmation/rejection"""
        try:
            from notifications.models import Notification, NotificationTemplate
            
            # Get notification template
            template_type = 'payment_received' if action == 'confirmed' else 'payment_rejected'
            try:
                template = NotificationTemplate.objects.get(notification_type=template_type)
                
                # Create notification
                message = template.message_template.format(
                    borrower_name=payment.loan.borrower.full_name,
                    amount=f"{payment.amount:,.2f}",
                    payment_number=payment.payment_number,
                    loan_number=payment.loan.application_number
                )
                
                Notification.objects.create(
                    recipient=payment.loan.borrower,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel=template.channel,
                    recipient_address=payment.loan.borrower.email or str(payment.loan.borrower.phone_number),
                    scheduled_at=timezone.now(),
                    loan=payment.loan,
                    payment=payment
                )
            except NotificationTemplate.DoesNotExist:
                # Create default notification
                subject = f'Payment {"Approved" if action == "confirmed" else "Rejected"}'
                if action == 'confirmed':
                    message = f'Your payment of K{payment.amount:,.2f} (Payment #{payment.payment_number}) for loan {payment.loan.application_number} has been approved and processed successfully.'
                else:
                    message = f'Your payment of K{payment.amount:,.2f} (Payment #{payment.payment_number}) for loan {payment.loan.application_number} has been rejected. Please contact us for more information.'
                
                Notification.objects.create(
                    recipient=payment.loan.borrower,
                    template=None,
                    subject=subject,
                    message=message,
                    channel='in_app',
                    recipient_address=payment.loan.borrower.email or '',
                    scheduled_at=timezone.now(),
                    loan=payment.loan,
                    payment=payment,
                    status='sent'
                )
        except Exception as e:
            print(f"Error creating payment notification: {e}")
    
    def _notify_staff_payment_confirmed(self, payment):
        """Notify staff that payment has been confirmed"""
        try:
            from notifications.models import Notification
            from accounts.models import User
            
            # Get staff users (admins, loan officers, managers)
            staff_users = User.objects.filter(role__in=['admin', 'loan_officer', 'manager']).exclude(id=self.request.user.id)
            
            # Create notifications for each staff member
            for staff_user in staff_users:
                Notification.objects.create(
                    recipient=staff_user,
                    template=None,
                    subject=f'Payment Confirmed - {payment.payment_number}',
                    message=f'Payment of K{payment.amount:,.2f} for loan {payment.loan.application_number} has been confirmed by {self.request.user.get_full_name()}.',
                    channel='in_app',
                    recipient_address=staff_user.email or '',
                    scheduled_at=timezone.now(),
                    loan=payment.loan,
                    payment=payment,
                    status='sent'
                )
        except Exception as e:
            print(f"Error notifying staff: {e}")

class RejectPaymentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role not in ['admin', 'loan_officer']:
            messages.error(request, 'You do not have permission to reject payments.')
            return redirect('payments:detail', pk=pk)
        
        payment = get_object_or_404(Payment, pk=pk)
        
        if payment.status != 'pending':
            messages.warning(request, f'Payment {payment.payment_number} is not pending review.')
            return redirect('payments:detail', pk=pk)
        
        # Get rejection reason
        rejection_reason = request.POST.get('reason', '')
        if not rejection_reason:
            messages.error(request, 'Please provide a reason for rejecting the payment.')
            return redirect('payments:detail', pk=pk)
        
        # Reject the payment
        payment.status = 'failed'
        payment.processed_by = request.user
        payment.updated_at = timezone.now()
        
        # Add rejection reason to notes
        if payment.notes:
            payment.notes += f"\n\nREJECTED: {rejection_reason}"
        else:
            payment.notes = f"REJECTED: {rejection_reason}"
        
        payment.save()
        
        # Create notification for borrower
        self._create_payment_notification(payment, 'rejected')
        
        messages.success(
            request, 
            f'Payment {payment.payment_number} has been rejected. Reason: {rejection_reason}'
        )
        return redirect('payments:detail', pk=pk)
    
    def _create_payment_notification(self, payment, action):
        """Create notification for payment confirmation/rejection"""
        try:
            from notifications.models import Notification, NotificationTemplate
            
            # Get notification template
            template_type = 'payment_received' if action == 'confirmed' else 'payment_rejected'
            try:
                template = NotificationTemplate.objects.get(notification_type=template_type)
                
                # Create notification
                message = template.message_template.format(
                    borrower_name=payment.loan.borrower.full_name,
                    amount=f"{payment.amount:,.2f}",
                    payment_number=payment.payment_number,
                    loan_number=payment.loan.application_number
                )
                
                Notification.objects.create(
                    recipient=payment.loan.borrower,
                    template=template,
                    subject=template.subject,
                    message=message,
                    channel=template.channel,
                    recipient_address=payment.loan.borrower.email or str(payment.loan.borrower.phone_number),
                    scheduled_at=timezone.now(),
                    loan=payment.loan,
                    payment=payment
                )
            except NotificationTemplate.DoesNotExist:
                pass  # Template not configured
        except ImportError:
            pass  # Notifications app not available

class UpfrontPaymentView(LoginRequiredMixin, View):
    """View for paying the 10% upfront payment for a new loan"""
    
    def get(self, request, loan_id):
        from loans.models import Loan
        from decimal import Decimal
        
        # Get the loan
        loan = get_object_or_404(Loan, pk=loan_id, borrower=request.user)
        
        # Check if loan is in pending status (just created)
        if loan.status != 'pending':
            messages.error(request, 'This loan is not in pending status. Upfront payment is only required for new applications.')
            return redirect('loans:detail', pk=loan_id)
        
        # Calculate upfront payment (10% of principal)
        upfront_amount = loan.principal_amount * Decimal('0.10')
        
        context = {
            'loan': loan,
            'upfront_amount': upfront_amount,
            'principal_amount': loan.principal_amount,
            'interest_rate': loan.interest_rate,
        }
        
        return render(request, 'payments/upfront_payment.html', context)
    
    def post(self, request, loan_id):
        from loans.models import Loan
        from django.utils import timezone
        from decimal import Decimal
        
        # Get the loan
        loan = get_object_or_404(Loan, pk=loan_id, borrower=request.user)
        
        # Check if loan is in pending status
        if loan.status != 'pending':
            messages.error(request, 'This loan is not in pending status.')
            return redirect('loans:detail', pk=loan_id)
        
        # Calculate upfront payment
        upfront_amount = loan.principal_amount * Decimal('0.10')
        
        # Get payment method
        payment_method = request.POST.get('payment_method', '')
        reference_number = request.POST.get('reference_number', '')
        
        if not payment_method:
            messages.error(request, 'Please select a payment method.')
            return redirect('payments:upfront_payment', loan_id=loan_id)
        
        if not reference_number:
            messages.error(request, 'Please enter a payment reference number.')
            return redirect('payments:upfront_payment', loan_id=loan_id)
        
        # Create payment record for upfront payment
        payment = Payment.objects.create(
            loan=loan,
            amount=upfront_amount,
            payment_method=payment_method,
            reference_number=reference_number,
            payment_date=timezone.now(),
            processed_by=request.user,
            notes=f'Upfront payment (10% of principal) for loan application {loan.application_number}',
            status='pending'  # Will be confirmed by admin
        )
        
        # Notify admins about upfront payment submission
        self._notify_admins_of_upfront_payment(payment)
        
        messages.success(
            request, 
            f'Upfront payment of K{upfront_amount:,.2f} has been submitted successfully! '
            'Your payment will be reviewed and processed by our team.'
        )
        
        return redirect('payments:detail', pk=payment.pk)
    
    def _notify_admins_of_upfront_payment(self, payment):
        """Notify admins about upfront payment submission"""
        try:
            from notifications.models import Notification, NotificationTemplate
            from accounts.models import User
            
            # Get staff users
            staff_users = User.objects.filter(role__in=['admin', 'loan_officer', 'manager'])
            
            # Try to get notification template
            try:
                template = NotificationTemplate.objects.get(
                    notification_type='payment_submitted',
                    is_active=True
                )
            except NotificationTemplate.DoesNotExist:
                # Create default notification
                for staff_user in staff_users:
                    Notification.objects.create(
                        recipient=staff_user,
                        template=None,
                        subject=f'Upfront Payment Submitted - {payment.payment_number}',
                        message=f'Upfront payment of K{payment.amount:,.2f} has been submitted by {payment.loan.borrower.get_full_name()} for loan {payment.loan.application_number}. Please review and confirm this payment.',
                        channel='in_app',
                        recipient_address=staff_user.email or '',
                        scheduled_at=timezone.now(),
                        loan=payment.loan,
                        payment=payment,
                        status='sent'
                    )
                return
            
            # Create notifications with template
            for staff_user in staff_users:
                message = template.message_template.format(
                    borrower_name=payment.loan.borrower.get_full_name(),
                    amount=f"{payment.amount:,.2f}",
                    payment_number=payment.payment_number,
                    loan_number=payment.loan.application_number
                )
                
                Notification.objects.create(
                    recipient=staff_user,
                    template=template,
                    subject=f'Upfront Payment - {template.subject}',
                    message=message,
                    channel=template.channel,
                    recipient_address=staff_user.email or '',
                    scheduled_at=timezone.now(),
                    loan=payment.loan,
                    payment=payment,
                    status='sent'
                )
        except Exception as e:
            print(f"Error notifying admins of upfront payment: {e}")


class PaymentScheduleView(LoginRequiredMixin, ListView):
    model = PaymentSchedule
    template_name = 'payments/schedule.html'
    context_object_name = 'schedule'
    
    def get_queryset(self):
        loan_id = self.kwargs['loan_id']
        queryset = PaymentSchedule.objects.filter(loan_id=loan_id).order_by('installment_number')
        
        # Check if user has permission to view this loan's schedule
        if self.request.user.role == 'borrower':
            queryset = queryset.filter(loan__borrower=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schedule = context['schedule']
        
        # Get the loan object
        loan_id = self.kwargs['loan_id']
        try:
            from loans.models import Loan
            loan = Loan.objects.get(id=loan_id)
            context['loan'] = loan
        except Loan.DoesNotExist:
            context['loan'] = None
        
        if schedule:
            # Calculate payment statistics
            context['paid_count'] = schedule.filter(is_paid=True).count()
            context['pending_count'] = schedule.filter(is_paid=False).count()
            context['overdue_count'] = sum(1 for payment in schedule if payment.is_overdue)
            
            # Calculate totals
            context['total_principal'] = sum(payment.principal_amount for payment in schedule)
            context['total_interest'] = sum(payment.interest_amount for payment in schedule)
            context['total_amount'] = sum(payment.total_amount for payment in schedule)
            context['total_penalties'] = sum(payment.penalty_amount for payment in schedule)
            
            # Find next payment due
            next_payment = None
            for payment in schedule:
                if not payment.is_paid:
                    next_payment = payment
                    break
            context['next_payment'] = next_payment
        else:
            # Initialize totals to 0 if no schedule
            context['total_principal'] = 0
            context['total_interest'] = 0
            context['total_amount'] = 0
            context['total_penalties'] = 0
        
        return context