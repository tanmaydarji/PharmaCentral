from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Medicine Management
    path('medicine-stock/', views.medicine_stock, name='medicine_stock'),
    path('add-medicine/', views.add_medicine, name='add_medicine'),
    path('edit-medicine/<int:pk>/', views.edit_medicine, name='edit_medicine'),
    path('delete-medicine/<int:pk>/', views.delete_medicine, name='delete_medicine'),
    
    # Sales Management
    path('sales/', views.sales, name='sales'),
    path('sales-history/', views.sales_history, name='sales_history'),
    path('sales-history-api/', views.sales_history_api, name='sales_history_api'),
    path('sales-edit/<int:pk>/', views.sales_edit, name='sales_edit'),
    path('delete-sale/<int:pk>/', views.delete_sale, name='delete_sale'),
    path('invoice/<int:pk>/', views.invoice_view, name='invoice_view'),
    
    # Customer Management
    path('customers/', views.customers, name='customers'),
    path('view-customer/<int:pk>/', views.view_customer, name='view_customer'),
    path('add-customer/', views.add_customer, name='add_customer'),
    path('edit-customer/<int:pk>/', views.edit_customer, name='edit_customer'),
    path('delete-customer/<int:pk>/', views.delete_customer, name='delete_customer'),
    path('customer-history/<int:pk>/', views.customer_history, name='customer_history'),
    
    # Debtor Management
    path('debtors/', views.debtors, name='debtors'),
    path('receive-payment/<int:pk>/', views.receive_payment, name='receive_payment'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    path('export-report-pdf/', views.export_report_pdf, name='export_report_pdf'),
    path('create-backup/', views.create_backup, name='create_backup'),
    # path('test-backup/', views.test_backup, name='test_backup'),
    path('get-user-backups/', views.get_user_backups, name='get_user_backups'),
    path('restore-user-backup/<int:backup_id>/', views.restore_user_backup, name='restore_user_backup'),

    
    # Settings
    path('settings/', views.settings_view, name='settings'),
    
    
    
    
     # Medicine Requests URLs
    path('medicine-requests/', views.medicine_requests, name='medicine_requests'),
    path('add-medicine-request/', views.add_medicine_request, name='add_medicine_request'),
    path('edit-medicine-request/<int:pk>/', views.edit_medicine_request, name='edit_medicine_request'),
    path('delete-medicine-request/<int:pk>/', views.delete_medicine_request, name='delete_medicine_request'),
    path('api/get-request/<int:pk>/', views.api_get_request, name='api_get_request'),
    
    
    
    
    
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
]