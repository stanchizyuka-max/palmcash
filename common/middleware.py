"""
Middleware for handling "Act As Officer" functionality
"""
from django.utils.deprecation import MiddlewareMixin


class ActAsOfficerMiddleware(MiddlewareMixin):
    """
    Middleware to track when a manager is acting as an officer.
    Stores the officer ID in session and makes it available in request.
    """
    
    def process_request(self, request):
        """Add acting_as_officer to request if set in session"""
        # Initialize to None for all requests
        request.acting_as_officer = None
        
        if request.user.is_authenticated:
            acting_as_officer_id = request.session.get('acting_as_officer_id')
            
            if acting_as_officer_id:
                # Manager is acting as an officer
                from accounts.models import User
                try:
                    acting_as_officer = User.objects.get(
                        id=acting_as_officer_id,
                        role='loan_officer',
                        is_active=True
                    )
                    
                    # Verify manager has permission (same branch)
                    if request.user.role in ['manager', 'admin']:
                        # For managers, check same branch
                        if request.user.role == 'manager':
                            from clients.models import OfficerAssignment
                            
                            # Get manager's branch from managed_branch relationship
                            try:
                                manager_branch_name = request.user.managed_branch.name
                            except:
                                manager_branch_name = None
                            
                            # Get officer's branch from OfficerAssignment
                            officer_assignment = OfficerAssignment.objects.filter(
                                officer=acting_as_officer
                            ).first()
                            officer_branch_name = officer_assignment.branch if officer_assignment else None
                            
                            # Check if both have branches and they match
                            if manager_branch_name and officer_branch_name and manager_branch_name == officer_branch_name:
                                request.acting_as_officer = acting_as_officer
                            else:
                                # Different branch or missing branch - clear session
                                if 'acting_as_officer_id' in request.session:
                                    del request.session['acting_as_officer_id']
                                if 'acting_as_officer_name' in request.session:
                                    del request.session['acting_as_officer_name']
                        else:
                            # Admin can act as any officer
                            request.acting_as_officer = acting_as_officer
                    else:
                        # Not a manager/admin - clear session
                        if 'acting_as_officer_id' in request.session:
                            del request.session['acting_as_officer_id']
                        if 'acting_as_officer_name' in request.session:
                            del request.session['acting_as_officer_name']
                        
                except User.DoesNotExist:
                    # Officer not found - clear session
                    if 'acting_as_officer_id' in request.session:
                        del request.session['acting_as_officer_id']
                    if 'acting_as_officer_name' in request.session:
                        del request.session['acting_as_officer_name']
        
        return None
