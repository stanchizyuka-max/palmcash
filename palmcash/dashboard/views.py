from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta

from loans.models import Loan, LoanApprovalRequest, LoanType
from payments.models import PaymentCollection, DefaultProvision
from clients.models import BorrowerGroup, Branch, AdminAuditLog
from accounts.models import User


@login_required
def dashboard(request):
    """Route to appropriate dashboard based on user role"""
    user = request.user
    
    # Debug: Check if user has role
    if not hasattr(user, 'role') or not user.role:
        # If role is missing, try to set default role
        if user.is_superuser:
            user.role = 'admin'
            user.save()
        else:
            return render(request, 'dashboard/access_denied.html', {
                'message': 'Your user account does not have a role assigned. Please contact your administrator.'
            })
    
    # Route based on role
    if user.role == 'loan_officer':
        return loan_officer_dashboard(request)
    elif user.role == 'manager':
        return manager_dashboard(request)
    elif user.role == 'admin':
        return admin_dashboard(request)
    elif user.role == 'borrower':
        return borrower_dashboard(request)
    else:
        return render(request, 'dashboard/access_denied.html', {
            'message': f'Unknown role: {user.role}. Please contact your administrator.'
        })


@login_required
def loan_officer_dashboard(request):
    """Loan Officer Dashboard"""
    officer = request.user
    
    # Get metrics
    groups = BorrowerGroup.objects.filter(assigned_officer=officer)
    
    # Get clients assigned to this officer - include both directly assigned and group members
    from django.db.models import Q
    clients = User.objects.filter(
        Q(assigned_officer=officer) | Q(group_memberships__group__assigned_officer=officer),
        role='borrower',
        is_active=True
    ).distinct()
    
    active_loans = Loan.objects.filter(
        loan_officer=officer,
        status='active'
    )
    
    # Today's collections
    today = date.today()
    today_collections = PaymentCollection.objects.filter(
        loan__loan_officer=officer,
        collection_date=today
    )
    
    today_expected = sum(c.expected_amount for c in today_collections) or 0
    today_collected = sum(c.collected_amount for c in today_collections) or 0
    today_defaults = today_collections.filter(is_default=True).count()
    
    # Pending actions
    pending_security = Loan.objects.filter(
        loan_officer=officer,
        security_deposit__is_verified=False
    ).count()
    
    ready_to_disburse = Loan.objects.filter(
        loan_officer=officer,
        status='approved',
        security_deposit__is_verified=True
    ).count()
    
    # Outstanding balance
    outstanding_balance = active_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
    
    # Workload percentage (assuming max capacity is 100 groups/clients)
    total_workload = groups.count() + clients.count()
    workload_percentage = (total_workload / 200 * 100) if total_workload > 0 else 0
    
    # Clients expected to pay today
    clients_expected_today = today_collections.select_related('loan__borrower').order_by('-expected_amount')
    
    # Recent transactions (from passbook/payment records)
    from payments.models import PaymentCollection as PC
    recent_transactions = PC.objects.filter(
        loan__loan_officer=officer
    ).select_related('loan__borrower').order_by('-collection_date')[:10]
    
    # Format recent transactions for display
    formatted_transactions = []
    for trans in recent_transactions:
        formatted_transactions.append({
            'type': 'payment',
            'description': f"Payment from {trans.loan.borrower.full_name}",
            'amount': trans.collected_amount,
            'created_at': trans.collection_date,
            'client_name': trans.loan.borrower.full_name,
        })
    
    # Passbook entries - get recent entries across all loans
    from payments.models import PassbookEntry
    passbook_entries = PassbookEntry.objects.filter(
        loan__loan_officer=officer
    ).select_related('loan__borrower').order_by('-entry_date')[:20]
    
    # Pending documents for review - get clients in officer's groups with pending documents
    from documents.models import ClientDocument
    
    pending_documents = []
    try:
        # Get all clients in officer's groups or directly assigned
        clients_in_groups = User.objects.filter(
            Q(group_memberships__group__assigned_officer=officer, group_memberships__is_active=True) |
            Q(assigned_officer=officer),
            role='borrower'
        ).values_list('id', flat=True).distinct()
        
        # Get pending documents from those clients
        pending_documents = ClientDocument.objects.filter(
            client_id__in=clients_in_groups,
            status='pending'
        ).select_related('client').distinct()[:10]
    except Exception as e:
        print(f"Error fetching pending documents: {e}")
        pending_documents = []
    
    context = {
        'groups_count': groups.count(),
        'clients_count': clients.count(),
        'active_loans_count': active_loans.count(),
        'today_expected': today_expected,
        'today_collected': today_collected,
        'today_pending': today_expected - today_collected,
        'today_defaults': today_defaults,
        'groups': groups[:5],
        'pending_security': pending_security,
        'ready_to_disburse': ready_to_disburse,
        'defaults_to_follow': DefaultProvision.objects.filter(
            loan__loan_officer=officer,
            status='active'
        ).count(),
        'outstanding_balance': outstanding_balance,
        'workload_percentage': workload_percentage,
        'clients_expected_today': clients_expected_today,
        'recent_transactions': formatted_transactions,
        'passbook_entries': passbook_entries,
        'pending_documents': pending_documents,
        'pending_documents_count': pending_documents.count(),
    }
    
    return render(request, 'dashboard/loan_officer_enhanced.html', context)


@login_required
def manager_dashboard(request):
    """Manager Dashboard"""
    manager = request.user
    
    # Check if user is actually a manager
    if manager.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    # Get branch - manager should have a managed_branch relationship
    try:
        branch = manager.managed_branch
        if not branch:
            # Manager doesn't have a branch assigned
            return render(request, 'dashboard/access_denied.html', {
                'message': 'You have not been assigned to a branch. Please contact your administrator.'
            })
    except:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'You have not been assigned to a branch. Please contact your administrator.'
        })
    
    # Branch metrics
    officers = User.objects.filter(role='loan_officer', officer_assignment__branch=branch.name)
    groups = BorrowerGroup.objects.filter(branch=branch.name)
    clients_count = sum(g.member_count for g in groups)
    
    # Today's collections
    today = date.today()
    today_collections = PaymentCollection.objects.filter(
        loan__loan_officer__officer_assignment__branch=branch.name,
        collection_date=today
    )
    
    today_expected = sum(c.expected_amount for c in today_collections) or 0
    today_collected = sum(c.collected_amount for c in today_collections) or 0
    collection_rate = (today_collected / today_expected * 100) if today_expected > 0 else 0
    
    # Pending approvals
    pending_security = 0
    pending_topups = 0
    pending_returns = 0
    pending_loan_approvals = 0
    ready_for_disbursement = 0
    
    try:
        from loans.models import SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, ManagerLoanApproval
        
        # Fix: Get all pending security deposits that have been paid but not verified
        # Remove branch filter to see all pending deposits, or use proper branch filtering
        pending_security = SecurityDeposit.objects.filter(
            is_verified=False,
            paid_amount__gt=0  # Only show deposits that have actually been paid
        ).count()
        
        # Alternative: If you want branch-specific deposits, use this query:
        # pending_security = SecurityDeposit.objects.filter(
        #     is_verified=False,
        #     paid_amount__gt=0,
        #     loan__loan_officer__officer_assignment__branch=branch.name
        # ).count()
        
        pending_topups = SecurityTopUpRequest.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            status='pending'
        ).count()
        
        pending_returns = SecurityReturnRequest.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            status='pending'
        ).count()
        
        # Pending loan approvals (approved loans with verified deposits but not yet approved by manager)
        pending_loan_approvals = Loan.objects.filter(
            status='approved',
            loan_officer__officer_assignment__branch=branch.name,
            upfront_payment_verified=True
        ).exclude(
            manager_approval__status='approved'
        ).count()
        
        # Ready for disbursement (manager approved loans)
        ready_for_disbursement = ManagerLoanApproval.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            status='approved'
        ).count()
    except:
        pass
    
    # Expense summary
    total_expenses = 0
    try:
        from expenses.models import Expense
        expenses = Expense.objects.filter(branch=branch.name)
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    except:
        pass
    
    # Fund summary
    total_transfers = 0
    total_deposits = 0
    try:
        from expenses.models import FundsTransfer, BankDeposit
        transfers = FundsTransfer.objects.filter(source_branch=branch.name)
        deposits = BankDeposit.objects.filter(source_branch=branch.name)
        total_transfers = transfers.aggregate(Sum('amount'))['amount__sum'] or 0
        total_deposits = deposits.aggregate(Sum('amount'))['amount__sum'] or 0
    except:
        pass
    
    # Officer performance
    officer_stats = []
    for officer in officers:
        try:
            assignment = officer.officer_assignment
            officer_loans = Loan.objects.filter(
                loan_officer=officer,
                status='active'
            )
            officer_collections = PaymentCollection.objects.filter(
                loan__loan_officer=officer,
                status='completed'
            )
            
            if officer_collections.exists():
                collection_rate_officer = (
                    officer_collections.filter(is_partial=False).count() / 
                    officer_collections.count() * 100
                )
            else:
                collection_rate_officer = 0
            
            stats = {
                'name': officer.full_name,
                'groups': assignment.current_group_count,
                'clients': assignment.current_client_count,
                'collection_rate': round(collection_rate_officer, 1),
            }
            officer_stats.append(stats)
        except:
            pass
    
    # Total disbursed for this branch
    # Get all officers in this branch
    branch_officers = User.objects.filter(
        role='loan_officer',
        officer_assignment__branch=branch.name
    ).values_list('id', flat=True)
    
    # Debug: Print branch info
    print(f"DEBUG: Branch name = {branch.name}")
    print(f"DEBUG: Branch officers count = {branch_officers.count()}")
    print(f"DEBUG: Branch officer IDs = {list(branch_officers)}")
    
    loans = Loan.objects.filter(
        loan_officer_id__in=branch_officers
    )
    
    # Debug: Check loan counts by status
    all_loans_count = loans.count()
    active_loans_count = loans.filter(status='active').count()
    completed_loans_count = loans.filter(status='completed').count()
    disbursed_loans_count = loans.filter(status='disbursed').count()
    
    print(f"DEBUG: Total loans = {all_loans_count}")
    print(f"DEBUG: Active loans = {active_loans_count}")
    print(f"DEBUG: Completed loans = {completed_loans_count}")
    print(f"DEBUG: Disbursed loans = {disbursed_loans_count}")
    
    # Check individual disbursed loans
    disbursed_loans = loans.filter(status='disbursed')
    for loan in disbursed_loans[:5]:  # Show first 5
        print(f"DEBUG: Disbursed loan - ID: {loan.id}, Amount: {loan.principal_amount}, Status: {loan.status}")
    
    total_disbursed = loans.filter(
        status__in=['active', 'completed', 'disbursed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    print(f"DEBUG: Total disbursed amount = {total_disbursed}")
    
    # Get document verification statistics
    pending_document_verifications = 0
    verified_document_clients = 0
    total_document_clients = 0
    
    try:
        from documents.models import ClientVerification, ClientDocument
        
        print(f"DEBUG: Branch name = {branch.name}")
        
        # For managers, get all clients in their branch
        from django.db.models import Q
        branch_client_ids = User.objects.filter(
            Q(assigned_officer__officer_assignment__branch=branch.name) | 
            Q(group_memberships__group__assigned_officer__branch=branch.name),
            role='borrower'
        ).values_list('id', flat=True).distinct()
        
        print(f"DEBUG: Branch client IDs count = {branch_client_ids.count()}")
        print(f"DEBUG: Branch client IDs = {list(branch_client_ids[:10])}")  # Show first 10
        
        # Check if ClientVerification model exists and has data
        all_verifications = ClientVerification.objects.all()
        print(f"DEBUG: Total ClientVerification records = {all_verifications.count()}")
        
        # Check ClientDocument model
        all_documents = ClientDocument.objects.all()
        print(f"DEBUG: Total ClientDocument records = {all_documents.count()}")
        
        # Get verification statistics for branch clients
        total_document_clients = ClientVerification.objects.filter(
            client_id__in=branch_client_ids
        ).count()
        
        print(f"DEBUG: Total document clients for branch = {total_document_clients}")
        
        # Check all verification statuses
        all_statuses = ClientVerification.objects.values_list('status', flat=True).distinct()
        print(f"DEBUG: All verification statuses = {list(all_statuses)}")
        
        verified_document_clients = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status='verified'
        ).count()
        
        print(f"DEBUG: Verified document clients = {verified_document_clients}")
        
        pending_document_verifications = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status__in=['documents_submitted', 'documents_rejected']
        ).count()
        
        print(f"DEBUG: Pending document verifications = {pending_document_verifications}")
        
        # Also check individual documents
        individual_docs = ClientDocument.objects.filter(
            client_id__in=branch_client_ids
        ).count()
        print(f"DEBUG: Individual documents for branch = {individual_docs}")
        
    except Exception as e:
        print(f"Error getting document verification stats: {e}")
        import traceback
        traceback.print_exc()
        pass
    
    # Calculate verification rate
    verification_rate = 0
    if total_document_clients > 0:
        verification_rate = round((verified_document_clients / total_document_clients) * 100, 1)
    
    print(f"DEBUG: Document verification stats - Total: {total_document_clients}, Verified: {verified_document_clients}, Pending: {pending_document_verifications}, Rate: {verification_rate}%")
    
    context = {
        'branch': branch,
        'today': today,
        'officers_count': officers.count(),
        'groups_count': groups.count(),
        'clients_count': clients_count,
        'today_expected': today_expected,
        'today_collected': today_collected,
        'collection_rate': round(collection_rate, 1),
        'pending_security': pending_security,
        'pending_topups': pending_topups,
        'pending_returns': pending_returns,
        'pending_loan_approvals': pending_loan_approvals,
        'ready_for_disbursement': ready_for_disbursement,
        'officer_stats': officer_stats,
        'total_expenses': total_expenses,
        'total_transfers': total_transfers,
        'total_deposits': total_deposits,
        'total_funds': total_transfers + total_deposits,
        'total_disbursed': total_disbursed,
        'pending_document_verifications': pending_document_verifications,
        'verified_document_clients': verified_document_clients,
        'total_document_clients': total_document_clients,
        'verification_rate': verification_rate,
    }
    
    return render(request, 'dashboard/manager_enhanced.html', context)


