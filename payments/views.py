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


class BulkCollectionView(LoginRequiredMixin, View):
    """Step 1: Show groups with due/overdue payments for the officer."""
    template_name = 'payments/bulk_collection.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ['loan_officer', 'admin']:
            messages.error(request, 'Only loan officers can record bulk collections.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        from loans.models import Loan
        from clients.models import BorrowerGroup
        from django.db.models import Q
        from datetime import date
        from decimal import Decimal

        officer = request.user
        today = date.today()

        groups = BorrowerGroup.objects.filter(
            assigned_officer=officer, is_active=True
        ).prefetch_related('members__borrower')

        group_rows = []
        for group in groups:
            borrowers = [m.borrower for m in group.members.filter(is_active=True)]
            loans = Loan.objects.filter(
                borrower__in=borrowers, status='active'
            ).prefetch_related('payment_schedule')

            due_count = 0
            total_expected = Decimal('0')
            for loan in loans:
                sched = PaymentSchedule.objects.filter(
                    loan=loan, is_paid=False
                ).order_by('due_date').first()
                if sched and (sched.due_date <= today or sched.amount_paid > 0):
                    due_count += 1
                    total_expected += sched.total_amount - sched.amount_paid

            if due_count > 0:
                group_rows.append({
                    'group': group,
                    'due_count': due_count,
                    'total_expected': total_expected,
                })

        return render(request, self.template_name, {'group_rows': group_rows, 'today': today})


class BulkCollectionGroupView(LoginRequiredMixin, View):
    """Step 2: Collect payments for all clients in a specific group."""
    template_name = 'payments/bulk_collection_group.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ['loan_officer', 'admin']:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def _get_rows(self, group):
        from loans.models import Loan
        from datetime import date
        today = date.today()
        borrowers = [m.borrower for m in group.members.filter(is_active=True)]
        loans = Loan.objects.filter(
            borrower__in=borrowers, status='active'
        ).select_related('borrower')
        rows = []
        for loan in loans:
            sched = PaymentSchedule.objects.filter(
                loan=loan, is_paid=False
            ).order_by('due_date').first()
            if not sched:
                continue
            outstanding = sched.total_amount - sched.amount_paid
            if outstanding <= 0:
                continue
            rows.append({
                'loan': loan,
                'schedule': sched,
                'expected': outstanding,
                'loan_balance': loan.balance_remaining or 0,
                'is_overdue': sched.due_date < today,
            })
        return rows

    def get(self, request, group_id):
        from clients.models import BorrowerGroup
        group = get_object_or_404(BorrowerGroup, pk=group_id, assigned_officer=request.user)
        rows = self._get_rows(group)
        return render(request, self.template_name, {'group': group, 'rows': rows})

    def post(self, request, group_id):
        from clients.models import BorrowerGroup
        from loans.models import Loan
        from decimal import Decimal, InvalidOperation
        from datetime import date, datetime as dt

        group = get_object_or_404(BorrowerGroup, pk=group_id, assigned_officer=request.user)
        today = date.today()
        recorded = 0
        skipped = 0

        for key, value in request.POST.items():
            if not key.startswith('amount_'):
                continue
            loan_id = key.split('_', 1)[1]
            amount_str = value.strip()
            if not amount_str:
                skipped += 1
                continue
            try:
                amount = Decimal(amount_str)
                if amount <= 0:
                    skipped += 1
                    continue
            except InvalidOperation:
                skipped += 1
                continue

            method = request.POST.get(f'method_{loan_id}', 'cash')
            method_map = {'mtn': 'mobile_money', 'airtel': 'mobile_money'}
            payment_method = method_map.get(method, method)

            try:
                loan = Loan.objects.get(pk=loan_id, status='active')
            except Loan.DoesNotExist:
                continue

            payment = Payment.objects.create(
                loan=loan,
                amount=amount,
                payment_method=payment_method,
                payment_date=dt.combine(today, dt.min.time()).replace(tzinfo=timezone.get_current_timezone()),
                processed_by=request.user,
                status='pending',
                notes=f'[BULK COLLECTION — {group.name}]',
            )

            oldest_unpaid = PaymentSchedule.objects.filter(loan=loan, is_paid=False).order_by('due_date').first()
            if oldest_unpaid:
                payment.payment_schedule = oldest_unpaid
                payment.save(update_fields=['payment_schedule'])

            expected = oldest_unpaid.total_amount - oldest_unpaid.amount_paid if oldest_unpaid else loan.payment_amount
            collection, _ = PaymentCollection.objects.get_or_create(
                loan=loan,
                collection_date=today,
                defaults={'expected_amount': expected, 'collected_amount': 0, 'status': 'scheduled'}
            )
            collection.collected_amount = min(amount, collection.expected_amount)
            collection.collected_by = request.user
            collection.actual_collection_date = timezone.now()
            collection.status = 'completed'
            collection.is_partial = collection.collected_amount < collection.expected_amount
            collection.save()

            recorded += 1

        messages.success(request, f'{recorded} payment(s) recorded for {group.name} — awaiting manager confirmation. {skipped} skipped.')
        return redirect('payments:bulk_collection')


class DefaultCollectionView(LoginRequiredMixin, View):
    """Step 1: Show groups with defaulted loans."""
    template_name = 'payments/default_collection.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ['loan_officer', 'admin', 'manager']:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        from loans.models import Loan
        from clients.models import BorrowerGroup
        from decimal import Decimal

        officer = request.user
        groups = BorrowerGroup.objects.filter(assigned_officer=officer, is_active=True)

        group_rows = []
        for group in groups:
            borrowers = [m.borrower for m in group.members.filter(is_active=True)]
            defaulted = Loan.objects.filter(
                borrower__in=borrowers,
                status='active',
                balance_remaining__gt=0,
            ).filter(
                payment_schedule__is_paid=False,
                payment_schedule__due_date__lt=__import__('datetime').date.today(),
            ).distinct()

            if defaulted.exists():
                total_balance = sum(l.balance_remaining or 0 for l in defaulted)
                group_rows.append({
                    'group': group,
                    'count': defaulted.count(),
                    'total_balance': total_balance,
                })

        return render(request, self.template_name, {'group_rows': group_rows})


class DefaultCollectionGroupView(LoginRequiredMixin, View):
    """Step 2: Collect payments for defaulted loans in a group."""
    template_name = 'payments/default_collection_group.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ['loan_officer', 'admin', 'manager']:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def _get_defaulted_loans(self, group):
        from loans.models import Loan
        import datetime
        today = datetime.date.today()
        borrowers = [m.borrower for m in group.members.filter(is_active=True)]
        return Loan.objects.filter(
            borrower__in=borrowers,
            status='active',
            balance_remaining__gt=0,
        ).filter(
            payment_schedule__is_paid=False,
            payment_schedule__due_date__lt=today,
        ).distinct().select_related('borrower')

    def get(self, request, group_id):
        from clients.models import BorrowerGroup
        group = get_object_or_404(BorrowerGroup, pk=group_id, assigned_officer=request.user)
        loans = self._get_defaulted_loans(group)
        return render(request, self.template_name, {'group': group, 'loans': loans})

    def post(self, request, group_id):
        from clients.models import BorrowerGroup
        from loans.models import Loan
        from decimal import Decimal, InvalidOperation
        from .models import DefaultCollection
        import datetime

        group = get_object_or_404(BorrowerGroup, pk=group_id, assigned_officer=request.user)
        today = datetime.date.today()
        recorded = 0
        skipped = 0

        for key, value in request.POST.items():
            if not key.startswith('amount_'):
                continue
            loan_id = key.split('_', 1)[1]
            amount_str = value.strip()
            if not amount_str:
                skipped += 1
                continue
            try:
                amount = Decimal(amount_str)
                if amount <= 0:
                    skipped += 1
                    continue
            except InvalidOperation:
                skipped += 1
                continue

            method = request.POST.get(f'method_{loan_id}', 'cash')

            try:
                loan = Loan.objects.get(pk=loan_id, status='active')
            except Loan.DoesNotExist:
                continue

            balance_before = loan.balance_remaining or Decimal('0')
            amount_applied = min(amount, balance_before)
            balance_after = balance_before - amount_applied

            # Update loan
            loan.amount_paid += amount_applied
            loan.balance_remaining = balance_after
            if balance_after <= 0:
                loan.status = 'completed'
            loan.save(update_fields=['amount_paid', 'balance_remaining', 'status', 'updated_at'])

            # Record default collection
            DefaultCollection.objects.create(
                loan=loan,
                amount_paid=amount_applied,
                balance_before=balance_before,
                balance_after=balance_after,
                payment_method=method,
                notes=f'[DEFAULT COLLECTION — {group.name}]',
                recorded_by=request.user,
                collection_date=today,
            )

            # Also distribute to payment schedule
            from payments.services import distribute_payment
            distribute_payment(loan, amount_applied, today)

            recorded += 1

        messages.success(request, f'{recorded} default payment(s) recorded for {group.name}. {skipped} skipped.')
        return redirect('payments:default_collection')


class DefaultCollectionHistoryView(LoginRequiredMixin, View):
    """View history of all default collections recorded by this officer."""
    template_name = 'payments/default_collection_history.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        from .models import DefaultCollection
        from django.db.models import Q, Sum

        if request.user.role == 'loan_officer':
            qs = DefaultCollection.objects.filter(
                recorded_by=request.user
            ).select_related('loan', 'loan__borrower').order_by('-collection_date', '-created_at')
        elif request.user.role == 'manager':
            try:
                branch = request.user.managed_branch
                qs = DefaultCollection.objects.filter(
                    Q(loan__loan_officer__officer_assignment__branch__iexact=branch.name) |
                    Q(loan__borrower__group_memberships__group__branch__iexact=branch.name)
                ).select_related('loan', 'loan__borrower', 'recorded_by').distinct().order_by('-collection_date')
            except Exception:
                qs = DefaultCollection.objects.none()
        else:
            qs = DefaultCollection.objects.all().select_related(
                'loan', 'loan__borrower', 'recorded_by'
            ).order_by('-collection_date')

        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        search = request.GET.get('search', '').strip()

        if date_from:
            qs = qs.filter(collection_date__gte=date_from)
        if date_to:
            qs = qs.filter(collection_date__lte=date_to)
        if search:
            qs = qs.filter(
                Q(loan__borrower__first_name__icontains=search) |
                Q(loan__borrower__last_name__icontains=search) |
                Q(loan__application_number__icontains=search)
            ).distinct()

        total = qs.aggregate(total=Sum('amount_paid'))['total'] or 0
        return render(request, self.template_name, {
            'collections': qs,
            'total': total,
            'filters': {'date_from': date_from, 'date_to': date_to, 'search': search},
        })


class CollectionHistoryView(LoginRequiredMixin, View):
    """Collection history with date range, group, client search, and status filters."""
    template_name = 'payments/collection_history.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        from django.db.models import Q, Sum
        from datetime import date, timedelta
        from loans.models import Loan
        from clients.models import BorrowerGroup

        officer = request.user

        # Base queryset scoped to officer
        if officer.role == 'loan_officer':
            qs = PaymentCollection.objects.filter(
                Q(loan__loan_officer=officer) |
                Q(loan__borrower__group_memberships__group__assigned_officer=officer)
            ).distinct()
        elif officer.role == 'manager':
            try:
                branch = officer.managed_branch
                qs = PaymentCollection.objects.filter(
                    Q(loan__loan_officer__officer_assignment__branch__iexact=branch.name) |
                    Q(loan__borrower__group_memberships__group__branch__iexact=branch.name)
                ).distinct()
            except Exception:
                qs = PaymentCollection.objects.none()
        else:
            qs = PaymentCollection.objects.all()

        qs = qs.select_related('loan__borrower', 'collected_by').order_by('-collection_date')

        # Filters
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        group_id = request.GET.get('group')
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status')

        # Default: last 7 days if no date filter
        if not date_from and not date_to:
            date_from = (date.today() - timedelta(days=6)).isoformat()
            date_to = date.today().isoformat()

        if date_from:
            qs = qs.filter(collection_date__gte=date_from)
        if date_to:
            qs = qs.filter(collection_date__lte=date_to)
        if search:
            qs = qs.filter(
                Q(loan__borrower__first_name__icontains=search) |
                Q(loan__borrower__last_name__icontains=search) |
                Q(loan__application_number__icontains=search)
            )
        if group_id:
            qs = qs.filter(
                loan__borrower__group_memberships__group_id=group_id,
                loan__borrower__group_memberships__is_active=True
            ).distinct()
        if status == 'paid':
            qs = qs.filter(status='completed', is_partial=False)
        elif status == 'partial':
            qs = qs.filter(is_partial=True)
        elif status == 'pending':
            qs = qs.filter(collected_amount=0)

        totals = qs.aggregate(
            total_expected=Sum('expected_amount'),
            total_collected=Sum('collected_amount'),
        )

        # Groups for filter dropdown
        if officer.role == 'loan_officer':
            groups = BorrowerGroup.objects.filter(assigned_officer=officer, is_active=True)
        elif officer.role == 'manager':
            try:
                groups = BorrowerGroup.objects.filter(branch__iexact=officer.managed_branch.name, is_active=True)
            except Exception:
                groups = BorrowerGroup.objects.none()
        else:
            groups = BorrowerGroup.objects.filter(is_active=True)

        return render(request, self.template_name, {
            'collections': qs[:200],  # cap at 200 rows
            'total_expected': totals['total_expected'] or 0,
            'total_collected': totals['total_collected'] or 0,
            'groups': groups,
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
                'group': group_id,
                'search': search,
                'status': status,
            },
        })


