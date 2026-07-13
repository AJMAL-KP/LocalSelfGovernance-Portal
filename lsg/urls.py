from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('posts/', views.posts_list_view, name='posts'),
    path('alerts/', views.alerts_list_view, name='alerts'),
    path('documents/', views.documents_list_view, name='documents'),
    path('complaints/', views.complaints_list_view, name='complaints'),
    path('manage-users/', views.manage_users_view, name='manage_users'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
