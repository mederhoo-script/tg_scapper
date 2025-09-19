from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Account management
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),
    
    # Group management
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/edit/', views.group_edit, name='group_edit'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),
    
    # Scraping
    path('scraping/', views.scraping_sessions, name='scraping_sessions'),
    path('scraping/start/', views.start_scraping, name='start_scraping'),
    path('scraping/<int:session_id>/members/', views.scraped_members, name='scraped_members'),
    path('scraping/<int:session_id>/export/', views.export_members_csv, name='export_members_csv'),
    path('members/<int:member_id>/toggle-active/', views.toggle_member_active, name='toggle_member_active'),
    
    # Message templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    
    # Invite/DM
    path('invite-dm/', views.invite_dm_interface, name='invite_dm_interface'),
    path('logs/invites/', views.invite_logs, name='invite_logs'),
    path('logs/dms/', views.dm_logs, name='dm_logs'),
    
    # Settings
    path('settings/', views.settings_view, name='settings'),
]