"""
Hierarchical drill-down views for Loans
Branch → Officer → Group → Client
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from collections import defaultdict

from loans.models import Loan
from clients.models import Branch, BorrowerGroup
from accounts.models import User


def _get_base_loan_queryset(user):
    """Get base loan queryset based on user role"""
    qs = Loan.objects.select_related(
        'borrower', 'loan_officer', 'loan_officer__officer_assignment'
    )
    
    if user.role == 'loan_officer':
        from django.db.models import Q
        qs = qs.filter(
            Q(loan_officer=user) |
            Q(borrower__group_memberships__group__assigned_officer=user)
        ).distinct()
    elif user.role == 'manager':
        try:
            branch = user.managed_branch
            qs = qs.filter(
                loan_officer__officer_assignment__branch__iexact=branch.name
            ).distinct()
        except:
            return Loan.objects.none()
    # admin sees all
    
    return qs


@login_required
def loans_hierarchical(request):
    """
    Hierarchical drill-down for loans: Branch → Officer → Group → Client
    Role-based access:
    - Admin: Branch → Officer → Group → Client
    - Manager: Officer → Group → Client (auto-filtered to their branch)
    - Loan Officer: Group → Client (auto-filtered to their assignments)
    """
    user = request.user
    
    # Determine starting level based on role
    if user.role == 'admin':
        default_level = 'branch'
    elif user.role == 'manager':
        default_level = 'officer'
    elif user.role == 'loan_officer':
        default_level = 'group'
    else:
        return render(request, 'dashboard/access_denied.html')
    
    # Get drill-down level parameters
    view_level = request.GET.get('level', default_level)
    branch_id = request.GET.get('branch_id')
    officer_id = request.GET.get('officer_id')
    group_id = request.GET.get('group_id')
    
    # Get base loan queryset
    loan_qs = _get_base_loan_queryset(user)
    
    # Build breadcrumb navigation
    breadcrumbs = []
    
    # LEVEL 1: BRANCH VIEW (Admin only)
    if view_level == 'branch' and user.role == 'admin':
        breadcrumbs = [{'name': 'All Branches', 'url': '?level=branch'}]
        
        branch_data = defaultdict(lambda: {
            'branch_name': None,
            'branch_id': None,
            'total_loans': 0,
            'total_amount': 0,
            'total_outstanding': 0,
        })
        
        for loan in loan_qs:
            if not loan.loan_officer:
                continue
            
            try:
                branch_name = loan.loan_officer.officer_assignment.branch
                branch_obj = Branch.objects.filter(name=branch_name).first()
                branch_key = branch_obj.id if branch_obj else 0
            except:
                branch_name = 'No Branch'
                branch_key = 0
            
            if branch_data[branch_key]['branch_name'] is None:
                branch_data[branch_key]['branch_name'] = branch_name
                branch_data[branch_key]['branch_id'] = branch_key
            
            branch_data[branch_key]['total_loans'] += 1
            branch_data[branch_key]['total_amount'] += loan.principal_amount or 0
            branch_data[branch_key]['total_outstanding'] += loan.balance_remaining or 0
        
        data_list = sorted(branch_data.values(), key=lambda x: x['branch_name'])
        grand_total_loans = sum(b['total_loans'] for b in data_list)
        grand_total_amount = sum(b['total_amount'] for b in data_list)
        grand_total_outstanding = sum(b['total_outstanding'] for b in data_list)
        
        return render(request, 'loans/hierarchical.html', {
            'view_level': 'branch',
            'data_list': data_list,
            'grand_total_loans': grand_total_loans,
            'grand_total_amount': grand_total_amount,
            'grand_total_outstanding': grand_total_outstanding,
            'breadcrumbs': breadcrumbs,
        })
    
    # LEVEL 2: OFFICER VIEW
    elif view_level == 'officer':
        if user.role == 'admin':
            if branch_id:
                selected_branch = Branch.objects.filter(id=branch_id).first()
                if selected_branch:
                    breadcrumbs = [
                        {'name': 'All Branches', 'url': '?level=branch'},
                        {'name': selected_branch.name, 'url': f'?level=officer&branch_id={branch_id}'}
                    ]
                    loan_qs = loan_qs.filter(loan_officer__officer_assignment__branch=selected_branch.name)
            else:
                breadcrumbs = [{'name': 'All Officers', 'url': '?level=officer'}]
        elif user.role == 'manager':
            try:
                branch = user.managed_branch
                breadcrumbs = [{'name': f'{branch.name} Officers', 'url': '?level=officer'}]
            except:
                breadcrumbs = [{'name': 'Officers', 'url': '?level=officer'}]
        
        officer_data = defaultdict(lambda: {
            'officer': None,
            'officer_id': None,
            'total_loans': 0,
            'total_amount': 0,
            'total_outstanding': 0,
        })
        
        for loan in loan_qs:
            if not loan.loan_officer:
                continue
            
            officer = loan.loan_officer
            officer_key = officer.id
            
            if officer_data[officer_key]['officer'] is None:
                officer_data[officer_key]['officer'] = officer
                officer_data[officer_key]['officer_id'] = officer.id
            
            officer_data[officer_key]['total_loans'] += 1
            officer_data[officer_key]['total_amount'] += loan.principal_amount or 0
            officer_data[officer_key]['total_outstanding'] += loan.balance_remaining or 0
        
        data_list = sorted(officer_data.values(), key=lambda x: x['officer'].get_full_name() if x['officer'] else '')
        grand_total_loans = sum(o['total_loans'] for o in data_list)
        grand_total_amount = sum(o['total_amount'] for o in data_list)
        grand_total_outstanding = sum(o['total_outstanding'] for o in data_list)
        
        return render(request, 'loans/hierarchical.html', {
            'view_level': 'officer',
            'data_list': data_list,
            'grand_total_loans': grand_total_loans,
            'grand_total_amount': grand_total_amount,
            'grand_total_outstanding': grand_total_outstanding,
            'breadcrumbs': breadcrumbs,
            'branch_id': branch_id,
        })
    
    # LEVEL 3: GROUP VIEW
    elif view_level == 'group':
        if officer_id:
            selected_officer = User.objects.filter(id=officer_id).first()
            if selected_officer:
                # Rebuild breadcrumbs
                if user.role == 'admin':
                    try:
                        officer_branch = selected_officer.officer_assignment.branch
                        officer_branch_obj = Branch.objects.filter(name=officer_branch).first()
                        if officer_branch_obj:
                            breadcrumbs = [
                                {'name': 'All Branches', 'url': '?level=branch'},
                                {'name': officer_branch_obj.name, 'url': f'?level=officer&branch_id={officer_branch_obj.id}'},
                                {'name': selected_officer.get_full_name(), 'url': f'?level=group&officer_id={officer_id}'}
                            ]
                    except:
                        breadcrumbs = [
                            {'name': 'All Officers', 'url': '?level=officer'},
                            {'name': selected_officer.get_full_name(), 'url': f'?level=group&officer_id={officer_id}'}
                        ]
                elif user.role == 'manager':
                    breadcrumbs = [
                        {'name': 'Officers', 'url': '?level=officer'},
                        {'name': selected_officer.get_full_name(), 'url': f'?level=group&officer_id={officer_id}'}
                    ]
                
                loan_qs = loan_qs.filter(loan_officer=selected_officer)
        elif user.role == 'loan_officer':
            breadcrumbs = [{'name': 'My Groups', 'url': '?level=group'}]
        
        group_data = defaultdict(lambda: {
            'group': None,
            'group_id': None,
            'group_name': None,
            'member_count': 0,
            'capacity': 0,
            'total_loans': 0,
            'total_amount': 0,
            'total_outstanding': 0,
        })
        
        for loan in loan_qs:
            membership = loan.borrower.group_memberships.filter(is_active=True).first()
            group = membership.group if membership else None
            group_key = group.id if group else 0
            group_name = group.name if group else 'No Group'
            
            if group_data[group_key]['group'] is None:
                group_data[group_key]['group'] = group
                group_data[group_key]['group_id'] = group_key
                group_data[group_key]['group_name'] = group_name
                if group:
                    group_data[group_key]['member_count'] = group.active_member_count
                    group_data[group_key]['capacity'] = group.capacity or 0
            
            group_data[group_key]['total_loans'] += 1
            group_data[group_key]['total_amount'] += loan.principal_amount or 0
            group_data[group_key]['total_outstanding'] += loan.balance_remaining or 0
        
        data_list = sorted(group_data.values(), key=lambda x: x['group_name'])
        grand_total_loans = sum(g['total_loans'] for g in data_list)
        grand_total_amount = sum(g['total_amount'] for g in data_list)
        grand_total_outstanding = sum(g['total_outstanding'] for g in data_list)
        
        return render(request, 'loans/hierarchical.html', {
            'view_level': 'group',
            'data_list': data_list,
            'grand_total_loans': grand_total_loans,
            'grand_total_amount': grand_total_amount,
            'grand_total_outstanding': grand_total_outstanding,
            'breadcrumbs': breadcrumbs,
            'officer_id': officer_id,
        })
    
    # LEVEL 4: CLIENT VIEW
    elif view_level == 'client' and group_id:
        selected_group = BorrowerGroup.objects.filter(id=group_id).first()
        if selected_group:
            # Rebuild breadcrumbs
            if selected_group.assigned_officer:
                officer = selected_group.assigned_officer
                
                if user.role == 'admin':
                    try:
                        officer_branch = officer.officer_assignment.branch
                        officer_branch_obj = Branch.objects.filter(name=officer_branch).first()
                        if officer_branch_obj:
                            breadcrumbs = [
                                {'name': 'All Branches', 'url': '?level=branch'},
                                {'name': officer_branch_obj.name, 'url': f'?level=officer&branch_id={officer_branch_obj.id}'},
                                {'name': officer.get_full_name(), 'url': f'?level=group&officer_id={officer.id}'},
                                {'name': selected_group.name, 'url': f'?level=client&group_id={group_id}'}
                            ]
                    except:
                        breadcrumbs = [
                            {'name': 'All Officers', 'url': '?level=officer'},
                            {'name': officer.get_full_name(), 'url': f'?level=group&officer_id={officer.id}'},
                            {'name': selected_group.name, 'url': f'?level=client&group_id={group_id}'}
                        ]
                elif user.role == 'manager':
                    breadcrumbs = [
                        {'name': 'Officers', 'url': '?level=officer'},
                        {'name': officer.get_full_name(), 'url': f'?level=group&officer_id={officer.id}'},
                        {'name': selected_group.name, 'url': f'?level=client&group_id={group_id}'}
                    ]
                elif user.role == 'loan_officer':
                    breadcrumbs = [
                        {'name': 'My Groups', 'url': '?level=group'},
                        {'name': selected_group.name, 'url': f'?level=client&group_id={group_id}'}
                    ]
            
            loan_qs = loan_qs.filter(
                borrower__group_memberships__group=selected_group,
                borrower__group_memberships__is_active=True
            )
        
        # Get individual loans
        loans = loan_qs.distinct().order_by('-created_at')
        
        grand_total_loans = loans.count()
        grand_total_amount = loans.aggregate(total=Sum('principal_amount'))['total'] or 0
        grand_total_outstanding = loans.aggregate(total=Sum('balance_remaining'))['total'] or 0
        
        return render(request, 'loans/hierarchical.html', {
            'view_level': 'client',
            'loans': loans,
            'grand_total_loans': grand_total_loans,
            'grand_total_amount': grand_total_amount,
            'grand_total_outstanding': grand_total_outstanding,
            'breadcrumbs': breadcrumbs,
            'group_id': group_id,
        })
    
    # Default: redirect to appropriate starting level
    return redirect(f'?level={default_level}')
