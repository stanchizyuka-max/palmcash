from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Payment, PaymentSchedule, PaymentCollection

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'borrower':
            return Payment.objects.filter(loan__borrower=user)
        if user.role == 'manager':
            try:
                branch = user.managed_branch
                from django.db.models import Q
                from loans.models import Loan
                branch_loans = Loan.objects.filter(
                    Q(loan_officer__officer_assignment__branch=branch.name) |
                    Q(borrower__group_memberships__group__branch=branch.name)
                ).values_list('id', flat=True)
                return Payment.objects.filter(loan_id__in=branch_loans).order_by('-created_at')
            except Exception:
                return Payment.objects.none()
        return Payment.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.role in ['admin', 'loan_officer', 'manager']:
            qs = self.get_queryset()
            context['pending_count'] = qs.filter(status='pending').count()
        return context

class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/detail.html'
    context_object_name = 'payment'

class MakePaymentView(LoginRequiredMixin, View):
    template_name = 'payments/make.html'

    def _get_form(self, request, data=None):
        from .forms import RecordPaymentForm
        loan_id = self.kwargs.get('loan_id')
        if request.user.role == 'loan_officer':
            return RecordPaymentForm(data, officer=request.user, loan_id=loan_id)
        return RecordPaymentForm(data, loan_id=loan_id)

    def get(self, request, *args, **kwargs):
        if request.user.role not in ['loan_officer', 'manager', 'admin']:
            messages.error(request, 'Only staff can record payments.')
            return redirect('dashboard:dashboard')
        return render(request, self.template_name, {'form': self._get_form(request)})

    def post(self, request, *args, **kwargs):
        if request.user.role not in ['loan_officer', 'manager', 'admin']:
            messages.error(request, 'Only staff can record payments.')
            return redirect('dashboard:dashboard')

        form = self._get_form(request, request.POST)
        if form.is_valid():
            from datetime import datetime
            loan = form.cleaned_data['loan']
            method = form.cleaned_data['payment_method']
            # Map custom choices to Payment model choices
            method_map = {'mtn': 'mobile_money', 'airtel': 'mobile_money'}
            payment_method = method_map.get(method, method)

            amount = form.cleaned_data['amount']
            payment_date = form.cleaned_data['payment_date']

            payment = Payment.objects.create(
                loan=loan,
                amount=amount,
                payment_method=payment_method,
                reference_number=form.cleaned_data.get('reference_number', ''),
                notes=f"[{method.upper()}] " + form.cleaned_data.get('notes', ''),
                payment_date=datetime.combine(payment_date, datetime.min.time()).replace(tzinfo=timezone.get_current_timezone()),
                processed_by=request.user,
                status='pending',
            )

            # Link to oldest unpaid schedule
            oldest_unpaid = PaymentSchedule.objects.filter(loan=loan, is_paid=False).order_by('due_date').first()
            if oldest_unpaid:
                payment.payment_schedule = oldest_unpaid
                payment.save(update_fields=['payment_schedule'])

            # Update PaymentCollection — cap collected at expected (overpayment handled by schedule)
            expected = oldest_unpaid.total_amount if oldest_unpaid else loan.payment_amount
            collection, _ = PaymentCollection.objects.get_or_create(
                loan=loan,
                collection_date=payment_date,
                defaults={
                    'expected_amount': expected,
                    'collected_amount': 0,
                    'status': 'scheduled',
                }
            )
            collection.collected_amount = min(amount, collection.expected_amount)
            collection.collected_by = request.user
            collection.actual_collection_date = timezone.now()
            collection.status = 'completed'
            collection.is_partial = collection.collected_amount < collection.expected_amount
            collection.save()

            messages.success(request, f'Payment of K{amount:,.2f} recorded for {loan.borrower.get_full_name()} — awaiting manager review.')
            return redirect('payments:detail', pk=payment.pk)

        return render(request, self.template_name, {'form': form})
    

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

        # Get loan first
        loan = payment.loan

        # Update payment schedule — distribute across installments (supports overpayment)
        from payments.services import distribute_payment
        distribute_payment(loan, payment.amount, payment.payment_date.date())
        
        # Update loan balance
        loan.amount_paid += payment.amount
        if loan.balance_remaining:
            loan.balance_remaining -= payment.amount
        
        # Check if this is an upfront payment (security deposit)
        if (loan.upfront_payment_required and 
            loan.upfront_payment_paid < loan.upfront_payment_required and
            not payment.payment_schedule):
            upfront_remaining = loan.upfront_payment_required - loan.upfront_payment_paid
            upfront_amount = min(payment.amount, upfront_remaining)
            loan.upfront_payment_paid += upfront_amount
            loan.upfront_payment_date = payment.payment_date
        
        self._update_loan_status_if_completed(loan)
        loan.save()

        # Record vault inflow for loan repayment
        try:
            from loans.vault_services import record_payment_collection
            record_payment_collection(loan, payment.amount, request.user)
        except Exception as e:
            print(f"Vault record error: {e}")

        # Update PaymentCollection — one entry per installment paid (handles overdue + overpayment)
        paid_schedules = PaymentSchedule.objects.filter(
            loan=loan,
            amount_paid__gt=0,
        ).order_by('due_date')
        for sched in paid_schedules:
            coll, _ = PaymentCollection.objects.get_or_create(
                loan=loan,
                collection_date=sched.due_date,
                defaults={
                    'expected_amount': sched.total_amount,
                    'collected_amount': 0,
                    'status': 'scheduled',
                }
            )
            if coll.collected_amount < sched.amount_paid:
                coll.collected_amount = sched.amount_paid
                coll.collected_by = request.user
                coll.actual_collection_date = timezone.now()
                coll.status = 'completed' if sched.is_paid else 'in_progress'
                coll.is_partial = not sched.is_paid
                coll.save()
        
        # Create passbook entry for payment
        try:
            from payments.models import PassbookEntry
            from datetime import date
            PassbookEntry.objects.create(
                loan=loan,
                entry_type='payment',
                amount=payment.amount,
                description=f'Payment received for {loan.application_number} (Payment #{payment.payment_number})',
                entry_date=date.today(),
                recorded_by=request.user
            )
        except Exception as e:
            print(f"Error creating passbook entry: {e}")
        
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
        
        # Check if loan is in approved status (ready for upfront payment)
        if loan.status not in ['approved', 'pending']:
            messages.error(request, 'This loan is not ready for upfront payment. Only approved or pending loans can receive upfront payments.')
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
        
        # Check if loan is ready for upfront payment
        if loan.status not in ['approved', 'pending']:
            messages.error(request, 'This loan is not ready for upfront payment.')
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
        
        # Create or update SecurityDeposit record
        from loans.models import SecurityDeposit
        security_deposit, created = SecurityDeposit.objects.get_or_create(
            loan=loan,
            defaults={
                'required_amount': upfront_amount,
                'paid_amount': upfront_amount,
                'payment_date': timezone.now(),
                'is_verified': False,
            }
        )
        
        # Always update the deposit to ensure payment is recorded
        security_deposit.paid_amount = upfront_amount
        security_deposit.payment_date = timezone.now()
        security_deposit.is_verified = False
        security_deposit.save()
        
        print(f"DEBUG: Updated SecurityDeposit - Required: K{security_deposit.required_amount}, Paid: K{security_deposit.paid_amount}, Verified: {security_deposit.is_verified}")
        
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