@login_required
def admin_dashboard(request):
    """Admin Dashboard"""
    if request.user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    # System metrics
    branches = Branch.objects.all()
    officers = User.objects.filter(role='loan_officer')
    clients = User.objects.filter(role='borrower')
    loans = Loan.objects.all()
    
    # High-value loans
    pending_approvals = LoanApprovalRequest.objects.filter(status='pending')
    approved_this_week = LoanApprovalRequest.objects.filter(
        status='approved',
        approval_date__gte=date.today() - timedelta(days=7)
    )
    
    # Total disbursed
    # Debug: Check loan counts for admin dashboard
    print(f"DEBUG ADMIN: Total loans in system = {loans.count()}")
    print(f"DEBUG ADMIN: Active loans = {loans.filter(status='active').count()}")
    print(f"DEBUG ADMIN: Completed loans = {loans.filter(status='completed').count()}")
    print(f"DEBUG ADMIN: Disbursed loans = {loans.filter(status='disbursed').count()}")
    
    # Check for any loans with different statuses
    all_statuses = loans.values_list('status', flat=True).distinct()
    print(f"DEBUG ADMIN: All loan statuses = {list(all_statuses)}")
    
    total_disbursed = loans.filter(
        status__in=['active', 'completed', 'disbursed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    print(f"DEBUG ADMIN: Total disbursed amount = {total_disbursed}")
    
    # System collection rate
    all_collections = PaymentCollection.objects.filter(status='completed')
    if all_collections.exists():
        system_collection_rate = (
            all_collections.filter(is_partial=False).count() / 
            all_collections.count() * 100
        )
    else:
        system_collection_rate = 0
    
    # Branch performance
    branch_stats = []
    for branch in branches:
        try:
            branch_groups = BorrowerGroup.objects.filter(branch=branch.name)
            branch_clients = sum(g.member_count for g in branch_groups)
            branch_loans = Loan.objects.filter(
                loan_officer__officer_assignment__branch=branch.name,
                status__in=['active', 'completed', 'disbursed']
            )
            branch_disbursed = branch_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
            
            branch_collections = PaymentCollection.objects.filter(
                loan__loan_officer__officer_assignment__branch=branch.name,
                status='completed'
            )
            
            if branch_collections.exists():
                branch_rate = (
                    branch_collections.filter(is_partial=False).count() / 
                    branch_collections.count() * 100
                )
            else:
                branch_rate = 0
            
            stats = {
                'name': branch.name,
                'clients': branch_clients,
                'total_disbursed': branch_disbursed,
                'collection_rate': round(branch_rate, 1),
            }
            branch_stats.append(stats)
        except:
            pass
    
    # System health
    active_loans = loans.filter(status='active').count()
    completed_loans = loans.filter(status='completed').count()
    defaulted_loans = loans.filter(status='defaulted').count()
    total_loans = loans.count()
    
    # Add pending security deposits count
    pending_security_deposits = 0
    try:
        from loans.models import SecurityDeposit
        pending_security_deposits = SecurityDeposit.objects.filter(
            is_verified=False,
            paid_amount__gt=0  # Only count deposits that have been paid but not verified
        ).count()
    except:
        pass
    
    active_pct = (active_loans / total_loans * 100) if total_loans > 0 else 0
    completed_pct = (completed_loans / total_loans * 100) if total_loans > 0 else 0
    defaulted_pct = (defaulted_loans / total_loans * 100) if total_loans > 0 else 0
    
    context = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_borrowers': clients.count(),
        'total_officers': officers.count(),
        'total_managers': User.objects.filter(role='manager').count(),
        'total_loans': total_loans,
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'defaulted_loans': defaulted_loans,
        'pending_security_deposits': pending_security_deposits,
        'pending_documents': 0,  # Will be calculated from ClientDocument
        'total_disbursed': total_disbursed,
        'total_repaid': 0,  # Will be calculated from PaymentCollection
        'overdue_count': 0,  # Will be calculated from PaymentSchedule
        'monthly_signups': 0,  # Will be calculated
        'monthly_applications': 0,  # Will be calculated
        'active_pct': round(active_pct, 1),
        'completed_pct': round(completed_pct, 1),
        'defaulted_pct': round(defaulted_pct, 1),
        'system_collection_rate': round(system_collection_rate, 1),
        'pending_approvals_count': pending_approvals.count(),
        'approved_this_week': approved_this_week.count(),
        'branch_stats': branch_stats,
        'transfers_this_month': 0,
        'client_transfers_this_month': 0,
        'pending_overrides': 0,
        'default_rate': round(defaulted_pct, 1),
        'recent_users': User.objects.all().order_by('-date_joined')[:5],
        'recent_loans': Loan.objects.all().order_by('-application_date')[:5],
    }
    
    # Add transfer counts from audit logs
    try:
        from adminpanel.models import OfficerTransferLog, ClientTransferLog
        from datetime import datetime
        current_month = date.today().replace(day=1)
        
        transfers_this_month = OfficerTransferLog.objects.filter(
            timestamp__gte=current_month
        ).count()
        context['transfers_this_month'] = transfers_this_month
        
        client_transfers_this_month = ClientTransferLog.objects.filter(
            timestamp__gte=current_month
        ).count()
        context['client_transfers_this_month'] = client_transfers_this_month
    except:
        pass
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def borrower_dashboard(request):
    """Borrower Dashboard"""
    borrower = request.user
    
    # Get borrower's loans
    loans = Loan.objects.filter(borrower=borrower)
    active_loans = loans.filter(status='active').count()
    completed_loans = loans.filter(status='completed').count()
    pending_loans = loans.filter(status='pending').count()
    
    # Get upcoming payments
    from payments.models import PaymentCollection
    upcoming_payments = PaymentCollection.objects.filter(
        loan__borrower=borrower,
        status='scheduled'
    ).order_by('collection_date')[:5]
    
    # Get total borrowed and repaid
    total_borrowed = loans.filter(
        status__in=['active', 'completed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    total_repaid = PaymentCollection.objects.filter(
        loan__borrower=borrower,
        status='completed'
    ).aggregate(total=Sum('collected_amount'))['total'] or 0
    
    # Get borrower's documents
    from documents.models import ClientDocument
    borrower_documents = ClientDocument.objects.filter(client=borrower)
    has_verified_documents = borrower_documents.filter(status='approved').exists()
    
    # Get rejected loans
    rejected_loans = loans.filter(status='rejected')
    
    # Get recent notifications
    from notifications.models import Notification
    recent_notifications = Notification.objects.filter(
        recipient=borrower
    ).order_by('-created_at')[:5]
    
    # Get repayment schedule
    from payments.models import PaymentSchedule
    repayment_schedule = PaymentSchedule.objects.filter(
        loan__borrower=borrower
    ).order_by('due_date')
    
    # Get pending applications
    pending_applications = loans.filter(status='pending').count()
    
    # Get approved loans awaiting upfront payment
    approved_loans = loans.filter(status='approved')
    loans_awaiting_upfront = []
    for loan in approved_loans:
        if not loan.upfront_payment_verified and loan.upfront_payment_paid == 0:
            loans_awaiting_upfront.append(loan)
    
    # Get overdue payments
    from payments.models import PaymentSchedule
    overdue_payments = PaymentSchedule.objects.filter(
        loan__borrower=borrower,
        is_paid=False,
        due_date__lt=timezone.now().date()
    )
    
    # Get next payment due
    next_payment = PaymentSchedule.objects.filter(
        loan__borrower=borrower,
        is_paid=False,
        due_date__gte=timezone.now().date()
    ).order_by('due_date').first()
    
    # Get loan status summary
    loan_status_summary = {
        'pending': loans.filter(status='pending').count(),
        'approved': loans.filter(status='approved').count(),
        'active': loans.filter(status='active').count(),
        'completed': loans.filter(status='completed').count(),
        'rejected': loans.filter(status='rejected').count(),
        'defaulted': loans.filter(status='defaulted').count(),
    }
    
    # Get total outstanding balance
    outstanding_balance = loans.filter(status='active').aggregate(
        total=Sum('principal_amount')
    )['total'] or 0
    
    # Get recent loan activity (actual loans, not approval requests)
    recent_approvals = loans.order_by('-application_date')[:5]
    
    # Get available loan types
    available_loan_types = LoanType.objects.filter(is_active=True)
    
    context = {
        'total_loans': loans.count(),
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'pending_loans': pending_loans,
        'upcoming_payments': upcoming_payments,
        'total_borrowed': total_borrowed,
        'total_repaid': total_repaid,
        'has_verified_documents': has_verified_documents,
        'rejected_loans': rejected_loans,
        'recent_notifications': recent_notifications,
        'borrower_documents': borrower_documents,
        'repayment_schedule': repayment_schedule,
        'pending_applications': pending_applications,
        'user_loans': loans,
        'loans_awaiting_upfront': loans_awaiting_upfront,
        'overdue_payments': overdue_payments,
        'next_payment': next_payment,
        'loan_status_summary': loan_status_summary,
        'outstanding_balance': outstanding_balance,
        'recent_approvals': recent_approvals,
        'available_loan_types': available_loan_types,
    }
    
    return render(request, 'dashboard/borrower_dashboard.html', context)


# Action Views for Dashboard Links

@login_required
def collection_details(request):
    """Collection Details View - Shows detailed collection information grouped by loan"""
    user = request.user
    
    if user.role == 'manager':
        # Manager sees collections for their branch
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
        
        collections = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name
        ).order_by('-collection_date')
    elif user.role == 'loan_officer':
        # Loan officer sees their collections
        collections = PaymentCollection.objects.filter(
            loan__loan_officer=user
        ).order_by('-collection_date')
    elif user.role == 'admin':
        # Admin sees all collections
        collections = PaymentCollection.objects.all().order_by('-collection_date')
    else:
        return render(request, 'dashboard/access_denied.html')
    
    # Group collections by loan
    from django.db.models import Sum
    loans_with_collections = {}
    
    for collection in collections:
        loan_id = collection.loan.id
        if loan_id not in loans_with_collections:
            loans_with_collections[loan_id] = {
                'loan': collection.loan,
                'collections': [],
                'total_expected': 0,
                'total_collected': 0,
                'completed_count': 0,
                'scheduled_count': 0
            }
        
        loans_with_collections[loan_id]['collections'].append(collection)
        loans_with_collections[loan_id]['total_expected'] += collection.expected_amount
        loans_with_collections[loan_id]['total_collected'] += collection.collected_amount
        
        if collection.status == 'completed':
            loans_with_collections[loan_id]['completed_count'] += 1
        else:
            loans_with_collections[loan_id]['scheduled_count'] += 1
    
    # Convert to list and sort by loan application number
    grouped_loans = list(loans_with_collections.values())
    grouped_loans.sort(key=lambda x: x['loan'].application_number)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(grouped_loans, 20)  # 20 loans per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'grouped_loans': page_obj.object_list,
        'total_collections': collections.count(),
        'total_collected': collections.aggregate(total=Sum('collected_amount'))['total'] or 0,
        'total_loans': len(grouped_loans),
    }
    
    return render(request, 'dashboard/collection_details.html', context)


