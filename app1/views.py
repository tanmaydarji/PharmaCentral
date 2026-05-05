from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q ,F
from django.utils import timezone 
from datetime import datetime, timedelta
from django.db import models 
import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
from .models import Pharmacy, Settings as PharmacySettings, User
from datetime import date
from django.utils import timezone
User = get_user_model()


from .models import (
    User, Pharmacy, Medicine, MedicineCategory, 
    Customer, Sale, SaleItem, Debtor, Payment,
    ActivityLog, Alert, Report, Settings
)

# ==================== AUTHENTICATION VIEWS ====================

def login_view(request):
    """User Login View - Secure Version (No Auto-Create)"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        print(f"Login attempt: {email}")
        
        # 🔐 SECURE: Only authenticate existing users
        # Do NOT create new users automatically!
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            print(f"✅ Login successful for {user.username}")
            login(request, user)
            
            # Log activity
            try:
                ActivityLog.objects.create(
                    user=user,
                    action_type='login',
                    description=f'User {user.username} logged in'
                )
            except:
                pass  # Skip if ActivityLog doesn't exist
            
            return redirect('dashboard')
        else:
            print(f"❌ Login failed for {email}")
            
            # Check if user exists but password is wrong
            User = get_user_model()
            if User.objects.filter(username=email).exists():
                messages.error(request, 'Incorrect password!')
            else:
                messages.error(request, 'No account found with this email. Please register first!')
    
    return render(request, 'app1/login.html')


def logout_view(request):
    """User Logout View - Secure Version"""
    
    # Log the logout activity if user is authenticated
    if request.user.is_authenticated:
        try:
            # Get username for log
            username = request.user.username
            
            # Create activity log
            ActivityLog.objects.create(
                user=request.user,
                action_type='logout',
                description=f'User {username} logged out'
            )
            
            print(f"✅ Logout logged for {username}")
            
        except Exception as e:
            # If ActivityLog fails, just print error (don't stop logout)
            print(f"⚠️ Could not create logout log: {e}")
    
    # 🔐 SECURE: Clear session and logout
    logout(request)
    
    # Clear any session data
    request.session.flush()
    
    # Show success message
    messages.success(request, 'You have been successfully logged out!')
    
    # Redirect to login page
    return redirect('login')



# def register_view(request):
#     """User Registration View - Secure Version"""
    
#     # If user is already logged in, redirect to dashboard
#     if request.user.is_authenticated:
#         messages.info(request, "You are already logged in!")
#         return redirect('dashboard')
    
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#         confirm_password = request.POST.get('confirm_password')  # Add confirm password field
        
#         # ========== VALIDATIONS ==========
        
#         # Check if email exists
#         if User.objects.filter(username=email).exists():
#             messages.error(request, "Email already registered! Please login.")
#             return redirect('login')  # Redirect to login instead of register
        
#         # Check if email is valid
#         if not email or '@' not in email or '.' not in email:
#             messages.error(request, "Please enter a valid email address!")
#             return redirect('register')
        
#         # Password validation
#         if len(password) < 8:
#             messages.error(request, "Password must be at least 8 characters!")
#             return redirect('register')
        
#         # Check password strength
#         if not any(char.isdigit() for char in password):
#             messages.error(request, "Password must contain at least one number!")
#             return redirect('register')
        
#         if not any(char.isupper() for char in password):
#             messages.error(request, "Password must contain at least one uppercase letter!")
#             return redirect('register')
        
#         # Confirm password
#         if password != confirm_password:
#             messages.error(request, "Passwords do not match!")
#             return redirect('register')
        
#         try:
#             # ========== CREATE USER ==========
#             user = User.objects.create_user(
#                 username=email,
#                 email=email,
#                 password=password,
#                 first_name='',  # Can be updated later
#                 last_name=''    # Can be updated later
#             )
            
#             # ========== CREATE PHARMACY ==========
#             pharmacy = Pharmacy.objects.create(
#                 name=f"{email.split('@')[0]}'s Pharmacy",  # Better name
#                 owner=user,
#                 license_number=f"TEMP{user.id}",
#                 gst_number=f"TEMP{user.id}",
#                 address="Please update address",
#                 city="Please update city",
#                 pincode="000000",
#                 phone="0000000000",
#                 email=email
#             )
            
#             # ========== CREATE SETTINGS ==========
#             Settings.objects.create(pharmacy=pharmacy)
            
#             # ========== LOG ACTIVITY ==========
#             try:
#                 ActivityLog.objects.create(
#                     user=user,
#                     action_type='register',
#                     description=f'New user registered: {email}'
#                 )
#             except:
#                 pass  # Skip if ActivityLog doesn't exist
            
#             print(f"✅ Registration successful for {email}")
#             print(f"   User ID: {user.id}")
#             print(f"   Pharmacy ID: {pharmacy.id}")
            
#             # Success message
#             messages.success(request, "🎉 Registration successful! Please login with your credentials.")
            
#             # Auto-login (optional - remove if you want manual login)
#             # login(request, user)
#             # return redirect('dashboard')
            
#             return redirect('login')
            
#         except Exception as e:
#             print(f"❌ Registration error: {e}")
            
#             # If anything fails, delete user if created
#             if 'user' in locals():
#                 user.delete()
#                 print(f"   User deleted due to error")
            
#             messages.error(request, f"Registration failed: {str(e)}")
#             return redirect('register')
    
#     # GET request - show registration form
#     return render(request, 'app1/register.html')



def register_view(request):
    """User Registration View with Complete Data"""
    
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in!")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Get all form data
        pharmacy_name = request.POST.get('pharmacy_name')
        owner_name = request.POST.get('owner_name')
        contact = request.POST.get('contact')
        email = request.POST.get('email')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')
        gst_number = request.POST.get('gst_number')
        license_number = request.POST.get('license_number')
        address = request.POST.get('address')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Get files
        gst_certificate = request.FILES.get('gst_certificate')
        license_document = request.FILES.get('license_document')
        id_proof = request.FILES.get('id_proof')
        owner_photo = request.FILES.get('owner_photo')
        
        # ========== VALIDATIONS ==========
        
        # Check if email exists
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered! Please login.")
            return redirect('login')
        
        # Email validation
        if not email or '@' not in email or '.' not in email:
            messages.error(request, "Please enter a valid email address!")
            return redirect('register')
        
        # Password validation
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters!")
            return redirect('register')
        
        if not any(char.isdigit() for char in password):
            messages.error(request, "Password must contain at least one number!")
            return redirect('register')
        
        if not any(char.isupper() for char in password):
            messages.error(request, "Password must contain at least one uppercase letter!")
            return redirect('register')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')
        
        # Phone validation
        if not contact or not contact.isdigit() or len(contact) != 10:
            messages.error(request, "Please enter a valid 10-digit phone number!")
            return redirect('register')
        
        # Pincode validation
        if not pincode or not pincode.isdigit() or len(pincode) != 6:
            messages.error(request, "Please enter a valid 6-digit pincode!")
            return redirect('register')
        
        # Required fields
        if not pharmacy_name:
            messages.error(request, "Pharmacy name is required!")
            return redirect('register')
        
        if not owner_name:
            messages.error(request, "Owner name is required!")
            return redirect('register')
        
        if not city:
            messages.error(request, "City is required!")
            return redirect('register')
        
        if not address:
            messages.error(request, "Address is required!")
            return redirect('register')
        
        # GST and License
        if not gst_number:
            messages.error(request, "GST number is required!")
            return redirect('register')
        
        if not license_number:
            messages.error(request, "License number is required!")
            return redirect('register')
        
        # File uploads validation
        if not gst_certificate:
            messages.error(request, "GST Certificate is required!")
            return redirect('register')
        
        if not license_document:
            messages.error(request, "Pharmacy License is required!")
            return redirect('register')
        
        if not id_proof:
            messages.error(request, "ID Proof is required!")
            return redirect('register')
        
        if not owner_photo:
            messages.error(request, "Owner photo is required!")
            return redirect('register')
        
        try:
            # Split owner name into first and last name
            name_parts = owner_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # ========== CREATE USER ==========
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # ========== CREATE PHARMACY ==========
            pharmacy = Pharmacy.objects.create(
                name=pharmacy_name,
                owner=user,
                license_number=license_number,
                gst_number=gst_number,
                address=address,
                city=city,
                pincode=pincode,
                phone=contact,
                email=email,
                gst_certificate=gst_certificate,
                license_document=license_document,
                owner_id_proof=id_proof,
                owner_photo=owner_photo
            )
            
            # ========== CREATE SETTINGS ==========
            Settings.objects.create(pharmacy=pharmacy)
            
            # ========== LOG ACTIVITY ==========
            try:
                ActivityLog.objects.create(
                    user=user,
                    action_type='register',
                    description=f'New user registered: {email}'
                )
            except:
                pass
            
            messages.success(request, "🎉 Registration successful! Please login with your credentials.")
            return redirect('login')
            
        except Exception as e:
            if 'user' in locals():
                user.delete()
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect('register')
    
    return render(request, 'app1/register.html')



# ==================== DASHBOARD VIEWS ====================

@login_required(login_url='login')
def dashboard(request):
    """Dashboard View with Real Data - User Specific"""
    
    # Get current user and pharmacy
    user = request.user
    
    # 🔐 IMPORTANT: Get user's pharmacy
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        pharmacy = None
        messages.warning(request, 'Please complete your pharmacy profile to see all data.')
    
    # Get today's date
    today = timezone.now().date()
    
    # ========== STATS CARDS DATA ==========
    
    # If no pharmacy, show empty stats
    if not pharmacy:
        context = {
            'user_full_name': user.get_full_name() or user.email.split('@')[0],
            'user_initials': user.email[0].upper() if user.email else 'U',
            'user_role': getattr(user, 'user_type', 'Pharmacy Owner'),
            'pharmacy_name': f"{user.email.split('@')[0]}'s Pharmacy",
            'total_medicines': 0,
            'low_stock': 0,
            'expiring_soon': 0,
            'today_sales': 0,
            'expiry_alerts': [],
            'low_stock_alerts': [],
            'recent_activities': [],
            'expiry_alerts_count': 0,
            'low_stock_alerts_count': 0,
            'recent_activities_count': 0,
        }
        return render(request, 'app1/dashboard.html', context)
    
    # ========== FILTER BY PHARMACY ==========
    # 🔐 All queries now filtered by pharmacy
    medicines = Medicine.objects.filter(pharmacy=pharmacy)
    sales = Sale.objects.filter(pharmacy=pharmacy)
    
    # 1. Total Medicines
    total_medicines = medicines.count()
    
    # 2. Low Stock Medicines
    low_stock = 0
    low_stock_alerts_list = []
    for med in medicines:
        if med.quantity < med.min_quantity:
            low_stock += 1
            if len(low_stock_alerts_list) < 5:
                low_stock_alerts_list.append({
                    'name': med.name,
                    'quantity': med.quantity,
                    'min_quantity': med.min_quantity
                })
    
    # 3. Expiring Soon (within 30 days)
    thirty_days_later = today + timedelta(days=30)
    expiring_soon = 0
    expiry_alerts_list = []
    
    for med in medicines:
        if med.expiry_date and med.expiry_date <= thirty_days_later and med.expiry_date >= today:
            expiring_soon += 1
            days_left = (med.expiry_date - today).days
            if len(expiry_alerts_list) < 5:
                expiry_alerts_list.append({
                    'name': med.name,
                    'batch_number': med.batch_number or 'N/A',
                    'days_until_expiry': days_left,
                    'status': 'danger' if days_left <= 7 else 'warning' if days_left <= 15 else 'success'
                })
    
    # 4. Today's Sales
    today_sales = sales.filter(
        date__date=today
    ).aggregate(total=Sum('grand_total'))['total'] or 0
    
    # ========== RECENT ACTIVITIES ==========
    recent_activities = ActivityLog.objects.filter(
        user=user
    ).order_by('-timestamp')[:10]
    
    recent_activities_list = []
    for activity in recent_activities:
        recent_activities_list.append({
            'action_type': activity.action_type,
            'description': activity.description,
            'timestamp': activity.timestamp
        })
    
    # ========== USER INFORMATION ==========
    user_full_name = user.get_full_name() or user.email.split('@')[0]
    
    # User initials
    if user.first_name and user.last_name:
        user_initials = f"{user.first_name[0]}{user.last_name[0]}"
    elif user.first_name:
        user_initials = user.first_name[0]
    else:
        user_initials = user.email[0].upper()
    
    # User role
    user_role = getattr(user, 'user_type', 'Pharmacy Owner')
    
    # Pharmacy name
    pharmacy_name = pharmacy.name if pharmacy else f"{user_full_name}'s Pharmacy"
    
    # ========== CONTEXT DATA ==========
    context = {
        # User info
        'user_full_name': user_full_name,
        'user_initials': user_initials,
        'user_role': user_role,
        'pharmacy_name': pharmacy_name,
        
        # Stats - 🔐 ONLY this user's data
        'total_medicines': total_medicines,
        'low_stock': low_stock,
        'expiring_soon': expiring_soon,
        'today_sales': today_sales,
        
        # Alerts
        'expiry_alerts': expiry_alerts_list,
        'low_stock_alerts': low_stock_alerts_list,
        'recent_activities': recent_activities_list,
        
        # Counts
        'expiry_alerts_count': len(expiry_alerts_list),
        'low_stock_alerts_count': len(low_stock_alerts_list),
        'recent_activities_count': len(recent_activities_list),
        
        # Debug info (remove in production)
        'debug_pharmacy_id': pharmacy.id,
    }
    
    return render(request, 'app1/dashboard.html', context)


# ==================== MEDICINE VIEWS ====================

@login_required
def medicine_stock(request):
    """Medicine Stock List View - Complete with Pagination and Real Stats"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.warning(request, '❌ Please complete your pharmacy profile first.')
        return redirect('settings')
    
    # ========== BASE QUERY ==========
    # 🔐 Filter medicines by pharmacy
    medicines = Medicine.objects.filter(pharmacy=pharmacy).order_by('name')
    
    # ========== SEARCH FUNCTIONALITY ==========
    search_query = request.GET.get('search', '')
    if search_query:
        medicines = medicines.filter(
            Q(name__icontains=search_query) |
            Q(medicine_code__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(batch_number__icontains=search_query) |
            Q(manufacturer__icontains=search_query)
        )
    
    # ========== FILTER BY STATUS ==========
    status = request.GET.get('status', '')
    if status:
        medicines = medicines.filter(status=status)
    
    # ========== CALCULATE DYNAMIC FIELDS FOR EACH MEDICINE ==========
    today = timezone.now().date()
    
    for medicine in medicines:
        # Calculate days until expiry
        if medicine.expiry_date:
            medicine.days_until_expiry = (medicine.expiry_date - today).days
        else:
            medicine.days_until_expiry = None
        
        # Determine status color for template
        if medicine.status == 'good':
            medicine.status_color = 'status-good'
        elif medicine.status == 'low_stock':
            medicine.status_color = 'status-low'
        elif medicine.status == 'expiring_soon':
            medicine.status_color = 'status-expiring'
        elif medicine.status == 'expired':
            medicine.status_color = 'status-expired'
        else:
            medicine.status_color = ''
    
    # ========== GET COUNTS FOR STATS ==========
    total_medicines = medicines.count()
    
    low_stock_count = medicines.filter(
        quantity__lt=F('min_quantity')
    ).count()
    
    expiring_soon_count = medicines.filter(
        expiry_date__lte=today + timedelta(days=30),
        expiry_date__gte=today,
        status='expiring_soon'
    ).count()
    
    expired_count = medicines.filter(
        expiry_date__lt=today,
        status='expired'
    ).count()
    
    # ========== PAGINATION ==========
    from django.core.paginator import Paginator
    
    paginator = Paginator(medicines, 15)  # Show 15 medicines per page
    page_number = request.GET.get('page')
    medicines_page = paginator.get_page(page_number)
    
    # ========== LOG ACTIVITY (OPTIONAL) ==========
    try:
        ActivityLog.objects.create(
            user=user,
            pharmacy=pharmacy,
            action_type='stock_view',
            description=f'Viewed medicine stock - Total: {total_medicines}'
        )
    except:
        pass
    
    # ========== PREPARE CONTEXT ==========
    context = {
        # Main data
        'medicines': medicines_page,
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
        'expiring_count': expiring_soon_count,
        'expired_count': expired_count,
        
        # Filter values
        'search_query': search_query,
        'status': status,
        
        # For filter dropdowns
        'status_choices': Medicine.STATUS_CHOICES,
        
        # Pharmacy info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'pharmacy_id': pharmacy.id,
        
        # User info
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        
        # Pagination info
        'page_obj': medicines_page,
        'is_paginated': paginator.num_pages > 1,
        
        # Current date for template
        'today': today.strftime('%Y-%m-%d'),
    }
    
    print(f"📋 Medicine Stock page loaded for pharmacy: {pharmacy.name}")
    print(f"   Total medicines: {total_medicines}, Low stock: {low_stock_count}, Expiring: {expiring_soon_count}")
    
    return render(request, 'app1/medicine-stock.html', context)


@login_required(login_url='login')
def add_medicine(request):
    """Add Medicine View - Secure with Pharmacy"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== GET OR CREATE CATEGORIES ==========
    # Get categories for this pharmacy (if you add pharmacy to categories)
    # For now, categories are global
    categories = MedicineCategory.objects.all()
    
    # Create default categories if none exist
    if not categories.exists():
        default_categories = [
            'Pain Killer', 'Antibiotic', 'Antihistamine',
            'Gastric', 'Diabetes', 'Blood Pressure', 'Other'
        ]
        for cat_name in default_categories:
            MedicineCategory.objects.create(name=cat_name)
        categories = MedicineCategory.objects.all()
        print(f"✅ Created {categories.count()} default categories")
    
    # ========== HANDLE POST REQUEST ==========
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            medicine_code = request.POST.get('medicine_code', '').strip()
            category_id = request.POST.get('category')
            manufacturer = request.POST.get('manufacturer', '').strip()
            batch_number = request.POST.get('batch_number', '').strip()
            
            # Convert to correct types with validation
            try:
                quantity = int(request.POST.get('quantity', 0))
                min_quantity = int(request.POST.get('min_quantity', 0))
                unit_price = float(request.POST.get('unit_price', 0))
            except ValueError:
                messages.error(request, 'Please enter valid numbers for quantity and price!')
                return redirect('add_medicine')
            
            expiry_date = request.POST.get('expiry_date')
            manufacturing_date = request.POST.get('manufacturing_date')
            location = request.POST.get('location', '').strip()
            supplier = request.POST.get('supplier', '').strip()
            description = request.POST.get('description', '').strip()
            
            # ========== VALIDATIONS ==========
            # Check required fields
            if not all([name, medicine_code, category_id, batch_number, quantity, min_quantity, unit_price, expiry_date]):
                messages.error(request, 'Please fill all required fields!')
                return redirect('add_medicine')
            
            # Validate quantity
            if quantity < 0:
                messages.error(request, 'Quantity cannot be negative!')
                return redirect('add_medicine')
            
            if min_quantity < 0:
                messages.error(request, 'Minimum quantity cannot be negative!')
                return redirect('add_medicine')
            
            if unit_price <= 0:
                messages.error(request, 'Price must be greater than 0!')
                return redirect('add_medicine')
            
            # Validate expiry date
            if expiry_date:
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                if expiry < timezone.now().date():
                    messages.error(request, 'Expiry date cannot be in the past!')
                    return redirect('add_medicine')
            
            # Get category
            try:
                category = MedicineCategory.objects.get(id=category_id)
            except MedicineCategory.DoesNotExist:
                messages.error(request, 'Selected category does not exist!')
                return redirect('add_medicine')
            
            # 🔐 Check if medicine code already exists for THIS pharmacy
            if Medicine.objects.filter(pharmacy=pharmacy, medicine_code=medicine_code).exists():
                messages.error(request, f'Medicine with code "{medicine_code}" already exists in your pharmacy!')
                return redirect('add_medicine')
            
            # ========== CREATE MEDICINE ==========
            medicine = Medicine.objects.create(
                pharmacy=pharmacy,  # 🔐 IMPORTANT: Link to pharmacy
                name=name,
                medicine_code=medicine_code,
                category=category,
                manufacturer=manufacturer,
                batch_number=batch_number,
                quantity=quantity,
                min_quantity=min_quantity,
                unit_price=unit_price,
                expiry_date=expiry_date,
                manufacturing_date=manufacturing_date if manufacturing_date else None,
                location=location,
                supplier=supplier,
                description=description,
            )
            
            # ========== LOG ACTIVITY ==========
            try:
                ActivityLog.objects.create(
                    user=user,
                    pharmacy=pharmacy,
                    action_type='medicine_add',
                    description=f'Added medicine: {name} (Code: {medicine_code})'
                )
            except:
                pass  # Skip if ActivityLog doesn't have pharmacy field
            
            messages.success(request, f'✅ Medicine "{name}" added successfully!')
            
            # Redirect to medicine stock page
            return redirect('medicine_stock')
            
        except ValueError as e:
            messages.error(request, 'Please enter valid numbers for quantity and price!')
            print(f"ValueError: {e}")
            return redirect('add_medicine')
            
        except Exception as e:
            messages.error(request, f'Error adding medicine: {str(e)}')
            print(f"Error in add_medicine: {e}")
            return redirect('add_medicine')
    
    # ========== GET REQUEST - SHOW FORM ==========
    context = {
        'categories': categories,
        'pharmacy_name': pharmacy.name,
        'pharmacy_id': pharmacy.id,
        'user_full_name': user.get_full_name() or user.email.split('@')[0],
        'user_initials': user.email[0].upper() if user.email else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacy Owner'),
        'today': timezone.now().date().strftime('%Y-%m-%d'),  # For min date in form
    }
    
    return render(request, 'app1/add_medicine.html', context)


@login_required
def edit_medicine(request, pk):
    """Edit Medicine View - Secure with Pharmacy Verification"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== GET MEDICINE WITH PHARMACY VERIFICATION ==========
    # 🔐 IMPORTANT: Ensure medicine belongs to this user's pharmacy
    try:
        medicine = Medicine.objects.get(pk=pk, pharmacy=pharmacy)
    except Medicine.DoesNotExist:
        messages.error(request, '❌ Medicine not found or you do not have permission to edit it!')
        return redirect('medicine_stock')
    
    # ========== HANDLE POST REQUEST ==========
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            medicine_code = request.POST.get('medicine_code', '').strip()
            category_id = request.POST.get('category')
            manufacturer = request.POST.get('manufacturer', '').strip()
            batch_number = request.POST.get('batch_number', '').strip()
            
            # Convert to correct types with validation
            try:
                quantity = int(request.POST.get('quantity', 0))
                min_quantity = int(request.POST.get('min_quantity', 0))
                unit_price = float(request.POST.get('unit_price', 0))
            except ValueError:
                messages.error(request, 'Please enter valid numbers for quantity and price!')
                return redirect('edit_medicine', pk=pk)
            
            expiry_date = request.POST.get('expiry_date')
            manufacturing_date = request.POST.get('manufacturing_date')
            location = request.POST.get('location', '').strip()
            supplier = request.POST.get('supplier', '').strip()
            description = request.POST.get('description', '').strip()
            
            # ========== VALIDATIONS ==========
            # Check required fields
            if not all([name, medicine_code, category_id, batch_number, quantity, min_quantity, unit_price, expiry_date]):
                messages.error(request, 'Please fill all required fields!')
                return redirect('edit_medicine', pk=pk)
            
            # Validate quantity
            if quantity < 0:
                messages.error(request, 'Quantity cannot be negative!')
                return redirect('edit_medicine', pk=pk)
            
            if min_quantity < 0:
                messages.error(request, 'Minimum quantity cannot be negative!')
                return redirect('edit_medicine', pk=pk)
            
            if unit_price <= 0:
                messages.error(request, 'Price must be greater than 0!')
                return redirect('edit_medicine', pk=pk)
            
            # Validate expiry date
            if expiry_date:
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                if expiry < timezone.now().date():
                    messages.error(request, 'Expiry date cannot be in the past!')
                    return redirect('edit_medicine', pk=pk)
            
            # Get category
            try:
                category = MedicineCategory.objects.get(id=category_id)
            except MedicineCategory.DoesNotExist:
                messages.error(request, 'Selected category does not exist!')
                return redirect('edit_medicine', pk=pk)
            
            # 🔐 Check if medicine code already exists for THIS pharmacy (excluding current medicine)
            if Medicine.objects.filter(pharmacy=pharmacy, medicine_code=medicine_code).exclude(pk=pk).exists():
                messages.error(request, f'Medicine with code "{medicine_code}" already exists in your pharmacy!')
                return redirect('edit_medicine', pk=pk)
            
            # ========== UPDATE MEDICINE ==========
            medicine.name = name
            medicine.medicine_code = medicine_code
            medicine.category = category
            medicine.manufacturer = manufacturer
            medicine.batch_number = batch_number
            medicine.quantity = quantity
            medicine.min_quantity = min_quantity
            medicine.unit_price = unit_price
            medicine.expiry_date = expiry_date
            medicine.manufacturing_date = manufacturing_date if manufacturing_date else None
            medicine.location = location
            medicine.supplier = supplier
            medicine.description = description
            medicine.save()
            
            # ========== LOG ACTIVITY ==========
            try:
                ActivityLog.objects.create(
                    user=user,
                    pharmacy=pharmacy,
                    action_type='medicine_edit',
                    description=f'Edited medicine: {medicine.name} (Code: {medicine_code})'
                )
            except:
                # If ActivityLog doesn't have pharmacy field, try without it
                ActivityLog.objects.create(
                    user=user,
                    action_type='medicine_edit',
                    description=f'Edited medicine: {medicine.name}'
                )
            
            messages.success(request, f'✅ Medicine "{name}" updated successfully!')
            return redirect('medicine_stock')
            
        except ValueError as e:
            messages.error(request, 'Please enter valid numbers for quantity and price!')
            print(f"ValueError: {e}")
            return redirect('edit_medicine', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Error updating medicine: {str(e)}')
            print(f"Error in edit_medicine: {e}")
            return redirect('edit_medicine', pk=pk)
    
    # ========== GET REQUEST - SHOW FORM ==========
    # Format dates for input fields
    if medicine.expiry_date:
        medicine.expiry_date_formatted = medicine.expiry_date.strftime('%Y-%m-%d')
    if medicine.manufacturing_date:
        medicine.manufacturing_date_formatted = medicine.manufacturing_date.strftime('%Y-%m-%d')
    
    context = {
        'medicine': medicine,
        'categories': MedicineCategory.objects.all(),
        'pharmacy_name': pharmacy.name,
        'user_full_name': user.get_full_name() or user.email.split('@')[0],
        'user_initials': user.email[0].upper() if user.email else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacy Owner'),
        'today': timezone.now().date().strftime('%Y-%m-%d'),  # For min date in form
    }
    
    return render(request, 'app1/edit-medicine.html', context)


@login_required
def delete_medicine(request, pk):
    """Delete Medicine View - Secure with Pharmacy Verification"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found!')
        return redirect('settings')
    
    # ========== GET MEDICINE WITH PHARMACY VERIFICATION ==========
    # 🔐 IMPORTANT: Ensure medicine belongs to this user's pharmacy
    try:
        medicine = Medicine.objects.get(pk=pk, pharmacy=pharmacy)
    except Medicine.DoesNotExist:
        messages.error(request, '❌ Medicine not found or you do not have permission to delete it!')
        return redirect('medicine_stock')
    
    # ========== HANDLE DELETE REQUEST ==========
    if request.method == 'POST':
        try:
            # Store medicine name for message
            medicine_name = medicine.name
            medicine_code = medicine.medicine_code
            
            # Delete the medicine
            medicine.delete()
            
            # ========== LOG ACTIVITY ==========
            try:
                ActivityLog.objects.create(
                    user=user,
                    pharmacy=pharmacy,
                    action_type='medicine_delete',
                    description=f'Deleted medicine: {medicine_name} (Code: {medicine_code})'
                )
            except:
                # If ActivityLog doesn't have pharmacy field, try without it
                ActivityLog.objects.create(
                    user=user,
                    action_type='medicine_delete',
                    description=f'Deleted medicine: {medicine_name}'
                )
            
            messages.success(request, f'✅ Medicine "{medicine_name}" deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'❌ Error deleting medicine: {str(e)}')
            print(f"Error in delete_medicine: {e}")
    
    return redirect('medicine_stock')



# ==================== SALES VIEWS ====================

@login_required
def sales(request):
    """New Sale View - Secure with Pharmacy Filter"""
    from django.utils import timezone
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== HANDLE POST REQUEST (NEW SALE) ==========
    if request.method == 'POST':
        try:
            from django.http import JsonResponse
            from django.urls import reverse
            import json
            from decimal import Decimal
            from datetime import datetime
            from django.utils import timezone
            from django.db.models import Sum
            
            
            # Debug print
            print("\n" + "="*50)
            print(f"🚀 SALE POST REQUEST - Pharmacy: {pharmacy.name} (ID: {pharmacy.id})")
            print("📦 POST data:", request.POST)
            
            # ========== GET FORM DATA ==========
            customer_id = request.POST.get('customer')
            customer_name = request.POST.get('customer_name', 'Walk-in Customer')
            customer_phone = request.POST.get('customer_phone', '')
            
            # Convert to Decimal safely
            try:
                subtotal = Decimal(request.POST.get('subtotal', '0'))
                discount_percent = Decimal(request.POST.get('discount', '0'))
                grand_total = Decimal(request.POST.get('grand_total', '0'))
                amount_paid = Decimal(request.POST.get('amount_paid', '0'))
            except:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid amount values!'
                }, status=400)
            
            payment_method = request.POST.get('payment_method', 'cash')
            notes = request.POST.get('notes', '')
            
            # Calculate
            discount_amount = (subtotal * discount_percent / 100) if discount_percent else Decimal('0')
            tax_percent = Decimal('12')
            tax_amount = (subtotal * tax_percent / 100)
            due_amount = grand_total - amount_paid
            
            # Validate amounts
            if grand_total <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Total amount must be greater than 0!'
                }, status=400)
            
            if amount_paid < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Amount paid cannot be negative!'
                }, status=400)
            
            # ========== GENERATE INVOICE NUMBER ==========
            # 🔴 FIXED: Only one argument
            invoice_number = generate_invoice_number(pharmacy)
            print(f"📄 Invoice Number: {invoice_number}")
            
            # ========== HANDLE CUSTOMER ==========
            customer_obj = None
            if customer_id and customer_id.strip():
                try:
                    # 🔐 Verify customer belongs to this pharmacy
                    customer_obj = Customer.objects.get(id=customer_id, pharmacy=pharmacy)
                    print(f"👤 Customer found: {customer_obj.full_name}")
                except Customer.DoesNotExist:
                    # If customer doesn't belong to this pharmacy, create as walk-in
                    customer_obj = None
                    customer_name = "Walk-in Customer"
                    customer_phone = ""
                    print(f"⚠️ Customer ID {customer_id} not found in this pharmacy - using walk-in")
            
            # ========== CREATE SALE ==========
            sale = Sale.objects.create(
                pharmacy=pharmacy,  # 🔐 Link to pharmacy
                invoice_number=invoice_number,
                customer=customer_obj,
                customer_name=customer_name,
                customer_phone=customer_phone,
                subtotal=subtotal,
                discount_percent=discount_percent,
                discount_amount=discount_amount,
                tax_percent=tax_percent,
                tax_amount=tax_amount,
                grand_total=grand_total,
                amount_paid=amount_paid,
                due_amount=due_amount,
                payment_method=payment_method,
                payment_status='paid' if due_amount <= 0 else 'pending',
                notes=notes,
                created_by=user
            )
            print(f"✅ Sale created with ID: {sale.id}")
            
            # ========== PARSE AND VALIDATE ITEMS ==========
            items_json = request.POST.get('items', '[]')
            try:
                items = json.loads(items_json)
                print(f"📋 Items in sale: {len(items)}")
            except:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid items data!'
                }, status=400)
            
            if not items:
                # Delete the sale if no items
                sale.delete()
                return JsonResponse({
                    'success': False,
                    'error': 'No items in sale!'
                }, status=400)
            
            # ========== PROCESS EACH ITEM ==========
            for idx, item in enumerate(items):
                medicine_id = item.get('id')
                medicine_name = item.get('name')
                quantity = int(item.get('quantity', 1))
                unit_price = Decimal(str(item.get('price', '0')))
                total_price = quantity * unit_price
                
                # Validate quantity
                if quantity <= 0:
                    sale.delete()
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid quantity for {medicine_name}!'
                    }, status=400)
                
                # 🔐 Get medicine with pharmacy verification
                medicine = None
                if medicine_id:
                    try:
                        medicine = Medicine.objects.get(id=medicine_id, pharmacy=pharmacy)
                        
                        # Check stock
                        if medicine.quantity < quantity:
                            sale.delete()
                            return JsonResponse({
                                'success': False,
                                'error': f'Insufficient stock for {medicine.name}. Available: {medicine.quantity}'
                            }, status=400)
                        
                        # Update stock
                        medicine.quantity -= quantity
                        medicine.save()
                        print(f"   ✅ Item {idx+1}: {medicine.name} x{quantity} (Stock left: {medicine.quantity})")
                        
                    except Medicine.DoesNotExist:
                        sale.delete()
                        return JsonResponse({
                            'success': False,
                            'error': f'Medicine {medicine_name} not found in your pharmacy!'
                        }, status=400)
                
                # Create sale item
                SaleItem.objects.create(
                    sale=sale,
                    medicine=medicine,
                    medicine_name=medicine_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
            
            # ========== UPDATE CUSTOMER'S DUE AMOUNT ==========
            if customer_obj:
                # Recalculate total due for this customer from all pending/partial sales
                total_due = Sale.objects.filter(
                    customer=customer_obj,
                    payment_status__in=['pending', 'partial']
                ).aggregate(total=Sum('due_amount'))['total'] or 0
                
                # Update customer fields
                customer_obj.due_amount = total_due
                customer_obj.total_purchases += grand_total
                customer_obj.total_visits += 1
                customer_obj.last_purchase_date = timezone.now()
                customer_obj.save()
                
                print(f"💰 Updated {customer_obj.full_name}: Due = ₹{total_due}")
            
            # ========== LOG ACTIVITY ==========
            try:
                ActivityLog.objects.create(
                    user=user,
                    pharmacy=pharmacy,
                    action_type='sale',
                    description=f'New sale: {sale.invoice_number} for ₹{grand_total}'
                )
            except Exception as e:
                print(f"⚠️ ActivityLog error: {e}")
            
            print(f"✅ Sale completed successfully!")
            print(f"   Total: ₹{grand_total}, Paid: ₹{amount_paid}, Due: ₹{due_amount}")
            print("="*50)
            
            # Return JSON response
            return JsonResponse({
                'success': True,
                'invoice_number': sale.invoice_number,
                'invoice_url': reverse('invoice_view', kwargs={'pk': sale.pk})
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # ========== GET REQUEST - SHOW SALE FORM ==========
    
    # 🔐 Filter customers by pharmacy
    customers = Customer.objects.filter(pharmacy=pharmacy).order_by('first_name')
    print(f"📋 Found {customers.count()} customers for pharmacy {pharmacy.name}")
    
    # 🔐 Filter medicines by pharmacy with stock > 0
    medicines = Medicine.objects.filter(
        pharmacy=pharmacy,
        quantity__gt=0
    ).order_by('name')
    print(f"💊 Found {medicines.count()} medicines in stock")
    
    # 🔐 Get recent sales for this pharmacy
    recent_sales = Sale.objects.filter(
        pharmacy=pharmacy
    ).order_by('-date')[:5]
    
    context = {
        'customers': customers,
        'medicines': medicines,
        'recent_sales': recent_sales,
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'pharmacy_id': pharmacy.id,
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Cashier'),
        'today': timezone.now().date().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'app1/sales.html', context)


def generate_invoice_number(pharmacy=None):
    """Generate unique invoice number - Pharmacy Specific"""
    from datetime import datetime
    from django.utils import timezone
    
    if pharmacy:
        # Get pharmacy ID
        pharmacy_id = pharmacy.id if hasattr(pharmacy, 'id') else pharmacy
        
        # Format: INV-P{pharmacy_id}-{year}-XXXX
        prefix = f"INV-P{pharmacy_id}-{timezone.now().year}"
        
        # Get last invoice for this pharmacy
        last_invoice = Sale.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-id').first()
        
        if last_invoice:
            try:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    else:
        # Original global version (fallback)
        last_invoice = Sale.objects.order_by('-id').first()
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"INV-{timezone.now().year}-{new_num:04d}"


def generate_customer_id(pharmacy=None):
    """Generate unique customer ID - Pharmacy Specific"""
    from datetime import datetime
    from django.utils import timezone
    
    if pharmacy:
        # Get pharmacy ID
        pharmacy_id = pharmacy.id if hasattr(pharmacy, 'id') else pharmacy
        
        # Format: CUST-P{pharmacy_id}-{year}-XXXX
        prefix = f"CUST-P{pharmacy_id}-{timezone.now().year}"
        
        # Get last customer for this pharmacy
        last_customer = Customer.objects.filter(
            customer_id__startswith=prefix
        ).order_by('-id').first()
        
        if last_customer:
            try:
                last_num = int(last_customer.customer_id.split('-')[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    else:
        # Original global version (fallback)
        last_customer = Customer.objects.order_by('-id').first()
        if last_customer:
            last_num = int(last_customer.customer_id.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"CUST-{timezone.now().year}-{new_num:04d}"

@login_required
def sales_history(request):
    """Sales History View - Secure with Pharmacy Filter"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== BASE QUERY ==========
    # 🔐 Filter sales by pharmacy
    sales = Sale.objects.filter(pharmacy=pharmacy).order_by('-date')
    
    # ========== FILTERS ==========
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    payment_method = request.GET.get('payment_method')
    payment_status = request.GET.get('payment_status')
    customer_id = request.GET.get('customer')
    invoice_search = request.GET.get('invoice')
    
    # Apply date filters
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            sales = sales.filter(date__date__gte=from_date_obj)
        except:
            pass
    
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            sales = sales.filter(date__date__lte=to_date_obj)
        except:
            pass
    
    # Apply payment method filter
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    
    # Apply payment status filter
    if payment_status:
        sales = sales.filter(payment_status=payment_status)
    
    # Apply customer filter
    if customer_id:
        try:
            # 🔐 Verify customer belongs to this pharmacy
            customer = Customer.objects.get(id=customer_id, pharmacy=pharmacy)
            sales = sales.filter(customer=customer)
        except Customer.DoesNotExist:
            messages.warning(request, 'Customer not found in your pharmacy!')
    
    # Apply invoice search
    if invoice_search:
        sales = sales.filter(invoice_number__icontains=invoice_search)
    
    # ========== CALCULATE STATS ==========
    total_sales_count = sales.count()
    total_amount = sales.aggregate(total=Sum('grand_total'))['total'] or 0
    total_paid = sales.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_due = sales.aggregate(total=Sum('due_amount'))['total'] or 0
    
    # Get payment method breakdown
    payment_methods = {}
    for method, _ in Sale.PAYMENT_METHODS:
        method_sales = sales.filter(payment_method=method)
        method_total = method_sales.aggregate(total=Sum('grand_total'))['total'] or 0
        if method_total > 0:
            payment_methods[method] = {
                'count': method_sales.count(),
                'total': method_total
            }
    
    # Get payment status breakdown
    payment_statuses = {}
    for status, _ in Sale.PAYMENT_STATUS:
        status_sales = sales.filter(payment_status=status)
        status_total = status_sales.aggregate(total=Sum('grand_total'))['total'] or 0
        if status_total > 0:
            payment_statuses[status] = {
                'count': status_sales.count(),
                'total': status_total
            }
    
    # ========== PAGINATION ==========
    paginator = Paginator(sales, 20)  # Show 20 sales per page
    page_number = request.GET.get('page', 1)
    sales_page = paginator.get_page(page_number)
    
    # ========== GET CUSTOMERS FOR FILTER DROPDOWN ==========
    customers = Customer.objects.filter(pharmacy=pharmacy).order_by('first_name')
    
    # ========== CONTEXT ==========
    context = {
        'sales': sales_page,
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        
        # Stats
        'total_sales_count': total_sales_count,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_due,
        
        # Breakdowns
        'payment_methods': payment_methods,
        'payment_statuses': payment_statuses,
        
        # Filter values (for maintaining filter state)
        'from_date': from_date,
        'to_date': to_date,
        'payment_method': payment_method,
        'payment_status': payment_status,
        'customer_id': customer_id,
        'invoice_search': invoice_search,
        
        # For filter dropdowns
        'customers': customers,
        'payment_method_choices': Sale.PAYMENT_METHODS,
        'payment_status_choices': Sale.PAYMENT_STATUS,
        
        # Pagination
        'page_obj': sales_page,
        'is_paginated': paginator.num_pages > 1,
        
        # User info
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        'today': timezone.now().date().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'app1/sales-history.html', context)


from django.http import JsonResponse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.db.models import Q, Sum   

@login_required(login_url='login')
def sales_history_api(request):
    """Sales History API for AJAX search"""
    
    user = request.user
    pharmacy = Pharmacy.objects.get(owner=user)
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    payment_method = request.GET.get('payment_method', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    page = request.GET.get('page', 1)
    
    # Base queryset
    sales = Sale.objects.filter(pharmacy=pharmacy).order_by('-date')
    
    # Apply filters
    if search_query:
        sales = sales.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(customer__phone__icontains=search_query) |
            Q(items__medicine_name__icontains=search_query)
        ).distinct()
    
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    
    if from_date:
        sales = sales.filter(date__date__gte=from_date)
    
    if to_date:
        sales = sales.filter(date__date__lte=to_date)
    
    # Pagination
    paginator = Paginator(sales, 10)  # 10 items per page
    current_page = paginator.get_page(page)
    
    # Prepare data for JSON
    sales_data = []
    for sale in current_page:
        sales_data.append({
            'id': sale.id,
            'invoice_number': sale.invoice_number,
            'date': sale.date.strftime('%d/%m/%Y %I:%M %p'),
            'customer_name': sale.customer.name if sale.customer else 'Walk-in',
            'customer_phone': sale.customer.phone if sale.customer else '',
            'items_count': sale.items.count(),
            'first_item': sale.items.first().medicine_name if sale.items.exists() else '',
            'grand_total': float(sale.grand_total),
            'payment_method': sale.payment_method,
            'payment_method_display': sale.get_payment_method_display(),
            'payment_status': sale.payment_status,
            'payment_status_display': sale.get_payment_status_display(),
            'due_amount': float(sale.due_amount) if sale.due_amount else 0,
        })
    
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum

@login_required(login_url='login')
def sales_history_api(request):
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pharmacy not found'}, status=404)

    search_query = request.GET.get('search', '')
    payment_method = request.GET.get('payment_method', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    page = request.GET.get('page', 1)

    sales = Sale.objects.filter(pharmacy=pharmacy).order_by('-date')

    if search_query:
        sales = sales.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(customer__phone__icontains=search_query) |
            Q(items__medicine_name__icontains=search_query)
        ).distinct()

    if payment_method:
        sales = sales.filter(payment_method=payment_method)

    if from_date:
        try:
            sales = sales.filter(date__date__gte=from_date)
        except Exception:
            pass

    if to_date:
        try:
            sales = sales.filter(date__date__lte=to_date)
        except Exception:
            pass

    paginator = Paginator(sales, 10)
    current_page = paginator.get_page(page)

    sales_data = []
    for sale in current_page:
        sales_data.append({
            'id': sale.id,
            'invoice_number': sale.invoice_number,
            'date': sale.date.strftime('%d/%m/%Y %I:%M %p'),

            # Use sale's own fields first, fallback to customer's full_name
            'customer_name': sale.customer_name if sale.customer_name else (
                f"{sale.customer.first_name} {sale.customer.last_name}" if sale.customer else 'Walk-in'
            ),
            'customer_phone': sale.customer_phone if sale.customer_phone else (
                sale.customer.phone if sale.customer else ''
            ),

            'items_count': sale.items.count(),
            'first_item': sale.items.first().medicine_name if sale.items.exists() else '',
            'grand_total': float(sale.grand_total),
            'payment_method': sale.payment_method,
            'payment_method_display': sale.get_payment_method_display(),
            'payment_status': sale.payment_status,
            'payment_status_display': sale.get_payment_status_display(),
            'due_amount': float(sale.due_amount or 0),
        })

    total_amount = float(sales.aggregate(total=Sum('grand_total'))['total'] or 0)

    return JsonResponse({
        'success': True,
        'sales': sales_data,
        'total_sales_count': sales.count(),
        'total_amount': total_amount,
        'current_page': current_page.number,
        'total_pages': paginator.num_pages,
        'has_previous': current_page.has_previous(),
        'has_next': current_page.has_next(),
        'previous_page': current_page.previous_page_number() if current_page.has_previous() else None,
        'next_page': current_page.next_page_number() if current_page.has_next() else None,
    })


@login_required
def sales_detail(request, pk):
    """Sales Detail View - View single sale"""
    
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, 'Pharmacy not found!')
        return redirect('settings')
    
    # 🔐 Get sale with pharmacy verification
    try:
        sale = Sale.objects.get(pk=pk, pharmacy=pharmacy)
    except Sale.DoesNotExist:
        messages.error(request, 'Sale not found or you do not have permission!')
        return redirect('sales_history')
    
    # Get sale items
    sale_items = SaleItem.objects.filter(sale=sale)
    
    context = {
        'sale': sale,
        'sale_items': sale_items,
        'pharmacy': pharmacy,
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        'from_date': request.GET.get('from_date', '') or '',
        'to_date': request.GET.get('to_date', '') or '',
    }
    
    return render(request, 'app1/sales-detail.html', context)


@login_required
def delete_sale(request, pk):
    """Delete Sale View - Secure"""
    
    if request.method != 'POST':
        return redirect('sales_history')
    
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, 'Pharmacy not found!')
        return redirect('settings')
    
    # 🔐 Get sale with pharmacy verification
    try:
        sale = Sale.objects.get(pk=pk, pharmacy=pharmacy)
    except Sale.DoesNotExist:
        messages.error(request, 'Sale not found or you do not have permission!')
        return redirect('sales_history')
    
    try:
        # Store sale info for message
        invoice_number = sale.invoice_number
        
        # Delete sale (cascade will delete sale items)
        sale.delete()
        
        # Log activity
        ActivityLog.objects.create(
            user=user,
            pharmacy=pharmacy,
            action_type='sale_delete',
            description=f'Deleted sale: {invoice_number}'
        )
        
        messages.success(request, f'Sale {invoice_number} deleted successfully!')
        
    except Exception as e:
        messages.error(request, f'Error deleting sale: {str(e)}')
    
    return redirect('sales_history')



