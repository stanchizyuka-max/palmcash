"""
Hierarchical views for clients
- Loan Officers: Groups > Clients
- Managers: Loan Officers > Groups > Clients
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Prefetch
from accounts.models import User
from clients.models import BorrowerGroup, GroupMembership


@login_required
def hierarchical_clients_view(request):
    """
    Hierarchical view of clients based on user role:
    - Loan Officers: Groups > Clients
    - Managers: Loan Officers > Groups > Clients
    - Admins: Redirect to regular list
    """
    user = request.user
    
    if user.role == 'admin':
        # Admins use the regular flat list
        return redirect('accounts:user_list')
    
    elif user.role == 'loan_officer':
        # Loan Officer: Show their groups with clients
        groups = BorrowerGroup.objects.filter(
            assigned_officer=user,
            is_active=True
        ).prefetch_related(
            Prefetch(
                'members',
                queryset=GroupMembership.objects.filter(is_active=True).select_related('borrower'),
                to_attr='active_members'
            )
        ).annotate(
            member_count=Count('members', filter=Q(members__is_active=True))
        ).order_by('name')
        
        # Get clients directly assigned (not in groups)
        direct_clients = User.objects.filter(
            role='borrower',
            is_active=True,
            assigned_officer=user
        ).exclude(
            group_memberships__group__assigned_officer=user,
            group_memberships__is_active=True
        ).distinct()
        
        context = {
            'view_type': 'officer',
            'groups': groups,
            'direct_clients': direct_clients,
            'total_groups': groups.count(),
            'total_clients': sum(g.member_count for g in groups) + direct_clients.count(),
        }
        
        return render(request, 'clients/hierarchical_officer.html', context)
    
    elif user.role == 'manager':
        # Manager: Show loan officers > groups > clients in their branch
        try:
            branch = user.managed_branch
            branch_name = branch.name
        except:
            messages.error(request, 'No branch assigned to your account.')
            return redirect('dashboard:dashboard')
        
        # Get all loan officers in the branch
        from clients.models import OfficerAssignment
        officers = User.objects.filter(
            role='loan_officer',
            is_active=True,
            officer_assignment__branch=branch_name
        ).prefetch_related(
            Prefetch(
                'assigned_groups',
                queryset=BorrowerGroup.objects.filter(
                    is_active=True,
                    branch__iexact=branch_name
                ).prefetch_related(
                    Prefetch(
                        'members',
                        queryset=GroupMembership.objects.filter(is_active=True).select_related('borrower'),
                        to_attr='active_members'
                    )
                ).annotate(
                    member_count=Count('members', filter=Q(members__is_active=True))
                ),
                to_attr='active_groups'
            )
        ).annotate(
            group_count=Count('assigned_groups', filter=Q(assigned_groups__is_active=True, assigned_groups__branch__iexact=branch_name)),
            client_count=Count('assigned_groups__members', filter=Q(
                assigned_groups__is_active=True,
                assigned_groups__branch__iexact=branch_name,
                assigned_groups__members__is_active=True
            ), distinct=True)
        ).order_by('first_name', 'last_name')
        
        # Calculate totals
        total_officers = officers.count()
        total_groups = sum(o.group_count for o in officers)
        total_clients = sum(o.client_count for o in officers)
        
        context = {
            'view_type': 'manager',
            'officers': officers,
            'branch': branch,
            'total_officers': total_officers,
            'total_groups': total_groups,
            'total_clients': total_clients,
        }
        
        return render(request, 'clients/hierarchical_manager.html', context)
    
    else:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
