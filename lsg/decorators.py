from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from .models import Role

def role_required(*allowed_roles):
    """
    Decorator to restrict view access to specific user roles.
    If unauthorized, redirects the user to the posts feed with a warning message.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # If not logged in, redirect to login
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), 'login')
            
            # Superusers should access only Django Admin site
            if request.user.is_superuser:
                return redirect('admin:index')
            
            # Allow access if the user's role is in the allowed roles list
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # Redirect unauthorized users to their landing page with a message
            messages.warning(request, "You are not authorized to view that page.")
            return redirect('posts')
            
        return _wrapped_view
    return decorator

# Convenience decorators
def villager_required(view_func):
    return role_required(Role.VILLAGER)(view_func)

def ward_member_required(view_func):
    return role_required(Role.WARD_MEMBER)(view_func)

def panchayat_president_required(view_func):
    return role_required(Role.PANCHAYAT_PRESIDENT)(view_func)

# Backwards compatibility alias
panchayat_admin_required = panchayat_president_required

