from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal
from django.utils import timezone
from datetime import datetime
import datetime as dt

# Create your models here.

class User(AbstractUser):
    """Custom User Model for PharmaCentral"""
    USER_TYPES = (
        ('admin', 'Admin'),
        ('pharmacy_owner', 'Pharmacy Owner'),
        ('pharmacist', 'Pharmacist'),
        ('cashier', 'Cashier'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='cashier')
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 🔴 FIX: Add unique related_name for groups and permissions
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="pharmacentral_user_set",  # Unique name
        related_query_name="pharmacentral_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="pharmacentral_user_set",  # Unique name
        related_query_name="pharmacentral_user",
    )
    
    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"



class Pharmacy(models.Model):
    """Pharmacy Information Model"""
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pharmacies')
    license_number = models.CharField(max_length=50, unique=True)
    gst_number = models.CharField(max_length=50, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    registration_date = models.DateField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    # Documents
    gst_certificate = models.FileField(upload_to='documents/gst/', null=True, blank=True)
    license_document = models.FileField(upload_to='documents/license/', null=True, blank=True)
    owner_id_proof = models.FileField(upload_to='documents/id_proof/', null=True, blank=True)
    owner_photo = models.ImageField(upload_to='profiles/owners/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class MedicineCategory(models.Model):
    """Medicine Categories"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Medicine Categories"
    
    def __str__(self):
        return self.name


class Medicine(models.Model):
    """Medicine Stock Model"""
    STATUS_CHOICES = (
        ('good', 'Good'),
        ('low_stock', 'Low Stock'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
    )
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=200)
    medicine_code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(MedicineCategory, on_delete=models.SET_NULL, null=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    batch_number = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)
    min_quantity = models.PositiveIntegerField(default=10)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    manufacturing_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=50, blank=True, help_text="Rack/Shelf location")
    supplier = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='good')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['expiry_date']
    
    def __str__(self):
        return f"{self.name} - {self.batch_number}"
    
    def save(self, *args, **kwargs):
        # Convert quantity and min_quantity to int
        try:
            if isinstance(self.quantity, str):
                self.quantity = int(self.quantity) if self.quantity else 0
            if isinstance(self.min_quantity, str):
                self.min_quantity = int(self.min_quantity) if self.min_quantity else 0
        except (ValueError, TypeError):
            self.quantity = 0
            self.min_quantity = 0
        
        # Convert expiry_date from string to date
        today = timezone.now().date()
        if isinstance(self.expiry_date, str):
            try:
                self.expiry_date = datetime.strptime(self.expiry_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                self.expiry_date = None
        
        # Set status based on expiry and quantity
        if self.expiry_date and self.expiry_date < today:
            self.status = 'expired'
        elif self.expiry_date and (self.expiry_date - today).days <= 30:
            self.status = 'expiring_soon'
        elif self.quantity <= 0:
            self.status = 'out_of_stock'  # Note: 'out_of_stock' choice નથી, પણ તમે ઉમેરી શકો છો
        elif self.quantity <= self.min_quantity:
            self.status = 'low_stock'
        else:
            self.status = 'good'
        
        super().save(*args, **kwargs)
    
    def days_until_expiry(self):
        if self.expiry_date:
            return (self.expiry_date - timezone.now().date()).days
        return None    


class Customer(models.Model):
    """Customer Model"""
    CUSTOMER_TYPES = (
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('debtor', 'Debtor'),
        ('new', 'New'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
    )
    
    BLOOD_GROUPS = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    )
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='customers', null=True, blank=True)
    customer_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='regular')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    emergency_contact = models.CharField(max_length=15, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUPS, blank=True)
    
    total_purchases = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_visits = models.PositiveIntegerField(default=0)
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_purchase_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer_id} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Sale(models.Model):
    """Sales Model"""
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('credit', 'Credit'),
    )
    
    PAYMENT_STATUS = (
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('partial', 'Partial'),
    )
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='sales' , null=True, blank=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=200, blank=True)  # For walk-in customers
    customer_phone = models.CharField(max_length=15, blank=True)
    
    date = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=12)  # GST 12%
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='paid')
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - ₹{self.grand_total}"
    
    def save(self, *args, **kwargs):
        self.due_amount = self.grand_total - self.amount_paid
        if self.due_amount <= 0:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'pending'
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    """Items in a Sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True)
    medicine_name = models.CharField(max_length=200)  # Store name at time of sale
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.medicine_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Debtor(models.Model):
    """Debtor Management"""
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='debts')
    total_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overdue_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_reminder_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_due']
    
    def __str__(self):
        return f"{self.customer.full_name} - Due: ₹{self.total_due}"


