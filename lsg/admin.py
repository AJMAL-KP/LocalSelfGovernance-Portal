from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import Taluk, Panchayat, Ward, User, Post, Role

def validate_user_role_constraints(form, cleaned_data):
    role = cleaned_data.get('role')
    panchayat = cleaned_data.get('panchayat')
    ward = cleaned_data.get('ward')
    
    def get_existing_query(filters):
        q = User.objects.filter(**filters)
        if form.instance and form.instance.pk:
            q = q.exclude(pk=form.instance.pk)
        return q
        
    if role == Role.PANCHAYAT_PRESIDENT and panchayat:
        existing = get_existing_query({'panchayat': panchayat, 'role': Role.PANCHAYAT_PRESIDENT})
        if existing.exists():
            raise forms.ValidationError(f"This Panchayat already has a Panchayat President ({existing.first().name or existing.first().username}).")
            
    if role == Role.WARD_MEMBER and ward:
        existing = get_existing_query({'ward': ward, 'role': Role.WARD_MEMBER})
        if existing.exists():
            raise forms.ValidationError(f"This Ward already has a Ward Representative ({existing.first().name or existing.first().username}).")
            
    if role == Role.WARD_MEMBER and ward:
        president_in_ward = get_existing_query({'ward': ward, 'role': Role.PANCHAYAT_PRESIDENT})
        if president_in_ward.exists():
            raise forms.ValidationError(f"This Ward belongs to a Panchayat President ({president_in_ward.first().name or president_in_ward.first().username}) and cannot have a separate Ward Representative.")
            
    if role == Role.PANCHAYAT_PRESIDENT and ward:
        member_in_ward = get_existing_query({'ward': ward, 'role': Role.WARD_MEMBER})
        if member_in_ward.exists():
            raise forms.ValidationError(f"This Ward already has a Ward Representative ({member_in_ward.first().name or member_in_ward.first().username}). A Panchayat President's Ward cannot have a separate Ward Representative.")

# Forms to properly integrate custom User fields into the Django admin
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'name', 'age', 'aadhar_id', 'phone', 'panchayat', 'ward')

    def clean(self):
        cleaned_data = super().clean()
        validate_user_role_constraints(self, cleaned_data)
        return cleaned_data


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        validate_user_role_constraints(self, cleaned_data)
        return cleaned_data


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    # Display these columns in the user list view
    list_display = ('username', 'email', 'name', 'role', 'panchayat', 'ward', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'panchayat')
    search_fields = ('username', 'email', 'name', 'aadhar_id', 'phone')
    
    # Include custom fields when editing a user
    fieldsets = UserAdmin.fieldsets + (
        ('Local Governance Details', {
            'fields': ('role', 'name', 'age', 'aadhar_id', 'phone', 'panchayat', 'ward'),
        }),
    )
    
    # Include custom fields when creating a user via admin panel
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Local Governance Details', {
            'fields': ('role', 'name', 'age', 'aadhar_id', 'phone', 'panchayat', 'ward'),
        }),
    )


@admin.register(Taluk)
class TalukAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# Inline administration of Wards inside Panchayat admin pages
class WardInline(admin.TabularInline):
    model = Ward
    extra = 1


@admin.register(Panchayat)
class PanchayatAdmin(admin.ModelAdmin):
    list_display = ('name', 'taluk', 'ward_count')
    list_filter = ('taluk',)
    search_fields = ('name',)
    inlines = [WardInline]

    def ward_count(self, obj):
        return obj.wards.count()
    ward_count.short_description = 'Number of Wards'


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'panchayat')
    list_filter = ('panchayat',)
    search_fields = ('name', 'number')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'scope', 'panchayat', 'ward', 'created_at')
    list_filter = ('scope', 'panchayat', 'ward')
    search_fields = ('title', 'content', 'author__username')