@login_required
def pending_approvals(request):
    """Pending Approvals View - Shows loans awaiting approval and security deposits"""
    user = request.user
    
    if user.role == 'manager':
        # Manager sees pending approvals for their branch
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
        
        # Get pending loan approvals (high-value loans awaiting admin approval)
        pending_loans = LoanApprovalRequest.objects.filter(
            status='pending',
            loan__loan_officer__officer_assignment__branch=branch.name
        ).order_by('-requested_date')
        
        # Get pending security deposits (paid but not verified)
        from loans.models import SecurityDeposit
        pending_deposits = SecurityDeposit.objects.filter(
            is_verified=False,
            paid_amount__gt=0,  # Only show deposits that have been paid
            loan__loan_officer__officer_assignment__branch=branch.name
        ).select_related('loan', 'loan__borrower').order_by('-payment_date')
        
    elif user.role == 'admin':
        # Admin sees all pending approvals
        pending_loans = LoanApprovalRequest.objects.filter(
            status='pending'
        ).order_by('-requested_date')
        
        # Get all pending security deposits (paid but not verified)
        from loans.models import SecurityDeposit
        pending_deposits = SecurityDeposit.objects.filter(
            is_verified=False,
            paid_amount__gt=0  # Only show deposits that have been paid
        ).select_related('loan', 'loan__borrower').order_by('-payment_date')
    else:
        return render(request, 'dashboard/access_denied.html')
    
    # Calculate totals for security deposits
    from django.db.models import Sum
    deposit_totals = pending_deposits.aggregate(
        total_required=Sum('required_amount'),
        total_collected=Sum('paid_amount')
    )
    
    total_required = deposit_totals['total_required'] or 0
    total_collected = deposit_totals['total_collected'] or 0
    total_outstanding = total_required - total_collected
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(pending_loans, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'pending_approvals': page_obj.object_list,
        'pending_deposits': pending_deposits,
        'total_pending': pending_loans.count(),
        'total_deposits': pending_deposits.count(),
        'total_required': total_required,
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
    }
    
    return render(request, 'dashboard/pending_approvals.html', context)


@login_required
def approved_security_deposits(request):
    """View approved security deposits and upfront payments"""
    user = request.user
    
    if user.role == 'manager':
        # Manager sees approved deposits for their branch
        try:
            branch = user.managed_branch
            if not branch:
                return render(request, 'dashboard/access_denied.html')
            
            # Get approved security deposits (verified) - try simpler query first
            from loans.models import SecurityDeposit
            approved_deposits = SecurityDeposit.objects.filter(
                is_verified=True
            ).select_related('loan', 'loan__borrower').order_by('-verification_date')
            
            # Filter by branch after getting results
            branch_deposits = []
            for deposit in approved_deposits:
                if deposit.loan and hasattr(deposit.loan, 'loan_officer'):
                    if hasattr(deposit.loan.loan_officer, 'officer_assignment'):
                        if deposit.loan.loan_officer.officer_assignment.branch == branch.name:
                            branch_deposits.append(deposit)
                elif deposit.loan and not hasattr(deposit.loan, 'loan_officer'):
                    # If loan has no officer, include it
                    branch_deposits.append(deposit)
            
            approved_deposits = branch_deposits
            branch_display_name = branch.name
            
        except Exception as e:
            # If there's an error with branch assignment, show access denied
            return render(request, 'dashboard/access_denied.html')
        
    elif user.role == 'admin':
        # Admin sees all approved deposits
        from loans.models import SecurityDeposit
        approved_deposits = SecurityDeposit.objects.filter(
            is_verified=True
        ).select_related('loan', 'loan__borrower').order_by('-verification_date')
        
        branch_display_name = 'All Branches'
    else:
        return render(request, 'dashboard/access_denied.html')
    
    # Calculate totals
    from django.db.models import Sum
    if approved_deposits:
        total_required = sum(deposit.required_amount for deposit in approved_deposits)
        total_collected = sum(deposit.paid_amount for deposit in approved_deposits)
    else:
        total_required = 0
        total_collected = 0
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(approved_deposits, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'approved_deposits': page_obj.object_list,
        'total_deposits': len(approved_deposits),
        'total_required': total_required,
        'total_collected': total_collected,
        'branch': branch_display_name,
    }
    
    return render(request, 'dashboard/approved_security_deposits.html', context)


@login_required
def manage_officers(request):
    """Manage Officers View - Shows loan officers and their assignments"""
    user = request.user
    
    if user.role == 'manager':
        # Manager sees officers in their branch
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
        
        officers = User.objects.filter(
            role='loan_officer',
            officer_assignment__branch=branch.name
        ).order_by('first_name', 'last_name')
    elif user.role == 'admin':
        # Admin sees all officers
        officers = User.objects.filter(role='loan_officer').order_by('first_name', 'last_name')
    else:
        return render(request, 'dashboard/access_denied.html')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(officers, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get officer assignments for display
    from clients.models import OfficerAssignment
    officer_assignments = {}
    for officer in page_obj.object_list:
        try:
            officer_assignments[officer.id] = OfficerAssignment.objects.get(officer=officer)
        except OfficerAssignment.DoesNotExist:
            officer_assignments[officer.id] = None
    
    context = {
        'page_obj': page_obj,
        'officers': page_obj.object_list,
        'officer_assignments': officer_assignments,
        'total_officers': officers.count(),
    }
    
    return render(request, 'dashboard/manage_officers.html', context)


@login_required
def manage_branches(request):
    """Manage Branches View - Shows all branches and their details"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    branches = Branch.objects.all().order_by('name')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(branches, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'branches': page_obj.object_list,
        'total_branches': branches.count(),
    }
    
    return render(request, 'dashboard/manage_branches.html', context)


@login_required
def audit_logs(request):
    """Audit Logs View - Shows admin audit logs"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    logs = AdminAuditLog.objects.all().order_by('-timestamp')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'total_logs': logs.count(),
    }
    
    return render(request, 'dashboard/audit_logs.html', context)



# Approval Views

@login_required
def approval_detail(request, approval_id):
    """View approval details and allow approve/reject actions"""
    from loans.models import SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, ApprovalLog
    
    user = request.user
    
    # Get the approval item based on ID and type
    approval_type = request.GET.get('type', 'security_deposit')
    
    if approval_type == 'security_deposit':
        try:
            approval = SecurityDeposit.objects.get(id=approval_id, is_verified=False)
            approval_type_display = 'Security Deposit'
        except SecurityDeposit.DoesNotExist:
            return render(request, 'dashboard/access_denied.html', {'message': 'Approval not found'})
    elif approval_type == 'security_topup':
        try:
            approval = SecurityTopUpRequest.objects.get(id=approval_id, status='pending')
            approval_type_display = 'Security Top-Up'
        except SecurityTopUpRequest.DoesNotExist:
            return render(request, 'dashboard/access_denied.html', {'message': 'Approval not found'})
    elif approval_type == 'security_return':
        try:
            approval = SecurityReturnRequest.objects.get(id=approval_id, status='pending')
            approval_type_display = 'Security Return'
        except SecurityReturnRequest.DoesNotExist:
            return render(request, 'dashboard/access_denied.html', {'message': 'Approval not found'})
    else:
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid approval type'})
    
    # Check if user is manager of the branch
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    # Get loan details
    loan = approval.loan if hasattr(approval, 'loan') else None
    
    context = {
        'approval': approval,
        'approval_type': approval_type,
        'approval_type_display': approval_type_display,
        'loan': loan,
        'branch': branch,
    }
    
    return render(request, 'dashboard/approval_detail.html', context)