class CollectionsHistoryView(LoginRequiredMixin, View):
    """Collections history with date range, group, status, and client search filters."""
    template_name = 'payments/collections_history.html'

    def get(self, request):
        from django.db.models import Q, Sum
        from datetime import date, timedelta
        from clients.models import BorrowerGroup

        user = request.user

        if user.role == 'loan_officer':
            qs = PaymentCollection.objects.filter(
                Q(loan__loan_officer=user) |
                Q(loan__borrower__group_memberships__group__assigned_officer=user)
            ).distinct()
        elif user.role == 'manager':
            try:
                branch = user.managed_branch
                qs = PaymentCollection.objects.filter(
                    Q(loan__loan_officer__officer_assignment__branch__iexact=branch.name) |
                    Q(loan__borrower__group_memberships__group__branch__iexact=branch.name)
                ).distinct()
            except Exception:
                qs = PaymentCollection.objects.none()
        else:
            qs = PaymentCollection.objects.all()

        qs = qs.select_related('loan__borrower', 'collected_by').order_by('-collection_date')

        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        group_id = request.GET.get('group', '')
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', '')

        if date_from:
            qs = qs.filter(collection_date__gte=date_from)
        if date_to:
            qs = qs.filter(collection_date__lte=date_to)
        if search:
            qs = qs.filter(
                Q(loan__borrower__first_name__icontains=search) |
                Q(loan__borrower__last_name__icontains=search) |
                Q(loan__application_number__icontains=search)
            ).distinct()
        if group_id:
            qs = qs.filter(
                loan__borrower__group_memberships__group_id=group_id,
                loan__borrower__group_memberships__is_active=True
            ).distinct()
        if status == 'paid':
            qs = qs.filter(status='completed', is_partial=False)
        elif status == 'partial':
            qs = qs.filter(is_partial=True)
        elif status == 'pending':
            qs = qs.filter(collected_amount=0)

        totals = qs.aggregate(
            total_expected=Sum('expected_amount'),
            total_collected=Sum('collected_amount'),
        )

        if user.role == 'loan_officer':
            groups = BorrowerGroup.objects.filter(assigned_officer=user, is_active=True)
        elif user.role == 'manager':
            try:
                groups = BorrowerGroup.objects.filter(branch__iexact=user.managed_branch.name, is_active=True)
            except Exception:
                groups = BorrowerGroup.objects.none()
        else:
            groups = BorrowerGroup.objects.filter(is_active=True)

        return render(request, self.template_name, {
            'collections': qs[:300],
            'total_expected': totals['total_expected'] or 0,
            'total_collected': totals['total_collected'] or 0,
            'groups': groups,
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
                'group': group_id,
                'search': search,
                'status': status,
            },
        })