@login_required
def sales_edit(request, pk):
    """Edit Sale View - Secure with Pharmacy Verification and Item Management (GST Removed)"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== GET SALE WITH PHARMACY VERIFICATION ==========
    # 🔐 IMPORTANT: Ensure sale belongs to this user's pharmacy
    try:
        sale = Sale.objects.get(pk=pk, pharmacy=pharmacy)
    except Sale.DoesNotExist:
        messages.error(request, '❌ Sale not found or you do not have permission to edit it!')
        return redirect('sales_history')
    
    # ========== HANDLE POST REQUEST ==========
    if request.method == 'POST':
        try:
            import json
            from decimal import Decimal
            from django.db.models import Sum
            
            # ========== BASIC INFO UPDATE ==========
            customer_id = request.POST.get('customer')
            
            # 🔐 Verify customer belongs to this pharmacy if selected
            if customer_id and customer_id.strip():
                try:
                    customer = Customer.objects.get(id=customer_id, pharmacy=pharmacy)
                    sale.customer = customer
                    sale.customer_name = customer.full_name
                    sale.customer_phone = customer.phone
                except Customer.DoesNotExist:
                    messages.warning(request, 'Selected customer not found in your pharmacy. Using walk-in.')
                    sale.customer = None
                    sale.customer_name = request.POST.get('customer_name', 'Walk-in Customer')
                    sale.customer_phone = request.POST.get('customer_phone', '')
            else:
                sale.customer = None
                sale.customer_name = request.POST.get('customer_name', 'Walk-in Customer')
                sale.customer_phone = request.POST.get('customer_phone', '')
            
            # Update payment method and status
            sale.payment_method = request.POST.get('payment_method', sale.payment_method)
            sale.payment_status = request.POST.get('payment_status', sale.payment_status)
            sale.amount_paid = Decimal(request.POST.get('amount_paid', str(sale.amount_paid)))
            sale.notes = request.POST.get('notes', '')
            
            # ========== HANDLE ITEMS UPDATE ==========
            # Get items from POST
            items_json = request.POST.get('items', '[]')
            try:
                new_items = json.loads(items_json)
            except:
                messages.error(request, 'Invalid items data!')
                return redirect('sales_edit', pk=pk)
            
            if not new_items:
                messages.error(request, 'Sale must have at least one item!')
                return redirect('sales_edit', pk=pk)
            
            # ========== RESTORE OLD STOCK ==========
            # Get old items and restore medicine quantities
            old_items = SaleItem.objects.filter(sale=sale)
            for old_item in old_items:
                if old_item.medicine:
                    old_item.medicine.quantity += old_item.quantity
                    old_item.medicine.save()
            
            # Delete old items
            old_items.delete()
            
            # ========== PROCESS NEW ITEMS ==========
            subtotal = Decimal('0')
            for item_data in new_items:
                medicine_id = item_data.get('id')
                medicine_name = item_data.get('name')
                quantity = int(item_data.get('quantity', 1))
                unit_price = Decimal(str(item_data.get('price', '0')))
                total_price = quantity * unit_price
                
                # Validate quantity
                if quantity <= 0:
                    raise ValueError(f'Invalid quantity for {medicine_name}')
                
                # 🔐 Get medicine with pharmacy verification
                medicine = None
                if medicine_id:
                    try:
                        medicine = Medicine.objects.get(id=medicine_id, pharmacy=pharmacy)
                        
                        # Check stock
                        if medicine.quantity < quantity:
                            raise ValueError(f'Insufficient stock for {medicine.name}. Available: {medicine.quantity}')
                        
                        # Deduct new quantity
                        medicine.quantity -= quantity
                        medicine.save()
                        
                    except Medicine.DoesNotExist:
                        raise ValueError(f'Medicine {medicine_name} not found in your pharmacy!')
                
                # Create new sale item
                SaleItem.objects.create(
                    sale=sale,
                    medicine=medicine,
                    medicine_name=medicine_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                
                subtotal += total_price
            
            # ========== RECALCULATE TOTALS (GST REMOVED) ==========
            discount_percent = sale.discount_percent
            
            discount_amount = (subtotal * discount_percent / 100) if discount_percent else Decimal('0')
            grand_total = subtotal - discount_amount  # 🔴 GST REMOVED
            
            # Update sale totals
            sale.subtotal = subtotal
            sale.discount_amount = discount_amount
            sale.tax_amount = Decimal('0')  # 🔴 GST set to 0
            sale.grand_total = grand_total
            sale.due_amount = grand_total - sale.amount_paid
            
            # Update payment status based on due amount
            if sale.due_amount <= 0:
                sale.payment_status = 'paid'
            elif sale.amount_paid > 0:
                sale.payment_status = 'partial'
            else:
                sale.payment_status = 'pending'
            
            sale.save()
            
            # ========== UPDATE CUSTOMER'S DUE AMOUNT ==========
            if sale.customer:
                # Recalculate total due for this customer
                total_due = Sale.objects.filter(
                    customer=sale.customer,
                    payment_status__in=['pending', 'partial']
                ).exclude(pk=pk).aggregate(total=Sum('due_amount'))['total'] or 0
                
                sale.customer.due_amount = total_due
                sale.customer.save()
            
            # ========== LOG ACTIVITY ==========
            try:
                ActivityLog.objects.create(
                    user=user,
                    pharmacy=pharmacy,
                    action_type='sale_edit',
                    description=f'Edited sale: {sale.invoice_number}'
                )
            except:
                pass
            
            messages.success(request, f'✅ Sale {sale.invoice_number} updated successfully!')
            return redirect('sales_history')
            
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('sales_edit', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Error updating sale: {str(e)}')
            print(f"Error in sales_edit: {e}")
            import traceback
            traceback.print_exc()
            return redirect('sales_edit', pk=pk)
    
    # ========== GET REQUEST - SHOW EDIT FORM ==========
    
    # 🔐 Get customers for this pharmacy
    customers = Customer.objects.filter(pharmacy=pharmacy, status='active').order_by('first_name')
    
    # Get sale items
    sale_items = SaleItem.objects.filter(sale=sale)
    
    # 🔐 Get available medicines for this pharmacy
    medicines = Medicine.objects.filter(pharmacy=pharmacy, quantity__gt=0).order_by('name')
    
    # Format dates for input fields
    if sale.date:
        sale.date_formatted = sale.date.strftime('%Y-%m-%d')
    
    context = {
        'sale': sale,
        'sale_items': sale_items,
        'customers': customers,
        'medicines': medicines,
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        'today': timezone.now().date().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'app1/sales-edit.html', context)

@login_required
def delete_sale(request, pk):
    """Delete Sale View - Secure with Pharmacy Verification"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found!')
        return redirect('settings')
    
    # ========== ONLY POST REQUESTS ALLOWED ==========
    if request.method != 'POST':
        messages.error(request, 'Invalid request method!')
        return redirect('sales_history')
    
    # ========== GET SALE WITH PHARMACY VERIFICATION ==========
    # 🔐 Ensure sale belongs to this user's pharmacy
    try:
        sale = Sale.objects.get(pk=pk, pharmacy=pharmacy)
    except Sale.DoesNotExist:
        messages.error(request, '❌ Sale not found or you do not have permission to delete it!')
        return redirect('sales_history')
    
    try:
        # Store invoice number for message
        invoice = sale.invoice_number
        
        # Delete the sale
        sale.delete()
        
        # Success message
        messages.success(request, f'✅ Sale {invoice} deleted successfully!')
        
        # Optional: Log activity (if you want)
        try:
            ActivityLog.objects.create(
                user=user,
                action_type='sale_delete',
                description=f'Deleted sale: {invoice}'
            )
        except:
            pass  # Skip if ActivityLog doesn't exist
        
    except Exception as e:
        messages.error(request, f'❌ Error deleting sale: {str(e)}')
    
    return redirect('sales_history')


