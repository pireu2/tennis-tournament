from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import Http404

class PlayerRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict views to player users only"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_player()
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('accounts:profile')

class RefereeRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict views to referee users only"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_referee()
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('accounts:profile')

class OwnershipRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure users can only access their own resources"""
    # Override this in the view to define the owner check
    def get_owner(self):
        return None
    
    def test_func(self):
        owner = self.get_owner()
        return self.request.user.is_authenticated and (
            self.request.user == owner 
            or self.request.user.is_admin() # Admins can see all
        )
    
    def handle_no_permission(self):
        # Use 404 for privacy reasons instead of 403
        raise Http404("Resource not found")
