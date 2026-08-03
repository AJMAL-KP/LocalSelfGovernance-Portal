from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from lsg.decorators import panchayat_president_required
from lsg.models import User, Role, Ward

def get_search_q_filters(q):
    if q.endswith('%') and len(q) > 1:
        prefix = q[:-1]
        return (
            Q(name__istartswith=prefix) | 
            Q(email__istartswith=prefix) | 
            Q(aadhar_id__istartswith=prefix) | 
            Q(phone__istartswith=prefix)
        )
    elif q.startswith('%') and len(q) > 1:
        suffix = q[1:]
        return (
            Q(name__iendswith=suffix) | 
            Q(email__iendswith=suffix) | 
            Q(aadhar_id__iendswith=suffix) | 
            Q(phone__iendswith=suffix)
        )
    else:
        return (
            Q(name__icontains=q) | 
            Q(email__icontains=q) | 
            Q(aadhar_id__icontains=q) | 
            Q(phone__icontains=q)
        )

@panchayat_president_required
@never_cache
def member_suggestions_view(request):
    q = request.GET.get('q', '').strip()
    search_ward_id = request.GET.get('search_ward_id', '').strip()
    
    results = []
    if q or search_ward_id:
        queryset = User.objects.filter(
            panchayat=request.user.panchayat,
            role=Role.VILLAGER
        ).exclude(id=request.user.id).exclude(is_superuser=True)
        
        if q:
            queryset = queryset.filter(get_search_q_filters(q))
            
        if search_ward_id:
            queryset = queryset.filter(ward_id=search_ward_id)
            
        users = queryset.order_by('name')[:15]
        
        for u in users:
            results.append({
                'id': u.id,
                'name': u.name or u.username,
                'email': u.email,
                'phone': u.phone,
                'aadhar_id': u.aadhar_id,
                'age': u.age or 'Not specified',
                'ward': f"Ward {u.ward.number}{' - ' + u.ward.name if u.ward.name else ''}" if u.ward else "None"
            })
            
    return JsonResponse({'suggestions': results})

@panchayat_president_required
@never_cache
def manage_members_view(request):
    user = request.user
    if not user.panchayat:
        messages.error(request, "You are not assigned to any Panchayat.")
        return redirect('posts')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'promote':
            member_user = get_object_or_404(User, id=user_id, panchayat=user.panchayat)
            
            if not member_user.ward:
                messages.error(request, f"Error: {member_user.name or member_user.username} does not have a Ward assigned in their profile.")
            else:
                # Promote user to Ward Member representing their profile Ward
                member_user.role = Role.WARD_MEMBER
                
                try:
                    member_user.full_clean()
                    member_user.save()
                    messages.success(request, f"Successfully promoted {member_user.name or member_user.username} to Ward Member for Ward {member_user.ward.number}.")
                except ValidationError as e:
                    # Extract and format validation errors
                    for field, errors in e.message_dict.items():
                        for err in errors:
                            messages.error(request, f"Error: {err}")
                            
        elif action == 'demote':
            member_user = get_object_or_404(User, id=user_id, panchayat=user.panchayat)
            member_user.role = Role.VILLAGER
            try:
                member_user.full_clean()
                member_user.save()
                messages.success(request, f"Successfully removed {member_user.name or member_user.username} as Ward Member.")
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for err in errors:
                        messages.error(request, f"Error: {err}")
                        
        return redirect('manage_members')
        
    # Handle GET request
    q = request.GET.get('q', '').strip()
    search_ward_id = request.GET.get('search_ward_id', '').strip()
    user_id = request.GET.get('user_id', '').strip()
    
    search_results = []
    # Trigger search if user_id, query, or ward filter is provided
    if user_id:
        search_results = User.objects.filter(
            id=user_id,
            panchayat=user.panchayat,
            role=Role.VILLAGER
        ).exclude(id=user.id).exclude(is_superuser=True)
    elif q or search_ward_id:
        queryset = User.objects.filter(
            panchayat=user.panchayat,
            role=Role.VILLAGER
        ).exclude(id=user.id).exclude(is_superuser=True)
        
        if q:
            queryset = queryset.filter(get_search_q_filters(q))
            
        if search_ward_id:
            queryset = queryset.filter(ward_id=search_ward_id)
            
        search_results = queryset.order_by('name')
        
    # Get current ward members
    members = User.objects.filter(
        panchayat=user.panchayat,
        role=Role.WARD_MEMBER
    ).exclude(id=user.id).exclude(is_superuser=True).order_by('ward__number', 'name')
    
    # Paginate members list (10 per page)
    paginator = Paginator(members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Fetch all wards for the panchayat to display in dropdown filters
    wards = Ward.objects.filter(panchayat=user.panchayat).order_by('number')
    
    return render(request, 'lsg/management/members.html', {
        'search_results': search_results,
        'members': page_obj,
        'page_obj': page_obj,
        'wards': wards,
        'q': q,
        'search_ward_id': search_ward_id,
        'user_id': user_id
    })