@login_required
def approval_approve(request, approval_id):
    """Approve a security-related request"""
    from loans.models import SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, ApprovalLog
    
    if request.method != 'POST':
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid request method'})
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    approval_type = request.POST.get('type', 'security_deposit')
    comments = request.POST.get('comments', '')
    
    try:
        if approval_type == 'security_deposit':
            approval = SecurityDeposit.objects.get(id=approval_id, is_verified=False)
            approval.is_verified = True
            approval.verified_by = user
            approval.verification_date = timezone.now()
            approval.save()
            
            # Update loan's upfront payment verified status
            loan = approval.loan
            loan.upfront_payment_verified = True
            loan.save()
            
            # Log the approval
            ApprovalLog.objects.create(
                approval_type='security_deposit',
                loan=approval.loan,
                manager=user,
                action='approve',
                comments=comments,
                branch=branch.name
            )
            
        elif approval_type == 'security_topup':
            approval = SecurityTopUpRequest.objects.get(id=approval_id, status='pending')
            approval.status = 'approved'
            approval.save()
            
            # Log the approval
            ApprovalLog.objects.create(
                approval_type='security_topup',
                loan=approval.loan,
                manager=user,
                action='approve',
                comments=comments,
                branch=branch.name
            )
            
        elif approval_type == 'security_return':
            approval = SecurityReturnRequest.objects.get(id=approval_id, status='pending')
            approval.status = 'approved'
            approval.save()
            
            # Log the approval
            ApprovalLog.objects.create(
                approval_type='security_return',
                loan=approval.loan,
                manager=user,
                action='approve',
                comments=comments,
                branch=branch.name
            )
        
        # Redirect to pending approvals
        from django.shortcuts import redirect
        return redirect('dashboard:pending_approvals')
        
    except Exception as e:
        return render(request, 'dashboard/access_denied.html', {'message': f'Error approving: {str(e)}'})


@login_required
def approval_reject(request, approval_id):
    """Reject a security-related request"""
    from loans.models import SecurityDeposit, SecurityTopUpRequest, SecurityReturnRequest, ApprovalLog
    
    if request.method != 'POST':
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid request method'})
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    approval_type = request.POST.get('type', 'security_deposit')
    comments = request.POST.get('comments', '')
    
    if not comments:
        return render(request, 'dashboard/access_denied.html', {'message': 'Comments are required for rejection'})
    
    try:
        if approval_type == 'security_deposit':
            approval = SecurityDeposit.objects.get(id=approval_id, is_verified=False)
            approval.is_verified = False  # Keep as unverified
            approval.save()
            
            # Log the rejection
            ApprovalLog.objects.create(
                approval_type='security_deposit',
                loan=approval.loan,
                manager=user,
                action='reject',
                comments=comments,
                branch=branch.name
            )
            
        elif approval_type == 'security_topup':
            approval = SecurityTopUpRequest.objects.get(id=approval_id, status='pending')
            approval.status = 'rejected'
            approval.save()
            
            # Log the rejection
            ApprovalLog.objects.create(
                approval_type='security_topup',
                loan=approval.loan,
                manager=user,
                action='reject',
                comments=comments,
                branch=branch.name
            )
            
        elif approval_type == 'security_return':
            approval = SecurityReturnRequest.objects.get(id=approval_id, status='pending')
            approval.status = 'rejected'
            approval.save()
            
            # Log the rejection
            ApprovalLog.objects.create(
                approval_type='security_return',
                loan=approval.loan,
                manager=user,
                action='reject',
                comments=comments,
                branch=branch.name
            )
        
        # Redirect to pending approvals
        from django.shortcuts import redirect
        return redirect('dashboard:pending_approvals')
        
    except Exception as e:
        return render(request, 'dashboard/access_denied.html', {'message': f'Error rejecting: {str(e)}'})


@login_required
def approval_history(request):
    """View approval history and logs"""
    from loans.models import ApprovalLog
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    # Get approval logs for this branch
    logs = ApprovalLog.objects.filter(branch=branch.name).order_by('-timestamp')
    
    # Apply filters
    approval_type = request.GET.get('approval_type', '')
    action = request.GET.get('action', '')
    loan_id = request.GET.get('loan_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if approval_type:
        logs = logs.filter(approval_type=approval_type)
    
    if action:
        logs = logs.filter(action=action)
    
    if loan_id:
        logs = logs.filter(loan__id=loan_id)
    
    if date_from:
        from datetime import datetime
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        from datetime import datetime, timedelta
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire day
            date_to_obj = date_to_obj + timedelta(days=1)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except:
            pass
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'total_logs': logs.count(),
        'branch': branch,
        'approval_type': approval_type,
        'action': action,
        'loan_id': loan_id,
        'date_from': date_from,
        'date_to': date_to,
        'approval_types': ApprovalLog.APPROVAL_TYPES,
        'actions': ApprovalLog.ACTION_CHOICES,
    }
    
    return render(request, 'dashboard/approval_history.html', context)


@login_required
def manager_loan_approval_detail(request, loan_id):
    """Manager view: Display loan details for approval decision"""
    from loans.models import Loan, ManagerLoanApproval, SecurityDeposit
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        messages.error(request, 'You do not have permission to approve loans.')
        return redirect('dashboard:dashboard')
    
    try:
        branch = user.managed_branch
        if not branch:
            messages.error(request, 'You are not assigned to a branch.')
            return redirect('dashboard:dashboard')
    except:
        messages.error(request, 'Error accessing branch information.')
        return redirect('dashboard:dashboard')
    
    # Get the loan
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        messages.error(request, 'Loan not found.')
        return redirect('dashboard:pending_approvals')
    
    # Check if loan is in approved status
    if loan.status != 'approved':
        messages.error(request, 'Loan is not in approved status.')
        return redirect('dashboard:pending_approvals')
    
    # Check if manager's branch matches loan officer's branch
    try:
        if loan.loan_officer.officer_assignment.branch != branch.name:
            messages.error(request, 'You do not have permission to approve this loan.')
            return redirect('dashboard:pending_approvals')
    except:
        messages.error(request, 'Error verifying loan assignment.')
        return redirect('dashboard:pending_approvals')
    
    # Get security deposit status
    try:
        security_deposit = loan.security_deposit
        deposit_verified = security_deposit.is_verified
    except:
        deposit_verified = False
    
    # Get manager approval status
    try:
        manager_approval = loan.manager_approval
    except:
        manager_approval = None
    
    context = {
        'loan': loan,
        'security_deposit': security_deposit if 'security_deposit' in locals() else None,
        'deposit_verified': deposit_verified,
        'manager_approval': manager_approval,
        'branch': branch,
    }
    
    return render(request, 'dashboard/manager_loan_approval_detail.html', context)


@login_required
def manager_loan_approve(request, loan_id):
    """Manager view: Approve a loan for disbursement"""
    from loans.models import Loan, ManagerLoanApproval, ApprovalLog
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('dashboard:pending_approvals')
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        messages.error(request, 'You do not have permission to approve loans.')
        return redirect('dashboard:dashboard')
    
    try:
        branch = user.managed_branch
        if not branch:
            messages.error(request, 'You are not assigned to a branch.')
            return redirect('dashboard:dashboard')
    except:
        messages.error(request, 'Error accessing branch information.')
        return redirect('dashboard:dashboard')
    
    # Get the loan
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        messages.error(request, 'Loan not found.')
        return redirect('dashboard:pending_approvals')
    
    # Validate loan status
    if loan.status != 'approved':
        messages.error(request, 'Loan is not in approved status.')
        return redirect('dashboard:pending_approvals')
    
    # Check if manager's branch matches loan officer's branch
    try:
        if loan.loan_officer.officer_assignment.branch != branch.name:
            messages.error(request, 'You do not have permission to approve this loan.')
            return redirect('dashboard:pending_approvals')
    except:
        messages.error(request, 'Error verifying loan assignment.')
        return redirect('dashboard:pending_approvals')
    
    # Validate security deposit is verified
    try:
        security_deposit = loan.security_deposit
        if not security_deposit.is_verified:
            messages.error(request, 'Security deposit must be verified before loan approval.')
            return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)
    except:
        messages.error(request, 'Security deposit not found.')
        return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)
    
    # Get comments
    comments = request.POST.get('comments', '')
    
    try:
        # Create or update manager approval
        manager_approval, created = ManagerLoanApproval.objects.get_or_create(loan=loan)
        manager_approval.status = 'approved'
        manager_approval.manager = user
        manager_approval.approved_date = timezone.now()
        manager_approval.comments = comments
        manager_approval.save()
        
        # Log the approval
        ApprovalLog.objects.create(
            approval_type='loan_approval',
            loan=loan,
            manager=user,
            action='approve',
            comments=comments,
            branch=branch.name
        )
        
        messages.success(request, f'Loan {loan.application_number} has been approved for disbursement.')
        return redirect('dashboard:pending_approvals')
        
    except Exception as e:
        messages.error(request, f'Error approving loan: {str(e)}')
        return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)


@login_required
def manager_loan_reject(request, loan_id):
    """Manager view: Reject a loan approval"""
    from loans.models import Loan, ManagerLoanApproval, ApprovalLog
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('dashboard:pending_approvals')
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        messages.error(request, 'You do not have permission to reject loans.')
        return redirect('dashboard:dashboard')
    
    try:
        branch = user.managed_branch
        if not branch:
            messages.error(request, 'You are not assigned to a branch.')
            return redirect('dashboard:dashboard')
    except:
        messages.error(request, 'Error accessing branch information.')
        return redirect('dashboard:dashboard')
    
    # Get the loan
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        messages.error(request, 'Loan not found.')
        return redirect('dashboard:pending_approvals')
    
    # Validate loan status
    if loan.status != 'approved':
        messages.error(request, 'Loan is not in approved status.')
        return redirect('dashboard:pending_approvals')
    
    # Check if manager's branch matches loan officer's branch
    try:
        if loan.loan_officer.officer_assignment.branch != branch.name:
            messages.error(request, 'You do not have permission to reject this loan.')
            return redirect('dashboard:pending_approvals')
    except:
        messages.error(request, 'Error verifying loan assignment.')
        return redirect('dashboard:pending_approvals')
    
    # Get comments (required for rejection)
    comments = request.POST.get('comments', '')
    
    if not comments:
        messages.error(request, 'Comments are required for rejection.')
        return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)
    
    try:
        # Create or update manager approval
        manager_approval, created = ManagerLoanApproval.objects.get_or_create(loan=loan)
        manager_approval.status = 'rejected'
        manager_approval.manager = user
        manager_approval.comments = comments
        manager_approval.save()
        
        # Log the rejection
        ApprovalLog.objects.create(
            approval_type='loan_approval',
            loan=loan,
            manager=user,
            action='reject',
            comments=comments,
            branch=branch.name
        )
        
        messages.success(request, f'Loan {loan.application_number} has been rejected.')
        return redirect('dashboard:pending_approvals')
        
    except Exception as e:
        messages.error(request, f'Error rejecting loan: {str(e)}')
        return redirect('dashboard:manager_loan_approval_detail', loan_id=loan_id)


# Expense Management Views

@login_required
def expense_list(request):
    """View and filter expenses for manager's branch"""
    from expenses.models import Expense, ExpenseCode
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    # Get expenses for this branch
    expenses = Expense.objects.filter(branch=branch.name).order_by('-expense_date')
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)
    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)
    
    # Filter by expense code
    expense_code = request.GET.get('expense_code')
    if expense_code:
        expenses = expenses.filter(expense_code_id=expense_code)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(expenses, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'page_obj': page_obj,
        'expenses': page_obj.object_list,
        'total_expenses': total_expenses,
        'expense_codes': ExpenseCode.objects.filter(is_active=True),
        'branch': branch,
    }
    
    return render(request, 'dashboard/expense_list.html', context)


