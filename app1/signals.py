# app1/signals.py
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import Medicine, Customer, Sale, ActivityLog, Alert

# Example 1: Log when medicine stock is updated
@receiver(pre_save, sender=Medicine)
def log_medicine_update(sender, instance, **kwargs):
    """Log when medicine details are being updated"""
    if instance.pk:  # If medicine already exists (update)
        print(f"Medicine '{instance.name}' is being updated")
        # You can add custom logic here

# Example 2: Create alert when medicine stock is low
@receiver(post_save, sender=Medicine)
def check_low_stock_alert(sender, instance, created, **kwargs):
    """Create alert if medicine stock is below minimum"""
    if instance.quantity <= instance.min_quantity:
        Alert.objects.create(
            alert_type='low_stock',
            medicine=instance,
            message=f"Low stock alert: {instance.name} - Only {instance.quantity} left",
        )

# Example 3: Log when a sale is created
@receiver(post_save, sender=Sale)
def log_sale_activity(sender, instance, created, **kwargs):
    """Create activity log when new sale is made"""
    if created:
        ActivityLog.objects.create(
            action_type='sale',
            description=f'New sale: {instance.invoice_number} for ₹{instance.grand_total}',
            amount=instance.grand_total
        )

# Example 4: Update customer's last purchase date
@receiver(post_save, sender=Sale)
def update_customer_last_purchase(sender, instance, created, **kwargs):
    """Update customer's last purchase date when sale is created"""
    if created and instance.customer:
        customer = instance.customer
        customer.last_purchase_date = instance.date
        customer.total_purchases += instance.grand_total
        customer.total_visits += 1
        customer.save()

# Example 5: Log user login activity
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log when user logs in"""
    ActivityLog.objects.create(
        user=user,
        action_type='login',
        description=f'User {user.username} logged in'
    )

# Example 6: Handle customer deletion
@receiver(post_delete, sender=Customer)
def log_customer_deletion(sender, instance, **kwargs):
    """Log when customer is deleted"""
    ActivityLog.objects.create(
        action_type='customer_delete',
        description=f'Customer {instance.full_name} was deleted'
    )