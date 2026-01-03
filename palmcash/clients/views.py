from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q
from .models import BorrowerGroup, GroupMembership, OfficerAssignment
from accounts.models import User


class GroupListView(LoginRequiredMixin, ListView):
    """View all borrower groups"""
    model = BorrowerGroup
    template_name = 'clients/group_list.html'
    context_object_name = 'groups'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            messages.error(request, 'Only staff members can access group management.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = BorrowerGroup.objects.all()
        
        # Loan officers only see their assigned groups
        if self.request.user.role == 'loan_officer':
            queryset = queryset.filter(assigned_officer=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_groups'] = self.get_queryset().count()
        context['active_groups'] = self.get_queryset().filter(is_active=True).count()
        return context


class GroupDetailView(LoginRequiredMixin, DetailView):
    """View group details and members"""
    model = BorrowerGroup
    template_name = 'clients/group_detail.html'
    context_object_name = 'group'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            messages.error(request, 'Only staff members can access group management.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = BorrowerGroup.objects.all()
        
        # Loan officers only see their assigned groups
        if self.request.user.role == 'loan_officer':
            queryset = queryset.filter(assigned_officer=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        
        # Get active members
        context['members'] = group.members.filter(is_active=True).select_related('borrower')
        context['inactive_members'] = group.members.filter(is_active=False).select_related('borrower')
        
        # Get available borrowers (not in this group)
        context['available_borrowers'] = User.objects.filter(
            role='borrower',
            is_active=True
        ).exclude(
            group_memberships__group=group,
            group_memberships__is_active=True
        )
        
        # Get group statistics
        from loans.models import Loan
        context['active_loans'] = Loan.objects.filter(
            borrower__in=[m.borrower for m in context['members']],
            status='active'
        ).count()
        
        return context


class GroupCreateView(LoginRequiredMixin, CreateView):
    """Create a new borrower group"""
    model = BorrowerGroup
    template_name = 'clients/group_form.html'
    form_class = None  # Will be set in get_form_class
    success_url = reverse_lazy('clients:group_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        # Check if user has permission to create groups
        if not (request.user.role in ['admin', 'manager', 'loan_officer'] or 
                request.user.has_perm('clients.can_create_group')):
            messages.error(request, 'You do not have permission to create groups.')
            return redirect('clients:group_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_class(self):
        from .forms import GroupForm
        return GroupForm
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # If loan officer is creating, auto-assign them as the officer
        if self.request.user.role == 'loan_officer' and not form.instance.assigned_officer:
            form.instance.assigned_officer = self.request.user
        
        messages.success(self.request, f'Group "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class GroupUpdateView(LoginRequiredMixin, UpdateView):
    """Update group details"""
    model = BorrowerGroup
    template_name = 'clients/group_form.html'
    form_class = None  # Will be set in get_form_class
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            messages.error(request, 'You do not have permission to edit groups.')
            return redirect('clients:group_list')
        
        # Loan officers can only edit their own groups
        if request.user.role == 'loan_officer':
            group = self.get_object()
            if group.assigned_officer != request.user:
                messages.error(request, 'You can only edit groups assigned to you.')
                return redirect('clients:group_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_class(self):
        from .forms import GroupForm
        return GroupForm
    
    def get_success_url(self):
        return reverse_lazy('clients:group_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Group "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


class AddMemberView(LoginRequiredMixin, View):
    """Add a borrower to a group"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            messages.error(request, 'You do not have permission to add members.')
            return redirect('clients:group_list')
        
        # Loan officers can only add members to their assigned groups
        if request.user.role == 'loan_officer':
            pk = kwargs.get('pk')
            group = get_object_or_404(BorrowerGroup, pk=pk)
            if group.assigned_officer != request.user:
                messages.error(request, 'You can only add members to groups assigned to you.')
                return redirect('clients:group_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        group = get_object_or_404(BorrowerGroup, pk=pk)
        borrower_id = request.POST.get('borrower_id')
        
        if not borrower_id:
            messages.error(request, 'Please select a borrower.')
            return redirect('clients:group_detail', pk=pk)
        
        borrower = get_object_or_404(User, pk=borrower_id, role='borrower')
        
        # Check if group is full
        if not group.can_add_member():
            messages.error(request, 'This group is full or inactive.')
            return redirect('clients:group_detail', pk=pk)
        
        # Check if already a member
        existing = GroupMembership.objects.filter(
            borrower=borrower,
            group=group,
            is_active=True
        ).exists()
        
        if existing:
            messages.warning(request, f'{borrower.full_name} is already a member of this group.')
            return redirect('clients:group_detail', pk=pk)
        
        # Add member
        GroupMembership.objects.create(
            borrower=borrower,
            group=group,
            added_by=request.user
        )
        
        # Update borrower's assigned officer
        borrower.assigned_officer = group.assigned_officer
        borrower.save(update_fields=['assigned_officer'])
        
        messages.success(request, f'{borrower.full_name} added to {group.name}!')
        return redirect('clients:group_detail', pk=pk)


class RemoveMemberView(LoginRequiredMixin, View):
    """Remove a borrower from a group"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            messages.error(request, 'You do not have permission to remove members.')
            return redirect('clients:group_list')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk, membership_id):
        group = get_object_or_404(BorrowerGroup, pk=pk)
        membership = get_object_or_404(GroupMembership, pk=membership_id, group=group)
        
        # Deactivate membership
        membership.deactivate()
        
        messages.success(request, f'{membership.borrower.full_name} removed from {group.name}.')
        return redirect('clients:group_detail', pk=pk)


class OfficerWorkloadView(LoginRequiredMixin, ListView):
    """View loan officer workload and assignments"""
    model = OfficerAssignment
    template_name = 'clients/officer_workload.html'
    context_object_name = 'officers'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'Only admins and managers can view officer workload.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Get all loan officers with their assignments
        officers = User.objects.filter(role='loan_officer').annotate(
            group_count=Count('managed_groups', filter=Q(managed_groups__is_active=True)),
            client_count=Count('assigned_clients', filter=Q(assigned_clients__role='borrower'))
        )
        return officers
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get officers without assignment settings
        all_officers = User.objects.filter(role='loan_officer')
        officers_with_settings = OfficerAssignment.objects.values_list('officer_id', flat=True)
        context['officers_without_settings'] = all_officers.exclude(id__in=officers_with_settings)
        
        return context


class AssignOfficerToGroupView(LoginRequiredMixin, View):
    """Assign or reassign a loan officer to a group"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'Only admins and managers can assign officers.')
            return redirect('clients:group_list')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, pk):
        group = get_object_or_404(BorrowerGroup, pk=pk)
        officer_id = request.POST.get('officer_id')
        
        if not officer_id:
            messages.error(request, 'Please select a loan officer.')
            return redirect('clients:group_detail', pk=pk)
        
        officer = get_object_or_404(User, pk=officer_id, role='loan_officer')
        
        # Check officer capacity
        try:
            assignment = OfficerAssignment.objects.get(officer=officer)
            if not assignment.can_accept_new_group and group.assigned_officer != officer:
                messages.warning(
                    request,
                    f'{officer.full_name} is at capacity. Assigning anyway (override).'
                )
        except OfficerAssignment.DoesNotExist:
            # Create default assignment settings
            OfficerAssignment.objects.create(officer=officer)
        
        # Assign officer
        old_officer = group.assigned_officer
        group.assigned_officer = officer
        group.save(update_fields=['assigned_officer'])
        
        # Update all active members' assigned officer
        for membership in group.members.filter(is_active=True):
            membership.borrower.assigned_officer = officer
            membership.borrower.save(update_fields=['assigned_officer'])
        
        if old_officer:
            messages.success(
                request,
                f'Group reassigned from {old_officer.full_name} to {officer.full_name}!'
            )
        else:
            messages.success(request, f'{officer.full_name} assigned to {group.name}!')
        
        return redirect('clients:group_detail', pk=pk)



class BorrowerListView(LoginRequiredMixin, ListView):
    """View all borrowers with filtering by loan officer's groups"""
    model = User
    template_name = 'clients/borrower_list.html'
    context_object_name = 'borrowers'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            messages.error(request, 'Only staff members can access borrower management.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = User.objects.filter(role='borrower', is_active=True)
        
        # Loan officers only see borrowers in their groups
        if self.request.user.role == 'loan_officer':
            # Get all groups assigned to this officer
            officer_groups = BorrowerGroup.objects.filter(
                assigned_officer=self.request.user,
                is_active=True
            )
            
            # Get borrowers who are members of these groups
            queryset = queryset.filter(
                group_memberships__group__in=officer_groups,
                group_memberships__is_active=True
            ).distinct()
        
        return queryset.order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_borrowers'] = self.get_queryset().count()
        
        # Add group information for loan officers
        if self.request.user.role == 'loan_officer':
            context['officer_groups'] = BorrowerGroup.objects.filter(
                assigned_officer=self.request.user,
                is_active=True
            )
        
        return context



class AssignClientToOfficerView(LoginRequiredMixin, View):
    """Assign a borrower client to a loan officer"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'Only admins and managers can assign clients.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, client_id):
        client = get_object_or_404(User, pk=client_id, role='borrower')
        officer_id = request.POST.get('officer_id')
        
        if not officer_id:
            messages.error(request, 'Please select a loan officer.')
            return redirect('accounts:user_detail', pk=client_id)
        
        officer = get_object_or_404(User, pk=officer_id, role='loan_officer')
        
        # Check if officer is accepting assignments
        try:
            assignment = OfficerAssignment.objects.get(officer=officer)
            if not assignment.is_accepting_assignments:
                messages.error(request, f'{officer.full_name} is not currently accepting new assignments.')
                return redirect('accounts:user_detail', pk=client_id)
            
            # Check officer capacity
            if not assignment.can_accept_new_client:
                messages.error(
                    request,
                    f'{officer.full_name} is at maximum capacity ({assignment.current_client_count}/{assignment.max_clients} clients). '
                    f'Please select a different officer.'
                )
                return redirect('accounts:user_detail', pk=client_id)
        except OfficerAssignment.DoesNotExist:
            # Create default assignment settings if not exists
            OfficerAssignment.objects.create(officer=officer)
        
        # Determine action type
        previous_officer = client.assigned_officer
        if previous_officer == officer:
            messages.warning(request, f'{client.full_name} is already assigned to {officer.full_name}.')
            return redirect('accounts:user_detail', pk=client_id)
        
        action = 'reassign' if previous_officer else 'assign'
        
        # Update client assignment
        client.assigned_officer = officer
        client.save(update_fields=['assigned_officer'])
        
        # Create audit log
        from .models import ClientAssignmentAuditLog
        ClientAssignmentAuditLog.objects.create(
            client=client,
            previous_officer=previous_officer,
            new_officer=officer,
            action=action,
            performed_by=request.user
        )
        
        if action == 'reassign':
            messages.success(
                request,
                f'{client.full_name} reassigned from {previous_officer.full_name} to {officer.full_name}!'
            )
        else:
            messages.success(request, f'{client.full_name} assigned to {officer.full_name}!')
        
        return redirect('accounts:user_detail', pk=client_id)


class UnassignClientFromOfficerView(LoginRequiredMixin, View):
    """Unassign a borrower client from their loan officer"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin']:
            messages.error(request, 'Only admins can unassign clients.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, client_id):
        client = get_object_or_404(User, pk=client_id, role='borrower')
        
        if not client.assigned_officer:
            messages.warning(request, f'{client.full_name} is not currently assigned to any officer.')
            return redirect('accounts:user_detail', pk=client_id)
        
        previous_officer = client.assigned_officer
        
        # Clear assignment
        client.assigned_officer = None
        client.save(update_fields=['assigned_officer'])
        
        # Create audit log
        from .models import ClientAssignmentAuditLog
        ClientAssignmentAuditLog.objects.create(
            client=client,
            previous_officer=previous_officer,
            new_officer=None,
            action='unassign',
            performed_by=request.user
        )
        
        messages.success(request, f'{client.full_name} unassigned from {previous_officer.full_name}.')
        return redirect('accounts:user_detail', pk=client_id)



class OfficerClientsListView(LoginRequiredMixin, ListView):
    """View all clients assigned to a specific loan officer"""
    model = User
    template_name = 'clients/officer_clients_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager', 'loan_officer']:
            messages.error(request, 'Only staff members can access client management.')
            return redirect('dashboard:home')
        
        # Loan officers can only view their own clients
        if request.user.role == 'loan_officer':
            officer_id = kwargs.get('officer_id')
            if int(officer_id) != request.user.id:
                messages.error(request, 'You can only view your own assigned clients.')
                return redirect('dashboard:home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        officer_id = self.kwargs.get('officer_id')
        officer = get_object_or_404(User, pk=officer_id, role='loan_officer')
        
        queryset = User.objects.filter(
            role='borrower',
            assigned_officer=officer,
            is_active=True
        )
        
        # Apply status filter
        status_filter = self.request.GET.get('status')
        if status_filter == 'inactive':
            queryset = User.objects.filter(
                role='borrower',
                assigned_officer=officer,
                is_active=False
            )
        
        # Apply sorting
        sort_by = self.request.GET.get('sort', 'name')
        if sort_by == 'balance':
            from django.db.models import Sum, Case, When, DecimalField
            from loans.models import Loan
            
            # Annotate with outstanding balance
            queryset = queryset.annotate(
                outstanding_balance=Sum(
                    Case(
                        When(
                            loans__status__in=['active', 'approved', 'disbursed'],
                            then='loans__principal_amount'
                        ),
                        default=0,
                        output_field=DecimalField()
                    )
                )
            ).order_by('-outstanding_balance')
        else:
            queryset = queryset.order_by('last_name', 'first_name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        officer_id = self.kwargs.get('officer_id')
        officer = get_object_or_404(User, pk=officer_id, role='loan_officer')
        
        context['officer'] = officer
        context['total_clients'] = self.get_queryset().count()
        
        # Get workload info
        try:
            assignment = OfficerAssignment.objects.get(officer=officer)
            context['workload_info'] = {
                'current_clients': assignment.current_client_count,
                'max_clients': assignment.max_clients,
                'workload_percentage': assignment.get_workload_percentage(),
            }
        except OfficerAssignment.DoesNotExist:
            context['workload_info'] = None
        
        # Add filter and sort options
        context['current_status'] = self.request.GET.get('status', 'active')
        context['current_sort'] = self.request.GET.get('sort', 'name')
        
        return context



class OfficerWorkloadDetailView(LoginRequiredMixin, DetailView):
    """View detailed workload information for a specific loan officer"""
    model = User
    template_name = 'clients/officer_workload_detail.html'
    context_object_name = 'officer'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin', 'manager']:
            messages.error(request, 'Only admins and managers can view officer workload.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return User.objects.filter(role='loan_officer')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        officer = self.get_object()
        
        # Get or create assignment settings
        try:
            assignment = OfficerAssignment.objects.get(officer=officer)
        except OfficerAssignment.DoesNotExist:
            assignment = OfficerAssignment.objects.create(officer=officer)
        
        context['assignment'] = assignment
        
        # Get groups and clients
        context['groups'] = BorrowerGroup.objects.filter(
            assigned_officer=officer,
            is_active=True
        ).order_by('name')
        
        context['clients'] = User.objects.filter(
            role='borrower',
            assigned_officer=officer,
            is_active=True
        ).order_by('last_name', 'first_name')
        
        # Calculate workload breakdown
        context['workload_breakdown'] = {
            'groups_count': assignment.current_group_count,
            'groups_max': assignment.max_groups,
            'groups_percentage': (assignment.current_group_count / assignment.max_groups * 100) if assignment.max_groups > 0 else 0,
            'clients_count': assignment.current_client_count,
            'clients_max': assignment.max_clients,
            'clients_percentage': (assignment.current_client_count / assignment.max_clients * 100) if assignment.max_clients > 0 else 0,
            'overall_percentage': assignment.get_workload_percentage(),
        }
        
        # Capacity warnings
        context['capacity_warnings'] = []
        if assignment.is_at_group_capacity:
            context['capacity_warnings'].append(f'Officer is at maximum group capacity ({assignment.current_group_count}/{assignment.max_groups})')
        if assignment.is_at_client_capacity:
            context['capacity_warnings'].append(f'Officer is at maximum client capacity ({assignment.current_client_count}/{assignment.max_clients})')
        if assignment.get_workload_percentage() >= 80:
            context['capacity_warnings'].append(f'Officer workload is at {assignment.get_workload_percentage():.0f}% capacity')
        
        return context



class UpdateOfficerCapacityView(LoginRequiredMixin, View):
    """Update loan officer capacity limits"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.role not in ['admin']:
            messages.error(request, 'Only admins can update officer capacity.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, officer_id):
        officer = get_object_or_404(User, pk=officer_id, role='loan_officer')
        
        try:
            assignment = OfficerAssignment.objects.get(officer=officer)
        except OfficerAssignment.DoesNotExist:
            assignment = OfficerAssignment.objects.create(officer=officer)
        
        # Get new capacity values
        try:
            max_groups = int(request.POST.get('max_groups', assignment.max_groups))
            max_clients = int(request.POST.get('max_clients', assignment.max_clients))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid capacity values provided.')
            return redirect('clients:officer_workload_detail', pk=officer_id)
        
        # Validate capacity limits
        if max_groups < 15:
            messages.error(request, 'Maximum groups must be at least 15.')
            return redirect('clients:officer_workload_detail', pk=officer_id)
        
        if max_clients < 1:
            messages.error(request, 'Maximum clients must be at least 1.')
            return redirect('clients:officer_workload_detail', pk=officer_id)
        
        # Check if update would exceed current assignments
        warnings = []
        if max_groups < assignment.current_group_count:
            warnings.append(f'Officer currently manages {assignment.current_group_count} groups, which exceeds the new limit of {max_groups}.')
        if max_clients < assignment.current_client_count:
            warnings.append(f'Officer currently manages {assignment.current_client_count} clients, which exceeds the new limit of {max_clients}.')
        
        if warnings:
            for warning in warnings:
                messages.warning(request, warning)
        
        # Update capacity
        assignment.max_groups = max_groups
        assignment.max_clients = max_clients
        assignment.save(update_fields=['max_groups', 'max_clients'])
        
        messages.success(
            request,
            f'Capacity limits updated for {officer.full_name}: {max_groups} groups, {max_clients} clients.'
        )
        return redirect('clients:officer_workload_detail', pk=officer_id)
