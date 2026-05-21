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
                            from clients.models import OfficeAssignment
                            manager_branch = OfficeAssignment.objects.filter(
                                officer=request.user
                            ).first()
                            officer_branch = OfficeAssignment.objects.filter(
                                officer=acting_as_officer
                            ).first()
                            
                            if manager_branch and officer_branch:
                                if manager_branch.branch == officer_branch.branch:
                                    request.acting_as_officer = acting_as_officer
                                else:
                                    # Different branch - clear session
                                    del request.session['acting_as_officer_id']
                        else:
                            # Admin can act as any officer
                            request.acting_as_officer = acting_as_officer
                    else:
                        # Not a manager/admin - clear session
                        del request.session['acting_as_officer_id']
                        
                except User.DoesNotExist:
                    # Officer not found - clear session
                    del request.session['acting_as_officer_id']
            else:
                request.acting_as_officer = None
        
        return None