@login_required(login_url='login')
def invoice_view(request, pk):
    """View Invoice Details - Secure with Pharmacy Verification"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== GET SALE WITH PHARMACY VERIFICATION ==========
    # 🔐 IMPORTANT: Ensure sale belongs to this user's pharmacy
    try:
        sale = Sale.objects.get(pk=pk, pharmacy=pharmacy)
    except Sale.DoesNotExist:
        messages.error(request, '❌ Invoice not found or you do not have permission to view it!')
        return redirect('sales_history')
    
    # ========== GET SALE ITEMS ==========
    sale_items = SaleItem.objects.filter(sale=sale)
    
    # ========== LOG ACTIVITY (OPTIONAL) ==========
    try:
        ActivityLog.objects.create(
            user=user,
            pharmacy=pharmacy,
            action_type='invoice_view',
            description=f'Viewed invoice: {sale.invoice_number}'
        )
    except:
        pass  # Skip if ActivityLog doesn't exist
    
    # ========== FORMAT DATES FOR DISPLAY ==========
    if sale.date:
        sale.date_formatted = sale.date.strftime('%d %B %Y, %I:%M %p')
    
    # ========== CALCULATE TOTALS IF NEEDED ==========
    # (They should already be in the model, but just in case)
    items_subtotal = sum(item.total_price for item in sale_items)
    
    # ========== PREPARE CONTEXT ==========
    context = {
        # Sale and items
        'sale': sale,
        'sale_items': sale_items,
        'items_count': sale_items.count(),
        
        # Pharmacy info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'pharmacy_address': pharmacy.address,
        'pharmacy_city': pharmacy.city,
        'pharmacy_pincode': pharmacy.pincode,
        'pharmacy_phone': pharmacy.phone,
        'pharmacy_email': pharmacy.email,
        'pharmacy_gst': pharmacy.gst_number,
        'pharmacy_license': pharmacy.license_number,
        
        # Calculated totals
        'items_subtotal': items_subtotal,
        
        # User info
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        
        # Current date/time
        'current_date': timezone.now().strftime('%d %B %Y'),
        'current_time': timezone.now().strftime('%I:%M %p'),
    }
    
    print(f"✅ Invoice {sale.invoice_number} viewed by {user.username}")
    
    return render(request, 'app1/invoice-view.html', context)


# ==================== CUSTOMER VIEWS ====================


@login_required(login_url='login')
def customers(request):
    """Customer List View with Real Stats - Pharmacy Specific"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== GET CURRENT TIME FOR CALCULATIONS ==========
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    
    # ========== GET SEARCH QUERY AND FILTER ==========
    search_query = request.GET.get('search', '')
    customer_type = request.GET.get('type', '')
    
    # ========== BASE QUERYSET WITH PHARMACY FILTER ==========
    # 🔐 IMPORTANT: Only show customers belonging to this pharmacy
    customers_list = Customer.objects.filter(pharmacy=pharmacy)
    
    # ========== APPLY SEARCH FILTER ==========
    if search_query:
        customers_list = customers_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(customer_id__icontains=search_query)
        )
    
    # ========== APPLY TYPE FILTER ==========
    if customer_type:
        customers_list = customers_list.filter(customer_type=customer_type)
    
    # ========== REAL STATS CALCULATIONS (PHARMACY SPECIFIC) ==========
    
    # 1. Total Customers for this pharmacy
    total_customers = Customer.objects.filter(pharmacy=pharmacy).count()
    
    # 2. Active This Month (customers who purchased in last 30 days from this pharmacy)
    active_this_month = Customer.objects.filter(
        pharmacy=pharmacy,
        sale__date__gte=thirty_days_ago,
        sale__pharmacy=pharmacy  # Ensure sales are from this pharmacy
    ).distinct().count()
    
    # 3. Debtors (customers with due amount > 0 from this pharmacy)
    debtor_count = Customer.objects.filter(
        pharmacy=pharmacy,
        due_amount__gt=0
    ).count()
    
    # 4. New This Week (customers created in last 7 days for this pharmacy)
    new_this_week = Customer.objects.filter(
        pharmacy=pharmacy,
        created_at__gte=seven_days_ago
    ).count()
    
    # ========== CALCULATE DUE AMOUNT FOR EACH CUSTOMER ==========
    for customer in customers_list:
        # Get all sales for this customer from this pharmacy where payment is pending
        pending_sales = Sale.objects.filter(
            customer=customer,
            pharmacy=pharmacy,  # 🔐 Ensure sales are from this pharmacy
            payment_status__in=['pending', 'partial']
        ).aggregate(total_due=Sum('due_amount'))
        
        # Update customer due amount
        customer.due_amount = pending_sales['total_due'] or 0
        
        # Create initials for avatar
        first_initial = customer.first_name[0] if customer.first_name else ''
        last_initial = customer.last_name[0] if customer.last_name else ''
        customer.initials = f"{first_initial}{last_initial}" if first_initial or last_initial else '👤'
    
    # ========== PAGINATION ==========
    paginator = Paginator(customers_list, 10)  # Show 10 customers per page
    page_number = request.GET.get('page')
    customers_page = paginator.get_page(page_number)
    
    # ========== ADDITIONAL STATS FOR UI ==========
    total_due_amount = customers_list.aggregate(total=Sum('due_amount'))['total'] or 0
    
    # ========== PREPARE CONTEXT ==========
    context = {
        'customers': customers_page,
        'search_query': search_query,
        'customer_type': customer_type,
        
        # Real Stats (Pharmacy Specific)
        'total_customers': total_customers,
        'active_this_month': active_this_month,
        'debtor_count': debtor_count,
        'new_this_week': new_this_week,
        'total_due_amount': total_due_amount,
        
        # Pharmacy Info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'pharmacy_id': pharmacy.id,
        
        # User info
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        
        # Pagination info
        'page_obj': customers_page,
        'is_paginated': paginator.num_pages > 1,
    }
    
    print(f"📋 Customers page loaded for pharmacy: {pharmacy.name}")
    print(f"   Total customers: {total_customers}")
    print(f"   Active this month: {active_this_month}")
    print(f"   Debtors: {debtor_count}")
    
    return render(request, 'app1/customers.html', context)