@login_required
def expense_create(request):
    """Create a new expense"""
    from expenses.models import Expense, ExpenseCode
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            amount = request.POST.get('amount')
            expense_code_id = request.POST.get('expense_code')
            expense_date = request.POST.get('expense_date')
            description = request.POST.get('description')
            
            # Validate required fields
            if not amount or not expense_code_id or not expense_date:
                return render(request, 'dashboard/expense_form.html', {
                    'error': 'Amount, expense code, and date are required',
                    'expense_codes': ExpenseCode.objects.filter(is_active=True),
                    'branch': branch,
                })
            
            # Create expense
            expense_code = ExpenseCode.objects.get(id=expense_code_id)
            expense = Expense.objects.create(
                amount=amount,
                expense_code=expense_code,
                expense_date=expense_date,
                description=description or '',
                branch=branch.name,
                recorded_by=user,
                title=f"{expense_code.name} - {expense_date}"
            )
            
            # Redirect to expense list
            from django.shortcuts import redirect
            return redirect('dashboard:expense_list')
            
        except Exception as e:
            return render(request, 'dashboard/expense_form.html', {
                'error': f'Error creating expense: {str(e)}',
                'expense_codes': ExpenseCode.objects.filter(is_active=True),
                'branch': branch,
            })
    
    context = {
        'expense_codes': ExpenseCode.objects.filter(is_active=True),
        'branch': branch,
    }
    
    return render(request, 'dashboard/expense_form.html', context)


@login_required
def expense_report(request):
    """Generate expense report by category and date"""
    from expenses.models import Expense, ExpenseCode
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    # Get expenses for this branch
    expenses = Expense.objects.filter(branch=branch.name)
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)
    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)
    
    # Aggregate by expense code
    category_totals = {}
    total_expenses = 0
    total_count = 0
    
    for code in ExpenseCode.objects.filter(is_active=True):
        code_expenses = expenses.filter(expense_code=code)
        total = code_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        if total > 0:
            count = code_expenses.count()
            total_count += count
            percentage = (total / expenses.aggregate(Sum('amount'))['amount__sum'] * 100) if expenses.aggregate(Sum('amount'))['amount__sum'] else 0
            category_totals[code.name] = {
                'total': total,
                'count': count,
                'percentage': round(percentage, 1)
            }
            total_expenses += total
    
    context = {
        'category_totals': category_totals,
        'total_expenses': total_expenses,
        'total_expenses_count': total_count,
        'expense_codes': ExpenseCode.objects.filter(is_active=True),
        'branch': branch,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'dashboard/expense_report.html', context)


# Funds Management Views

@login_required
def fund_transfer_create(request):
    """Create a new fund transfer between branches"""
    from expenses.models import FundsTransfer
    from clients.models import Branch
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            amount = request.POST.get('amount')
            destination_branch = request.POST.get('destination_branch')
            date_str = request.POST.get('date')
            reference = request.POST.get('reference')
            description = request.POST.get('description', '')
            
            # Validate required fields
            if not amount or not destination_branch or not date_str or not reference:
                return render(request, 'dashboard/fund_transfer_form.html', {
                    'error': 'Amount, destination branch, date, and reference are required',
                    'branches': Branch.objects.exclude(name=branch.name),
                    'branch': branch,
                })
            
            # Create fund transfer
            transfer = FundsTransfer.objects.create(
                amount=amount,
                source_branch=branch.name,
                destination_branch=destination_branch,
                reference_number=reference,
                description=description,
                requested_by=user,
                status='pending'
            )
            
            # Redirect to fund history
            from django.shortcuts import redirect
            return redirect('dashboard:fund_history')
            
        except Exception as e:
            return render(request, 'dashboard/fund_transfer_form.html', {
                'error': f'Error creating transfer: {str(e)}',
                'branches': Branch.objects.exclude(name=branch.name),
                'branch': branch,
            })
    
    context = {
        'branches': Branch.objects.exclude(name=branch.name),
        'branch': branch,
    }
    
    return render(request, 'dashboard/fund_transfer_form.html', context)


@login_required
def fund_deposit_create(request):
    """Create a new bank deposit"""
    from expenses.models import BankDeposit
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html')
    except:
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            amount = request.POST.get('amount')
            bank_name = request.POST.get('bank_name')
            account_number = request.POST.get('account_number')
            date_str = request.POST.get('date')
            reference = request.POST.get('reference')
            description = request.POST.get('description', '')
            
            # Validate required fields
            if not amount or not bank_name or not account_number or not date_str or not reference:
                return render(request, 'dashboard/fund_deposit_form.html', {
                    'error': 'Amount, bank name, account number, date, and reference are required',
                    'branch': branch,
                })
            
            # Create bank deposit
            deposit = BankDeposit.objects.create(
                amount=amount,
                source_branch=branch.name,
                bank_name=bank_name,
                account_number=account_number,
                reference_number=reference,
                description=description,
                requested_by=user,
                deposit_date=date_str,
                status='pending'
            )
            
            # Redirect to fund history
            from django.shortcuts import redirect
            return redirect('dashboard:fund_history')
            
        except Exception as e:
            return render(request, 'dashboard/fund_deposit_form.html', {
                'error': f'Error creating deposit: {str(e)}',
                'branch': branch,
            })
    
    context = {
        'branch': branch,
    }
    
    return render(request, 'dashboard/fund_deposit_form.html', context)


@login_required
def fund_history(request):
    """View fund transfer and deposit history"""
    from expenses.models import FundsTransfer, BankDeposit
    
    user = request.user
    
    # Check if user is manager
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = user.managed_branch
        if not branch:
            # If manager has no branch, show all records
            transfers = FundsTransfer.objects.all().order_by('-requested_date')
            deposits = BankDeposit.objects.all().order_by('-requested_date')
            branch_name = "All Branches"
        else:
            # Get transfers for this branch (as source or destination)
            transfers = FundsTransfer.objects.filter(
                Q(source_branch=branch.name) | Q(destination_branch=branch.name)
            ).order_by('-requested_date')
            
            # Get deposits for this branch
            deposits = BankDeposit.objects.filter(source_branch=branch.name).order_by('-requested_date')
            branch_name = branch.name
    except:
        return render(request, 'dashboard/access_denied.html')
    
    # Filter by type
    fund_type = request.GET.get('type')
    if fund_type == 'transfer':
        transfers = transfers
        deposits = BankDeposit.objects.none()
    elif fund_type == 'deposit':
        transfers = FundsTransfer.objects.none()
        deposits = deposits
    else:
        # Show all by default
        transfers = transfers
        deposits = deposits
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        transfers = transfers.filter(requested_date__gte=start_date)
        deposits = deposits.filter(requested_date__gte=start_date)
    if end_date:
        transfers = transfers.filter(requested_date__lte=end_date)
        deposits = deposits.filter(requested_date__lte=end_date)
    
    # Filter by amount range
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if min_amount:
        transfers = transfers.filter(amount__gte=min_amount)
        deposits = deposits.filter(amount__gte=min_amount)
    if max_amount:
        transfers = transfers.filter(amount__lte=max_amount)
        deposits = deposits.filter(amount__lte=max_amount)
    
    # Combine and paginate
    from django.core.paginator import Paginator
    from itertools import chain
    
    all_records = list(chain(transfers, deposits))
    all_records.sort(key=lambda x: x.requested_date, reverse=True)
    
    paginator = Paginator(all_records, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals
    total_transfers = transfers.aggregate(Sum('amount'))['amount__sum'] or 0
    total_deposits = deposits.aggregate(Sum('amount'))['amount__sum'] or 0
    total_funds = total_transfers + total_deposits
    
    context = {
        'page_obj': page_obj,
        'records': page_obj.object_list,
        'total_records': len(all_records),
        'total_transfers': total_transfers,
        'total_deposits': total_deposits,
        'total_funds': total_funds,
        'branch': branch_name,
    }
    
    return render(request, 'dashboard/fund_history.html', context)


# User Management Views

@login_required
def user_create(request):
    """Create a new user (officer or manager)"""
    user = request.user
    
    # Check if user is admin
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone_number = request.POST.get('phone_number')
            role = request.POST.get('role')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            # Validate required fields
            if not all([username, email, first_name, last_name, role, password]):
                return render(request, 'dashboard/user_form.html', {
                    'error': 'All fields are required',
                })
            
            # Validate passwords match
            if password != password_confirm:
                return render(request, 'dashboard/user_form.html', {
                    'error': 'Passwords do not match',
                })
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                return render(request, 'dashboard/user_form.html', {
                    'error': 'Username already exists',
                })
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return render(request, 'dashboard/user_form.html', {
                    'error': 'Email already exists',
                })
            
            # Create user
            new_user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=role,
                phone_number=phone_number or '',
                is_active=True
            )
            
            # If loan officer, create officer assignment
            if role == 'loan_officer':
                from clients.models import OfficerAssignment
                OfficerAssignment.objects.create(
                    officer=new_user,
                    branch='',
                    max_groups=15,
                    max_clients=50,
                    is_accepting_assignments=True
                )
            
            # Redirect to manage officers
            from django.shortcuts import redirect
            return redirect('dashboard:manage_officers')
            
        except Exception as e:
            return render(request, 'dashboard/user_form.html', {
                'error': f'Error creating user: {str(e)}',
            })
    
    context = {}
    return render(request, 'dashboard/user_form.html', context)