class SecuritiesHistoryView(LoginRequiredMixin, View):
    """Securities transaction history with filters."""
    template_name = 'payments/securities_history.html'

    def get(self, request):
        from django.db.models import Q, Sum
        from loans.models import SecurityTransaction

        user = request.user

        if user.role == 'loan_officer':
            qs = SecurityTransaction.objects.filter(
                Q(loan__loan_officer=user) |
                Q(loan__borrower__group_memberships__group__assigned_officer=user)
            ).distinct()
        elif user.role == 'manager':
            try:
                branch = user.managed_branch
                qs = SecurityTransaction.objects.filter(
                    Q(loan__loan_officer__officer_assignment__branch__iexact=branch.name) |
                    Q(loan__borrower__group_memberships__group__branch__iexact=branch.name)
                ).distinct()
            except Exception:
                qs = SecurityTransaction.objects.none()
        else:
            qs = SecurityTransaction.objects.all()

        qs = qs.select_related('loan__borrower', 'initiated_by', 'approved_by').order_by('-created_at')

        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        txn_type = request.GET.get('transaction_type', '')
        status = request.GET.get('status', '')
        search = request.GET.get('search', '').strip()

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if txn_type:
            qs = qs.filter(transaction_type=txn_type)
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(loan__borrower__first_name__icontains=search) |
                Q(loan__borrower__last_name__icontains=search) |
                Q(loan__application_number__icontains=search)
            ).distinct()

        total_amount = qs.aggregate(total=Sum('amount'))['total'] or 0

        return render(request, self.template_name, {
            'transactions': qs[:300],
            'total_amount': total_amount,
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
                'transaction_type': txn_type,
                'status': status,
                'search': search,
            },
        })