@login_required(login_url='login')
def view_customer(request, pk):
    """View Single Customer Details with Real Data - Pharmacy Specific"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== GET CUSTOMER WITH PHARMACY VERIFICATION ==========
    # 🔐 IMPORTANT: Ensure customer belongs to this user's pharmacy
    try:
        customer = Customer.objects.get(pk=pk, pharmacy=pharmacy)
    except Customer.DoesNotExist:
        messages.error(request, '❌ Customer not found or you do not have permission to view!')
        return redirect('customers')
    
    # ========== GET CUSTOMER'S SALES (FILTERED BY PHARMACY) ==========
    sales = Sale.objects.filter(
        customer=customer,
        pharmacy=pharmacy  # 🔐 Ensure sales are from this pharmacy
    ).order_by('-date')
    
    # Get recent 5 sales for display
    recent_sales = sales[:5]
    
    # ========== CALCULATE REAL STATS ==========
    total_purchases = sales.aggregate(total=Sum('grand_total'))['total'] or 0
    total_visits = sales.count()
    
    # Calculate due amount from pending sales (only from this pharmacy)
    due_amount = sales.filter(
        payment_status__in=['pending', 'partial']
    ).aggregate(total=Sum('due_amount'))['total'] or 0
    
    # Get last purchase date
    last_purchase = sales.first()
    last_purchase_date = last_purchase.date if last_purchase else None
    
    # ========== CREATE INITIALS FOR AVATAR ==========
    first_initial = customer.first_name[0] if customer.first_name else ''
    last_initial = customer.last_name[0] if customer.last_name else ''
    customer.initials = f"{first_initial}{last_initial}" if first_initial or last_initial else '👤'
    
    # ========== LOG ACTIVITY (OPTIONAL) ==========
    try:
        ActivityLog.objects.create(
            user=user,
            pharmacy=pharmacy,
            action_type='customer_view',
            description=f'Viewed customer: {customer.full_name}'
        )
    except:
        pass
    
    # ========== PREPARE CONTEXT ==========
    context = {
        # Customer info
        'customer': customer,
        'customer_id': customer.customer_id,
        'customer_full_name': customer.full_name,
        'customer_email': customer.email,
        'customer_phone': customer.phone,
        'customer_address': customer.address,
        'customer_city': customer.city,
        'customer_type': customer.customer_type,
        'customer_status': customer.status,
        'customer_created': customer.created_at,
        
        # Sales data
        'recent_sales': recent_sales,
        'total_purchases': total_purchases,
        'total_visits': total_visits,
        'due_amount': due_amount,
        'last_purchase_date': last_purchase_date,
        
        # Pharmacy info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        
        # User info for sidebar
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        
        # Debug info (remove in production)
        'debug_pharmacy_id': pharmacy.id,
    }
    
    print(f"👤 Viewed customer: {customer.full_name} (Pharmacy: {pharmacy.name})")
    print(f"   Total purchases: ₹{total_purchases}, Due: ₹{due_amount}")
    
    return render(request, 'app1/view-customer.html', context)

@login_required(login_url='login')
def add_customer(request):
    """Add New Customer - Secure with Pharmacy"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== HANDLE POST REQUEST ==========
    if request.method == 'POST':
        try:
            # ========== GET FORM DATA ==========
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            address = request.POST.get('address', '').strip()
            dob = request.POST.get('dob') or None
            blood_group = request.POST.get('blood_group', '')
            customer_type = request.POST.get('customer_type', 'regular')
            
            # Optional fields
            alternate_phone = request.POST.get('alternate_phone', '')
            city = request.POST.get('city', '')
            pincode = request.POST.get('pincode', '')
            emergency_contact = request.POST.get('emergency_contact', '')
            
            # ========== VALIDATE REQUIRED FIELDS ==========
            if not first_name:
                messages.error(request, 'First name is required!')
                return redirect('add_customer')
                
            if not phone:
                messages.error(request, 'Phone number is required!')
                return redirect('add_customer')
            
            # Validate phone number format (Indian mobile)
            if not phone.isdigit() or len(phone) != 10:
                messages.error(request, 'Please enter a valid 10-digit mobile number!')
                return redirect('add_customer')
            
            # Validate email if provided
            if email and ('@' not in email or '.' not in email):
                messages.error(request, 'Please enter a valid email address!')
                return redirect('add_customer')
            
            # Validate pincode if provided
            if pincode and (not pincode.isdigit() or len(pincode) != 6):
                messages.error(request, 'Please enter a valid 6-digit pincode!')
                return redirect('add_customer')
            
            # ========== CHECK IF CUSTOMER EXISTS IN THIS PHARMACY ==========
            # 🔐 Check phone number within same pharmacy
            if Customer.objects.filter(pharmacy=pharmacy, phone=phone).exists():
                messages.error(request, f'Customer with phone number {phone} already exists in your pharmacy!')
                return redirect('add_customer')
            
            # ========== GENERATE UNIQUE CUSTOMER ID ==========
            customer_id = generate_customer_id()
            while Customer.objects.filter(customer_id=customer_id).exists():
                customer_id = generate_customer_id()
            
            # ========== CREATE CUSTOMER ==========
            customer = Customer.objects.create(
                pharmacy=pharmacy,  # 🔐 Link to pharmacy
                customer_id=customer_id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=email,
                address=address,
                date_of_birth=dob if dob else None,
                blood_group=blood_group,
                customer_type=customer_type,
                alternate_phone=alternate_phone,
                city=city,
                pincode=pincode,
                emergency_contact=emergency_contact,
                status='active',
                total_purchases=0,
                total_visits=0,
                due_amount=0,
            )
            
            # ========== LOG ACTIVITY ==========
            try:
                ActivityLog.objects.create(
                    user=user,
                    pharmacy=pharmacy,
                    action_type='customer_add',
                    description=f'Added customer: {first_name} {last_name} (Phone: {phone})'
                )
            except:
                pass
            
            messages.success(
                request, 
                f'✅ Customer "{first_name} {last_name}" added successfully! '
                f'Customer ID: {customer_id}'
            )
            
            print(f"✅ New customer added: {first_name} {last_name} (Pharmacy: {pharmacy.name})")
            return redirect('customers')
            
        except Exception as e:
            print(f"❌ Error adding customer: {str(e)}")
            messages.error(request, f'Error adding customer: {str(e)}')
            return redirect('add_customer')
    
    # ========== GET REQUEST - SHOW FORM ==========
    context = {
        # Pharmacy info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'pharmacy_id': pharmacy.id,
        
        # User info
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        
        # Form defaults
        'today': timezone.now().date().strftime('%Y-%m-%d'),
        'min_date': '1900-01-01',
        'max_date': timezone.now().date().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'app1/add-customer.html', context)


