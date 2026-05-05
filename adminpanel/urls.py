from django.urls import path
from . import views

urlpatterns = [
    # Admin Authentication
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Admin Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # User Management
    path('users/', views.admin_users, name='admin_users'),
    
    # Actions
    path('toggle-active/<int:user_id>/', views.toggle_active, name='toggle_active'),
    path('toggle-verify/<int:pharmacy_id>/', views.toggle_verify, name='toggle_verify'),
    path('delete-pharmacy/<int:user_id>/', views.delete_pharmacy, name='delete_pharmacy'),    
    
    # APIs
    path('search-api/', views.admin_search_api, name='admin_search_api'),
    path('stats-api/', views.admin_stats_api, name='admin_stats_api'),
]