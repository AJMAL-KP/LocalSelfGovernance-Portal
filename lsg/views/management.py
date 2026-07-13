from django.shortcuts import render
from django.views.decorators.cache import never_cache
from lsg.decorators import panchayat_admin_required
from lsg.models import User

@panchayat_admin_required
@never_cache
def manage_users_view(request):
    users = []
    if request.user.panchayat:
        users = User.objects.filter(
            panchayat=request.user.panchayat
        ).exclude(id=request.user.id).exclude(is_superuser=True).order_by('role', 'name')
        
    return render(request, 'lsg/management/users.html', {
        'users': users
    })