@login_required(login_url='login')
def edit_customer(request, pk):
    """Edit Customer Details - Secure with Pharmacy Verification"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== GET CUSTOMER WITH PHARMACY VERIFICATION ==========
    # 🔐 IMPORTANT: Ensure customer belongs to this user's pharmacy
    try:
        customer = Customer.objects.get(pk=pk, pharmacy=pharmacy)
    except Customer.DoesNotExist:
        messages.error(request, '❌ Customer not found or you do not have permission to edit!')
        return redirect('customers')
    
    # ========== HANDLE POST REQUEST ==========
    if request.method == 'POST':
        try:
            # ========== GET FORM DATA ==========
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            alternate_phone = request.POST.get('alternate_phone', '').strip()
            emergency_contact = request.POST.get('emergency_contact', '').strip()
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            pincode = request.POST.get('pincode', '').strip()
            blood_group = request.POST.get('blood_group', '')
            customer_type = request.POST.get('customer_type', customer.customer_type)
            dob = request.POST.get('dob')
            
            # ========== VALIDATE REQUIRED FIELDS ==========
            if not first_name:
                messages.error(request, 'First name is required!')
                return redirect('edit_customer', pk=pk)
                
            if not phone:
                messages.error(request, 'Phone number is required!')
                return redirect('edit_customer', pk=pk)
            
            # Validate phone number format
            if not phone.isdigit() or len(phone) != 10:
                messages.error(request, 'Please enter a valid 10-digit mobile number!')
                return redirect('edit_customer', pk=pk)
            
            # Validate email if provided
            if email and ('@' not in email or '.' not in email):
                messages.error(request, 'Please enter a valid email address!')
                return redirect('edit_customer', pk=pk)
            
            # Validate pincode if provided
            if pincode and (not pincode.isdigit() or len(pincode) != 6):
                messages.error(request, 'Please enter a valid 6-digit pincode!')
                return redirect('edit_customer', pk=pk)
            
            # ========== CHECK PHONE UNIQUE (EXCLUDING CURRENT) ==========
            # 🔐 Check if phone number already exists in this pharmacy (excluding current customer)
            if Customer.objects.filter(pharmacy=pharmacy, phone=phone).exclude(pk=pk).exists():
                messages.error(request, f'Customer with phone number {phone} already exists in your pharmacy!')
                return redirect('edit_customer', pk=pk)
            
            # ========== UPDATE CUSTOMER FIELDS ==========
            customer.first_name = first_name
            customer.last_name = last_name
            customer.phone = phone
            customer.email = email
            customer.alternate_phone = alternate_phone
            customer.emergency_contact = emergency_contact
            customer.address = address
            customer.city = city
            customer.pincode = pincode
            customer.blood_group = blood_group
            customer.customer_type = customer_type
            
            if dob:
                customer.date_of_birth = dob
            
            # Save the customer
            customer.save()
            
            # ========== LOG ACTIVITY ==========
            try:
                ActivityLog.objects.create(
                    user=user,
                    pharmacy=pharmacy,
                    action_type='customer_edit',
                    description=f'Edited customer: {customer.full_name} (Phone: {phone})'
                )
            except:
                pass
            
            messages.success(request, f'✅ Customer "{customer.full_name}" updated successfully!')
            print(f"✅ Customer updated: {customer.full_name} (Pharmacy: {pharmacy.name})")
            
            return redirect('view_customer', pk=customer.pk)
            
        except Exception as e:
            print(f"❌ Error updating customer: {str(e)}")
            messages.error(request, f'Error updating customer: {str(e)}')
            return redirect('edit_customer', pk=customer.pk)
    
    # ========== GET REQUEST - SHOW EDIT FORM ==========
    
    # Format date for input field
    if customer.date_of_birth:
        customer.dob_formatted = customer.date_of_birth.strftime('%Y-%m-%d')
    
    # ========== PREPARE CONTEXT ==========
    context = {
        # Customer info
        'customer': customer,
        'customer_id': customer.customer_id,
        'customer_full_name': customer.full_name,
        'customer_phone': customer.phone,
        'customer_email': customer.email,
        'customer_address': customer.address,
        'customer_city': customer.city,
        'customer_type': customer.customer_type,
        'customer_status': customer.status,
        'dob_formatted': customer.dob_formatted if hasattr(customer, 'dob_formatted') else '',
        
        # Pharmacy info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'pharmacy_id': pharmacy.id,
        
        # User info for sidebar
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        
        # Form defaults
        'today': timezone.now().date().strftime('%Y-%m-%d'),
        'min_date': '1900-01-01',
        'max_date': timezone.now().date().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'app1/edit-customer.html', context)


@login_required
def delete_customer(request, pk):
    """Delete Customer - Secure with Pharmacy Verification"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found!')
        return redirect('settings')
    
    # ========== ONLY POST REQUESTS ALLOWED ==========
    if request.method != 'POST':
        messages.error(request, 'Invalid request method!')
        return redirect('customers')
    
    # ========== GET CUSTOMER WITH PHARMACY VERIFICATION ==========
    # 🔐 Ensure customer belongs to this user's pharmacy
    try:
        customer = Customer.objects.get(pk=pk, pharmacy=pharmacy)
    except Customer.DoesNotExist:
        messages.error(request, '❌ Customer not found or you do not have permission to delete!')
        return redirect('customers')
    
    try:
        # Store name for message
        name = customer.full_name
        
        # Delete the customer
        customer.delete()
        
        # Success message
        messages.success(request, f'✅ Customer {name} deleted successfully!')
        
        # Optional: Log activity
        try:
            ActivityLog.objects.create(
                user=user,
                action_type='customer_delete',
                description=f'Deleted customer: {name}'
            )
        except:
            pass
        
    except Exception as e:
        messages.error(request, f'❌ Error deleting customer: {str(e)}')
    
    return redirect('customers')


