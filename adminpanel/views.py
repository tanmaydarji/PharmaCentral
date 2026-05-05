from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.http import JsonResponse

# Import your models
from app1.models import Pharmacy, User, ActivityLog

User = get_user_model()

# ============================================
# ADMIN LOGIN
# ============================================
def admin_login(request):
    """Admin Login View"""
    
    # If already logged in as superuser, redirect to dashboard
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an admin!')
    
    return render(request, 'admin-login.html')

# ============================================
# ADMIN LOGOUT
# ============================================
def admin_logout(request):
    """Admin Logout"""
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('admin_login')

# ============================================
# ADMIN DASHBOARD
# ============================================
@staff_member_required(login_url='admin_login')
def admin_dashboard(request):
    """Admin Dashboard with Statistics"""
    
    # Get counts
    total_users = User.objects.filter(is_superuser=False).count()
    
    # Active now (last 30 minutes)
    thirty_minutes_ago = timezone.now() - timedelta(minutes=30)
    active_now = User.objects.filter(
        is_superuser=False,
        last_login__gte=thirty_minutes_ago
    ).count()
    
    # Active today (last 24 hours)
    yesterday = timezone.now() - timedelta(days=1)
    active_today = User.objects.filter(
        is_superuser=False,
        last_login__gte=yesterday
    ).count()
    
    # Inactive (7+ days)
    week_ago = timezone.now() - timedelta(days=7)
    inactive_users = User.objects.filter(
        is_superuser=False,
        last_login__lt=week_ago
    ).count()
    
    # Total pharmacies
    total_pharmacies = Pharmacy.objects.count()
    
    # Recent activities
    recent_activities = []
    recent_users = User.objects.filter(is_superuser=False).order_by('-last_login')[:10]
    
    for user in recent_users:
        last_seen = user.last_login
        if last_seen:
            time_diff = timezone.now() - last_seen
            
            if time_diff < timedelta(minutes=30):
                status = "Active Now"
                icon = "🟢"
                last_seen_text = "Online now"
            elif time_diff < timedelta(hours=24):
                status = "Active Today"
                icon = "📅"
                hours = int(time_diff.total_seconds() / 3600)
                last_seen_text = f"{hours} hours ago"
            elif time_diff < timedelta(days=7):
                status = "Active This Week"
                icon = "📊"
                days = int(time_diff.days)
                last_seen_text = f"{days} days ago"
            else:
                status = "Inactive"
                icon = "🔴"
                days = int(time_diff.days)
                last_seen_text = f"{days} days ago"
        else:
            status = "Never Logged In"
            icon = "🆕"
            last_seen_text = "New user"
        
        recent_activities.append({
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'status_text': status,
            'icon': icon,
            'last_seen_text': last_seen_text,
            'user': user
        })
    
    context = {
        'total_users': total_users,
        'active_now': active_now,
        'active_today': active_today,
        'inactive_users': inactive_users,
        'total_pharmacies': total_pharmacies,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'admin-dashboard.html', context)

