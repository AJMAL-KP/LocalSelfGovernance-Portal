from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from lsg.forms.auth import RegistrationForm, LoginForm
from lsg.models import User, Role, Panchayat, Ward

# We import get_ward_members lazily or dynamically to avoid circular import issues if any,
# or we can import it directly. Let's do it directly.
from lsg.views.content import get_ward_members

def register_view(request):
    if request.user.is_authenticated:
        return redirect('posts')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('posts')
    else:
        form = RegistrationForm()
        
    panchayats = Panchayat.objects.all().order_by('name')
    wards = Ward.objects.all().order_by('panchayat__name', 'number')
    
    return render(request, 'lsg/auth/register.html', {
        'form': form,
        'panchanyats': panchayats,
        'panchayats': panchayats,
        'wards': wards
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('posts')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            login(request, user)
            next_url = request.GET.get('next', 'posts')
            return redirect(next_url)
    else:
        form = LoginForm()
        
    return render(request, 'lsg/auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
@never_cache
def profile_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload' and request.FILES.get('profile_picture'):
            if user.profile_picture:
                user.profile_picture.delete(save=False)
            user.profile_picture = request.FILES['profile_picture']
            user.save()
        elif action == 'delete':
            if user.profile_picture:
                user.profile_picture.delete(save=True)
        return redirect('profile')

    return render(request, 'lsg/auth/profile.html', {
        'user': user,
        'ward_members': get_ward_members(user)
    })