@login_required
def branch_create(request):
    """Create a new branch"""
    user = request.user
    
    # Check if user is admin
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            location = request.POST.get('location')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            manager_id = request.POST.get('manager')
            
            # Validate required fields
            if not all([name, code, location]):
                return render(request, 'dashboard/branch_form.html', {
                    'error': 'Name, code, and location are required',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if branch name already exists
            if Branch.objects.filter(name=name).exists():
                return render(request, 'dashboard/branch_form.html', {
                    'error': 'Branch name already exists',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if branch code already exists
            if Branch.objects.filter(code=code).exists():
                return render(request, 'dashboard/branch_form.html', {
                    'error': 'Branch code already exists',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Get manager if provided
            manager = None
            if manager_id:
                try:
                    manager = User.objects.get(id=manager_id, role='manager')
                except User.DoesNotExist:
                    return render(request, 'dashboard/branch_form.html', {
                        'error': 'Invalid manager selected',
                        'managers': User.objects.filter(role='manager'),
                    })
            
            # Create branch
            branch = Branch.objects.create(
                name=name,
                code=code,
                location=location,
                phone=phone or '',
                email=email or '',
                manager=manager,
                is_active=True
            )
            
            # Redirect to manage branches
            from django.shortcuts import redirect
            return redirect('dashboard:manage_branches')
            
        except Exception as e:
            return render(request, 'dashboard/branch_form.html', {
                'error': f'Error creating branch: {str(e)}',
                'managers': User.objects.filter(role='manager'),
            })
    
    context = {
        'managers': User.objects.filter(role='manager'),
    }
    return render(request, 'dashboard/branch_form.html', context)


# Admin Branch Management Views

@login_required
def admin_branches_list(request):
    """Admin view: List all branches with filtering and pagination"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    branches = Branch.objects.all().order_by('name')
    
    # Search by name, code, or location
    search_query = request.GET.get('search', '')
    if search_query:
        branches = branches.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'active':
            branches = branches.filter(is_active=True)
        elif status_filter == 'inactive':
            branches = branches.filter(is_active=False)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(branches, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'branches': page_obj.object_list,
        'total_branches': branches.count(),
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/admin_branches_list.html', context)


@login_required
def admin_branch_detail(request, branch_id):
    """Admin view: Display branch details and statistics"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Branch not found'})
    
    # Get branch statistics
    officers = User.objects.filter(
        role='loan_officer',
        officer_assignment__branch=branch.name
    )
    
    groups = BorrowerGroup.objects.filter(branch=branch.name)
    
    # Calculate client count
    clients_count = sum(g.member_count for g in groups)
    
    # Get loans for this branch
    loans = Loan.objects.filter(
        loan_officer__officer_assignment__branch=branch.name
    )
    
    total_disbursed = loans.filter(
        status__in=['active', 'completed', 'disbursed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    active_loans = loans.filter(status='active').count()
    
    context = {
        'branch': branch,
        'officers_count': officers.count(),
        'officers': officers,
        'groups_count': groups.count(),
        'groups': groups,
        'clients_count': clients_count,
        'total_disbursed': total_disbursed,
        'active_loans': active_loans,
    }
    
    return render(request, 'dashboard/admin_branch_detail.html', context)


@login_required
def admin_branch_create(request):
    """Admin view: Create a new branch"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            location = request.POST.get('location')
            phone = request.POST.get('phone', '')
            email = request.POST.get('email', '')
            manager_id = request.POST.get('manager')
            
            # Validate required fields
            if not all([name, code, location]):
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Name, code, and location are required',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if branch name already exists
            if Branch.objects.filter(name=name).exists():
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Branch name already exists',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if branch code already exists
            if Branch.objects.filter(code=code).exists():
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Branch code already exists',
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Get manager if provided
            manager = None
            if manager_id:
                try:
                    manager = User.objects.get(id=manager_id, role='manager')
                except User.DoesNotExist:
                    return render(request, 'dashboard/admin_branch_form.html', {
                        'error': 'Invalid manager selected',
                        'managers': User.objects.filter(role='manager'),
                    })
            
            # Create branch
            branch = Branch.objects.create(
                name=name,
                code=code,
                location=location,
                phone=phone,
                email=email,
                manager=manager,
                is_active=True
            )
            
            # Log creation in AdminAuditLog
            AdminAuditLog.objects.create(
                admin_user=user,
                action='branch_create',
                affected_branch=branch,
                description=f'Created branch: {name} ({code})',
                new_value=f'Branch: {name}, Code: {code}, Location: {location}'
            )
            
            # Redirect to branch detail
            from django.shortcuts import redirect
            return redirect('dashboard:admin_branch_detail', branch_id=branch.id)
            
        except Exception as e:
            return render(request, 'dashboard/admin_branch_form.html', {
                'error': f'Error creating branch: {str(e)}',
                'managers': User.objects.filter(role='manager'),
            })
    
    context = {
        'managers': User.objects.filter(role='manager'),
    }
    return render(request, 'dashboard/admin_branch_form.html', context)


@login_required
def admin_branch_edit(request, branch_id):
    """Admin view: Edit branch details"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Branch not found'})
    
    if request.method == 'POST':
        try:
            old_values = {
                'name': branch.name,
                'code': branch.code,
                'location': branch.location,
                'phone': branch.phone,
                'email': branch.email,
                'manager': str(branch.manager) if branch.manager else 'None',
            }
            
            name = request.POST.get('name')
            code = request.POST.get('code')
            location = request.POST.get('location')
            phone = request.POST.get('phone', '')
            email = request.POST.get('email', '')
            manager_id = request.POST.get('manager')
            
            # Validate required fields
            if not all([name, code, location]):
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Name, code, and location are required',
                    'branch': branch,
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if new name already exists (excluding current branch)
            if name != branch.name and Branch.objects.filter(name=name).exists():
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Branch name already exists',
                    'branch': branch,
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Check if new code already exists (excluding current branch)
            if code != branch.code and Branch.objects.filter(code=code).exists():
                return render(request, 'dashboard/admin_branch_form.html', {
                    'error': 'Branch code already exists',
                    'branch': branch,
                    'managers': User.objects.filter(role='manager'),
                })
            
            # Get manager if provided
            manager = None
            if manager_id:
                try:
                    manager = User.objects.get(id=manager_id, role='manager')
                except User.DoesNotExist:
                    return render(request, 'dashboard/admin_branch_form.html', {
                        'error': 'Invalid manager selected',
                        'branch': branch,
                        'managers': User.objects.filter(role='manager'),
                    })
            
            # Update branch
            branch.name = name
            branch.code = code
            branch.location = location
            branch.phone = phone
            branch.email = email
            branch.manager = manager
            branch.save()
            
            # Log changes in AdminAuditLog
            new_values = {
                'name': branch.name,
                'code': branch.code,
                'location': branch.location,
                'phone': branch.phone,
                'email': branch.email,
                'manager': str(branch.manager) if branch.manager else 'None',
            }
            
            changes = []
            for key in old_values:
                if old_values[key] != new_values[key]:
                    changes.append(f'{key}: {old_values[key]} → {new_values[key]}')
            
            if changes:
                AdminAuditLog.objects.create(
                    admin_user=user,
                    action='branch_update',
                    affected_branch=branch,
                    description=f'Updated branch: {branch.name}',
                    old_value=str(old_values),
                    new_value=str(new_values)
                )
            
            # Redirect to branch detail
            from django.shortcuts import redirect
            return redirect('dashboard:admin_branch_detail', branch_id=branch.id)
            
        except Exception as e:
            return render(request, 'dashboard/admin_branch_form.html', {
                'error': f'Error updating branch: {str(e)}',
                'branch': branch,
                'managers': User.objects.filter(role='manager'),
            })
    
    context = {
        'branch': branch,
        'managers': User.objects.filter(role='manager'),
        'is_edit': True,
    }
    return render(request, 'dashboard/admin_branch_form.html', context)


@login_required
def admin_branch_deactivate(request, branch_id):
    """Admin view: Deactivate a branch"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        branch = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Branch not found'})
    
    if request.method == 'POST':
        try:
            # Get existing assignments
            officers = User.objects.filter(
                role='loan_officer',
                officer_assignment__branch=branch.name
            )
            
            groups = BorrowerGroup.objects.filter(branch=branch.name)
            
            # Deactivate branch
            branch.is_active = False
            branch.save()
            
            # Log deactivation
            AdminAuditLog.objects.create(
                admin_user=user,
                action='branch_delete',
                affected_branch=branch,
                description=f'Deactivated branch: {branch.name}',
                old_value=f'is_active: True',
                new_value=f'is_active: False'
            )
            
            # Redirect to branches list
            from django.shortcuts import redirect
            return redirect('dashboard:admin_branches_list')
            
        except Exception as e:
            return render(request, 'dashboard/admin_branch_deactivate_confirm.html', {
                'error': f'Error deactivating branch: {str(e)}',
                'branch': branch,
            })
    
    # Get existing assignments to warn admin
    officers = User.objects.filter(
        role='loan_officer',
        officer_assignment__branch=branch.name
    )
    
    groups = BorrowerGroup.objects.filter(branch=branch.name)
    
    context = {
        'branch': branch,
        'officers_count': officers.count(),
        'groups_count': groups.count(),
    }
    return render(request, 'dashboard/admin_branch_deactivate_confirm.html', context)


# Admin Officer Transfer Views

@login_required
def admin_officers_list(request):
    """Admin view: List all loan officers and managers with details"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    officers = User.objects.filter(role__in=['loan_officer', 'manager']).order_by('first_name', 'last_name')
    
    # Search by name, email, or username
    search_query = request.GET.get('search', '')
    if search_query:
        officers = officers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        officers = officers.filter(role=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'active':
            officers = officers.filter(is_active=True)
        elif status_filter == 'inactive':
            officers = officers.filter(is_active=False)
    
    # Filter by branch (for loan officers)
    branch_filter = request.GET.get('branch')
    if branch_filter:
        officers = officers.filter(officer_assignment__branch=branch_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(officers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get branches for filter dropdown
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'officers': page_obj.object_list,
        'total_officers': officers.count(),
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'branches': branches,
    }
    
    return render(request, 'dashboard/admin_officers_list.html', context)


@login_required
def admin_officer_transfer(request):
    """Admin view: Transfer a loan officer to a different branch"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    # Get officer_id from query string if provided
    selected_officer_id = request.GET.get('officer_id')
    selected_officer = None
    if selected_officer_id:
        try:
            selected_officer = User.objects.get(id=selected_officer_id, role='loan_officer')
        except User.DoesNotExist:
            pass
    
    if request.method == 'POST':
        officer_id = request.POST.get('officer_id')
        new_branch = request.POST.get('new_branch')
        reason = request.POST.get('reason')
        
        try:
            officer = User.objects.get(id=officer_id, role='loan_officer')
            # Update officer's branch assignment
            if hasattr(officer, 'officer_assignment'):
                officer.officer_assignment.branch = new_branch
                officer.officer_assignment.save()
            
            messages.success(request, f'{officer.full_name} has been transferred to {new_branch}')
        except User.DoesNotExist:
            messages.error(request, 'Officer not found')
        
        return redirect('dashboard:admin_officers_list')
    
    officers = User.objects.filter(role='loan_officer')
    branches = Branch.objects.all()
    
    context = {
        'officers': officers,
        'branches': branches,
        'selected_officer': selected_officer,
    }
    
    return render(request, 'dashboard/admin/officer_transfer.html', context)


@login_required
def admin_transfer_history(request):
    """Admin view: Display all officer transfers with dates, reasons, affected groups"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    from clients.models import OfficerTransferLog
    transfers = OfficerTransferLog.objects.all().order_by('-timestamp')
    
    # Search by officer name
    search_query = request.GET.get('search', '')
    if search_query:
        transfers = transfers.filter(
            Q(officer__first_name__icontains=search_query) |
            Q(officer__last_name__icontains=search_query)
        )
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        transfers = transfers.filter(timestamp__gte=start_date)
    if end_date:
        transfers = transfers.filter(timestamp__lte=end_date)
    
    # Filter by branch
    branch_filter = request.GET.get('branch')
    if branch_filter:
        transfers = transfers.filter(
            Q(previous_branch=branch_filter) | Q(new_branch=branch_filter)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transfers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'transfers': page_obj.object_list,
        'total_transfers': transfers.count(),
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'branch_filter': branch_filter,
        'branches': branches,
    }
    
    return render(request, 'dashboard/admin_transfer_history.html', context)


# Admin Client Transfer Views

@login_required
def admin_client_transfer(request):
    """Admin view: Transfer a client to a different group"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            client_id = request.POST.get('client_id')
            destination_group_id = request.POST.get('destination_group')
            reason = request.POST.get('reason')
            
            # Validate required fields
            if not client_id or not destination_group_id or not reason:
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': 'Client, destination group, and reason are required',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Get client
            try:
                client = User.objects.get(id=client_id, role='borrower')
            except User.DoesNotExist:
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': 'Client not found',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Get destination group
            try:
                dest_group = BorrowerGroup.objects.get(id=destination_group_id)
            except BorrowerGroup.DoesNotExist:
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': 'Destination group not found',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Validate destination group is active
            if not dest_group.is_active:
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': 'Destination group is not active',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Validate destination group is not at capacity
            if dest_group.is_full:
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': f'Destination group is at capacity ({dest_group.member_count}/{dest_group.max_members})',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Get current group membership
            try:
                current_membership = GroupMembership.objects.get(borrower=client, is_active=True)
                previous_group = current_membership.group
            except GroupMembership.DoesNotExist:
                previous_group = None
            
            # Check for active loans
            active_loans = Loan.objects.filter(borrower=client, status='active')
            if active_loans.exists():
                return render(request, 'dashboard/admin_client_transfer_form.html', {
                    'error': f'Client has {active_loans.count()} active loan(s). Cannot transfer client with active loans.',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                    'active_loans': active_loans,
                })
            
            # Deactivate current membership if exists
            if previous_group:
                current_membership.is_active = False
                current_membership.save()
            
            # Create new membership
            new_membership = GroupMembership.objects.create(
                borrower=client,
                group=dest_group,
                is_active=True,
                added_by=user
            )
            
            # Create ClientTransferLog
            from clients.models import ClientTransferLog
            ClientTransferLog.objects.create(
                client=client,
                previous_group=previous_group,
                new_group=dest_group,
                reason=reason,
                performed_by=user
            )
            
            # Create AdminAuditLog
            AdminAuditLog.objects.create(
                admin_user=user,
                action='client_transfer',
                affected_user=client,
                affected_group=dest_group,
                description=f'Transferred client {client.full_name} from {previous_group.name if previous_group else "no group"} to {dest_group.name}',
                old_value=f'group: {previous_group.name if previous_group else "none"}',
                new_value=f'group: {dest_group.name}'
            )
            
            # Redirect to transfer history
            from django.shortcuts import redirect
            return redirect('dashboard:admin_client_transfer_history')
            
        except Exception as e:
            return render(request, 'dashboard/admin_client_transfer_form.html', {
                'error': f'Error transferring client: {str(e)}',
                'clients': User.objects.filter(role='borrower'),
                'groups': BorrowerGroup.objects.filter(is_active=True),
            })
    
    context = {
        'clients': User.objects.filter(role='borrower'),
        'groups': BorrowerGroup.objects.filter(is_active=True),
    }
    return render(request, 'dashboard/admin_client_transfer_form.html', context)


@login_required
def admin_client_transfer_history(request):
    """Admin view: Display all client transfers with dates, reasons, affected groups"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    from clients.models import ClientTransferLog
    transfers = ClientTransferLog.objects.all().order_by('-timestamp')
    
    # Search by client name
    search_query = request.GET.get('search', '')
    if search_query:
        transfers = transfers.filter(
            Q(client__first_name__icontains=search_query) |
            Q(client__last_name__icontains=search_query)
        )
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        transfers = transfers.filter(timestamp__gte=start_date)
    if end_date:
        transfers = transfers.filter(timestamp__lte=end_date)
    
    # Filter by group
    group_filter = request.GET.get('group')
    if group_filter:
        transfers = transfers.filter(
            Q(previous_group_id=group_filter) | Q(new_group_id=group_filter)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transfers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get groups for filter
    groups = BorrowerGroup.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'transfers': page_obj.object_list,
        'total_transfers': transfers.count(),
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'group_filter': group_filter,
        'groups': groups,
    }
    
    return render(request, 'dashboard/admin_client_transfer_history.html', context)


# Admin Group Assignment Override Views

@login_required
def admin_override_assignment(request):
    """Admin view: Override or correct group assignments for clients"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method == 'POST':
        try:
            client_id = request.POST.get('client_id')
            destination_group_id = request.POST.get('destination_group')
            override_reason = request.POST.get('override_reason')
            
            # Validate required fields
            if not client_id or not destination_group_id or not override_reason:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': 'Client, destination group, and reason are required',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Get client
            try:
                client = User.objects.get(id=client_id, role='borrower')
            except User.DoesNotExist:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': 'Client not found',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Get destination group
            try:
                dest_group = BorrowerGroup.objects.get(id=destination_group_id)
            except BorrowerGroup.DoesNotExist:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': 'Destination group not found',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Validate destination group is active
            if not dest_group.is_active:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': 'Destination group is not active',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Validate destination group is not at capacity
            if dest_group.is_full:
                return render(request, 'dashboard/admin_override_assignment_form.html', {
                    'error': f'Destination group is at capacity ({dest_group.member_count}/{dest_group.max_members})',
                    'clients': User.objects.filter(role='borrower'),
                    'groups': BorrowerGroup.objects.filter(is_active=True),
                })
            
            # Get current group membership
            try:
                current_membership = GroupMembership.objects.get(borrower=client, is_active=True)
                previous_group = current_membership.group
            except GroupMembership.DoesNotExist:
                previous_group = None
            
            # Deactivate current membership if exists
            if previous_group:
                current_membership.is_active = False
                current_membership.save()
            
            # Create new membership
            new_membership = GroupMembership.objects.create(
                borrower=client,
                group=dest_group,
                is_active=True,
                added_by=user
            )
            
            # Create AdminAuditLog with override reason
            AdminAuditLog.objects.create(
                admin_user=user,
                action='override_assignment',
                affected_user=client,
                affected_group=dest_group,
                description=f'Overrode assignment for {client.full_name}: {previous_group.name if previous_group else "no group"} → {dest_group.name}',
                old_value=f'group: {previous_group.name if previous_group else "none"}',
                new_value=f'group: {dest_group.name}, reason: {override_reason}'
            )
            
            # Redirect to success page
            from django.shortcuts import redirect
            return redirect('dashboard:admin_branches_list')
            
        except Exception as e:
            return render(request, 'dashboard/admin_override_assignment_form.html', {
                'error': f'Error overriding assignment: {str(e)}',
                'clients': User.objects.filter(role='borrower'),
                'groups': BorrowerGroup.objects.filter(is_active=True),
            })
    
    context = {
        'clients': User.objects.filter(role='borrower'),
        'groups': BorrowerGroup.objects.filter(is_active=True),
    }
    return render(request, 'dashboard/admin_override_assignment_form.html', context)


# Admin High-Value Loan Approval Views

@login_required
def admin_pending_approvals(request):
    """Admin view: Display all pending high-value loans awaiting approval"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    from clients.models import LoanApprovalQueue
    pending_loans = LoanApprovalQueue.objects.filter(status='pending').order_by('-submitted_date')
    
    # Search by borrower name or loan ID
    search_query = request.GET.get('search', '')
    if search_query:
        pending_loans = pending_loans.filter(
            Q(loan__borrower__first_name__icontains=search_query) |
            Q(loan__borrower__last_name__icontains=search_query) |
            Q(loan__id__icontains=search_query)
        )
    
    # Filter by branch
    branch_filter = request.GET.get('branch')
    if branch_filter:
        pending_loans = pending_loans.filter(
            loan__loan_officer__officer_assignment__branch=branch_filter
        )
    
    # Filter by amount range
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if min_amount:
        pending_loans = pending_loans.filter(loan__principal_amount__gte=min_amount)
    if max_amount:
        pending_loans = pending_loans.filter(loan__principal_amount__lte=max_amount)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(pending_loans, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'pending_loans': page_obj.object_list,
        'total_pending': pending_loans.count(),
        'search_query': search_query,
        'branch_filter': branch_filter,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'branches': branches,
    }
    
    return render(request, 'dashboard/admin_pending_approvals.html', context)


@login_required
def admin_loan_approval_detail(request, loan_id):
    """Admin view: Display complete loan information for approval decision"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Loan not found'})
    
    # Get approval queue entry
    try:
        from clients.models import LoanApprovalQueue
        approval_queue = LoanApprovalQueue.objects.get(loan=loan)
    except:
        approval_queue = None
    
    # Get borrower details
    borrower = loan.borrower
    
    # Get security deposit
    try:
        from loans.models import SecurityDeposit
        security_deposit = SecurityDeposit.objects.get(loan=loan)
    except:
        security_deposit = None
    
    # Get group membership
    try:
        group_membership = GroupMembership.objects.get(borrower=borrower, is_active=True)
        group = group_membership.group
    except:
        group = None
    
    context = {
        'loan': loan,
        'approval_queue': approval_queue,
        'borrower': borrower,
        'security_deposit': security_deposit,
        'group': group,
    }
    
    return render(request, 'dashboard/admin_loan_approval_detail.html', context)


@login_required
def admin_loan_approve(request, loan_id):
    """Admin view: Approve a high-value loan"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method != 'POST':
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid request method'})
    
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Loan not found'})
    
    try:
        from clients.models import LoanApprovalQueue, ApprovalAuditLog
        
        reason = request.POST.get('reason', '')
        
        # Get approval queue entry
        approval_queue = LoanApprovalQueue.objects.get(loan=loan, status='pending')
        
        # Update approval queue
        approval_queue.status = 'approved'
        approval_queue.decided_by = user
        approval_queue.decision_date = timezone.now()
        approval_queue.decision_reason = reason
        approval_queue.save()
        
        # Update loan status to allow disbursement
        loan.status = 'approved'
        loan.save()
        
        # Create ApprovalAuditLog
        ApprovalAuditLog.objects.create(
            loan=loan,
            action='approved',
            performed_by=user,
            reason=reason,
            ip_address=get_client_ip(request)
        )
        
        # Create AdminAuditLog
        AdminAuditLog.objects.create(
            admin_user=user,
            action='loan_approve',
            affected_user=loan.borrower,
            description=f'Approved high-value loan {loan.id} for K{loan.principal_amount}',
            new_value=f'status: approved, reason: {reason}'
        )
        
        # Redirect to pending approvals
        from django.shortcuts import redirect
        return redirect('dashboard:admin_pending_approvals')
        
    except Exception as e:
        return render(request, 'dashboard/access_denied.html', {'message': f'Error approving loan: {str(e)}'})


@login_required
def admin_loan_reject(request, loan_id):
    """Admin view: Reject a high-value loan"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    if request.method != 'POST':
        return render(request, 'dashboard/access_denied.html', {'message': 'Invalid request method'})
    
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Loan not found'})
    
    try:
        from clients.models import LoanApprovalQueue, ApprovalAuditLog
        
        reason = request.POST.get('reason', '')
        
        if not reason:
            return render(request, 'dashboard/admin_loan_approval_detail.html', {
                'error': 'Rejection reason is required',
                'loan': loan,
            })
        
        # Get approval queue entry
        approval_queue = LoanApprovalQueue.objects.get(loan=loan, status='pending')
        
        # Update approval queue
        approval_queue.status = 'rejected'
        approval_queue.decided_by = user
        approval_queue.decision_date = timezone.now()
        approval_queue.decision_reason = reason
        approval_queue.save()
        
        # Update loan status to rejected
        loan.status = 'rejected'
        loan.save()
        
        # Create ApprovalAuditLog
        ApprovalAuditLog.objects.create(
            loan=loan,
            action='rejected',
            performed_by=user,
            reason=reason,
            ip_address=get_client_ip(request)
        )
        
        # Create AdminAuditLog
        AdminAuditLog.objects.create(
            admin_user=user,
            action='loan_reject',
            affected_user=loan.borrower,
            description=f'Rejected high-value loan {loan.id} for K{loan.principal_amount}',
            new_value=f'status: rejected, reason: {reason}'
        )
        
        # Redirect to pending approvals
        from django.shortcuts import redirect
        return redirect('dashboard:admin_pending_approvals')
        
    except Exception as e:
        return render(request, 'dashboard/access_denied.html', {'message': f'Error rejecting loan: {str(e)}'})


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Admin Company-Wide Loan Viewing

@login_required
def admin_all_loans(request):
    """Admin view: Display all loans across all branches"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    loans = Loan.objects.all().order_by('-created_at')
    
    # Search by borrower name or loan ID
    search_query = request.GET.get('search', '')
    if search_query:
        loans = loans.filter(
            Q(borrower__first_name__icontains=search_query) |
            Q(borrower__last_name__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Filter by branch
    branch_filter = request.GET.get('branch')
    if branch_filter:
        loans = loans.filter(loan_officer__officer_assignment__branch=branch_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        loans = loans.filter(status=status_filter)
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        loans = loans.filter(created_at__gte=start_date)
    if end_date:
        loans = loans.filter(created_at__lte=end_date)
    
    # Filter by amount range
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if min_amount:
        loans = loans.filter(principal_amount__gte=min_amount)
    if max_amount:
        loans = loans.filter(principal_amount__lte=max_amount)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(loans, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get branches and statuses for filters
    branches = Branch.objects.filter(is_active=True).order_by('name')
    statuses = Loan._meta.get_field('status').choices
    
    context = {
        'page_obj': page_obj,
        'loans': page_obj.object_list,
        'total_loans': loans.count(),
        'search_query': search_query,
        'branch_filter': branch_filter,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'branches': branches,
        'statuses': statuses,
    }
    
    return render(request, 'dashboard/admin_all_loans.html', context)


@login_required
def admin_loan_detail(request, loan_id):
    """Admin view: Display complete loan information"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        return render(request, 'dashboard/access_denied.html', {'message': 'Loan not found'})
    
    # Get borrower
    borrower = loan.borrower
    
    # Get group membership
    try:
        group_membership = GroupMembership.objects.get(borrower=borrower, is_active=True)
        group = group_membership.group
    except:
        group = None
    
    # Get collections
    from payments.models import PaymentCollection
    collections = PaymentCollection.objects.filter(loan=loan).order_by('-collection_date')
    
    total_collected = collections.aggregate(total=Sum('collected_amount'))['total'] or 0
    
    # Get security deposit
    try:
        from loans.models import SecurityDeposit
        security_deposit = SecurityDeposit.objects.get(loan=loan)
    except:
        security_deposit = None
    
    context = {
        'loan': loan,
        'borrower': borrower,
        'group': group,
        'collections': collections,
        'total_collected': total_collected,
        'security_deposit': security_deposit,
    }
    
    return render(request, 'dashboard/admin_loan_detail.html', context)


@login_required
def admin_loan_statistics(request):
    """Admin view: Display portfolio metrics and branch comparison"""
    user = request.user
    
    if user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    # Get all loans
    all_loans = Loan.objects.all()
    
    # Total metrics
    total_disbursed = all_loans.filter(
        status__in=['active', 'completed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    active_loans = all_loans.filter(status='active').count()
    completed_loans = all_loans.filter(status='completed').count()
    defaulted_loans = all_loans.filter(status='defaulted').count()
    total_loans = all_loans.count()
    
    # Collection metrics
    from payments.models import PaymentCollection
    all_collections = PaymentCollection.objects.filter(status='completed')
    total_collected = all_collections.aggregate(total=Sum('collected_amount'))['total'] or 0
    
    if all_collections.exists():
        collection_rate = (all_collections.filter(is_partial=False).count() / all_collections.count() * 100)
    else:
        collection_rate = 0
    
    # Branch performance
    branches = Branch.objects.filter(is_active=True)
    branch_stats = []
    
    for branch in branches:
        branch_loans = all_loans.filter(
            loan_officer__officer_assignment__branch=branch.name
        )
        
        branch_disbursed = branch_loans.filter(
            status__in=['active', 'completed']
        ).aggregate(total=Sum('principal_amount'))['total'] or 0
        
        branch_active = branch_loans.filter(status='active').count()
        branch_defaulted = branch_loans.filter(status='defaulted').count()
        
        branch_collections = PaymentCollection.objects.filter(
            loan__loan_officer__officer_assignment__branch=branch.name,
            status='completed'
        )
        
        if branch_collections.exists():
            branch_rate = (branch_collections.filter(is_partial=False).count() / branch_collections.count() * 100)
        else:
            branch_rate = 0
        
        stats = {
            'name': branch.name,
            'total_disbursed': branch_disbursed,
            'active_loans': branch_active,
            'defaulted_loans': branch_defaulted,
            'collection_rate': round(branch_rate, 1),
        }
        branch_stats.append(stats)
    
    context = {
        'total_disbursed': total_disbursed,
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'defaulted_loans': defaulted_loans,
        'total_loans': total_loans,
        'total_collected': total_collected,
        'collection_rate': round(collection_rate, 1),
        'branch_stats': branch_stats,
        'average_loan_amount': total_disbursed / total_loans if total_loans > 0 else 0,
        'default_rate': (defaulted_loans / total_loans * 100) if total_loans > 0 else 0,
        'completion_rate': (completed_loans / total_loans * 100) if total_loans > 0 else 0,
        'outstanding_amount': total_disbursed - total_collected,
        'collection_percentage': (total_collected / total_disbursed * 100) if total_disbursed > 0 else 0,
    }
    
    return render(request, 'dashboard/admin_loan_statistics.html', context)



@login_required
def groups_permissions(request):
    """Groups and Permissions Management"""
    if request.user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    return render(request, 'dashboard/admin/groups_permissions.html')


@login_required
def system_reports(request):
    """System Reports View"""
    if request.user.role != 'admin':
        return render(request, 'dashboard/access_denied.html')
    
    return render(request, 'dashboard/admin/system_reports.html')


@login_required
def analytics(request):
    """Analytics Dashboard"""
    if request.user.role not in ['admin', 'manager']:
        return render(request, 'dashboard/access_denied.html')
    
    return render(request, 'dashboard/analytics.html')


@login_required
def loan_officer_document_verification(request):
    """Document verification dashboard for loan officers only"""
    user = request.user
    
    if user.role != 'loan_officer':
        return render(request, 'dashboard/access_denied.html')
    
    # Get branch from officer assignment
    branch = None
    try:
        if hasattr(user, 'officer_assignment') and user.officer_assignment:
            officer_assignment = user.officer_assignment
            branch_name = officer_assignment.branch
            # Create a simple branch object for template
            from collections import namedtuple
            Branch = namedtuple('Branch', ['name'])
            branch = Branch(name=branch_name)
        else:
            # If no officer assignment, create a default branch object
            from collections import namedtuple
            Branch = namedtuple('Branch', ['name'])
            branch = Branch(name='Unassigned')
    except Exception as e:
        print(f"Error getting officer assignment: {e}")
        from collections import namedtuple
        Branch = namedtuple('Branch', ['name'])
        branch = Branch(name='Unassigned')
    
    try:
        from documents.models import ClientVerification, ClientDocument
        from django.db.models import Q
        from accounts.models import User
        
        # Loan officer sees only their assigned clients
        branch_clients = User.objects.filter(
            Q(assigned_officer=user) | Q(group_memberships__group__assigned_officer=user),
            role='borrower'
        ).distinct()
        
        branch_client_ids = branch_clients.values_list('id', flat=True)
        
        # Get pending verifications for loan officers (documents submitted but not yet verified)
        pending_verifications = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status__in=['documents_submitted', 'documents_rejected']
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        # Get verified verifications
        verified_verifications = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status='verified'
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        # Get statistics
        total_clients = ClientVerification.objects.filter(client_id__in=branch_client_ids).count()
        verified_clients = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status='verified'
        ).count()
        pending_count = pending_verifications.count()
        
        # Get documents needing review
        documents_needing_review = ClientDocument.objects.filter(
            client_id__in=branch_client_ids,
            status='pending'
        ).select_related('client').order_by('-uploaded_at')
        
    except Exception as e:
        print(f"Error in loan officer document verification: {e}")
        pending_verifications = []
        verified_verifications = []
        documents_needing_review = []
        total_clients = 0
        verified_clients = 0
        pending_count = 0
    
    context = {
        'branch': branch,
        'pending_verifications': pending_verifications,
        'verified_verifications': verified_verifications,
        'documents_needing_review': documents_needing_review,
        'total_clients': total_clients,
        'verified_clients': verified_clients,
        'pending_count': pending_count,
        'verification_rate': round((verified_clients / total_clients * 100) if total_clients > 0 else 0, 1),
    }
    
    return render(request, 'dashboard/loan_officer_document_verification.html', context)


@login_required
def manager_document_verification(request):
    """Document verification dashboard for managers only"""
    user = request.user
    
    if user.role != 'manager':
        return render(request, 'dashboard/access_denied.html')
    
    # Get branch
    try:
        branch = user.managed_branch
        if not branch:
            return render(request, 'dashboard/access_denied.html', {
                'message': 'You have not been assigned to a branch. Please contact your administrator.'
            })
    except:
        return render(request, 'dashboard/access_denied.html', {
            'message': 'You have not been assigned to a branch. Please contact your administrator.'
        })
    
    try:
        from documents.models import ClientVerification, ClientDocument
        from accounts.models import User
        
        # Manager sees all clients in their branch
        branch_clients = User.objects.filter(
            role='borrower'
        ).distinct()
        
        branch_client_ids = branch_clients.values_list('id', flat=True)
        
        # Get pending document verifications
        pending_verifications = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status__in=['documents_submitted', 'documents_rejected']
        ).select_related('client').prefetch_related('client__documents').order_by('-updated_at')
        
        # Get recently verified documents
        recent_verifications = ClientDocument.objects.filter(
            client_id__in=branch_client_ids,
            status='approved'
        ).select_related('client', 'verified_by').order_by('-verification_date')[:10]
        
        # Get statistics
        total_clients = ClientVerification.objects.filter(client_id__in=branch_client_ids).count()
        verified_clients = ClientVerification.objects.filter(
            client_id__in=branch_client_ids,
            status='verified'
        ).count()
        pending_count = pending_verifications.count()
        
        # Get documents needing review
        documents_needing_review = ClientDocument.objects.filter(
            client_id__in=branch_client_ids,
            status='pending'
        ).select_related('client').order_by('-uploaded_at')
        
    except Exception as e:
        print(f"Error in document verification: {e}")
        pending_verifications = []
        recent_verifications = []
        documents_needing_review = []
        total_clients = 0
        verified_clients = 0
        pending_count = 0
    
    context = {
        'branch': branch,
        'user_role': 'manager',
        'pending_verifications': pending_verifications,
        'recent_verifications': recent_verifications,
        'documents_needing_review': documents_needing_review,
        'total_clients': total_clients,
        'verified_clients': verified_clients,
        'pending_count': pending_count,
        'verification_rate': round((verified_clients / total_clients * 100) if total_clients > 0 else 0, 1),
    }
    
    return render(request, 'dashboard/manager_document_verification.html', context)