# ============================================
# ADMIN USERS (PHARMACIES)
# ============================================
@staff_member_required(login_url='admin_login')
def admin_users(request):
    """View all pharmacies/users with real data"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    # Base queryset - WITHOUT select_related (since no direct relation)
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    
    # Apply search
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        ).distinct()
    
    # Apply status filter
    if status == 'active':
        week_ago = timezone.now() - timedelta(days=7)
        users = users.filter(last_login__gte=week_ago)
    elif status == 'inactive':
        week_ago = timezone.now() - timedelta(days=7)
        users = users.filter(Q(last_login__lt=week_ago) | Q(last_login__isnull=True))
    
    # Pagination
    paginator = Paginator(users, 10)
    current_page = paginator.get_page(page)
    
    # Manually attach pharmacy to each user
    from app1.models import Pharmacy
    for user in current_page:
        try:
            user.pharmacy = Pharmacy.objects.get(owner=user)
        except Pharmacy.DoesNotExist:
            user.pharmacy = None
    
    context = {
        'users': current_page,
        'search_query': search_query,
        'status': status,
        'paginator': paginator,
    }
    
    return render(request, 'admin-user.html', context)



# ============================================
# TOGGLE PHARMACY ACTIVE STATUS
# ============================================
@staff_member_required(login_url='admin_login')
def toggle_active(request, user_id):
    """Toggle user active status"""
    
    user = get_object_or_404(User, id=user_id, is_superuser=False)
    
    user.is_active = not user.is_active
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User {user.username} {status} successfully!')
    
    return redirect('admin_users')

# ============================================
# TOGGLE PHARMACY VERIFICATION
# ============================================
@staff_member_required(login_url='admin_login')
def toggle_verify(request, pharmacy_id):
    """Toggle pharmacy verification status"""
    
    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
    
    pharmacy.is_verified = not pharmacy.is_verified
    pharmacy.save()
    
    status = "verified" if pharmacy.is_verified else "unverified"
    messages.success(request, f'Pharmacy {pharmacy.name} {status} successfully!')
    
    return redirect('admin_users')


# ============================================
# ADMIN SEARCH API (AJAX)
# ============================================
@staff_member_required(login_url='admin_login')
def admin_search_api(request):
    """AJAX search for pharmacies"""
    
    search_query = request.GET.get('search', '')
    
    users = User.objects.filter(is_superuser=False).select_related('pharmacy')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(pharmacy__name__icontains=search_query) |
            Q(pharmacy__city__icontains=search_query)
        ).distinct()[:20]
    
    data = []
    for user in users:
        try:
            pharmacy = user.pharmacy
            data.append({
                'id': user.id,
                'pharmacy_id': pharmacy.id,
                'pharmacy_name': pharmacy.name,
                'owner_name': user.get_full_name() or user.username,
                'license': pharmacy.license_number,
                'gst': pharmacy.gst_number,
                'city': pharmacy.city,
                'phone': pharmacy.phone,
                'email': user.email,
                'join_date': user.date_joined.strftime('%d %b %Y'),
                'is_active': user.is_active,
                'is_verified': pharmacy.is_verified,
            })
        except:
            pass
    
    return JsonResponse({'success': True, 'data': data})

# ============================================
# ADMIN STATS API
# ============================================
@staff_member_required(login_url='admin_login')
def admin_stats_api(request):
    """Get admin dashboard stats via AJAX"""
    
    total_users = User.objects.filter(is_superuser=False).count()
    
    thirty_minutes_ago = timezone.now() - timedelta(minutes=30)
    active_now = User.objects.filter(
        is_superuser=False,
        last_login__gte=thirty_minutes_ago
    ).count()
    
    yesterday = timezone.now() - timedelta(days=1)
    active_today = User.objects.filter(
        is_superuser=False,
        last_login__gte=yesterday
    ).count()
    
    week_ago = timezone.now() - timedelta(days=7)
    inactive_users = User.objects.filter(
        is_superuser=False,
        last_login__lt=week_ago
    ).count()
    
    total_pharmacies = Pharmacy.objects.count()
    
    return JsonResponse({
        'success': True,
        'total_users': total_users,
        'active_now': active_now,
        'active_today': active_today,
        'inactive_users': inactive_users,
        'total_pharmacies': total_pharmacies,
    })
    
    
    
  
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from app1.models import Pharmacy, Medicine, Customer, Sale, SaleItem, Debtor, Payment, ActivityLog ,  MedicineRequest,Alert, Settings, PasswordResetOTP

User = get_user_model()

@staff_member_required(login_url='admin_login')
def delete_pharmacy(request, user_id):
    """Simple delete with CASCADE"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        user = get_object_or_404(User, id=user_id, is_superuser=False)
        email = user.email
        
        # Get pharmacy name if exists
        pharmacy_name = "No Pharmacy"
        try:
            pharmacy = Pharmacy.objects.get(owner=user)
            pharmacy_name = pharmacy.name
        except Pharmacy.DoesNotExist:
            pass
        
        # Just delete user - CASCADE will handle everything
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {email} (Pharmacy: {pharmacy_name}) deleted successfully!'
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})