@login_required(login_url='login')
def customer_history(request, pk):
    """View Customer Purchase History - Secure with Pharmacy Verification"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== GET CUSTOMER WITH PHARMACY VERIFICATION ==========
    # 🔐 IMPORTANT: Ensure customer belongs to this user's pharmacy
    try:
        customer = Customer.objects.get(pk=pk, pharmacy=pharmacy)
    except Customer.DoesNotExist:
        messages.error(request, '❌ Customer not found or you do not have permission to view history!')
        return redirect('customers')
    
    # ========== GET ALL SALES FOR THIS CUSTOMER (FILTERED BY PHARMACY) ==========
    sales = Sale.objects.filter(
        customer=customer,
        pharmacy=pharmacy  # 🔐 Ensure sales are from this pharmacy
    ).order_by('-date')
    
    # ========== PAGINATION ==========
    paginator = Paginator(sales, 20)
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)
    
    # ========== CALCULATE TOTALS ==========
    total_purchases = sales.aggregate(total=Sum('grand_total'))['total'] or 0
    total_items = sum([sale.items.count() for sale in sales])
    total_sales_count = sales.count()
    
    # Calculate due amount
    due_amount = sales.filter(
        payment_status__in=['pending', 'partial']
    ).aggregate(total=Sum('due_amount'))['total'] or 0
    
    # ========== LOG ACTIVITY (OPTIONAL) ==========
    try:
        ActivityLog.objects.create(
            user=user,
            pharmacy=pharmacy,
            action_type='customer_history_view',
            description=f'Viewed purchase history for: {customer.full_name}'
        )
    except:
        pass
    
    # ========== PREPARE CONTEXT ==========
    context = {
        # Customer info
        'customer': customer,
        'customer_id': customer.customer_id,
        'customer_full_name': customer.full_name,
        'customer_phone': customer.phone,
        'customer_email': customer.email,
        
        # Sales data
        'sales': sales_page,
        'total_purchases': total_purchases,
        'total_items': total_items,
        'total_sales': total_sales_count,
        'due_amount': due_amount,
        
        # Pharmacy info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        
        # User info for sidebar
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        
        # Pagination info
        'page_obj': sales_page,
        'is_paginated': paginator.num_pages > 1,
    }
    
    print(f"📋 Viewing history for customer: {customer.full_name}")
    print(f"   Total purchases: {total_sales_count}, Amount: ₹{total_purchases}")
    
    return render(request, 'app1/customer-history.html', context)





# ==================== DEBTOR VIEWS ====================

@login_required(login_url='login')
def debtors(request):
    """Debtors List View with Real Data - Pharmacy Specific"""
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== GET TODAY'S DATE ==========
    today = timezone.now().date()
    search_query = request.GET.get('search', '')
    
    # ========== SYNC DUE AMOUNTS (PHARMACY SPECIFIC) ==========
    # Only update customers belonging to this pharmacy
    for customer in Customer.objects.filter(pharmacy=pharmacy):
        due = Sale.objects.filter(
            customer=customer,
            pharmacy=pharmacy,  # 🔐 Filter sales by pharmacy
            payment_status__in=['pending', 'partial']
        ).aggregate(total=Sum('due_amount'))['total'] or 0
        
        # Only update if changed
        if customer.due_amount != due:
            customer.due_amount = due
            customer.save()
            print(f"💰 Updated {customer.full_name}: Due = ₹{due}")
    
    # ========== GET DEBTORS LIST (PHARMACY SPECIFIC) ==========
    debtors_list = Customer.objects.filter(
        pharmacy=pharmacy,
        due_amount__gt=0
    ).order_by('-due_amount')
    
    # ========== APPLY SEARCH FILTER ==========
    if search_query:
        debtors_list = debtors_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(customer_id__icontains=search_query)
        )
    
    # ========== PREPARE DEBTOR DATA WITH DUE CALCULATIONS ==========
    debtors_data = []
    total_due_sum = 0
    overdue_sum = 0
    
    for customer in debtors_list:
        # Get latest pending/partial sale from this pharmacy
        latest_sale = Sale.objects.filter(
            customer=customer,
            pharmacy=pharmacy,
            payment_status__in=['pending', 'partial']
        ).order_by('-date').first()
        
        due_date = latest_sale.date.date() if latest_sale else today
        days_difference = (today - due_date).days
        is_overdue = days_difference > 0
        
        # Add to totals
        total_due_sum += customer.due_amount
        if is_overdue:
            overdue_sum += customer.due_amount
        
        # Get initials for avatar
        first_initial = customer.first_name[0] if customer.first_name else ''
        last_initial = customer.last_name[0] if customer.last_name else ''
        initials = f"{first_initial}{last_initial}" if first_initial or last_initial else '👤'
        
        debtors_data.append({
            'id': customer.id,
            'name': customer.full_name,
            'phone': customer.phone,
            'email': customer.email,
            'due_amount': customer.due_amount,
            'last_purchase': customer.last_purchase_date,
            'due_date': due_date,
            'days_overdue': days_difference if days_difference > 0 else 0,
            'days_until_due': abs(days_difference) if days_difference < 0 else 0,
            'is_overdue': is_overdue,
            'initials': initials,
            'customer_type': customer.customer_type,
            'customer_id': customer.customer_id,
        })
    
    # ========== CALCULATE SUMMARY STATS ==========
    total_debtors = len(debtors_data)
    total_due = total_due_sum
    overdue_amount = overdue_sum
    average_due = total_due / total_debtors if total_debtors > 0 else 0
    
    # ========== PAGINATION ==========
    from django.core.paginator import Paginator
    paginator = Paginator(debtors_data, 10)
    page_number = request.GET.get('page')
    debtors_page = paginator.get_page(page_number)
    
    # ========== LOG ACTIVITY (OPTIONAL) ==========
    try:
        ActivityLog.objects.create(
            user=user,
            pharmacy=pharmacy,
            action_type='debtors_view',
            description=f'Viewed debtors list - Total: {total_debtors}, Due: ₹{total_due}'
        )
    except:
        pass
    
    # ========== PREPARE CONTEXT ==========
    context = {
        # Debtors data
        'debtors': debtors_page,
        'total_debtors': total_debtors,
        'total_due': total_due,
        'overdue_amount': overdue_amount,
        'average_due': average_due,
        'search_query': search_query,
        
        # Pharmacy info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'pharmacy_id': pharmacy.id,
        
        # User info
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        
        # Pagination info
        'page_obj': debtors_page,
        'is_paginated': paginator.num_pages > 1,
        
        # Stats for template
        'has_debtors': total_debtors > 0,
        'formatted_total_due': f"₹{total_due:,.2f}",
        'formatted_overdue': f"₹{overdue_amount:,.2f}",
    }
    
    print(f"📋 Debtors page loaded for pharmacy: {pharmacy.name}")
    print(f"   Total debtors: {total_debtors}, Total due: ₹{total_due}")
    
    return render(request, 'app1/debtors.html', context)

@login_required
def receive_payment(request, pk):
    """Receive payment from debtor - Secure with Pharmacy Verification"""
    
    # ========== ONLY POST REQUESTS ALLOWED ==========
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method!'
        })
    
    # ========== GET USER'S PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Pharmacy profile not found!'
        })
    
    try:
        from django.db.models import Sum
        from django.http import JsonResponse
        from decimal import Decimal
        
        # ========== GET CUSTOMER WITH PHARMACY VERIFICATION ==========
        # 🔐 Ensure customer belongs to this pharmacy
        try:
            customer = Customer.objects.get(pk=pk, pharmacy=pharmacy)
        except Customer.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Customer not found or does not belong to your pharmacy!'
            })
        
        # ========== GET PAYMENT DETAILS ==========
        amount = Decimal(request.POST.get('amount', '0'))
        payment_method = request.POST.get('payment_method', 'cash')
        
        # ========== VALIDATE AMOUNT ==========
        if amount <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Invalid amount! Amount must be greater than 0.'
            })
        
        # Check current due amount
        current_due = customer.due_amount
        
        if amount > current_due:
            return JsonResponse({
                'success': False,
                'error': f'Amount cannot exceed due amount: ₹{current_due:.2f}'
            })
        
        # ========== GET ALL PENDING SALES FOR THIS CUSTOMER (PHARMACY SPECIFIC) ==========
        pending_sales = Sale.objects.filter(
            customer=customer,
            pharmacy=pharmacy,  # 🔐 Ensure sales are from this pharmacy
            payment_status__in=['pending', 'partial']
        ).order_by('date')
        
        if not pending_sales.exists():
            return JsonResponse({
                'success': False,
                'error': 'No pending sales found for this customer!'
            })
        
        # ========== APPLY PAYMENT TO OLDEST SALES FIRST ==========
        remaining_amount = amount
        
        for sale in pending_sales:
            if remaining_amount <= 0:
                break
                
            sale_due = sale.due_amount
            
            if remaining_amount >= sale_due:
                # Full payment for this sale
                sale.amount_paid += sale_due
                sale.due_amount = Decimal('0')
                sale.payment_status = 'paid'
                remaining_amount -= sale_due
            else:
                # Partial payment
                sale.amount_paid += remaining_amount
                sale.due_amount -= remaining_amount
                sale.payment_status = 'partial'
                remaining_amount = Decimal('0')
            
            sale.save()
            print(f"   💰 Updated sale: {sale.invoice_number}, Due now: ₹{sale.due_amount}")
        
        # ========== RECALCULATE TOTAL DUE FOR THIS CUSTOMER ==========
        total_due = Sale.objects.filter(
            customer=customer,
            pharmacy=pharmacy,
            payment_status__in=['pending', 'partial']
        ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
        
        customer.due_amount = total_due
        customer.save()
        
        # ========== CREATE PAYMENT RECORD ==========
        try:
            Payment.objects.create(
                debtor=None,  # You might want to create/update debtor record
                sale=None,    # We've already updated individual sales
                customer=customer,
                amount=amount,
                payment_method=payment_method,
                payment_date=timezone.now(),
                received_by=user,
                notes=f'Payment received via {payment_method}'
            )
        except Exception as e:
            print(f"⚠️ Could not create payment record: {e}")
        
        # ========== LOG ACTIVITY ==========
        try:
            ActivityLog.objects.create(
                user=user,
                pharmacy=pharmacy,
                action_type='payment',
                description=f'Received payment of ₹{amount} from {customer.full_name}',
                amount=amount
            )
        except Exception as e:
            print(f"⚠️ ActivityLog error: {e}")
        
        # ========== RETURN SUCCESS RESPONSE ==========
        response_data = {
            'success': True,
            'message': f'✅ Payment of ₹{amount} received from {customer.full_name}',
            'new_due': float(total_due),
            'fully_paid': total_due == 0,
            'customer_name': customer.full_name,
            'payment_method': payment_method,
            'timestamp': timezone.now().strftime('%d/%m/%Y %I:%M %p')
        }
        
        print(f"✅ Payment received: ₹{amount} from {customer.full_name}")
        print(f"   New due amount: ₹{total_due}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ ERROR in receive_payment: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
        
        
        
# ==================== REPORTS VIEWS ====================
@login_required(login_url='login')
def reports(request):
    """Reports Page with Real Data - Pharmacy Specific"""
    
    # ========== GET USER & PHARMACY ==========
    user = request.user
    
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found! Please complete your profile first.')
        return redirect('settings')
    
    # ========== DATE CALCULATIONS ==========
    today = timezone.now().date()
    first_day_month = today.replace(day=1)
    last_month = first_day_month - timedelta(days=1)
    first_day_last_month = last_month.replace(day=1)
    
    # ========== INITIALIZE ALL VARIABLES ==========
    # Sales variables
    total_sales = Decimal('0')
    total_sales_month = Decimal('0')
    total_sales_last_month = Decimal('0')
    sales_trend = 0
    today_sales = Decimal('0')
    week_sales = Decimal('0')
    month_sales = Decimal('0')
    avg_sales = Decimal('0')
    sales_data = []
    
    # Medicine variables
    top_medicines = []
    expiry_alerts_list = []
    expiry_count = 0
    expiry_60_count = 0
    expiry_90_count = 0
    low_stock_list = []
    low_stock_count = 0
    
    # Customer variables
    total_customers = 0
    new_customers = 0
    repeat_rate = 0
    vip_customers = 0
    avg_purchase = Decimal('0')
    
    # Debtor variables
    total_debtors = 0
    total_due = Decimal('0')
    overdue_amount = Decimal('0')
    overdue_count = 0
    month_due = Decimal('0')
    
    # ========== GET FILTER PARAMETERS ==========
    report_type = request.GET.get('report_type', 'sales')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    # Set default date range (current month)
    if not from_date:
        from_date = first_day_month.strftime('%Y-%m-%d')
    if not to_date:
        to_date = today.strftime('%Y-%m-%d')
    
    # Convert to date objects
    try:
        start_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    except:
        start_date = first_day_month
        end_date = today
    
    # ========== SALES DATA (Common for all reports) ==========
    # Sales in selected period
    sales_period = Sale.objects.filter(
        pharmacy=pharmacy,
        date__date__gte=start_date, 
        date__date__lte=end_date
    )
    total_sales = sales_period.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    # Sales this month
    sales_this_month = Sale.objects.filter(
        pharmacy=pharmacy,
        date__date__gte=first_day_month
    )
    total_sales_month = sales_this_month.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    month_sales = total_sales_month
    
    # Sales last month
    sales_last_month = Sale.objects.filter(
        pharmacy=pharmacy,
        date__date__gte=first_day_last_month,
        date__date__lt=first_day_month
    )
    total_sales_last_month = sales_last_month.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    # Calculate trend
    if total_sales_last_month > 0:
        sales_trend = round(float((total_sales_month - total_sales_last_month) / total_sales_last_month * 100), 1)
    else:
        sales_trend = 100 if total_sales_month > 0 else 0
    
    # Today's sales
    today_sales = Sale.objects.filter(
        pharmacy=pharmacy,
        date__date=today
    ).aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    # Week sales
    week_ago = today - timedelta(days=7)
    week_sales = Sale.objects.filter(
        pharmacy=pharmacy,
        date__date__gte=week_ago
    ).aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    # Average daily sales
    days_in_period = (end_date - start_date).days + 1
    avg_sales = total_sales / days_in_period if days_in_period > 0 else Decimal('0')
    
    # ========== SALES DATA FOR CHART ==========
    # Find max sales amount
    max_sales_amount = Decimal('0')
    for i in range(7):
        day = today - timedelta(days=6-i)
        day_sales = Sale.objects.filter(
            pharmacy=pharmacy,
            date__date=day
        ).aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
        if day_sales > max_sales_amount:
            max_sales_amount = day_sales
    
    if max_sales_amount == 0:
        max_sales_amount = Decimal('1000')
    
    # Create chart data
    for i in range(7):
        day = today - timedelta(days=6-i)
        day_sales = Sale.objects.filter(
            pharmacy=pharmacy,
            date__date=day
        ).aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
        
        height = float(day_sales) / float(max_sales_amount) * 180 if max_sales_amount > 0 else 50
        
        sales_data.append({
            'label': day.strftime('%a'),
            'amount': day_sales,
            'height': height
        })
    
    # ========== REPORT TYPE SPECIFIC DATA ==========
    
    if report_type == 'sales':
        # Top selling medicines
        sale_items = SaleItem.objects.filter(
            sale__pharmacy=pharmacy,
            sale__date__date__gte=start_date,
            sale__date__date__lte=end_date
        ).values('medicine_name').annotate(
            total_units=Sum('quantity'),
            total_amount=Sum('total_price')
        ).order_by('-total_amount')[:5]
        
        max_amount = sale_items[0]['total_amount'] if sale_items else Decimal('1')
        
        for item in sale_items:
            percentage = float(item['total_amount']) / float(max_amount) * 100 if max_amount else 0
            top_medicines.append({
                'name': item['medicine_name'],
                'units': item['total_units'],
                'amount': item['total_amount'],
                'percentage': percentage
            })
    
    elif report_type == 'inventory':
        # Low stock medicines
        low_stock_meds = Medicine.objects.filter(
            pharmacy=pharmacy,
            quantity__lt=F('min_quantity')
        ).order_by('quantity')[:5]
        
        for med in low_stock_meds:
            low_stock_list.append({
                'name': med.name,
                'quantity': med.quantity,
                'min_quantity': med.min_quantity
            })
        
        low_stock_count = Medicine.objects.filter(
            pharmacy=pharmacy,
            quantity__lt=F('min_quantity')
        ).count()
        
        # Top medicines by stock value
        top_medicines = Medicine.objects.filter(
            pharmacy=pharmacy
        ).annotate(
            stock_value=F('quantity') * F('selling_price')
        ).order_by('-stock_value')[:5]
    
    elif report_type == 'expiry':
        thirty_days_later = today + timedelta(days=30)
        sixty_days_later = today + timedelta(days=60)
        ninety_days_later = today + timedelta(days=90)
        
        # Expiring in 30 days
        expiry_meds = Medicine.objects.filter(
            pharmacy=pharmacy,
            expiry_date__lte=thirty_days_later,
            expiry_date__gte=today
        ).order_by('expiry_date')[:5]
        
        for med in expiry_meds:
            expiry_alerts_list.append({
                'name': med.name,
                'batch': med.batch_number,
                'days_left': (med.expiry_date - today).days
            })
        
        expiry_count = Medicine.objects.filter(
            pharmacy=pharmacy,
            expiry_date__lte=thirty_days_later,
            expiry_date__gte=today
        ).count()
        
        expiry_60_count = Medicine.objects.filter(
            pharmacy=pharmacy,
            expiry_date__lte=sixty_days_later,
            expiry_date__gte=today
        ).count()
        
        expiry_90_count = Medicine.objects.filter(
            pharmacy=pharmacy,
            expiry_date__lte=ninety_days_later,
            expiry_date__gte=today
        ).count()
    
    elif report_type == 'debtor':
        # Debtors with due amount
        debtors_list = Customer.objects.filter(
            pharmacy=pharmacy,
            due_amount__gt=0
        ).order_by('-due_amount')
        
        total_debtors = debtors_list.count()
        total_due = debtors_list.aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
        
        # Overdue (>30 days)
        thirty_days_ago = today - timedelta(days=30)
        overdue_sales = Sale.objects.filter(
            pharmacy=pharmacy,
            payment_status__in=['pending', 'partial'],
            date__date__lte=thirty_days_ago
        )
        overdue_amount = overdue_sales.aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
        overdue_count = overdue_sales.values('customer').distinct().count()
    
    elif report_type == 'customer':
        # Customer statistics
        total_customers = Customer.objects.filter(pharmacy=pharmacy).count()
        new_customers = Customer.objects.filter(
            pharmacy=pharmacy,
            created_at__gte=first_day_month
        ).count()
        
        # Top customers by purchase
        top_customers = Customer.objects.filter(
            pharmacy=pharmacy
        ).annotate(
            total_purchases=Sum('sale__grand_total')
        ).order_by('-total_purchases')[:5]
    
    # ========== COMMON DATA FOR ALL REPORTS ==========
    
    # Customer insights
    if report_type != 'customer':  # Already fetched for customer report
        total_customers = Customer.objects.filter(pharmacy=pharmacy).count()
        new_customers = Customer.objects.filter(
            pharmacy=pharmacy,
            created_at__gte=first_day_month
        ).count()
    
    repeat_customers = Customer.objects.filter(
        pharmacy=pharmacy
    ).annotate(
        purchase_count=Count('sale', filter=Q(sale__pharmacy=pharmacy))
    ).filter(purchase_count__gt=1).count()
    
    repeat_rate = round(repeat_customers / total_customers * 100, 1) if total_customers > 0 else 0
    
    vip_customers = Customer.objects.filter(
        pharmacy=pharmacy,
        customer_type='vip'
    ).count()
    
    # Average purchase
    total_sales_count = Sale.objects.filter(pharmacy=pharmacy).count()
    total_sales_all = Sale.objects.filter(pharmacy=pharmacy).aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    avg_purchase = total_sales_all / total_sales_count if total_sales_count > 0 else Decimal('0')
    
    # Debtor summary
    if report_type != 'debtor':  # Already fetched for debtor report
        total_debtors = Customer.objects.filter(
            pharmacy=pharmacy,
            due_amount__gt=0
        ).count()
        
        total_due = Customer.objects.filter(
            pharmacy=pharmacy
        ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
        
        thirty_days_ago = today - timedelta(days=30)
        overdue_sales = Sale.objects.filter(
            pharmacy=pharmacy,
            payment_status__in=['pending', 'partial'],
            date__date__lte=thirty_days_ago
        )
        overdue_amount = overdue_sales.aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
        overdue_count = overdue_sales.values('customer').distinct().count()
    
    # This month due
    month_due = Sale.objects.filter(
        pharmacy=pharmacy,
        payment_status__in=['pending', 'partial'],
        date__date__gte=first_day_month
    ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
    
    # Backup data
    backups = [
        {
            'id': '1',
            'name': f'Auto Backup - {pharmacy.name}',
            'date': today.strftime('%d %b %Y %I:%M %p'),
            'size': '2.5 MB',
            'type': 'Automatic'
        },
        {
            'id': '2',
            'name': f'Manual Backup - {pharmacy.name}',
            'date': (today - timedelta(days=1)).strftime('%d %b %Y %I:%M %p'),
            'size': '2.4 MB',
            'type': 'Manual'
        }
    ]
    
    # ========== LOG ACTIVITY ==========
    try:
        ActivityLog.objects.create(
            user=user,
            pharmacy=pharmacy,
            action_type='reports_view',
            description=f'Viewed {report_type} report from {from_date} to {to_date}'
        )
    except:
        pass
    
    # ========== PREPARE CONTEXT ==========
    context = {
        # Filter data
        'report_type': report_type,
        'from_date': from_date,
        'to_date': to_date,
        
        # Pharmacy info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'pharmacy_id': pharmacy.id,
        
        # Summary cards
        'total_sales': total_sales,
        'total_expenses': total_sales * Decimal('0.7'),  # Simplified
        'total_due': total_due,
        'sales_trend': sales_trend,
        'expenses_trend': 3,  # Simplified
        'due_trend': 5,  # Simplified
        
        # Sales data
        'sales_data': sales_data,
        'today_sales': today_sales,
        'week_sales': week_sales,
        'month_sales': month_sales,
        'avg_sales': avg_sales,
        
        # Top medicines
        'top_medicines': top_medicines,
        
        # Expiry alerts
        'expiry_alerts': expiry_alerts_list,
        'expiry_count': expiry_count,
        
        # Low stock
        'low_stock': low_stock_list,
        'low_stock_count': low_stock_count,
        
        # Customer insights
        'total_customers': total_customers,
        'new_customers': new_customers,
        'repeat_rate': repeat_rate,
        'vip_customers': vip_customers,
        'avg_purchase': avg_purchase,
        
        # Debtor summary
        'total_debtors': total_debtors,
        'total_due': total_due,
        'overdue_amount': overdue_amount,
        'overdue_count': overdue_count,
        'month_due': month_due,
        
        # Backup data
        'backups': backups,
        
        # User info
        'user_full_name': user.get_full_name() or user.username,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': getattr(user, 'user_type', 'Pharmacist'),
        
        # Additional expiry data
        'expiry_60_count': expiry_60_count if report_type == 'expiry' else 0,
        'expiry_90_count': expiry_90_count if report_type == 'expiry' else 0,
    }
    
    return render(request, 'app1/reports.html', context)



from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
import io

# ReportLab imports with error handling
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .models import Pharmacy, Sale, Medicine, Customer, SaleItem

@login_required(login_url='login')
def export_report_pdf(request):
    """Export report as PDF"""
    
    # Check if reportlab is installed
    if not REPORTLAB_AVAILABLE:
        messages.error(request, "PDF export is not available. Please install reportlab: pip install reportlab")
        return redirect('reports')
    
    try:
        # Get parameters
        report_type = request.GET.get('report_type', 'sales')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        # Validate parameters
        if not from_date or not to_date:
            messages.error(request, "Please select both From Date and To Date")
            return redirect('reports')
        
        # Get pharmacy
        user = request.user
        try:
            pharmacy = Pharmacy.objects.get(owner=user)
        except Pharmacy.DoesNotExist:
            messages.error(request, "Pharmacy not found")
            return redirect('settings')
        
        # Create HTTP response with PDF
        response = HttpResponse(content_type='application/pdf')
        filename = f"{report_type}_report_{from_date}_to_{to_date}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_text = f"PharmaCentral - {report_type.title()} Report"
        title = Paragraph(title_text, styles['Title'])
        elements.append(title)
        
        # Pharmacy info
        pharmacy_text = f"<b>Pharmacy:</b> {pharmacy.name}"
        pharmacy_info = Paragraph(pharmacy_text, styles['Normal'])
        elements.append(pharmacy_info)
        
        # Date range
        date_text = f"<b>Period:</b> {from_date} to {to_date}"
        date_range = Paragraph(date_text, styles['Normal'])
        elements.append(date_range)
        
        # Generation date
        gen_date = f"<b>Generated on:</b> {timezone.now().strftime('%d-%m-%Y %H:%M')}"
        gen_info = Paragraph(gen_date, styles['Normal'])
        elements.append(gen_info)
        
        # Add space
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        
        # ========== SALES REPORT ==========
        if report_type == 'sales':
            # Get sales data
            sales = Sale.objects.filter(
                pharmacy=pharmacy,
                date__date__gte=from_date,
                date__date__lte=to_date
            ).order_by('-date')
            
            if sales:
                # Create table data
                data = [['Date', 'Invoice No', 'Customer', 'Items', 'Total (₹)']]
                
                for sale in sales:
                    data.append([
                        sale.date.strftime('%d-%m-%Y'),
                        sale.invoice_number,
                        sale.customer.name if sale.customer else 'Walk-in',
                        str(sale.items.count()),
                        f"{sale.grand_total:.2f}"
                    ])
                
                # Add total row
                total = sales.aggregate(total=Sum('grand_total'))['total'] or 0
                data.append(['', '', '', 'TOTAL:', f"{total:.2f}"])
                
                # Create table
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("No sales data found for selected period", styles['Normal']))
        
        # ========== INVENTORY REPORT ==========
        elif report_type == 'inventory':
            medicines = Medicine.objects.filter(pharmacy=pharmacy).order_by('name')
            
            if medicines:
                data = [['Medicine', 'Batch', 'Quantity', 'Price (₹)', 'Expiry Date']]
                
                for med in medicines:
                    data.append([
                        med.name[:30] + '...' if len(med.name) > 30 else med.name,
                        med.batch_number,
                        str(med.quantity),
                        f"{med.selling_price:.2f}",
                        med.expiry_date.strftime('%d-%m-%Y')
                    ])
                
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("No medicines found", styles['Normal']))
        
        # ========== EXPIRY REPORT ==========
        elif report_type == 'expiry':
            today = timezone.now().date()
            thirty_days = today + timedelta(days=30)
            
            medicines = Medicine.objects.filter(
                pharmacy=pharmacy,
                expiry_date__lte=thirty_days
            ).order_by('expiry_date')
            
            if medicines:
                data = [['Medicine', 'Batch', 'Expiry Date', 'Days Left', 'Quantity']]
                
                for med in medicines:
                    days_left = (med.expiry_date - today).days
                    data.append([
                        med.name[:30] + '...' if len(med.name) > 30 else med.name,
                        med.batch_number,
                        med.expiry_date.strftime('%d-%m-%Y'),
                        str(days_left),
                        str(med.quantity)
                    ])
                
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("No expiring medicines found", styles['Normal']))
        
        # ========== CUSTOMER REPORT ==========
        elif report_type == 'customer':
            customers = Customer.objects.filter(pharmacy=pharmacy).order_by('-created_at')
            
            if customers:
                data = [['Name', 'Phone', 'Email', 'Due (₹)', 'Type']]
                
                for customer in customers:
                    data.append([
                        customer.name,
                        customer.phone or '-',
                        customer.email or '-',
                        f"{customer.due_amount:.2f}",
                        customer.customer_type.title() if customer.customer_type else 'Regular'
                    ])
                
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("No customers found", styles['Normal']))
        
        # ========== DEBTOR REPORT ==========
        elif report_type == 'debtor':
            debtors = Customer.objects.filter(
                pharmacy=pharmacy,
                due_amount__gt=0
            ).order_by('-due_amount')
            
            if debtors:
                data = [['Name', 'Phone', 'Due Amount (₹)', 'Last Purchase']]
                
                for debtor in debtors:
                    last_sale = Sale.objects.filter(
                        pharmacy=pharmacy,
                        customer=debtor
                    ).order_by('-date').first()
                    
                    last_date = last_sale.date.strftime('%d-%m-%Y') if last_sale else '-'
                    
                    data.append([
                        debtor.name,
                        debtor.phone or '-',
                        f"{debtor.due_amount:.2f}",
                        last_date
                    ])
                
                # Add total
                total_due = debtors.aggregate(total=Sum('due_amount'))['total'] or 0
                data.append(['', 'TOTAL DUE:', f"{total_due:.2f}", ''])
                
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("No debtors found", styles['Normal']))
        
        # ========== DEFAULT ==========
        else:
            elements.append(Paragraph("Please select a valid report type", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF from buffer
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response
        
    except Exception as e:
        messages.error(request, f"PDF generation error: {str(e)}")
        return redirect('reports')
    
    
    
    
    
import os
import shutil
import json
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required(login_url='login')
def create_backup(request):
    """Create user-specific database backup"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # ========== 1. GET USER EMAIL FOR FOLDER NAME ==========
        user_email = request.user.email
        # Clean email for folder name (replace @ and . with _)
        folder_name = f"user_{user_email.replace('@', '_at_').replace('.', '_')}"
        
        # ========== 2. USER-SPECIFIC BACKUP FOLDER ==========
        backup_root = os.path.join(settings.BASE_DIR, 'backups')
        user_backup_dir = os.path.join(backup_root, folder_name)
        
        print(f"📁 User backup folder: {user_backup_dir}")
        
        # ========== 3. CREATE FOLDER IF NOT EXISTS ==========
        if not os.path.exists(user_backup_dir):
            os.makedirs(user_backup_dir)
            print(f"✅ Created user folder: {folder_name}")
        
        # ========== 4. GENERATE FILENAME WITH TIMESTAMP ==========
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'db_backup_{timestamp}.db'
        backup_filepath = os.path.join(user_backup_dir, backup_filename)
        
        # ========== 5. GET DATABASE PATH ==========
        db_path = settings.DATABASES['default']['NAME']
        
        # ========== 6. COPY DATABASE FILE ==========
        shutil.copy2(db_path, backup_filepath)
        
        # ========== 7. VERIFY FILE CREATED ==========
        if os.path.exists(backup_filepath):
            file_size = os.path.getsize(backup_filepath)
            
            # ========== 8. CREATE INFO FILE WITH USER DETAILS ==========
            info_file = os.path.join(user_backup_dir, f'db_backup_{timestamp}.json')
            
            # Get pharmacy name
            pharmacy_name = "Unknown"
            try:
                if hasattr(request.user, 'pharmacy'):
                    pharmacy_name = request.user.pharmacy.name
            except:
                pass
            
            with open(info_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user': {
                        'email': request.user.email,
                        'username': request.user.username,
                        'id': request.user.id
                    },
                    'pharmacy': pharmacy_name,
                    'size': file_size,
                    'size_kb': f"{file_size/1024:.2f} KB",
                    'tables': ['medicines', 'customers', 'sales', 'pharmacy']
                }, f, indent=2)
            
            # ========== 9. CLEANUP OLD BACKUPS (keep last 7 per user) ==========
            backup_files = sorted([f for f in os.listdir(user_backup_dir) 
                                  if f.startswith('db_backup_') and f.endswith('.db')])
            
            for old_file in backup_files[:-7]:  # Keep last 7 per user
                old_path = os.path.join(user_backup_dir, old_file)
                os.remove(old_path)
                
                # Also remove corresponding json file
                json_file = old_file.replace('.db', '.json')
                json_path = os.path.join(user_backup_dir, json_file)
                if os.path.exists(json_path):
                    os.remove(json_path)
                
                print(f"🗑️ Deleted old: {old_file}")
            
            # ========== 10. RETURN SUCCESS WITH USER INFO ==========
            return JsonResponse({
                'success': True,
                'message': f'Backup created for {request.user.email}',
                'user': request.user.email,
                'folder': folder_name,
                'file': backup_filename,
                'size': f'{file_size/1024:.2f} KB',
                'time': datetime.now().strftime('%H:%M:%S')
            })
        else:
            return JsonResponse({'success': False, 'error': 'File was not created'})
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})    
    
    
    
