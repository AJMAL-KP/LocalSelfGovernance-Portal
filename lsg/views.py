from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .forms import RegistrationForm, LoginForm
from .models import User, Role, Panchayat, Ward
from .decorators import panchayat_admin_required


def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else:
        form = RegistrationForm()
        
    # We pass all panchayats and wards to render the dynamic options client-side
    panchayats = Panchayat.objects.all().order_by('name')
    wards = Ward.objects.all().order_by('panchayat__name', 'number')
    
    return render(request, 'lsg/register.html', {
        'form': form,
        'panchanyats': panchayats,  # keep name compatibility if needed
        'panchayats': panchayats,
        'wards': wards
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            login(request, user)
            next_url = request.GET.get('next', 'profile')
            return redirect(next_url)
    else:
        form = LoginForm()
        
    return render(request, 'lsg/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
@never_cache
def dashboard_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
    return redirect('posts')

def get_ward_members(user):
    if user.is_authenticated and user.panchayat:
        return User.objects.filter(
            role=Role.WARD_MEMBER,
            panchayat=user.panchayat
        ).order_by('ward__number', 'name')
    return []

@login_required(login_url='login')
@never_cache
def posts_list_view(request):
    return render(request, 'lsg/posts.html', {
        'user': request.user,
        'ward_members': get_ward_members(request.user)
    })

@login_required(login_url='login')
@never_cache
def alerts_list_view(request):
    return render(request, 'lsg/alerts.html', {
        'user': request.user,
        'ward_members': get_ward_members(request.user)
    })

@login_required(login_url='login')
@never_cache
def documents_list_view(request):
    return render(request, 'lsg/documents.html', {
        'user': request.user,
        'ward_members': get_ward_members(request.user)
    })

@login_required(login_url='login')
@never_cache
def complaints_list_view(request):
    return render(request, 'lsg/complaints.html', {
        'user': request.user,
        'ward_members': get_ward_members(request.user)
    })

@panchayat_admin_required
@never_cache
def manage_users_view(request):
    # Fetch registered users in the admin's Panchayat
    users = []
    if request.user.panchayat:
        users = User.objects.filter(
            panchayat=request.user.panchayat
        ).exclude(id=request.user.id).exclude(is_superuser=True).order_by('role', 'name')
        
    return render(request, 'lsg/manage_users.html', {
        'users': users
    })


@login_required(login_url='login')
@never_cache
def profile_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload' and request.FILES.get('profile_picture'):
            # Delete the old picture file if it exists to keep storage clean
            if user.profile_picture:
                user.profile_picture.delete(save=False)
            user.profile_picture = request.FILES['profile_picture']
            user.save()
        elif action == 'delete':
            if user.profile_picture:
                user.profile_picture.delete(save=True)
        return redirect('profile')

    return render(request, 'lsg/profile.html', {
        'user': user,
        'ward_members': get_ward_members(user)
    })
