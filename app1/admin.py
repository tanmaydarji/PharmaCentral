from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'phone_number', 'is_active')
    list_filter = ('user_type', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'profile_picture')}),
    )

# Pharmacy Admin
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'license_number', 'city', 'is_verified')
    list_filter = ('is_verified', 'city')
    search_fields = ('name', 'license_number', 'gst_number')

# Medicine Admin
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'medicine_code', 'category', 'quantity', 'unit_price', 'expiry_date', 'status')
    list_filter = ('category', 'status', 'expiry_date')
    search_fields = ('name', 'medicine_code', 'batch_number')
    date_hierarchy = 'expiry_date'

# Sale Admin
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer_name', 'date', 'grand_total', 'payment_method', 'payment_status')
    list_filter = ('payment_method', 'payment_status', 'date')
    search_fields = ('invoice_number', 'customer_name', 'customer_phone')
    date_hierarchy = 'date'

# Customer Admin
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'customer_id', 'phone', 'customer_type', 'total_purchases', 'due_amount')
    list_filter = ('customer_type', 'status')
    search_fields = ('first_name', 'last_name', 'phone', 'email')

# Debtor Admin
class DebtorAdmin(admin.ModelAdmin):
    list_display = ('customer', 'total_due', 'last_reminder_date')
    search_fields = ('customer__first_name', 'customer__last_name', 'customer__phone')

# Register all models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Pharmacy, PharmacyAdmin)
admin.site.register(MedicineCategory)
admin.site.register(Medicine, MedicineAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(SaleItem)
admin.site.register(Debtor, DebtorAdmin)
admin.site.register(Payment)
admin.site.register(ActivityLog)
admin.site.register(Alert)
admin.site.register(Report)
admin.site.register(Settings)