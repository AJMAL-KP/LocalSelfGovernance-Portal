from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from lsg.models import User, Role, Post, PostScope, Alert, AlertCategory
from lsg.forms.content import PostForm, AlertForm

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


def can_user_manage_alert(user, alert):
    if not user or not user.is_authenticated:
        return False
    if alert.author == user:
        return True
    if user.role == Role.PANCHAYAT_PRESIDENT and user.panchayat and alert.panchayat == user.panchayat:
        return True
    return False


@login_required(login_url='login')
@never_cache
def alerts_list_view(request):
    user = request.user
    if not user.panchayat:
        messages.error(request, "You are not assigned to any Panchayat.")
        return redirect('posts')

    # Base query: filter by user's Panchayat
    alerts = Alert.objects.filter(panchayat=user.panchayat)
    
    # Content filtering based on role / ward
    if user.role != Role.PANCHAYAT_PRESIDENT:
        if user.ward:
            alerts = alerts.filter(
                Q(scope=PostScope.PANCHAYAT) | Q(scope=PostScope.WARD, ward=user.ward)
            )
        else:
            alerts = alerts.filter(scope=PostScope.PANCHAYAT)

    # Get query params for category, scope, year, sort
    category_filter = request.GET.get('category', '').strip()
    scope_filter = request.GET.get('scope', '').strip()
    year_filter = request.GET.get('year', '').strip()
    sort_by = request.GET.get('sort', 'newest').strip()

    if category_filter:
        alerts = alerts.filter(category=category_filter)
    if scope_filter:
        alerts = alerts.filter(scope=scope_filter)
    if year_filter:
        try:
            alerts = alerts.filter(created_at__year=int(year_filter))
        except ValueError:
            pass

    # Sort
    if sort_by == 'oldest':
        alerts = alerts.order_by('created_at')
    else:
        alerts = alerts.order_by('-created_at')

    # Pagination: 10 per page
    paginator = Paginator(alerts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Annotate edit/delete permissions
    for alert in page_obj:
        alert.can_manage = can_user_manage_alert(user, alert)

    # Get distinct years of alerts for this Panchayat to populate year filter
    available_years = Alert.objects.filter(panchayat=user.panchayat).dates('created_at', 'year', order='DESC')
    years = [date.year for date in available_years]

    return render(request, 'lsg/content/alerts.html', {
        'user': user,
        'alerts': page_obj,
        'page_obj': page_obj,
        'panchayat_president': get_panchayat_president(user),
        'ward_members': get_ward_members(user),
        'categories': AlertCategory.choices,
        'years': years,
        'selected_category': category_filter,
        'selected_scope': scope_filter,
        'selected_year': year_filter,
        'selected_sort': sort_by,
    })


@login_required(login_url='login')
@never_cache
def create_alert_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    if user.role not in [Role.WARD_MEMBER, Role.PANCHAYAT_PRESIDENT]:
        messages.error(request, "Access Denied: You do not have permission to create alerts.")
        return redirect('alerts')

    if request.method == 'POST':
        form = AlertForm(request.POST, user=user)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.author = user
            alert.panchayat = user.panchayat
            if user.role == Role.WARD_MEMBER:
                alert.scope = PostScope.WARD
                alert.ward = user.ward
            else:
                chosen_scope = form.cleaned_data.get('scope', PostScope.PANCHAYAT)
                alert.scope = chosen_scope
                if chosen_scope == PostScope.WARD:
                    alert.ward = user.ward
                else:
                    alert.ward = None
            try:
                alert.full_clean()
                alert.save()
                messages.success(request, "Alert created successfully.")
                return redirect('alerts')
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for err in errors:
                        messages.error(request, f"Error: {err}")
    else:
        form = AlertForm(user=user)
        
    return render(request, 'lsg/content/alert_form.html', {
        'form': form,
        'title': 'Create New Alert',
        'is_edit': False,
        'active_page': 'alerts',
        'panchayat_president': get_panchayat_president(user),
        'ward_members': get_ward_members(user)
    })


@login_required(login_url='login')
@never_cache
def edit_alert_view(request, alert_id):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    alert = get_object_or_404(Alert, pk=alert_id)

    if not can_user_manage_alert(user, alert):
        messages.error(request, "Access Denied: You do not have permission to edit this alert.")
        return redirect('alerts')

    if request.method == 'POST':
        form = AlertForm(request.POST, instance=alert, user=user)
        if form.is_valid():
            updated_alert = form.save(commit=False)
            if user.role == Role.PANCHAYAT_PRESIDENT:
                chosen_scope = form.cleaned_data.get('scope', PostScope.PANCHAYAT)
                updated_alert.scope = chosen_scope
                if chosen_scope == PostScope.WARD:
                    updated_alert.ward = user.ward
                else:
                    updated_alert.ward = None
            try:
                updated_alert.full_clean()
                updated_alert.save()
                messages.success(request, "Alert updated successfully.")
                return redirect('alerts')
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for err in errors:
                        messages.error(request, f"Error: {err}")
    else:
        form = AlertForm(instance=alert, user=user)
        
    return render(request, 'lsg/content/alert_form.html', {
        'form': form,
        'title': 'Edit Alert',
        'is_edit': True,
        'alert': alert,
        'active_page': 'alerts',
        'panchayat_president': get_panchayat_president(user),
        'ward_members': get_ward_members(user)
    })


@login_required(login_url='login')
@never_cache
def delete_alert_view(request, alert_id):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    alert = get_object_or_404(Alert, pk=alert_id)

    if not can_user_manage_alert(user, alert):
        messages.error(request, "Access Denied: You do not have permission to delete this alert.")
        return redirect('alerts')

    if request.method == 'POST':
        alert.delete()
        messages.success(request, "Alert deleted successfully.")
        
    return redirect('alerts')

def can_user_manage_document(user, document):
    if user.is_superuser:
        return True
    if document.author == user:
        return True
    if user.role == Role.PANCHAYAT_PRESIDENT and user.panchayat and document.panchayat == user.panchayat:
        return True
    return False


@login_required(login_url='login')
@never_cache
def documents_list_view(request):
    user = request.user
    if not user.panchayat:
        messages.error(request, "You are not assigned to any Panchayat.")
        return redirect('posts')

    from lsg.models import Document, DocumentCategory

    # Base query: filter by user's Panchayat
    documents = Document.objects.filter(panchayat=user.panchayat)

    # Scoping authorization filtering
    if user.role != Role.PANCHAYAT_PRESIDENT:
        if user.ward:
            documents = documents.filter(
                Q(scope=PostScope.PANCHAYAT) | Q(scope=PostScope.WARD, ward=user.ward)
            )
        else:
            documents = documents.filter(scope=PostScope.PANCHAYAT)

    # Get query params for category, scope, year, sort
    category_filter = request.GET.get('category', '').strip()
    scope_filter = request.GET.get('scope', '').strip()
    year_filter = request.GET.get('year', '').strip()
    sort_by = request.GET.get('sort', 'newest').strip()

    if category_filter:
        documents = documents.filter(category=category_filter)
    if scope_filter:
        documents = documents.filter(scope=scope_filter)
    if year_filter:
        try:
            documents = documents.filter(created_at__year=int(year_filter))
        except ValueError:
            pass

    # Sort: pinned always at top (-is_pinned), then newest or oldest
    if sort_by == 'oldest':
        documents = documents.order_by('-is_pinned', 'created_at')
    else:
        documents = documents.order_by('-is_pinned', '-created_at')

    # Pagination: 10 per page
    paginator = Paginator(documents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Annotate edit/delete/pin permissions
    for doc in page_obj:
        doc.can_manage = can_user_manage_document(user, doc)

    # Get distinct years of documents for this Panchayat to populate year filter
    available_years = Document.objects.filter(panchayat=user.panchayat).dates('created_at', 'year', order='DESC')
    years = [date.year for date in available_years]

    return render(request, 'lsg/content/documents.html', {
        'user': user,
        'documents': page_obj,
        'page_obj': page_obj,
        'panchayat_president': get_panchayat_president(user),
        'ward_members': get_ward_members(user),
        'categories': DocumentCategory.choices,
        'years': years,
        'selected_category': category_filter,
        'selected_scope': scope_filter,
        'selected_year': year_filter,
        'selected_sort': sort_by,
    })


@login_required(login_url='login')
@never_cache
def upload_document_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
        
    user = request.user
    if user.role not in [Role.WARD_MEMBER, Role.PANCHAYAT_PRESIDENT]:
        messages.error(request, "Access Denied: You do not have permission to upload documents.")
        return redirect('documents')

    from lsg.forms.content import DocumentForm

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.author = user
            doc.panchayat = user.panchayat
            if user.role == Role.WARD_MEMBER:
                doc.scope = PostScope.WARD
                doc.ward = user.ward
            else:
                chosen_scope = form.cleaned_data.get('scope', PostScope.PANCHAYAT)
                doc.scope = chosen_scope
                if chosen_scope == PostScope.WARD:
                    doc.ward = user.ward
                else:
                    doc.ward = None
            doc.save()
            messages.success(request, "Document uploaded successfully.")
            return redirect('documents')
    else:
        form = DocumentForm(user=user)

    return render(request, 'lsg/content/document_form.html', {
        'form': form,
        'is_edit': False,
        'panchayat_president': get_panchayat_president(user),
        'ward_members': get_ward_members(user),
    })


@login_required(login_url='login')
@never_cache
def edit_document_view(request, document_id):
    if request.user.is_superuser:
        return redirect('admin:index')

    from lsg.models import Document
    from lsg.forms.content import DocumentForm

    doc = get_object_or_404(Document, id=document_id)
    user = request.user

    if not can_user_manage_document(user, doc):
        messages.error(request, "Access Denied: You do not have permission to edit this document.")
        return redirect('documents')

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=doc, user=user)
        if form.is_valid():
            updated_doc = form.save(commit=False)
            # If no new file is uploaded, keep the old one
            if not request.FILES.get('file') and doc.file:
                updated_doc.file = doc.file
            
            if user.role == Role.WARD_MEMBER:
                updated_doc.scope = PostScope.WARD
                updated_doc.ward = user.ward
            else:
                chosen_scope = form.cleaned_data.get('scope', PostScope.PANCHAYAT)
                updated_doc.scope = chosen_scope
                if chosen_scope == PostScope.WARD:
                    updated_doc.ward = user.ward
                else:
                    updated_doc.ward = None

            updated_doc.save()
            messages.success(request, "Document updated successfully.")
            return redirect('documents')
    else:
        form = DocumentForm(instance=doc, user=user)

    return render(request, 'lsg/content/document_form.html', {
        'form': form,
        'is_edit': True,
        'document': doc,
        'panchayat_president': get_panchayat_president(user),
        'ward_members': get_ward_members(user),
    })


@login_required(login_url='login')
@never_cache
def delete_document_view(request, document_id):
    if request.user.is_superuser:
        return redirect('admin:index')

    from lsg.models import Document
    doc = get_object_or_404(Document, id=document_id)
    user = request.user

    if not can_user_manage_document(user, doc):
        messages.error(request, "Access Denied: You do not have permission to delete this document.")
        return redirect('documents')

    if request.method == 'POST':
        # Also clean up the physical file on disk
        if doc.file:
            doc.file.delete(save=False)
        doc.delete()
        messages.success(request, "Document deleted successfully.")
        
    return redirect('documents')


from django.views.decorators.http import require_POST

@login_required(login_url='login')
@never_cache
@require_POST
def toggle_pin_document_view(request, document_id):
    from lsg.models import Document
    doc = get_object_or_404(Document, id=document_id)
    user = request.user

    if not can_user_manage_document(user, doc):
        messages.error(request, "Access Denied: You do not have permission to pin/unpin this document.")
        return redirect('documents')

    doc.is_pinned = not doc.is_pinned
    doc.save()
    if doc.is_pinned:
        messages.success(request, f"Document '{doc.title}' pinned to top.")
    else:
        messages.success(request, f"Document '{doc.title}' unpinned.")

    return redirect('documents')


