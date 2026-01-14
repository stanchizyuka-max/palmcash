"""
Views for multi-schedule payment functionality
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db import transaction
import json
from decimal import Decimal

from loans.models import Loan
from .models import PaymentSchedule, MultiSchedulePayment, MultiSchedulePaymentAssignment


class MultiSchedulePaymentView(LoginRequiredMixin, DetailView):
    """View to create multi-schedule payments for a loan"""
    model = Loan
    template_name = 'payments/multi_schedule_payment.html'
    context_object_name = 'loan'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loan = self.get_object()
        
        # Get unpaid schedules
        unpaid_schedules = PaymentSchedule.objects.filter(
            loan=loan,
            is_paid=False
        ).order_by('installment_number')
        
        # Calculate totals
        total_unpaid = sum(schedule.total_amount for schedule in unpaid_schedules)
        
        # Get overdue schedules
        from datetime import date
        overdue_schedules = unpaid_schedules.filter(due_date__lt=date.today())
        total_overdue = sum(schedule.total_amount for schedule in overdue_schedules)
        
        context.update({
            'unpaid_schedules': unpaid_schedules,
            'total_unpaid': total_unpaid,
            'overdue_schedules': overdue_schedules,
            'total_overdue': total_overdue,
            'can_pay': unpaid_schedules.exists(),
            'schedule_amounts_json': json.dumps({schedule.pk: float(schedule.total_amount) for schedule in unpaid_schedules}),
        })
        
        return context


class CreateMultiSchedulePaymentView(LoginRequiredMixin, CreateView):
    """Create a multi-schedule payment"""
    model = MultiSchedulePayment
    template_name = 'payments/create_multi_payment.html'
    fields = ['total_amount', 'payment_method', 'reference_number', 'notes']
    
    def dispatch(self, request, *args, **kwargs):
        # Only borrowers can create payments for their own loans
        loan = get_object_or_404(Loan, pk=self.kwargs['loan_id'])
        
        if request.user.role != 'borrower' or loan.borrower != request.user:
            messages.error(request, 'Only borrowers can submit payments for their own loans.')
            return redirect('loans:detail', pk=loan.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loan_id = self.kwargs['loan_id']
        loan = get_object_or_404(Loan, pk=loan_id)
        
        # Get selected schedules from POST or session
        selected_schedule_ids = self.request.POST.getlist('schedules') or \
                              self.request.session.get('selected_schedule_ids', [])
        
        if selected_schedule_ids:
            selected_schedule_ids = [int(id) for id in selected_schedule_ids]
            selected_schedules = PaymentSchedule.objects.filter(
                id__in=selected_schedule_ids,
                loan=loan,
                is_paid=False
            ).order_by('installment_number')
            
            total_selected = sum(schedule.total_amount for schedule in selected_schedules)
        else:
            selected_schedules = PaymentSchedule.objects.none()
            total_selected = Decimal('0')
        
        context.update({
            'loan': loan,
            'selected_schedules': selected_schedules,
            'total_selected': total_selected,
            'selected_schedule_ids': selected_schedule_ids,
        })
        
        return context
    
    def form_valid(self, form):
        loan_id = self.kwargs['loan_id']
        loan = get_object_or_404(Loan, pk=loan_id)
        
        # Get selected schedules
        selected_schedule_ids = self.request.POST.getlist('schedules')
        if not selected_schedule_ids:
            form.add_error(None, 'Please select at least one payment schedule to pay.')
            return self.form_invalid(form)
        
        selected_schedule_ids = [int(id) for id in selected_schedule_ids]
        selected_schedules = PaymentSchedule.objects.filter(
            id__in=selected_schedule_ids,
            loan=loan,
            is_paid=False
        )
        
        # Calculate required amount
        required_amount = sum(schedule.total_amount for schedule in selected_schedules)
        
        # Validate payment amount
        if form.cleaned_data['total_amount'] < required_amount:
            form.add_error('total_amount', 
                          f'Payment amount must be at least K{required_amount:,.2f} to cover selected schedules.')
            return self.form_invalid(form)
        
        # Create the multi-schedule payment
        with transaction.atomic():
            form.instance.loan = loan
            form.instance.payment_date = timezone.now()
            multi_payment = form.save()
            
            # Apply to schedules
            try:
                assignments = multi_payment.apply_to_schedules(selected_schedule_ids)
                
                # Create notifications for staff
                self._notify_staff(multi_payment, assignments)
                
                messages.success(self.request, 
                    f'Payment of K{multi_payment.total_amount:,.2f} submitted for {len(assignments)} payment schedules. '
                    f'Payment is pending approval.')
                
            except ValueError as e:
                form.add_error(None, str(e))
                return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('payments:multi_payment_detail', kwargs={'pk': self.object.pk})
    
    def _notify_staff(self, payment, assignments):
        """Notify staff about the multi-schedule payment"""
        from notifications.models import NotificationTemplate
        
        try:
            template = NotificationTemplate.objects.get(
                name='multi_schedule_payment_submitted',
                is_active=True
            )
            
            # Get staff users
            from accounts.models import User
            staff_users = User.objects.filter(
                role__in=['admin', 'loan_officer', 'manager'],
                is_active=True
            )
            
            schedule_numbers = [str(a.payment_schedule.installment_number) for a in assignments]
            schedules_text = ', '.join(schedule_numbers)
            
            for staff_user in staff_users:
                template.send_notification(
                    recipient=staff_user,
                    context={
                        'payment': payment,
                        'loan': payment.loan,
                        'borrower': payment.loan.borrower,
                        'schedules_count': len(assignments),
                        'schedules_text': schedules_text,
                        'amount': payment.total_amount,
                    }
                )
        except NotificationTemplate.DoesNotExist:
            pass


class MultiSchedulePaymentDetailView(LoginRequiredMixin, DetailView):
    """View details of a multi-schedule payment"""
    model = MultiSchedulePayment
    template_name = 'payments/multi_payment_detail.html'
    context_object_name = 'payment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment = self.get_object()
        
        # Get schedule assignments
        assignments = payment.schedule_assignments.select_related('payment_schedule').order_by('payment_schedule__installment_number')
        
        context.update({
            'assignments': assignments,
            'can_approve': self.request.user.role in ['admin', 'loan_officer', 'manager'],
        })
        
        return context


class ApproveMultiSchedulePaymentView(LoginRequiredMixin, View):
    """Approve a multi-schedule payment"""
    
    def post(self, request, pk):
        if request.user.role not in ['admin', 'loan_officer', 'manager']:
            messages.error(request, 'You do not have permission to approve payments.')
            return redirect('payments:multi_payment_detail', pk=pk)
        
        payment = get_object_or_404(MultiSchedulePayment, pk=pk)
        
        if payment.status != 'pending':
            messages.error(request, 'This payment has already been processed.')
            return redirect('payments:multi_payment_detail', pk=pk)
        
        try:
            with transaction.atomic():
                payment.approve_payment(processed_by=request.user)
                
                # Create notifications
                self._notify_approval(payment)
                
                messages.success(request, 
                    f'Payment of K{payment.total_amount:,.2f} approved. '
                    f'{payment.schedules_covered} payment schedules marked as paid.')
                
        except Exception as e:
            messages.error(request, f'Error approving payment: {str(e)}')
        
        return redirect('payments:multi_payment_detail', pk=pk)
    
    def _notify_approval(self, payment):
        """Notify borrower about payment approval"""
        try:
            template = NotificationTemplate.objects.get(
                name='multi_schedule_payment_approved',
                is_active=True
            )
            
            template.send_notification(
                recipient=payment.loan.borrower,
                context={
                    'payment': payment,
                    'loan': payment.loan,
                    'schedules_count': payment.schedules_covered,
                    'amount': payment.total_amount,
                    'processed_by': payment.processed_by,
                }
            )
        except NotificationTemplate.DoesNotExist:
            pass


class MultiSchedulePaymentListView(LoginRequiredMixin, ListView):
    """List multi-schedule payments"""
    model = MultiSchedulePayment
    template_name = 'payments/multi_payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        if self.request.user.role == 'borrower':
            return MultiSchedulePayment.objects.filter(
                loan__borrower=self.request.user
            ).order_by('-payment_date')
        
        return MultiSchedulePayment.objects.all().order_by('-payment_date')
