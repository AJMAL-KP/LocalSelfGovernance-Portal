from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from lsg.forms.auth import RegistrationForm, LoginForm, UserProfileForm, EmailChangeForm, CustomPasswordChangeForm
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

from lsg.views.content import get_ward_members, can_user_manage_post
from django.utils import timezone

@login_required(login_url='login')
@never_cache
def profile_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    
    # Initialize form
    form = UserProfileForm(instance=user)
    show_edit_modal = False
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload' and request.FILES.get('profile_picture'):
            if user.profile_picture:
                user.profile_picture.delete(save=False)
            user.profile_picture = request.FILES['profile_picture']
            user.save()
            messages.success(request, "Profile picture uploaded successfully.")
            return redirect('profile')
        elif action == 'delete':
            if user.profile_picture:
                user.profile_picture.delete(save=True)
                messages.success(request, "Profile picture removed.")
            return redirect('profile')
        elif action == 'update_profile':
            form = UserProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect('profile')
            else:
                show_edit_modal = True

    user_posts = user.posts.all().order_by('-created_at')
    for post in user_posts:
        post.can_manage = can_user_manage_post(user, post)

    return render(request, 'lsg/auth/profile.html', {
        'user': user,
        'profile_form': form,
        'show_edit_modal': show_edit_modal,
        'user_posts': user_posts,
        'ward_members': get_ward_members(user)
    })


@login_required(login_url='login')
@never_cache
def settings_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    
    # Initialize forms
    email_form = EmailChangeForm(instance=user)
    active_form = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_email':
            active_form = 'email'
            email_form = EmailChangeForm(request.POST, instance=user)
            password_form = CustomPasswordChangeForm(user=user)
            if email_form.is_valid():
                new_user = email_form.save(commit=False)
                new_user.username = new_user.email
                new_user.save()
                messages.success(request, "Email address updated successfully.")
                return redirect('settings')
                
        elif action == 'change_password':
            active_form = 'password'
            password_form = CustomPasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                updated_user = password_form.save(commit=False)
                updated_user.password_changed_at = timezone.now()
                updated_user.save()
                update_session_auth_hash(request, updated_user)
                messages.success(request, "Password changed successfully.")
                return redirect('settings')
            # If invalid, email_form needs to be re-initialized
            email_form = EmailChangeForm(instance=user)
    else:
        password_form = CustomPasswordChangeForm(user=user)
        
    return render(request, 'lsg/auth/settings.html', {
        'user': user,
        'email_form': email_form,
        'password_form': password_form,
        'active_form': active_form,
        'ward_members': get_ward_members(user)
    })