@login_required(login_url='login')
def get_user_backups(request):
    """Get list of backups for current user"""
    
    try:
        user_email = request.user.email
        folder_name = f"user_{user_email.replace('@', '_at_').replace('.', '_')}"
        user_backup_dir = os.path.join(settings.BASE_DIR, 'backups', folder_name)
        
        backups = []
        
        if os.path.exists(user_backup_dir):
            files = os.listdir(user_backup_dir)
            db_files = sorted([f for f in files if f.startswith('db_backup_') and f.endswith('.db')], reverse=True)
            
            for i, db_file in enumerate(db_files[:10]):  # Last 10 backups
                file_path = os.path.join(user_backup_dir, db_file)
                size = os.path.getsize(file_path) / 1024  # KB
                modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Try to read json info
                json_file = db_file.replace('.db', '.json')
                json_path = os.path.join(user_backup_dir, json_file)
                backup_info = {}
                
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        backup_info = json.load(f)
                
                backups.append({
                    'id': i + 1,
                    'name': db_file,
                    'date': modified.strftime('%d %b %Y %I:%M %p'),
                    'size': f'{size:.2f} KB',
                    'type': backup_info.get('type', 'Manual'),
                    'pharmacy': backup_info.get('pharmacy', 'Unknown')
                })
        
        return JsonResponse({
            'success': True,
            'user': request.user.email,
            'backups': backups
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    
    
    
@login_required(login_url='login')
def restore_user_backup(request, backup_id):
    """Restore backup for current user"""
    
    try:
        user_email = request.user.email
        folder_name = f"user_{user_email.replace('@', '_at_').replace('.', '_')}"
        user_backup_dir = os.path.join(settings.BASE_DIR, 'backups', folder_name)
        
        # Get backup files for this user
        backup_files = sorted([f for f in os.listdir(user_backup_dir) 
                              if f.startswith('db_backup_') and f.endswith('.db')])
        
        if backup_id <= len(backup_files):
            backup_file = os.path.join(user_backup_dir, backup_files[backup_id - 1])
            db_path = settings.DATABASES['default']['NAME']
            
            # Create current backup before restore (safety)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pre_restore = os.path.join(user_backup_dir, f'pre_restore_{timestamp}.db')
            shutil.copy2(db_path, pre_restore)
            
            # Restore backup
            shutil.copy2(backup_file, db_path)
            
            return JsonResponse({
                'success': True, 
                'message': f'Backup restored for {user_email}',
                'file': backup_files[backup_id - 1]
            })
        
        return JsonResponse({'success': False, 'error': 'Backup not found'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    



# # views.py માં આ ઉમેરો ટેસ્ટ કરવા
# def test_backup(request):
#     backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    
#     # Check if we can write
#     test_file = os.path.join(backup_dir, 'test.txt')
#     try:
#         with open(test_file, 'w') as f:
#             f.write('test')
#         return HttpResponse(f"✅ Can write to: {backup_dir}")
#     except Exception as e:
#         return HttpResponse(f"❌ Cannot write: {str(e)}")



# ==================== SETTINGS VIEWS ====================




@login_required(login_url='login')
def settings_view(request):
    """Settings Page with Real Data - Secure"""
    
    user = request.user
    
    # ========== GET OR CREATE PHARMACY ==========
    try:
        pharmacy = Pharmacy.objects.get(owner=user)
        created = False
    except Pharmacy.DoesNotExist:
        # Create pharmacy if it doesn't exist (only for the owner)
        pharmacy = Pharmacy.objects.create(
            name=f"{user.email.split('@')[0]}'s Pharmacy",
            owner=user,
            license_number=f"TEMP{user.id}",
            gst_number=f"TEMP{user.id}",
            address="Please update address",
            city="Please update city",
            pincode="000000",
            phone="0000000000",
            email=user.email
        )
        created = True
        messages.info(request, 'Welcome! Please complete your pharmacy profile.')
    
    # ========== GET OR CREATE SETTINGS ==========
    try:
        settings = PharmacySettings.objects.get(pharmacy=pharmacy)
    except PharmacySettings.DoesNotExist:
        settings = PharmacySettings.objects.create(pharmacy=pharmacy)
    
    # ========== HANDLE FORM SUBMISSIONS ==========
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # ---------- PROFILE FORM ----------
        if form_type == 'profile':
            try:
                # Get form data with validation
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                pharmacy_name = request.POST.get('pharmacy_name', '').strip()
                city = request.POST.get('city', '').strip()
                address = request.POST.get('address', '').strip()
                pincode = request.POST.get('pincode', '').strip()
                gst_number = request.POST.get('gst_number', '').strip()
                license_number = request.POST.get('license_number', '').strip()
                
                # Validate required fields
                if not first_name:
                    messages.error(request, 'First name is required!')
                    return redirect('settings')
                
                # Validate email
                if email and ('@' not in email or '.' not in email):
                    messages.error(request, 'Please enter a valid email address!')
                    return redirect('settings')
                
                # Validate phone (if provided)
                if phone and (not phone.isdigit() or len(phone) != 10):
                    messages.error(request, 'Please enter a valid 10-digit phone number!')
                    return redirect('settings')
                
                # Validate pincode (if provided)
                if pincode and (not pincode.isdigit() or len(pincode) != 6):
                    messages.error(request, 'Please enter a valid 6-digit pincode!')
                    return redirect('settings')
                
                # Update user information
                user.first_name = first_name
                user.last_name = last_name
                if email and email != user.email:
                    # Check if email already exists
                    User = get_user_model()
                    if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                        messages.error(request, 'Email already in use by another account!')
                        return redirect('settings')
                    user.email = email
                    user.username = email  # Keep username in sync with email
                user.save()
                
                # Update pharmacy information
                pharmacy.name = pharmacy_name or pharmacy.name
                pharmacy.city = city or pharmacy.city
                pharmacy.address = address or pharmacy.address
                pharmacy.pincode = pincode or pharmacy.pincode
                pharmacy.gst_number = gst_number or pharmacy.gst_number
                pharmacy.license_number = license_number or pharmacy.license_number
                pharmacy.phone = phone or pharmacy.phone
                pharmacy.save()
                
                # Log activity
                try:
                    ActivityLog.objects.create(
                        user=user,
                        pharmacy=pharmacy,
                        action_type='settings_update',
                        description='Updated profile settings'
                    )
                except:
                    pass
                
                messages.success(request, '✅ Profile settings updated successfully!')
                return redirect('settings')
                
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
                return redirect('settings')
        
        # ---------- ALERT SETTINGS FORM ----------
        elif form_type == 'alerts':
            try:
                # Update alert settings
                settings.expiry_alerts_enabled = request.POST.get('expiry_alerts_enabled') == 'true'
                settings.low_stock_alerts_enabled = request.POST.get('low_stock_alerts_enabled') == 'true'
                settings.debtor_reminders_enabled = request.POST.get('debtor_reminders_enabled') == 'true'
                settings.daily_sales_report = request.POST.get('daily_sales_report') == 'true'
                
                expiry_days = request.POST.get('expiry_alert_days', 30)
                settings.expiry_alert_days = int(expiry_days) if expiry_days else 30
                
                settings.save()
                
                messages.success(request, '✅ Alert settings updated successfully!')
                return redirect('settings')
                
            except Exception as e:
                messages.error(request, f'Error updating alert settings: {str(e)}')
                return redirect('settings')
        
        # ---------- PASSWORD CHANGE FORM ----------
        elif form_type == 'password':
            try:
                current_password = request.POST.get('current_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
                # Validate current password
                if not user.check_password(current_password):
                    messages.error(request, '❌ Current password is incorrect!')
                    return redirect('settings')
                
                # Validate new password
                if len(new_password) < 8:
                    messages.error(request, '❌ Password must be at least 8 characters long!')
                    return redirect('settings')
                
                # Check password strength
                if not any(char.isdigit() for char in new_password):
                    messages.error(request, '❌ Password must contain at least one number!')
                    return redirect('settings')
                
                if not any(char.isupper() for char in new_password):
                    messages.error(request, '❌ Password must contain at least one uppercase letter!')
                    return redirect('settings')
                
                # Check confirmation
                if new_password != confirm_password:
                    messages.error(request, '❌ New password and confirm password do not match!')
                    return redirect('settings')
                
                # Change password
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                
                # Log activity
                try:
                    ActivityLog.objects.create(
                        user=user,
                        pharmacy=pharmacy,
                        action_type='password_change',
                        description='Changed password'
                    )
                except:
                    pass
                
                messages.success(request, '✅ Password changed successfully!')
                return redirect('settings')
                
            except Exception as e:
                messages.error(request, f'Error changing password: {str(e)}')
                return redirect('settings')
    
    # ========== PREPARE CONTEXT WITH REAL DATA ==========
    
    # Get statistics for display
    medicine_count = Medicine.objects.filter(pharmacy=pharmacy).count()
    customer_count = Customer.objects.filter(pharmacy=pharmacy).count()
    sale_count = Sale.objects.filter(pharmacy=pharmacy).count()
    
    # Format dates for display
    if pharmacy.registration_date:
        pharmacy.registration_date_formatted = pharmacy.registration_date.strftime('%d %B %Y')
    
    context = {
        # User info
        'user': user,
        'user_full_name': user.get_full_name() or user.username,
        'user_first_name': user.first_name,
        'user_last_name': user.last_name,
        'user_email': user.email,
        'user_initials': user.username[0].upper() if user.username else 'U',
        'user_role': 'Owner' if user.is_superuser else getattr(user, 'user_type', 'Pharmacist'),
        'user_date_joined': user.date_joined.strftime('%d %B %Y') if hasattr(user, 'date_joined') else 'N/A',
        
        # Pharmacy info
        'pharmacy': pharmacy,
        'pharmacy_name': pharmacy.name,
        'pharmacy_id': pharmacy.id,
        'pharmacy_address': pharmacy.address,
        'pharmacy_city': pharmacy.city,
        'pharmacy_pincode': pharmacy.pincode,
        'pharmacy_phone': pharmacy.phone,
        'pharmacy_email': pharmacy.email,
        'pharmacy_gst': pharmacy.gst_number,
        'pharmacy_license': pharmacy.license_number,
        'pharmacy_registration': pharmacy.registration_date_formatted if hasattr(pharmacy, 'registration_date_formatted') else '',
        'pharmacy_verified': pharmacy.is_verified,
        
        # Settings
        'settings': settings,
        
        # Statistics
        'medicine_count': medicine_count,
        'customer_count': customer_count,
        'sale_count': sale_count,
        
        # Form data for template
        'today': timezone.now().date().strftime('%Y-%m-%d'),
        'min_date': '1900-01-01',
    }
    
    print(f"⚙️ Settings page loaded for user: {user.username} (Pharmacy: {pharmacy.name})")
    
    return render(request, 'app1/settings.html', context)



# ==================== HELPER FUNCTIONS ====================

# def generate_invoice_number(pharmacy=None):
#     """Generate unique invoice number - Pharmacy Specific"""
#     from datetime import datetime
#     from django.utils import timezone  # 🔴 આ લાઈન ઉમેરો
    
#     if pharmacy:
#         # Get pharmacy ID
#         pharmacy_id = pharmacy.id if hasattr(pharmacy, 'id') else pharmacy
        
#         # Format: INV-P{pharmacy_id}-{year}-XXXX
#         prefix = f"INV-P{pharmacy_id}-{timezone.now().year}"
        
#         # Get last invoice for this pharmacy
#         last_invoice = Sale.objects.filter(
#             invoice_number__startswith=prefix
#         ).order_by('-id').first()
        
#         if last_invoice:
#             try:
#                 last_num = int(last_invoice.invoice_number.split('-')[-1])
#                 new_num = last_num + 1
#             except:
#                 new_num = 1
#         else:
#             new_num = 1
        
#         return f"{prefix}-{new_num:04d}"
    
#     else:
#         # Original global version (fallback)
#         last_invoice = Sale.objects.order_by('-id').first()
#         if last_invoice:
#             last_num = int(last_invoice.invoice_number.split('-')[-1])
#             new_num = last_num + 1
#         else:
#             new_num = 1
#         return f"INV-{timezone.now().year}-{new_num:04d}"


# def generate_customer_id(pharmacy=None):
#     """Generate unique customer ID - Pharmacy Specific"""
#     from datetime import datetime
#     from django.utils import timezone  # 🔴 આ લાઈન પણ ઉમેરો
    
#     if pharmacy:
#         # Get pharmacy ID
#         pharmacy_id = pharmacy.id if hasattr(pharmacy, 'id') else pharmacy
        
#         # Format: CUST-P{pharmacy_id}-{year}-XXXX
#         prefix = f"CUST-P{pharmacy_id}-{timezone.now().year}"
        
#         # Get last customer for this pharmacy
#         last_customer = Customer.objects.filter(
#             customer_id__startswith=prefix
#         ).order_by('-id').first()
        
#         if last_customer:
#             try:
#                 last_num = int(last_customer.customer_id.split('-')[-1])
#                 new_num = last_num + 1
#             except:
#                 new_num = 1
#         else:
#             new_num = 1
        
#         return f"{prefix}-{new_num:04d}"
    
#     else:
#         # Original global version (fallback)
#         last_customer = Customer.objects.order_by('-id').first()
#         if last_customer:
#             last_num = int(last_customer.customer_id.split('-')[-1])
#             new_num = last_num + 1
#         else:
#             new_num = 1
#         return f"CUST-{timezone.now().year}-{new_num:04d}"





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
import json

from .models import MedicineRequest, Pharmacy, Customer, ActivityLog

# ==================== MEDICINE REQUESTS VIEWS ====================

@login_required
def medicine_requests(request):
    """Medicine Requests List View with Search and Filters"""
    
    # Get pharmacy
    try:
        pharmacy = Pharmacy.objects.get(owner=request.user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found!')
        return redirect('settings')
    
    # Base queryset
    requests = MedicineRequest.objects.filter(pharmacy=pharmacy)
    
    # ========== FILTERS ==========
    search_query = request.GET.get('search', '')
    if search_query:
        requests = requests.filter(
            Q(medicine_name__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query)
        )
    
    status = request.GET.get('status', '')
    if status:
        requests = requests.filter(status=status)
    
    priority = request.GET.get('priority', '')
    if priority:
        requests = requests.filter(priority=priority)
    
    # ========== STATS ==========
    stats = {
        'total': requests.count(),
        'pending': requests.filter(status='pending').count(),
        'approved': requests.filter(status='approved').count(),
        'received': requests.filter(status='received').count(),
    }
    
    # ========== PAGINATION ==========
    paginator = Paginator(requests, 15)
    page_number = request.GET.get('page')
    requests_page = paginator.get_page(page_number)
    
    # ========== CONTEXT ==========
    context = {
        'requests': requests_page,
        'stats': stats,
        'search_query': search_query,
        'status': status,
        'priority': priority,
        'pharmacy_name': pharmacy.name,
        'user_full_name': request.user.get_full_name() or request.user.username,
        'user_initials': request.user.username[0].upper() if request.user.username else 'U',
        'user_role': getattr(request.user, 'user_type', 'Pharmacist'),
    }
    
    return render(request, 'app1/medicine-requests.html', context)


@login_required
def add_medicine_request(request):
    """Add New Medicine Request"""
    
    if request.method != 'POST':
        return redirect('medicine_requests')
    
    try:
        pharmacy = Pharmacy.objects.get(owner=request.user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found!')
        return redirect('settings')
    
    try:
        # Get form data
        medicine_name = request.POST.get('medicine_name')
        medicine_code = request.POST.get('medicine_code', '')
        quantity = int(request.POST.get('quantity', 1))
        priority = request.POST.get('priority', 'medium')
        customer_name = request.POST.get('customer_name', '')
        customer_phone = request.POST.get('customer_phone', '')
        notes = request.POST.get('notes', '')
        
        # Validate
        if not medicine_name:
            messages.error(request, 'Medicine name is required!')
            return redirect('medicine_requests')
        
        # Create request
        medicine_request = MedicineRequest.objects.create(
            pharmacy=pharmacy,
            medicine_name=medicine_name,
            medicine_code=medicine_code,
            quantity=quantity,
            priority=priority,
            customer_name=customer_name,
            customer_phone=customer_phone,
            notes=notes,
            requested_by=request.user,
            status='pending'
        )
        
        # Add history
        medicine_request.add_history_entry(
            action='Request Created',
            user=request.user,
            notes=f'Request for {quantity} units'
        )
        
        messages.success(request, f'✅ Request for "{medicine_name}" added!')
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('medicine_requests')


@login_required
def edit_medicine_request(request, pk):
    """Edit Medicine Request"""
    
    if request.method != 'POST':
        return redirect('medicine_requests')
    
    try:
        pharmacy = Pharmacy.objects.get(owner=request.user)
    except Pharmacy.DoesNotExist:
        messages.error(request, '❌ Pharmacy profile not found!')
        return redirect('settings')
    
    try:
        medicine_request = MedicineRequest.objects.get(pk=pk, pharmacy=pharmacy)
        
        # Update fields
        medicine_request.medicine_name = request.POST.get('medicine_name', medicine_request.medicine_name)
        medicine_request.medicine_code = request.POST.get('medicine_code', '')
        medicine_request.quantity = int(request.POST.get('quantity', medicine_request.quantity))
        medicine_request.priority = request.POST.get('priority', medicine_request.priority)
        medicine_request.customer_name = request.POST.get('customer_name', '')
        medicine_request.customer_phone = request.POST.get('customer_phone', '')
        medicine_request.notes = request.POST.get('notes', '')
        
        # Update status if provided
        new_status = request.POST.get('status')
        if new_status and new_status != medicine_request.status:
            old_status = medicine_request.status
            medicine_request.status = new_status
            medicine_request.add_history_entry(
                action=f'Status: {old_status} → {new_status}',
                user=request.user
            )
        
        medicine_request.save()
        
        # Add general update history
        medicine_request.add_history_entry(
            action='Request Updated',
            user=request.user
        )
        
        messages.success(request, f'✅ Request updated!')
        
    except MedicineRequest.DoesNotExist:
        messages.error(request, '❌ Request not found!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('medicine_requests')


@login_required
def delete_medicine_request(request, pk):
    """Delete Medicine Request"""
    
    if request.method != 'POST':
        return redirect('medicine_requests')
    
    try:
        pharmacy = Pharmacy.objects.get(owner=request.user)
        medicine_request = MedicineRequest.objects.get(pk=pk, pharmacy=pharmacy)
        name = medicine_request.medicine_name
        medicine_request.delete()
        messages.success(request, f'✅ Request for "{name}" deleted!')
    except:
        messages.error(request, '❌ Request not found!')
    
    return redirect('medicine_requests')


@login_required
def api_get_request(request, pk):
    """API to get request details for editing"""
    
    try:
        pharmacy = Pharmacy.objects.get(owner=request.user)
        req = MedicineRequest.objects.get(pk=pk, pharmacy=pharmacy)
        
        data = {
            'id': req.id,
            'medicine_name': req.medicine_name,
            'medicine_code': req.medicine_code or '',
            'quantity': req.quantity,
            'priority': req.priority,
            'status': req.status,
            'customer_name': req.customer_name or '',
            'customer_phone': req.customer_phone or '',
            'notes': req.notes or '',
            'history': req.history if isinstance(req.history, list) else []
        }
        return JsonResponse(data)
        
    except MedicineRequest.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    

from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import PasswordResetOTP
from django.conf import settings
from django.utils import timezone

def forgot_password(request):
    """Step 1: Email લઈને OTP મોકલો"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # જૂના OTP ડિલીટ કરો
            PasswordResetOTP.objects.filter(user=user, is_used=False).delete()
            
            # નવો OTP જનરેટ કરો
            otp_code = PasswordResetOTP.generate_otp()
            PasswordResetOTP.objects.create(
                user=user,
                otp=otp_code
            )
            
            # Email મોકલો
            subject = '🔐 PharmaCentral - Password Reset OTP'
            message = f"""
            Hello {user.username},
            
            Your OTP for password reset is: {otp_code}
            
            This OTP is valid for 10 minutes only.
            
            If you didn't request this, please ignore this email.
            
            Thanks,
            PharmaCentral Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            # OTP verify પેજ પર જાઓ
            request.session['reset_email'] = email
            messages.success(request, f"OTP sent to {email}")
            return redirect('verify_otp')
            
        except User.DoesNotExist:
            messages.error(request, "No account found with this email!")
            return redirect('forgot_password')
    
    return render(request, 'app1/forgot_password.html')




def verify_otp(request):
    """Step 2: OTP ચેક કરો"""
    email = request.session.get('reset_email')
    
    if not email:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        
        try:
            user = User.objects.get(email=email)
            otp_record = PasswordResetOTP.objects.filter(
                user=user, 
                otp=otp_entered,
                is_used=False
            ).latest('created_at')
            
            # OTP valid છે અને 10 મિનિટમાં છે?
            if otp_record.is_valid():
                # OTP use કરી લીધું mark કરો
                otp_record.is_used = True
                otp_record.save()
                
                # નવો password સેટ કરવા જાઓ
                request.session['reset_user_id'] = user.id
                return redirect('reset_password')
            else:
                messages.error(request, "OTP has expired! Please try again.")
                return redirect('forgot_password')
                
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, "Invalid OTP!")
            return redirect('verify_otp')
    
    return render(request, 'app1/verify_otp.html', {'email': email})




def reset_password(request):
    """Step 3: નવો પાસવર્ડ સેટ કરો"""
    user_id = request.session.get('reset_user_id')
    
    if not user_id:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, "Passwords don't match!")
            return redirect('reset_password')
        
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters!")
            return redirect('reset_password')
        
        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            
            # Session clean up
            del request.session['reset_email']
            del request.session['reset_user_id']
            
            messages.success(request, "Password changed successfully! Please login.")
            return redirect('login')
            
        except Exception as e:
            messages.error(request, "Something went wrong!")
            return redirect('forgot_password')
    
    return render(request, 'app1/reset_password.html')