class Payment(models.Model):
    """Payment Received from Debtors"""
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE, related_name='payments')
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=Sale.PAYMENT_METHODS)
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment of ₹{self.amount} from {self.debtor.customer.full_name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update debtor's total due
        total_paid = Payment.objects.filter(debtor=self.debtor).aggregate(models.Sum('amount'))['amount__sum'] or 0
        total_invoiced = Sale.objects.filter(customer=self.debtor.customer).aggregate(models.Sum('due_amount'))['due_amount__sum'] or 0
        self.debtor.total_due = total_invoiced - total_paid
        self.debtor.save()


class ActivityLog(models.Model):
    """Track all activities in the system"""
    ACTION_TYPES = (
        ('sale', 'New Sale'),
        ('payment', 'Payment Received'),
        ('stock_add', 'Stock Added'),
        ('stock_update', 'Stock Updated'),
        ('medicine_add', 'Medicine Added'),
        ('medicine_edit', 'Medicine Edited'),
        ('medicine_delete', 'Medicine Deleted'),
        ('customer_add', 'Customer Added'),
        ('customer_edit', 'Customer Edited'),
        ('customer_delete', 'Customer Deleted'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action_type}"


class Alert(models.Model):
    """System Alerts for Expiry, Low Stock, etc."""
    ALERT_TYPES = (
        ('expiry', 'Expiry Alert'),
        ('low_stock', 'Low Stock Alert'),
        ('debtor', 'Debtor Reminder'),
    )
    
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    days_left = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.message}"


class Report(models.Model):
    """Store generated reports"""
    REPORT_TYPES = (
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('expiry', 'Expiry Report'),
        ('debtor', 'Debtor Report'),
        ('customer', 'Customer Report'),
        ('profit_loss', 'Profit & Loss'),
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    from_date = models.DateField()
    to_date = models.DateField()
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.generated_at.date()}"


class Settings(models.Model):
    """System Settings"""
    pharmacy = models.OneToOneField(Pharmacy, on_delete=models.CASCADE, related_name='settings')
    
    # Alert Settings
    expiry_alert_days = models.PositiveIntegerField(default=30)
    expiry_alerts_enabled = models.BooleanField(default=True)
    low_stock_alerts_enabled = models.BooleanField(default=True)
    debtor_reminders_enabled = models.BooleanField(default=True)
    daily_sales_report = models.BooleanField(default=False)
    
    # Invoice Settings
    invoice_prefix = models.CharField(max_length=10, default='INV')
    invoice_next_number = models.PositiveIntegerField(default=1)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12)
    
    # Notification Settings
    sms_notifications = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settings for {self.pharmacy.name}"
    
    def get_next_invoice_number(self):
        """Generate next invoice number"""
        invoice_no = f"{self.invoice_prefix}-{self.invoice_next_number:04d}"
        self.invoice_next_number += 1
        self.save()
        return invoice_no
    
    
    
    
class MedicineRequest(models.Model):
    """Medicine Request from Customers"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='medicine_requests')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Request Details
    medicine_name = models.CharField(max_length=200)
    medicine_code = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    # Customer Info
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    
    # Tracking
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    requested_date = models.DateTimeField(default=timezone.now)
    
    # History
    history = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-requested_date']
    
    def __str__(self):
        return f"{self.medicine_name} - {self.get_status_display()}"
    
    def add_history_entry(self, action, user, notes=None):
        entry = {
            'action': action,
            'user': user.get_full_name() or user.username,
            'timestamp': timezone.now().isoformat(),
            'notes': notes
        }
        if not isinstance(self.history, list):
            self.history = []
        self.history.append(entry)
        self.save(update_fields=['history'])
        
        
        
        
        
        
import random
from datetime import datetime, timedelta

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        # OTP only valid for 10 minutes
        return (datetime.now() - self.created_at.replace(tzinfo=None)) < timedelta(minutes=10)
    
    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))
    
    def __str__(self):
        return f"{self.user.email} - {self.otp}"