class HistoryHubView(LoginRequiredMixin, View):
    """Hierarchical history: Officers → Groups → Clients → Records."""
    template_name = 'payments/history.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        from django.db.models import Q, Sum
        from loans.models import SecurityTransaction, SecurityDeposit
        from .models import DefaultCollection
        from clients.models import BorrowerGroup
        from accounts.models import User as _User

        user = request.user
        tab = request.GET.get('tab', 'collections')
        officer_id = request.GET.get('officer')
        group_id = request.GET.get('group')
        client_id = request.GET.get('client')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        search = request.GET.get('search', '').strip()

        # ── Determine scope based on role ──────────────────────────────────
        if user.role == 'manager':
            try:
                branch = user.managed_branch
                branch_officers = _User.objects.filter(
                    role='loan_officer',
                    officer_assignment__branch__iexact=branch.name,
                    is_active=True
                ).order_by('first_name', 'last_name')
            except Exception:
                branch_officers = _User.objects.none()
        elif user.role == 'loan_officer':
            branch_officers = _User.objects.filter(pk=user.pk)
            if not officer_id:
                officer_id = str(user.pk)
        else:
            branch_officers = _User.objects.filter(role='loan_officer', is_active=True).order_by('first_name')

        # ── Resolve selected objects ───────────────────────────────────────
        selected_officer = _User.objects.filter(pk=officer_id).first() if officer_id else None
        selected_group = BorrowerGroup.objects.filter(pk=group_id).first() if group_id else None
        selected_client = _User.objects.filter(pk=client_id, role='borrower').first() if client_id else None

        # ── Smart search: resolve what was searched ────────────────────────
        search_results = None
        if search:
            # Search officers
            matched_officers = branch_officers.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
            # Search groups
            matched_groups = BorrowerGroup.objects.filter(
                Q(name__icontains=search),
                assigned_officer__in=branch_officers
            )
            # Search clients
            matched_clients = _User.objects.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search),
                role='borrower',
                group_memberships__group__assigned_officer__in=branch_officers,
                group_memberships__is_active=True,
            ).distinct()
            search_results = {
                'officers': matched_officers,
                'groups': matched_groups,
                'clients': matched_clients,
            }

        # ── Build level data ───────────────────────────────────────────────
        level = 'officers'
        groups_for_officer = None
        clients_for_group = None
        records = None
        totals = {}
        extra = {}

        if selected_client:
            level = 'records'
            # Get records for this client
            def get_records(qs_model):
                return qs_model.objects.filter(loan__borrower=selected_client).distinct()

            if tab == 'collections':
                qs = get_records(PaymentCollection).select_related('loan').filter(
                    collected_amount__gt=0
                ).order_by('-collection_date')
                if date_from: qs = qs.filter(collection_date__gte=date_from)
                if date_to:   qs = qs.filter(collection_date__lte=date_to)
                status = request.GET.get('status', '')
                if status == 'paid':    qs = qs.filter(status='completed', is_partial=False)
                elif status == 'partial': qs = qs.filter(is_partial=True)
                t = qs.aggregate(exp=Sum('expected_amount'), col=Sum('collected_amount'))
                totals = {'expected': t['exp'] or 0, 'collected': t['col'] or 0}
                records = qs

            elif tab == 'securities':
                sec_type = request.GET.get('sec_type', 'transactions')
                if sec_type == 'deposits':
                    qs = get_records(SecurityDeposit).select_related('loan', 'verified_by').order_by('-payment_date')
                    if date_from: qs = qs.filter(payment_date__date__gte=date_from)
                    if date_to:   qs = qs.filter(payment_date__date__lte=date_to)
                    totals = {'amount': qs.aggregate(a=Sum('paid_amount'))['a'] or 0}
                    extra = {'sec_type': 'deposits'}
                else:
                    qs = get_records(SecurityTransaction).select_related('loan', 'approved_by').order_by('-created_at')
                    if date_from: qs = qs.filter(created_at__date__gte=date_from)
                    if date_to:   qs = qs.filter(created_at__date__lte=date_to)
                    txn_type = request.GET.get('transaction_type', '')
                    if txn_type: qs = qs.filter(transaction_type=txn_type)
                    totals = {'amount': qs.aggregate(a=Sum('amount'))['a'] or 0}
                    extra = {'sec_type': 'transactions'}
                records = qs

            elif tab == 'defaults':
                qs = get_records(DefaultCollection).select_related('loan', 'recorded_by').order_by('-collection_date')
                if date_from: qs = qs.filter(collection_date__gte=date_from)
                if date_to:   qs = qs.filter(collection_date__lte=date_to)
                totals = {'amount': qs.aggregate(a=Sum('amount_paid'))['a'] or 0}
                records = qs

        elif selected_group:
            level = 'clients'
            clients_for_group = _User.objects.filter(
                group_memberships__group=selected_group,
                group_memberships__is_active=True,
                role='borrower',
            ).distinct().order_by('first_name', 'last_name')

            # Group-level performance summary
            group_client_ids = clients_for_group.values_list('pk', flat=True)
            def _date_filter_col(qs):
                if date_from: qs = qs.filter(collection_date__gte=date_from)
                if date_to:   qs = qs.filter(collection_date__lte=date_to)
                return qs
            def _date_filter_sec(qs):
                if date_from: qs = qs.filter(created_at__date__gte=date_from)
                if date_to:   qs = qs.filter(created_at__date__lte=date_to)
                return qs
            def _date_filter_def(qs):
                if date_from: qs = qs.filter(collection_date__gte=date_from)
                if date_to:   qs = qs.filter(collection_date__lte=date_to)
                return qs

            col_qs = _date_filter_col(PaymentCollection.objects.filter(loan__borrower__in=group_client_ids, collected_amount__gt=0))
            col_agg = col_qs.aggregate(exp=Sum('expected_amount'), col=Sum('collected_amount'))
            sec_qs = _date_filter_sec(SecurityTransaction.objects.filter(loan__borrower__in=group_client_ids, status='approved'))
            sec_agg = sec_qs.aggregate(t=Sum('amount'))
            def_qs = _date_filter_def(DefaultCollection.objects.filter(loan__borrower__in=group_client_ids))
            def_agg = def_qs.aggregate(t=Sum('amount_paid'))
            totals = {
                'collections_expected': col_agg['exp'] or 0,
                'collections_collected': col_agg['col'] or 0,
                'securities_amount': sec_agg['t'] or 0,
                'defaults_collected': def_agg['t'] or 0,
            }

        elif selected_officer:
            level = 'groups'
            raw_groups = BorrowerGroup.objects.filter(
                assigned_officer=selected_officer, is_active=True
            ).order_by('name')
            groups_for_officer = []
            all_client_ids = _User.objects.filter(
                group_memberships__group__assigned_officer=selected_officer,
                group_memberships__is_active=True,
                role='borrower',
            ).values_list('pk', flat=True).distinct()

            for g in raw_groups:
                client_ids = _User.objects.filter(
                    group_memberships__group=g,
                    group_memberships__is_active=True,
                    role='borrower',
                ).values_list('pk', flat=True).distinct()
                col = PaymentCollection.objects.filter(
                    loan__borrower__in=client_ids, collected_amount__gt=0,
                )
                if date_from: col = col.filter(collection_date__gte=date_from)
                if date_to:   col = col.filter(collection_date__lte=date_to)
                col_agg = col.aggregate(exp=Sum('expected_amount'), col=Sum('collected_amount'))
                groups_for_officer.append({
                    'group': g,
                    'client_count': len(client_ids),
                    'total_collected': col_agg['col'] or 0,
                    'total_expected': col_agg['exp'] or 0,
                })

            # Officer-level totals
            def _df_col(qs):
                if date_from: qs = qs.filter(collection_date__gte=date_from)
                if date_to:   qs = qs.filter(collection_date__lte=date_to)
                return qs
            def _df_sec(qs):
                if date_from: qs = qs.filter(created_at__date__gte=date_from)
                if date_to:   qs = qs.filter(created_at__date__lte=date_to)
                return qs
            def _df_def(qs):
                if date_from: qs = qs.filter(collection_date__gte=date_from)
                if date_to:   qs = qs.filter(collection_date__lte=date_to)
                return qs

            o_col = _df_col(PaymentCollection.objects.filter(loan__borrower__in=all_client_ids, collected_amount__gt=0))
            o_col_agg = o_col.aggregate(exp=Sum('expected_amount'), col=Sum('collected_amount'))
            o_sec = _df_sec(SecurityTransaction.objects.filter(loan__borrower__in=all_client_ids, status='approved'))
            o_sec_agg = o_sec.aggregate(t=Sum('amount'))
            o_def = _df_def(DefaultCollection.objects.filter(loan__borrower__in=all_client_ids))
            o_def_agg = o_def.aggregate(t=Sum('amount_paid'))
            totals = {
                'collections_expected': o_col_agg['exp'] or 0,
                'collections_collected': o_col_agg['col'] or 0,
                'securities_amount': o_sec_agg['t'] or 0,
                'defaults_collected': o_def_agg['t'] or 0,
            }

        # Branch-level totals (for officers level)
        branch_totals = None
        if level == 'officers':
            all_branch_client_ids = _User.objects.filter(
                group_memberships__group__assigned_officer__in=branch_officers,
                group_memberships__is_active=True,
                role='borrower',
            ).values_list('pk', flat=True).distinct()
            b_col = PaymentCollection.objects.filter(loan__borrower__in=all_branch_client_ids, collected_amount__gt=0)
            b_sec = SecurityTransaction.objects.filter(loan__borrower__in=all_branch_client_ids, status='approved')
            b_def = DefaultCollection.objects.filter(loan__borrower__in=all_branch_client_ids)
            if date_from:
                b_col = b_col.filter(collection_date__gte=date_from)
                b_sec = b_sec.filter(created_at__date__gte=date_from)
                b_def = b_def.filter(collection_date__gte=date_from)
            if date_to:
                b_col = b_col.filter(collection_date__lte=date_to)
                b_sec = b_sec.filter(created_at__date__lte=date_to)
                b_def = b_def.filter(collection_date__lte=date_to)
            b_col_agg = b_col.aggregate(exp=Sum('expected_amount'), col=Sum('collected_amount'))
            branch_totals = {
                'collections_expected': b_col_agg['exp'] or 0,
                'collections_collected': b_col_agg['col'] or 0,
                'securities_amount': b_sec.aggregate(t=Sum('amount'))['t'] or 0,
                'defaults_collected': b_def.aggregate(t=Sum('amount_paid'))['t'] or 0,
            }

        return render(request, self.template_name, {
            'tab': tab,
            'level': level,
            'branch_officers': branch_officers,
            'selected_officer': selected_officer,
            'selected_group': selected_group,
            'selected_client': selected_client,
            'groups_for_officer': groups_for_officer,
            'clients_for_group': clients_for_group,
            'records': records,
            'totals': totals,
            'branch_totals': branch_totals,
            'sec_type': extra.get('sec_type', 'transactions'),
            'search_results': search_results,
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
                'search': search,
                'status': request.GET.get('status', ''),
                'transaction_type': request.GET.get('transaction_type', ''),
                'sec_type': request.GET.get('sec_type', 'transactions'),
                'officer': officer_id or '',
                'group': group_id or '',
                'client': client_id or '',
            },
        })
