from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse

from lsg.models import User, Role, Complaint, ComplaintStatus, ComplaintCategory
from lsg.forms.complaints import ComplaintForm, ComplaintStatusForm
from lsg.views.content import get_ward_members, get_panchayat_president

def get_recipient_for_villager(user):
    """
    Finds the designated recipient for a villager's complaint:
    1. Ward Member representing the villager's ward.
    2. If no Ward Member exists for that ward (e.g., President's ward), fallback to Panchayat President.
    """
    if not user.ward or not user.panchayat:
        return None
        
    ward_member = User.objects.filter(
        role=Role.WARD_MEMBER,
        ward=user.ward
    ).first()
    
    if ward_member:
        return ward_member
        
    return get_panchayat_president(user)


@login_required(login_url='login')
@never_cache
def complaints_list_view(request):
    user = request.user
    
    # Base queryset filtering by user role
    if user.role == Role.VILLAGER:
        base_user_qs = Complaint.objects.filter(villager=user)
    elif user.role == Role.WARD_MEMBER:
        base_user_qs = Complaint.objects.filter(
            Q(recipient=user) | Q(ward=user.ward)
        )
    elif user.role == Role.PANCHAYAT_PRESIDENT:
        base_user_qs = Complaint.objects.filter(panchayat=user.panchayat)
    else:
        base_user_qs = Complaint.objects.none()

    complaints_qs = base_user_qs

    # Query params (defaults to PENDING)
    status_filter = request.GET.get('status', 'PENDING').strip().upper()
    category_filter = request.GET.get('category', '').strip()
    year_filter = request.GET.get('year', '').strip()
    sort_by = request.GET.get('sort', 'newest').strip()

    valid_statuses = [choice[0] for choice in ComplaintStatus.choices]
    if status_filter not in valid_statuses:
        status_filter = 'PENDING'

    complaints_qs = complaints_qs.filter(status=status_filter)


    if category_filter and category_filter.upper() != 'ALL':
        valid_categories = [choice[0] for choice in ComplaintCategory.choices]
        if category_filter in valid_categories:
            complaints_qs = complaints_qs.filter(category=category_filter)

    if year_filter:
        try:
            complaints_qs = complaints_qs.filter(created_at__year=int(year_filter))
        except ValueError:
            pass

    # Sorting
    if sort_by == 'oldest':
        complaints_qs = complaints_qs.order_by('created_at')
    else:
        complaints_qs = complaints_qs.order_by('-created_at')

    # Available years list for filter
    available_years = base_user_qs.dates('created_at', 'year', order='DESC')
    years = [date.year for date in available_years]

    # Count statistics for top status tabs
    status_counts = {
        'PENDING': base_user_qs.filter(status=ComplaintStatus.PENDING).count(),
        'IN_PROGRESS': base_user_qs.filter(status=ComplaintStatus.IN_PROGRESS).count(),
        'SOLVED': base_user_qs.filter(status=ComplaintStatus.SOLVED).count(),
        'REJECTED': base_user_qs.filter(status=ComplaintStatus.REJECTED).count(),
    }


    # Pagination (10 per page)
    paginator = Paginator(complaints_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    recipient = get_recipient_for_villager(user) if user.role == Role.VILLAGER else None

    context = {
        'user': user,
        'complaints': page_obj,
        'page_obj': page_obj,
        'selected_status': status_filter,
        'selected_category': category_filter,
        'selected_year': year_filter,
        'selected_sort': sort_by,
        'status_counts': status_counts,
        'categories': ComplaintCategory.choices,
        'statuses': ComplaintStatus.choices,
        'years': years,
        'recipient': recipient,
        'ward_members': get_ward_members(user)
    }
    return render(request, 'lsg/complaints/complaints.html', context)


@login_required(login_url='login')
@never_cache
def create_complaint_view(request):
    user = request.user
    
    if user.role != Role.VILLAGER and not user.is_superuser:
        messages.error(request, "Only villagers can register new civic complaints.")
        return redirect('complaints')

    recipient = get_recipient_for_villager(user)
    if not recipient:
        messages.error(request, "No designated representative is assigned to your ward/panchayat yet. Please contact your Panchayat administrator.")
        return redirect('complaints')

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.villager = user
            complaint.recipient = recipient
            complaint.panchayat = user.panchayat
            complaint.ward = user.ward
            complaint.save()
            messages.success(request, f"Your complaint '{complaint.subject}' has been registered successfully with {recipient.name or recipient.username}.")
            return redirect('complaints')
    else:
        form = ComplaintForm()

    context = {
        'form': form,
        'recipient': recipient,
        'user': user,
        'ward_members': get_ward_members(user)
    }
    return render(request, 'lsg/complaints/complaint_form.html', context)


@login_required(login_url='login')
@never_cache
def complaint_detail_view(request, complaint_id):
    user = request.user
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Permission check
    is_author = (complaint.villager == user)
    is_recipient_or_rep = (
        user == complaint.recipient or 
        (user.role == Role.WARD_MEMBER and user.ward == complaint.ward) or
        (user.role == Role.PANCHAYAT_PRESIDENT and user.panchayat == complaint.panchayat) or
        user.is_superuser
    )

    if not (is_author or is_recipient_or_rep):
        messages.error(request, "You do not have permission to view this complaint.")
        return redirect('complaints')

    context = {
        'complaint': complaint,
        'is_author': is_author,
        'is_recipient_or_rep': is_recipient_or_rep,
        'statuses': ComplaintStatus.choices,
        'user': user,
        'ward_members': get_ward_members(user)
    }
    return render(request, 'lsg/complaints/complaint_detail.html', context)


@login_required(login_url='login')
@never_cache
def update_complaint_status_view(request, complaint_id):
    if request.method != 'POST':
        return redirect('complaints')
        
    user = request.user
    complaint = get_object_or_404(Complaint, id=complaint_id)

    is_recipient_or_rep = (
        user == complaint.recipient or 
        (user.role == Role.WARD_MEMBER and user.ward == complaint.ward) or
        (user.role == Role.PANCHAYAT_PRESIDENT and user.panchayat == complaint.panchayat) or
        user.is_superuser
    )

    if not is_recipient_or_rep:
        messages.error(request, "You do not have permission to update the status of this complaint.")
        return redirect('complaint_detail', complaint_id=complaint.id)

    form = ComplaintStatusForm(request.POST, instance=complaint)
    if form.is_valid():
        updated_complaint = form.save()
        messages.success(request, f"Complaint status updated to '{updated_complaint.get_status_display()}'.")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('complaint_detail', args=[complaint.id])
    return redirect(next_url)
