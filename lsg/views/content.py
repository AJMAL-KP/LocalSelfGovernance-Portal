from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from lsg.models import User, Role, Post, PostScope
from lsg.forms.content import PostForm

def get_ward_members(user):
    if user.is_authenticated and user.panchayat:
        return User.objects.filter(
            role=Role.WARD_MEMBER,
            panchayat=user.panchayat
        ).order_by('ward__number', 'name')
    return []

def get_panchayat_president(user):
    if user.is_authenticated and user.panchayat:
        return User.objects.filter(
            role=Role.PANCHAYAT_PRESIDENT,
            panchayat=user.panchayat
        ).first()
    return None

get_panchayat_admin = get_panchayat_president

def can_user_manage_post(user, post):
    if not user or not user.is_authenticated:
        return False
    if post.author == user:
        return True
    if user.role == Role.PANCHAYAT_PRESIDENT and user.panchayat and post.panchayat == user.panchayat and post.scope == PostScope.PANCHAYAT:
        return True
    return False

@login_required(login_url='login')
@never_cache
def dashboard_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
    return redirect('posts')

@login_required(login_url='login')
@never_cache
def posts_list_view(request):
    user = request.user
    
    # Base queryset filtering by user's Panchayat
    posts = Post.objects.filter(panchayat=user.panchayat)
    
    # Filter based on user's Ward if they have one
    if user.ward:
        posts = posts.filter(
            Q(scope=PostScope.PANCHAYAT) | Q(scope=PostScope.WARD, ward=user.ward)
        )
    else:
        # Fallback: only show Panchayat posts if they don't belong to a ward
        posts = posts.filter(scope=PostScope.PANCHAYAT)
        
    posts = posts.order_by('-created_at')
    
    # Paginate posts (20 per page)
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Annotate manage permissions for the UI
    for post in page_obj:
        post.can_manage = can_user_manage_post(user, post)

    return render(request, 'lsg/content/posts.html', {
        'user': user,
        'posts': page_obj,
        'page_obj': page_obj,
        'panchayat_president': get_panchayat_president(user),
        'ward_members': get_ward_members(user)
    })

@login_required(login_url='login')
@never_cache
def create_post_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    if user.role not in [Role.WARD_MEMBER, Role.PANCHAYAT_PRESIDENT]:
        messages.error(request, "Access Denied: You do not have permission to create posts.")
        return redirect('posts')
        
    next_param = request.GET.get('next') or request.POST.get('next') or ''
    redirect_target = 'profile' if next_param == 'profile' else 'posts'

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = user
            post.panchayat = user.panchayat
            if user.role == Role.WARD_MEMBER:
                post.scope = PostScope.WARD
                post.ward = user.ward
            else:
                # Panchayat President selects scope
                chosen_scope = form.cleaned_data.get('scope', PostScope.PANCHAYAT)
                post.scope = chosen_scope
                if chosen_scope == PostScope.WARD:
                    post.ward = user.ward
                else:
                    post.ward = None
            post.save()
            messages.success(request, "Post created successfully.")
            return redirect(redirect_target)
    else:
        form = PostForm(user=user)
        
    return render(request, 'lsg/content/post_form.html', {
        'form': form,
        'title': 'Create New Post',
        'is_edit': False,
        'next': next_param,
        'active_page': 'profile' if next_param == 'profile' else 'posts',
        'panchayat_president': get_panchayat_president(user),
        'ward_members': get_ward_members(user)
    })

@login_required(login_url='login')
@never_cache
def edit_post_view(request, post_id):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    post = get_object_or_404(Post, pk=post_id)
    
    next_param = request.GET.get('next') or request.POST.get('next') or ''
    redirect_target = 'profile' if next_param == 'profile' else 'posts'

    if not can_user_manage_post(user, post):
        messages.error(request, "Access Denied: You do not have permission to edit this post.")
        return redirect(redirect_target)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post, user=user)
        if form.is_valid():
            updated_post = form.save(commit=False)
            if user.role == Role.PANCHAYAT_PRESIDENT:
                chosen_scope = form.cleaned_data.get('scope', PostScope.PANCHAYAT)
                updated_post.scope = chosen_scope
                if chosen_scope == PostScope.WARD:
                    updated_post.ward = user.ward
                else:
                    updated_post.ward = None
            updated_post.save()
            messages.success(request, "Post updated successfully.")
            return redirect(redirect_target)
    else:
        form = PostForm(instance=post, user=user)
        
    return render(request, 'lsg/content/post_form.html', {
        'form': form,
        'title': 'Edit Post',
        'is_edit': True,
        'post': post,
        'next': next_param,
        'active_page': 'profile' if next_param == 'profile' else 'posts',
        'panchayat_president': get_panchayat_president(user),
        'ward_members': get_ward_members(user)
    })

@login_required(login_url='login')
@never_cache
def delete_post_view(request, post_id):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    post = get_object_or_404(Post, pk=post_id)
    
    next_param = request.GET.get('next') or request.POST.get('next') or ''
    redirect_target = 'profile' if next_param == 'profile' else 'posts'

    if not can_user_manage_post(user, post):
        messages.error(request, "Access Denied: You do not have permission to delete this post.")
        return redirect(redirect_target)

    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post deleted successfully.")
        
    return redirect(redirect_target)


@login_required(login_url='login')
@never_cache
def alerts_list_view(request):
    return render(request, 'lsg/content/alerts.html', {
        'user': request.user,
        'panchayat_president': get_panchayat_president(request.user),
        'ward_members': get_ward_members(request.user)
    })

@login_required(login_url='login')
@never_cache
def documents_list_view(request):
    return render(request, 'lsg/content/documents.html', {
        'user': request.user,
        'panchayat_president': get_panchayat_president(request.user),
        'ward_members': get_ward_members(request.user)
    })


