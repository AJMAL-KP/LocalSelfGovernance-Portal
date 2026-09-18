from django.urls import path
from lsg.views import auth as auth_views
from lsg.views import content as content_views
from lsg.views import complaints as complaint_views
from lsg.views import management as mgmt_views

urlpatterns = [
    path('', content_views.dashboard_view, name='dashboard'),
    path('posts/', content_views.posts_list_view, name='posts'),
    path('posts/create/', content_views.create_post_view, name='create_post'),
    path('posts/<int:post_id>/edit/', content_views.edit_post_view, name='edit_post'),
    path('posts/<int:post_id>/delete/', content_views.delete_post_view, name='delete_post'),
    path('alerts/', content_views.alerts_list_view, name='alerts'),
    path('alerts/create/', content_views.create_alert_view, name='create_alert'),
    path('alerts/<int:alert_id>/edit/', content_views.edit_alert_view, name='edit_alert'),
    path('alerts/<int:alert_id>/delete/', content_views.delete_alert_view, name='delete_alert'),
    path('documents/', content_views.documents_list_view, name='documents'),
    path('documents/upload/', content_views.upload_document_view, name='upload_document'),
    path('documents/<int:document_id>/edit/', content_views.edit_document_view, name='edit_document'),
    path('documents/<int:document_id>/delete/', content_views.delete_document_view, name='delete_document'),
    path('documents/<int:document_id>/toggle-pin/', content_views.toggle_pin_document_view, name='toggle_pin_document'),
    path('complaints/', complaint_views.complaints_list_view, name='complaints'),
    path('complaints/lodge/', complaint_views.create_complaint_view, name='create_complaint'),
    path('complaints/<int:complaint_id>/', complaint_views.complaint_detail_view, name='complaint_detail'),
    path('complaints/<int:complaint_id>/update-status/', complaint_views.update_complaint_status_view, name='update_complaint_status'),

    path('manage-members/', mgmt_views.manage_members_view, name='manage_members'),
    path('manage-members/suggest/', mgmt_views.member_suggestions_view, name='member_suggestions'),
    path('register/', auth_views.register_view, name='register'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.profile_view, name='profile'),
    path('settings/', auth_views.settings_view, name='settings'),
]
