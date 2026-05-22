"""
Common views for acting as officer functionality
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from clients.models import OfficerAssignment


@login_required
def start_acting_as_officer(request, officer_id):
    """
    Start acting as a specific officer.
    Only managers and admins can do this.
    """
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, "You don't have permission to act as an officer.")
        return redirect('dashboard:dashboard')
    
    officer = get_object_or_404(User, id=officer_id, role='loan_officer', is_active=True)
    
    # Verify same branch for managers
    if request.user.role == 'manager':
        try:
            manager_branch_name = request.user.managed_branch.name
        except:
            messages.error(request, "You don't have a branch assignment.")
            return redirect('dashboard:dashboard')
        
        officer_assignment = OfficerAssignment.objects.filter(officer=officer).first()
        officer_branch_name = officer_assignment.branch if officer_assignment else None
        
        if not officer_branch_name:
            messages.error(request, f"{officer.get_full_name()} doesn't have a branch assignment.")
            return redirect('dashboard:dashboard')
        
        if manager_branch_name != officer_branch_name:
            messages.error(request, f"You can only act as officers in your branch ({manager_branch_name}).")
            return redirect('dashboard:dashboard')
    
    # Set session
    request.session['acting_as_officer_id'] = officer.id
    request.session['acting_as_officer_name'] = officer.get_full_name()
    request.session.modified = True  # Ensure session is saved
    
    messages.success(
        request, 
        f"You are now acting as {officer.get_full_name()}. All actions will be recorded on their behalf."
    )
    
    # Redirect to officer's dashboard
    next_url = request.GET.get('next', 'dashboard:loan_officer_dashboard')
    if next_url == 'dashboard:dashboard':
        # Force redirect to officer dashboard instead of generic dashboard
        next_url = 'dashboard:loan_officer_dashboard'
    return redirect(next_url)


@login_required
def stop_acting_as_officer(request):
    """
    Stop acting as an officer and return to normal mode.
    """
    if 'acting_as_officer_id' in request.session:
        officer_name = request.session.get('acting_as_officer_name', 'officer')
        del request.session['acting_as_officer_id']
        if 'acting_as_officer_name' in request.session:
            del request.session['acting_as_officer_name']
        
        messages.info(request, f"You are no longer acting as {officer_name}.")
    
    return redirect('dashboard:dashboard')
