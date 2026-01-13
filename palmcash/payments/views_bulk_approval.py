"""
Bulk collection approval views for payment processing
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta

from .models import PaymentCollection, Payment
from loans.models import Loan
from accounts.models import User


class BulkCollectionApprovalView(LoginRequiredMixin, View):
    """Bulk approval for collections on a specific date"""
    
    def get(self, request):
        """Show bulk approval interface"""
        user = request.user
        
        if user.role not in ['loan_officer', 'manager', 'admin'] and not user.is_superuser:
            messages.error(request, 'You do not have permission to approve collections.')
            return redirect('dashboard:dashboard')
        
        # Get filter parameters
        target_date = request.GET.get('date')
        if not target_date:
            target_date = date.today().strftime('%Y-%m-%d')
        
        target_date = timezone.datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Base query for collections
        collections_query = PaymentCollection.objects.filter(
            collection_date=target_date,
            status='scheduled'  # Only pending collections
        )
        
        # Filter by user role
        if user.role == 'loan_officer':
            collections_query = collections_query.filter(loan__loan_officer=user)
        elif user.role == 'manager':
            if hasattr(user, 'managed_branch') and user.managed_branch:
                collections_query = collections_query.filter(
                    loan__loan_officer__officer_assignment__branch=user.managed_branch.name
                )
        
        # Get collections with loan details
        collections = collections_query.select_related(
            'loan', 'loan__borrower', 'loan__group_memberships__group'
        ).order_by('loan__application_number')
        
        # Group by loan
        loans_with_collections = {}
        
        for collection in collections:
            loan_id = collection.loan.id
            if loan_id not in loans_with_collections:
                loans_with_collections[loan_id] = {
                    'loan': collection.loan,
                    'collections': [],
                    'total_expected': Decimal('0.00'),
                    'total_collected': Decimal('0.00'),
                    'can_approve': False,
                    'group_name': None
                }
            
            loans_with_collections[loan_id]['collections'].append(collection)
            loans_with_collections[loan_id]['total_expected'] += collection.expected_amount
            loans_with_collections[loan_id]['total_collected'] += collection.collected_amount
            
            # Check if all collections for this loan are paid
            if collection.collected_amount >= collection.expected_amount:
                loans_with_collections[loan_id]['can_approve'] = True
            
            # Get group name
            group_membership = collection.loan.group_memberships.filter(is_active=True).first()
            if group_membership:
                loans_with_collections[loan_id]['group_name'] = group_membership.group.name
        
        # Convert to list and sort
        grouped_loans = list(loans_with_collections.values())
        grouped_loans.sort(key=lambda x: x['loan'].application_number)
        
        # Calculate totals
        total_expected = sum(loan['total_expected'] for loan in grouped_loans)
        total_collected = sum(loan['total_collected'] for loan in grouped_loans)
        total_approvable = sum(loan['total_expected'] for loan in grouped_loans if loan['can_approve'])
        
        context = {
            'target_date': target_date,
            'grouped_loans': grouped_loans,
            'total_expected': total_expected,
            'total_collected': total_collected,
            'total_approvable': total_approvable,
            'total_loans': len(grouped_loans),
            'title': f'Bulk Collection Approval - {target_date.strftime("%B %d, %Y")}'
        }
        
        return render(request, 'payments/bulk_approval.html', context)
    
    def post(self, request):
        """Process bulk approval"""
        user = request.user
        
        if user.role not in ['loan_officer', 'manager', 'admin'] and not user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        try:
            with transaction.atomic():
                target_date = request.POST.get('date')
                selected_loans = request.POST.getlist('selected_loans')
                
                if not target_date or not selected_loans:
                    return JsonResponse({'error': 'Invalid request'}, status=400)
                
                target_date = timezone.datetime.strptime(target_date, '%Y-%m-%d').date()
                
                approved_count = 0
                skipped_count = 0
                error_count = 0
                
                for loan_id in selected_loans:
                    try:
                        loan = get_object_or_404(Loan, pk=loan_id)
                        
                        # Check permissions
                        if user.role == 'loan_officer' and loan.loan_officer != user:
                            skipped_count += 1
                            continue
                        elif user.role == 'manager':
                            if hasattr(user, 'managed_branch') and user.managed_branch:
                                if not loan.loan_officer or not hasattr(loan.loan_officer, 'officer_assignment'):
                                    skipped_count += 1
                                    continue
                                if loan.loan_officer.officer_assignment.branch != user.managed_branch.name:
                                    skipped_count += 1
                                    continue
                            else:
                                skipped_count += 1
                                continue
                        
                        # Get all collections for this loan on the target date
                        collections = PaymentCollection.objects.filter(
                            loan=loan,
                            collection_date=target_date,
                            status='scheduled'
                        )
                        
                        loan_approved = False
                        for collection in collections:
                            # Check if collection is fully paid
                            if collection.collected_amount >= collection.expected_amount:
                                # Approve the collection
                                collection.status = 'completed'
                                collection.collected_date = timezone.now()
                                collection.approved_by = user
                                collection.approved_date = timezone.now()
                                collection.save()
                                
                                # Update payment schedule
                                payment_schedules = loan.payment_schedule.filter(
                                    due_date=target_date
                                )
                                for schedule in payment_schedules:
                                    if schedule.status == 'pending':
                                        schedule.status = 'paid'
                                        schedule.paid_date = timezone.now()
                                        schedule.paid_amount = collection.collected_amount
                                        schedule.save()
                                
                                loan_approved = True
                                approved_count += 1
                            else:
                                # Partial payment - skip for now
                                continue
                        
                        # Update loan status if all collections for this loan are approved
                        if loan_approved:
                            # Check if all payment schedules are paid
                            all_schedules = loan.payment_schedule.all()
                            if all_schedules.exists() and all_schedules.filter(status='paid').count() == all_schedules.count():
                                loan.status = 'completed'
                                loan.completion_date = timezone.now()
                                loan.save()
                                
                                # Create completion notification
                                from common.email_utils import send_loan_completion_email
                                try:
                                    send_loan_completion_email(loan)
                                except:
                                    pass  # Email error is not critical
                                
                    except Exception as e:
                        error_count += 1
                        continue
                
                if approved_count > 0:
                    messages.success(request, f'Successfully approved {approved_count} collection(s) for {target_date.strftime("%B %d, %Y")}')
                if skipped_count > 0:
                    messages.warning(request, f'Skipped {skipped_count} collection(s) due to permissions or partial payments')
                if error_count > 0:
                    messages.error(request, f'Failed to approve {error_count} collection(s)')
                
                return JsonResponse({
                    'success': True,
                    'approved_count': approved_count,
                    'skipped_count': skipped_count,
                    'error_count': error_count,
                    'message': f'Approved {approved_count} collections for {target_date.strftime("%B %d, %Y")}'
                })
                
        except Exception as e:
            return JsonResponse({'error': f'Error processing approval: {str(e)}'}, status=500)


class QuickApproveTodayView(LoginRequiredMixin, View):
    """Quick approval for today's collections"""
    
    def post(self, request):
        """Quick approve all today's payable collections"""
        user = request.user
        
        if user.role not in ['loan_officer', 'manager', 'admin'] and not user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        try:
            with transaction.atomic():
                today = date.today()
                
                # Get today's collections that can be approved (fully paid)
                collections_query = PaymentCollection.objects.filter(
                    collection_date=today,
                    status='scheduled',
                    collected_amount__gte=models.F('expected_amount')
                )
                
                # Filter by user role
                if user.role == 'loan_officer':
                    collections_query = collections_query.filter(loan__loan_officer=user)
                elif user.role == 'manager':
                    if hasattr(user, 'managed_branch') and user.managed_branch:
                        collections_query = collections_query.filter(
                            loan__loan_officer__officer_assignment__branch=user.managed_branch.name
                        )
                
                collections = collections_query.select_related('loan', 'loan__borrower')
                
                approved_count = 0
                for collection in collections:
                    # Approve the collection
                    collection.status = 'completed'
                    collection.collected_date = timezone.now()
                    collection.approved_by = user
                    collection.approved_date = timezone.now()
                    collection.save()
                    
                    # Update payment schedule
                    payment_schedules = collection.loan.payment_schedule.filter(
                        due_date=today
                    )
                    for schedule in payment_schedules:
                        if schedule.status == 'pending':
                            schedule.status = 'paid'
                            schedule.paid_date = timezone.now()
                            schedule.paid_amount = collection.collected_amount
                            schedule.save()
                    
                    # Check if loan should be marked as completed
                    loan = collection.loan
                    all_schedules = loan.payment_schedule.all()
                    if all_schedules.exists() and all_schedules.filter(status='paid').count() == all_schedules.count():
                        loan.status = 'completed'
                        loan.completion_date = timezone.now()
                        loan.save()
                    
                    approved_count += 1
                
                if approved_count > 0:
                    messages.success(request, f'Successfully approved {approved_count} collections for today!')
                
                return JsonResponse({
                    'success': True,
                    'approved_count': approved_count,
                    'message': f'Approved {approved_count} collections for today'
                })
                
        except Exception as e:
            return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


