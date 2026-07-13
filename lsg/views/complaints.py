from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from lsg.views.content import get_ward_members

@login_required(login_url='login')
@never_cache
def complaints_list_view(request):
    return render(request, 'lsg/complaints/complaints.html', {
        'user': request.user,
        'ward_members': get_ward_members(request.user)
    })
