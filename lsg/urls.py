from django.urls import path
from lsg.views import auth as auth_views
from lsg.views import content as content_views
from lsg.views import complaints as complaint_views
from lsg.views import management as mgmt_views

urlpatterns = [
    path('', content_views.dashboard_view, name='dashboard'),
    path('posts/', content_views.posts_list_view, name='posts'),
    path('alerts/', content_views.alerts_list_view, name='alerts'),
    path('documents/', content_views.documents_list_view, name='documents'),
    path('complaints/', complaint_views.complaints_list_view, name='complaints'),
    path('manage-users/', mgmt_views.manage_users_view, name='manage_users'),
    path('register/', auth_views.register_view, name='register'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.profile_view, name='profile'),
    path('settings/', auth_views.settings_view, name='settings'),
]