class GroupCollectionApprovalView(LoginRequiredMixin, View):
    """Approve collections for a specific group on a specific date"""
    
    def get(self, request):
        """Show group collection approval interface"""
        user = request.user
        
        if user.role not in ['loan_officer', 'manager', 'admin'] and not user.is_superuser:
            messages.error(request, 'You do not have permission to approve collections.')
            return redirect('dashboard:dashboard')
        
        # Get parameters
        target_date = request.GET.get('date')
        group_id = request.GET.get('group_id')
        
        if not target_date:
            target_date = date.today().strftime('%Y-%m-%d')
        
        target_date = timezone.datetime.strptime(target_date, '%Y-%m-%d').date()
        
        if not group_id:
            messages.error(request, 'Please select a group.')
            return redirect('dashboard:dashboard')
        
        # Get group
        from clients.models import BorrowerGroup
        group = get_object_or_404(BorrowerGroup, pk=group_id)
        
        # Check if user has permission for this group
        if user.role == 'loan_officer':
            if group.assigned_officer != user:
                messages.error(request, 'You can only approve collections for your assigned groups.')
                return redirect('dashboard:dashboard')
        elif user.role == 'manager':
            if hasattr(user, 'managed_branch') and user.managed_branch:
                if group.branch != user.managed_branch.name:
                    messages.error(request, 'You can only approve collections for groups in your branch.')
                    return redirect('dashboard:dashboard')
        
        # Get collections for this group on the target date
        collections = PaymentCollection.objects.filter(
            collection_date=target_date,
            loan__group_memberships__group=group,
            status='scheduled'
        ).select_related('loan', 'loan__borrower').order_by('loan__application_number')
        
        # Group by loan
        loans_with_collections = {}
        
        for collection in collections:
            loan_id = collection.loan.id
            if loan_id not in loans_with_collections:
                loans_with_collections[loan_id] = {
                    'loan': collection.loan,
                    'collections': [],
                    'total_expected': Decimal('0.00'),
                    'total_collected': Decimal('0.00'),
                    'can_approve': False
                }
            
            loans_with_collections[loan_id]['collections'].append(collection)
            loans_with_collections[loan_id]['total_expected'] += collection.expected_amount
            loans_with_collections[loan_id]['total_collected'] += collection.collected_amount
            
            # Check if all collections for this loan are paid
            if collection.collected_amount >= collection.expected_amount:
                loans_with_collections[loan_id]['can_approve'] = True
        
        # Convert to list and sort
        grouped_loans = list(loans_with_collections.values())
        grouped_loans.sort(key=lambda x: x['loan'].application_number)
        
        # Calculate totals
        total_expected = sum(loan['total_expected'] for loan in grouped_loans)
        total_collected = sum(loan['total_collected'] for loan in grouped_loans)
        total_approvable = sum(loan['total_expected'] for loan in grouped_loans if loan['can_approve'])
        
        context = {
            'group': group,
            'target_date': target_date,
            'grouped_loans': grouped_loans,
            'total_expected': total_expected,
            'total_collected': total_collected,
            'total_approvable': total_approvable,
            'total_loans': len(grouped_loans),
            'title': f'Group Collection Approval - {group.name} - {target_date.strftime("%B %d, %Y")}'
        }
        
        return render(request, 'payments/group_approval.html', context)
    
    def post(self, request):
        """Process group collection approval"""
        user = request.user
        
        if user.role not in ['loan_officer', 'manager', 'admin'] and not user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        try:
            with transaction.atomic():
                target_date = request.POST.get('date')
                group_id = request.POST.get('group_id')
                selected_loans = request.POST.getlist('selected_loans')
                
                if not target_date or not group_id or not selected_loans:
                    return JsonResponse({'error': 'Invalid request'}, status=400)
                
                target_date = timezone.datetime.strptime(target_date, '%Y-%m-%d').date()
                
                from clients.models import BorrowerGroup
                group = get_object_or_404(BorrowerGroup, pk=group_id)
                
                # Check permissions
                if user.role == 'loan_officer' and group.assigned_officer != user:
                    return JsonResponse({'error': 'Permission denied'}, status=403)
                elif user.role == 'manager':
                    if hasattr(user, 'managed_branch') and user.managed_branch:
                        if group.branch != user.managed_branch.name:
                            return JsonResponse({'error': 'Permission denied'}, status=403)
                
                approved_count = 0
                skipped_count = 0
                error_count = 0
                
                for loan_id in selected_loans:
                    try:
                        loan = get_object_or_404(Loan, pk=loan_id)
                        
                        # Get collections for this loan on the target date
                        collections = PaymentCollection.objects.filter(
                            loan=loan,
                            collection_date=target_date,
                            status='scheduled'
                        )
                        
                        loan_approved = False
                        for collection in collections:
                            # Check if collection is fully paid
                            if collection.collected_amount >= collection.expected_amount:
                                # Approve the collection
                                collection.status = 'completed'
                                collection.collected_date = timezone.now()
                                collection.approved_by = user
                                collection.approved_date = timezone.now()
                                collection.save()
                                
                                # Update payment schedule
                                payment_schedules = loan.payment_schedule.filter(
                                    due_date=target_date
                                )
                                for schedule in payment_schedules:
                                    if schedule.status == 'pending':
                                        schedule.status = 'paid'
                                        schedule.paid_date = timezone.now()
                                        schedule.paid_amount = collection.collected_amount
                                        schedule.save()
                                
                                loan_approved = True
                                approved_count += 1
                            else:
                                # Partial payment - skip for now
                                continue
                        
                        # Update loan status if all collections for this loan are approved
                        if loan_approved:
                            # Check if all payment schedules are paid
                            all_schedules = loan.payment_schedule.all()
                            if all_schedules.exists() and all_schedules.filter(status='paid').count() == all_schedules.count():
                                loan.status = 'completed'
                                loan.completion_date = timezone.now()
                                loan.save()
                                
                                # Create completion notification
                                from common.email_utils import send_loan_completion_email
                                try:
                                    send_loan_completion_email(loan)
                                except:
                                    pass # Email error is not critical
                                
                    except Exception as e:
                        error_count += 1
                        continue
                
                if approved_count > 0:
                    messages.success(request, f'Successfully approved {approved_count} collection(s) for {group.name} on {target_date.strftime("%B %d, %Y")}')
                if skipped_count > 0:
                    messages.warning(request, f'Skipped {skipped_count} collection(s) due to partial payments')
                if error_count > 0:
                    messages.error(request, f'Failed to approve {error_count} collection(s)')
                
                return JsonResponse({
                    'success': True,
                    'approved_count': approved_count,
                    'skipped_count': skipped_count,
                    'error_count': error_count,
                    'message': f'Approved {approved_count} collections for {group.name} on {target_date.strftime("%B %d, %Y")}'
                })
                
        except Exception as e:
            return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
