from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from lsg.models import User, Role

def get_ward_members(user):
    if user.is_authenticated and user.panchayat:
        return User.objects.filter(
            role=Role.WARD_MEMBER,
            panchayat=user.panchayat
        ).order_by('ward__number', 'name')
    return []

@login_required(login_url='login')
@never_cache
def dashboard_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
    return redirect('posts')

@login_required(login_url='login')
@never_cache
def posts_list_view(request):
    return render(request, 'lsg/content/posts.html', {
        'user': request.user,
        'ward_members': get_ward_members(request.user)
    })

@login_required(login_url='login')
@never_cache
def alerts_list_view(request):
    return render(request, 'lsg/content/alerts.html', {
        'user': request.user,
        'ward_members': get_ward_members(request.user)
    })

@login_required(login_url='login')
@never_cache
def documents_list_view(request):
    return render(request, 'lsg/content/documents.html', {
        'user': request.user,
        'ward_members': get_ward_members(request.user)
    })
