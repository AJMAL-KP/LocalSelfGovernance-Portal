from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import Taluk, Panchayat, Ward, User, Post

# Forms to properly integrate custom User fields into the Django admin
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'name', 'age', 'aadhar_id', 'phone', 'panchayat', 'ward')


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


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

