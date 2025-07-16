from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, SetPasswordForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, Http404
from django.views.decorators.http import require_POST, require_GET
from .models import JobPost, JobLike, JobRequest, JobFlag, RecentActivity, JobCategory, BookedJob, ContactMessage
from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
import csv
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateformat import format as date_format
from decimal import Decimal, InvalidOperation
from datetime import time
import re
from django.core.exceptions import ValidationError

def convert_time_window_to_time(time_window):
    """Convert time window string like '06:00-12:00' to time objects"""
    if not time_window:
        return None, None
    
    try:
        # Extract start and end times from window like "06:00-12:00"
        start_time_str, end_time_str = time_window.split('-')
        start_hour, start_minute = map(int, start_time_str.split(':'))
        end_hour, end_minute = map(int, end_time_str.split(':'))
        
        start_time = time(start_hour, start_minute)
        end_time = time(end_hour, end_minute)
        
        return start_time, end_time
    except (ValueError, AttributeError):
        return None, None

def word_limit_validator(max_words):
    def validate(value):
        if value and len(value.split()) > max_words:
            raise ValidationError(f'Maximum {max_words} words allowed.')
    return validate

def zip_code_validator(value):
    if not re.match(r'^\d{5}$', value):
        raise ValidationError('ZIP code must be exactly 5 digits.')

def one_word_validator(value):
    if value and (len(value.split()) > 1 or not value.isalpha()):
        raise ValidationError('City must be a single word (letters only).')

# Create your views here.

def home(request):
    """Home page view"""
    from .models import JobPost
    # Exclude booked jobs from carousel
    booked_job_ids = set(BookedJob.objects.values_list('job_id', flat=True))
    carousel_jobs = JobPost.objects.filter(hidden=False).exclude(id__in=booked_job_ids).order_by('-created_at')[:10]
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('logistics:manager_dashboard')
        elif request.user.is_staff:
            return redirect('logistics:admin_dashboard')
    return render(request, 'home.html', {'carousel_jobs': carousel_jobs})

def job_list(request):
    """Display list of all job posts with filtering"""
    jobs = JobPost.objects.select_related('cargo_type', 'created_by').filter(hidden=False)
    
    # Exclude jobs that have been booked by any user
    booked_job_ids = set(BookedJob.objects.values_list('job_id', flat=True))
    jobs = jobs.exclude(id__in=booked_job_ids)
    
    q = request.GET.get('q', '').strip()
    cargo_type = request.GET.get('cargo_type', '').strip()
    origin = request.GET.get('origin', '').strip()
    destination = request.GET.get('destination', '').strip()
    pickup_date = request.GET.get('pickup_date', '').strip()

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) | Q(description__icontains=q) |
            Q(origin__icontains=q) | Q(destination__icontains=q)
        )
    if cargo_type:
        jobs = jobs.filter(cargo_type__id=cargo_type)
    if origin:
        jobs = jobs.filter(origin__icontains=origin)
    if destination:
        jobs = jobs.filter(destination__icontains=destination)
    if pickup_date:
        jobs = jobs.filter(pickup_date=pickup_date)

    categories = JobCategory.objects.all()
    user_booked_job_ids = set()
    if request.user.is_authenticated:
        user_booked_job_ids = set(BookedJob.objects.filter(user=request.user, job__in=jobs).values_list('job_id', flat=True))

    # PAGINATION: Dynamic page size based on screen size
    # Default: 6 jobs per page, but can be overridden by 'per_page' parameter
    per_page = request.GET.get('per_page', 6)
    try:
        per_page = int(per_page)
        # Ensure per_page is within reasonable bounds (1-12)
        per_page = max(1, min(12, per_page))
    except (ValueError, TypeError):
        per_page = 6
    
    paginator = Paginator(jobs, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'job_list.html', {
        'categories': categories,
        'q': q,
        'cargo_type': cargo_type,
        'origin': origin,
        'destination': destination,
        'pickup_date': pickup_date,
        'booked_job_ids': user_booked_job_ids,
        'paginator': paginator,
        'page_obj': page_obj,
        'per_page': per_page,
    })

def job_detail(request, job_id):
    """Display detailed view of a specific job post"""
    job = get_object_or_404(JobPost, id=job_id)
    is_liked = job.is_liked_by(request.user) if request.user.is_authenticated else False
    # Recommended jobs: same cargo_type, exclude current job and booked jobs, order by created_at desc
    booked_job_ids = set(BookedJob.objects.values_list('job_id', flat=True))
    recommended_jobs = JobPost.objects.filter(cargo_type=job.cargo_type, hidden=False).exclude(id=job.id).exclude(id__in=booked_job_ids).order_by('-created_at')[:5]
    booked = False
    if request.user.is_authenticated:
        booked = BookedJob.objects.filter(user=request.user, job=job).exists()
    return render(request, 'job_detail.html', {
        'job': job, 
        'is_liked': is_liked,
        'like_count': job.like_count(),
        'recommended_jobs': recommended_jobs,
        'booked': booked
    })

def job_detail_json(request, job_id):
    job = get_object_or_404(JobPost, id=job_id)
    is_authenticated = request.user.is_authenticated
    liked = False
    booked = False
    user_booked = False
    if is_authenticated:
        liked = job.is_liked_by(request.user)
        user_booked = BookedJob.objects.filter(user=request.user, job=job).exists()
    # Check if job is booked by any user
    booked = BookedJob.objects.filter(job=job).exists()
    
    # Get booking information for staff
    booked_by_username = None
    booked_by_id = None
    if booked:
        booking = BookedJob.objects.filter(job=job).first()
        if booking:
            booked_by_username = booking.user.username
            booked_by_id = booking.user.id
    
    data = {
        'id': job.id,
        'title': job.title,
        'origin': job.origin,
        'origin_address': job.origin_address if job.origin_address else None,
        'origin_zip': job.origin_zip if job.origin_zip else None,
        'destination': job.destination,
        'destination_address': job.destination_address if job.destination_address else None,
        'destination_zip': job.destination_zip if job.destination_zip else None,
        'pickup_date': job.pickup_date.strftime('%Y-%m-%d') if job.pickup_date else None,
        'pickup_time_from': job.pickup_time_from.strftime('%H:%M') if job.pickup_time_from else None,
        'pickup_time_to': job.pickup_time_to.strftime('%H:%M') if job.pickup_time_to else None,
        'delivery_deadline': job.delivery_deadline.strftime('%Y-%m-%d') if job.delivery_deadline else None,
        'cargo_type': job.cargo_type.name if job.cargo_type else None,
        'weight_kg': job.weight_kg if job.weight_kg is not None else None,
        'length_cm': job.length_cm if job.length_cm is not None else None,
        'width_cm': job.width_cm if job.width_cm is not None else None,
        'height_cm': job.height_cm if job.height_cm is not None else None,
        'special_requirements': job.special_requirements if job.special_requirements else None,
        'declared_value': str(job.declared_value) if job.declared_value else None,
        'reference_code': job.reference_code if job.reference_code else None,
        'description': job.description,
        'created_at': date_format(job.created_at, 'Y-m-d H:i'),
        'like_count': job.like_count(),
        'is_authenticated': is_authenticated,
        'liked': liked,
        'booked': booked,
        'user_booked': user_booked,
    }
    
    # Add staff-only information if user is staff
    if request.user.is_staff:
        data.update({
            'created_by_username': job.created_by.username,
            'created_by_id': job.created_by.id,
            'hidden': job.hidden,
            'booked_by_username': booked_by_username,
            'booked_by_id': booked_by_id,
            'flag_count': job.flags.filter(status='open').count(),
            'view_count': 0,  # Placeholder for future view tracking
        })
    
    return JsonResponse(data)

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    email = forms.EmailField(max_length=254, required=True, label='Email Address')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with that email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('logistics:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'GET':
        # Clear all messages on GET (login page load)
        list(messages.get_messages(request))
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('logistics:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    """User logout view"""
    logout(request)
    # Clear all messages after logout
    list(messages.get_messages(request))
    messages.success(request, 'You have been logged out successfully.')
    return redirect('logistics:login')



@login_required
@require_POST
def like_job(request, job_id):
    """Like or unlike a job via AJAX"""
    job = get_object_or_404(JobPost, id=job_id)
    
    # Check if user already liked this job
    existing_like = JobLike.objects.filter(user=request.user, job=job).first()
    
    if existing_like:
        # Unlike the job
        existing_like.delete()
        action = 'unliked'
    else:
        # Like the job
        JobLike.objects.create(user=request.user, job=job)
        action = 'liked'
    
    return JsonResponse({
        'likes': job.like_count(),
        'action': action,
        'success': True
    })

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return render(request, 'admin_error.html', status=403)
    q = request.GET.get('q', '').strip()
    job_id = request.GET.get('job_id', '').strip()
    # Jobs
    live_jobs_qs = JobPost.objects.filter(hidden=False).exclude(flags__status='open').order_by('-created_at')
    hidden_jobs_qs = JobPost.objects.filter(hidden=True).order_by('-created_at')
    flagged_jobs_qs = JobPost.objects.filter(flags__status='open').distinct().order_by('-created_at')
    job_requests_qs = JobRequest.objects.filter(status='pending').order_by('-created_at')
    booked_jobs_qs = BookedJob.objects.select_related('job', 'user').order_by('-booked_at')
    users = User.objects.all()
    # Filter by Job ID if provided
    if job_id:
        try:
            job_id_int = int(job_id)
            live_jobs_qs = live_jobs_qs.filter(id=job_id_int)
            hidden_jobs_qs = hidden_jobs_qs.filter(id=job_id_int)
            flagged_jobs_qs = flagged_jobs_qs.filter(id=job_id_int)
            booked_jobs_qs = booked_jobs_qs.filter(job__id=job_id_int)
            job_requests_qs = job_requests_qs.filter(id=job_id_int)
        except ValueError:
            pass
    # Existing q search logic
    if q:
        job_filter = (
            Q(title__icontains=q) | Q(description__icontains=q) |
            Q(origin__icontains=q) | Q(destination__icontains=q) |
            Q(cargo_type__name__icontains=q) | Q(created_by__username__icontains=q)
        )
        live_jobs_qs = live_jobs_qs.filter(job_filter)
        hidden_jobs_qs = hidden_jobs_qs.filter(job_filter)
        flagged_jobs_qs = flagged_jobs_qs.filter(job_filter)
        job_requests_qs = job_requests_qs.filter(
            Q(title__icontains=q) | Q(description__icontains=q) |
            Q(origin__icontains=q) | Q(destination__icontains=q) |
            Q(cargo_type__name__icontains=q) | Q(requested_by__username__icontains=q)
        )
        users = users.filter(
            Q(username__icontains=q) | Q(email__icontains=q) |
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    # Pagination for live jobs
    live_jobs_paginator = Paginator(live_jobs_qs, 10)
    live_jobs_page_number = request.GET.get('live_jobs_page')
    live_jobs_page_obj = live_jobs_paginator.get_page(live_jobs_page_number)
    live_jobs = live_jobs_page_obj.object_list

    # Paginate hidden jobs
    hidden_jobs_paginator = Paginator(hidden_jobs_qs, 10)
    hidden_jobs_page_number = request.GET.get('hidden_jobs_page')
    hidden_jobs_page_obj = hidden_jobs_paginator.get_page(hidden_jobs_page_number)
    hidden_jobs = hidden_jobs_page_obj.object_list

    # Paginate flagged jobs
    flagged_jobs_paginator = Paginator(flagged_jobs_qs, 10)
    flagged_jobs_page_number = request.GET.get('flagged_jobs_page')
    flagged_jobs_page_obj = flagged_jobs_paginator.get_page(flagged_jobs_page_number)
    flagged_jobs = flagged_jobs_page_obj.object_list

    # Paginate job requests
    job_requests_paginator = Paginator(job_requests_qs, 10)
    job_requests_page_number = request.GET.get('job_requests_page')
    job_requests_page_obj = job_requests_paginator.get_page(job_requests_page_number)
    job_requests = job_requests_page_obj.object_list.select_related('cargo_type', 'requested_by') if hasattr(job_requests_page_obj.object_list, 'select_related') else job_requests_page_obj.object_list

    # Paginate booked jobs
    booked_jobs_paginator = Paginator(booked_jobs_qs, 10)
    booked_jobs_page_number = request.GET.get('booked_jobs_page')
    booked_jobs_page_obj = booked_jobs_paginator.get_page(booked_jobs_page_number)
    booked_jobs = booked_jobs_page_obj.object_list

    # Users (for user management)
    # The users filtering is now handled by the q search, so we just pass the current users
    # If q is empty, this will be all users. If q is not empty, it will be filtered.

    # Quick stats
    stats = {
        'pending_requests': job_requests_qs.count(),
        'live_jobs': live_jobs_qs.count(),
        'flagged_jobs': flagged_jobs_qs.count(),
        'hidden_jobs': hidden_jobs_qs.count(),
        'user_count': User.objects.filter(joblike__isnull=False).distinct().count(),
        'total_jobs': JobPost.objects.count(),
    }
    # Recent activity (last 10 actions)
    recent_requests = JobRequest.objects.order_by('-created_at')[:5]
    recent_flags = JobFlag.objects.order_by('-created_at')[:5]
    recent_jobs = JobPost.objects.order_by('-created_at')[:5]
    recent_bulk = RecentActivity.objects.order_by('-timestamp')[:5]
    return render(request, 'admin_dashboard.html', {
        'job_requests': job_requests,
        'job_requests_paginator': job_requests_paginator,
        'job_requests_page_obj': job_requests_page_obj,
        'live_jobs': live_jobs,
        'live_jobs_paginator': live_jobs_paginator,
        'live_jobs_page_obj': live_jobs_page_obj,
        'hidden_jobs': hidden_jobs,
        'hidden_jobs_paginator': hidden_jobs_paginator,
        'hidden_jobs_page_obj': hidden_jobs_page_obj,
        'flagged_jobs': flagged_jobs,
        'flagged_jobs_paginator': flagged_jobs_paginator,
        'flagged_jobs_page_obj': flagged_jobs_page_obj,
        'booked_jobs': booked_jobs,
        'booked_jobs_paginator': booked_jobs_paginator,
        'booked_jobs_page_obj': booked_jobs_page_obj,
        'stats': stats,
        'recent_requests': recent_requests,
        'recent_flags': recent_flags,
        'recent_jobs': recent_jobs,
        'recent_bulk': recent_bulk,
        'users': users,
        'q': q,
        'job_id': job_id, # Pass job_id to template for filtering
    })

class JobPostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
        # Set min date for the date picker
        self.fields['pickup_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'min': timezone.now().date().isoformat(),
        })

    def clean_pickup_date(self):
        date = self.cleaned_data['pickup_date']
        if date < timezone.now().date():
            raise forms.ValidationError('Pickup date cannot be in the past.')
        return date

    class Meta:
        model = JobPost
        fields = ['title', 'description', 'origin', 'destination', 'cargo_type', 'weight_kg', 'pickup_date']

@login_required
def post_job(request):
    if not request.user.is_staff:
        return redirect('logistics:home')  # or use HttpResponseForbidden or render a permission denied template
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('logistics:admin_dashboard')
    else:
        form = JobPostForm()
    return render(request, 'post_job.html', {'form': form})



class UserProfileForm(forms.ModelForm):
    username = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={'autocomplete': 'off'}), help_text='Max 20 characters.')
    first_name = forms.CharField(required=False, max_length=20, help_text='Max 20 characters.')
    last_name = forms.CharField(required=False, max_length=20, help_text='Max 20 characters.')
    email = forms.EmailField(required=False, max_length=20, help_text='Max 20 characters.')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        if username == '':
            return username
        if len(username) < 2:
            raise forms.ValidationError('Username must be at least 2 characters long.')
        qs = User.objects.exclude(pk=self.instance.pk).filter(username__iexact=username)
        if qs.exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if email == '':
            return email
        qs = User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email)
        if qs.exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if first_name == '':
            return first_name
        if len(first_name.strip()) < 2:
            raise forms.ValidationError('First name must be at least 2 characters long.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if last_name == '':
            return last_name
        if len(last_name.strip()) < 2:
            raise forms.ValidationError('Last name must be at least 2 characters long.')
        return last_name

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'maxlength': 30}),
        label='Current Password',
        max_length=30,
        help_text='Enter your current password. Max 30 characters.'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'maxlength': 30}),
        label='New Password',
        max_length=30,
        help_text='8-30 chars, one uppercase, one special character. Must not match your current password.'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'maxlength': 30}),
        label='Confirm New Password',
        max_length=30,
        help_text='Re-enter the new password. Max 30 characters.'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Your current password is incorrect.')
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('New passwords do not match.')
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
            if not re.search(r'[A-Z]', password1):
                raise forms.ValidationError('Password must contain at least one uppercase letter.')
            if not re.search(r'[^A-Za-z0-9]', password1):
                raise forms.ValidationError('Password must contain at least one special character.')
            if self.user.check_password(password1):
                raise forms.ValidationError('New password cannot be the same as the current password.')
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user

@login_required
def edit_profile(request):
    user = request.user
    profile_form = UserProfileForm(request.POST or None, instance=user)
    password_form = PasswordChangeForm(user, request.POST or None)
    date_joined = user.date_joined
    if request.method == 'POST':
        if 'save_profile' in request.POST:
            # Merge empty fields with current user values
            post_data = request.POST.copy()
            for field in ['username', 'first_name', 'last_name', 'email']:
                if not post_data.get(field):
                    post_data[field] = getattr(user, field)
            # Always ensure username is set to current if blank or missing
            if not post_data.get('username'):
                post_data['username'] = user.username
            profile_form = UserProfileForm(post_data, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                # Stay on the edit profile page after saving
                return redirect('logistics:edit_profile')
            else:
                messages.error(request, 'Invalid input in profile form.')
        elif 'change_password' in request.POST:
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('logistics:edit_profile')
            else:
                messages.error(request, 'Please correct the errors in the password form.')
    else:
        profile_form = UserProfileForm()
        password_form = PasswordChangeForm(user)
    return render(request, 'edit_profile.html', {
        'form': profile_form,
        'password_form': password_form,
        'date_joined': date_joined
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            if is_ajax:
                return JsonResponse({'success': True})
            else:
                messages.success(request, 'Your password was successfully updated!')
                return redirect('logistics:dashboard')
        else:
            if is_ajax:
                error = next(iter(form.errors.values()))[0] if form.errors else 'Invalid input.'
                return JsonResponse({'success': False, 'error': error})
            else:
                # For non-AJAX requests, render the form with errors
                return render(request, 'change_password.html', {'form': form})
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'change_password.html', {'form': form})

class JobRequestForm(forms.ModelForm):
    TIME_WINDOWS = [
        ("06:00-12:00", "06:00 - 12:00"),
        ("12:00-18:00", "12:00 - 18:00"),
        ("18:00-00:00", "18:00 - 00:00"),
        ("00:00-06:00", "00:00 - 06:00"),
    ]
    pickup_time_from = forms.ChoiceField(choices=TIME_WINDOWS, label="Pickup Time Window")
    pickup_time_to = forms.ChoiceField(choices=TIME_WINDOWS, label="Dropoff Time Window")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tomorrow = (timezone.now() + timezone.timedelta(days=1)).date()
        self.fields['pickup_date'].widget.attrs['min'] = tomorrow
        self.fields['delivery_deadline'].widget.attrs['min'] = tomorrow
        # Set required and widget attributes for all fields
        self.fields['title'].widget.attrs.update({'maxlength': 50, 'required': True})
        self.fields['description'].widget.attrs.update({'maxlength': 100, 'required': True})
        self.fields['special_requirements'].widget.attrs.update({'maxlength': 100})
        self.fields['origin'].widget.attrs.update({'maxlength': 20, 'required': True, 'pattern': r'^[A-Za-z]{1,20}$', 'title': 'One word, letters only'})
        self.fields['destination'].widget.attrs.update({'maxlength': 20, 'required': True, 'pattern': r'^[A-Za-z]{1,20}$', 'title': 'One word, letters only'})
        self.fields['origin_address'].widget.attrs.update({'maxlength': 20, 'required': True})
        self.fields['destination_address'].widget.attrs.update({'maxlength': 20, 'required': True})
        # Add word limit validators
        word_limited_fields = [
            'title', 'description', 'origin', 'origin_address', 'destination', 'destination_address', 'special_requirements', 'reference_code'
        ]
        for field in word_limited_fields:
            if field in self.fields:
                self.fields[field].validators.append(word_limit_validator(50))
        # Add ZIP code validator
        for zip_field in ['origin_zip', 'destination_zip']:
            if zip_field in self.fields:
                self.fields[zip_field].validators.append(zip_code_validator)
        self.fields['origin'].validators.append(one_word_validator)
        self.fields['destination'].validators.append(one_word_validator)
    def clean_pickup_date(self):
        date = self.cleaned_data['pickup_date']
        tomorrow = (timezone.now() + timezone.timedelta(days=1)).date()
        if date < tomorrow:
            raise forms.ValidationError('Pickup date must be from tomorrow onwards.')
        return date
    def clean(self):
        cleaned_data = super().clean()
        pickup_date = cleaned_data.get('pickup_date')
        delivery_deadline = cleaned_data.get('delivery_deadline')
        if pickup_date and delivery_deadline and delivery_deadline < pickup_date:
            self.add_error('delivery_deadline', 'Dropoff date cannot be before pickup date.')
        return cleaned_data

    class Meta:
        model = JobRequest
        fields = [
            'title', 'description', 'cargo_type',
            'num_boxes', 'weight_per_box_kg', 'length_per_box_cm', 'width_per_box_cm', 'height_per_box_cm',
            'origin', 'origin_address', 'origin_zip',
            'pickup_date', 'pickup_time_from',
            'destination', 'destination_address', 'destination_zip',
            'delivery_deadline', 'pickup_time_to',
            'special_requirements', 'declared_value', 'reference_code',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'maxlength': 50, 'required': True}),
            'description': forms.Textarea(attrs={'rows': 2, 'maxlength': 100, 'required': True}),
            'cargo_type': forms.Select(attrs={'required': 'required'}),
            'num_boxes': forms.NumberInput(attrs={'min': 1, 'max': 999, 'required': 'required'}),
            'weight_per_box_kg': forms.NumberInput(attrs={'min': 0.1, 'max': 500, 'step': 0.1, 'required': 'required'}),
            'length_per_box_cm': forms.NumberInput(attrs={'min': 1, 'max': 300, 'required': 'required'}),
            'width_per_box_cm': forms.NumberInput(attrs={'min': 1, 'max': 200, 'required': 'required'}),
            'height_per_box_cm': forms.NumberInput(attrs={'min': 1, 'max': 200, 'required': 'required'}),
            'origin': forms.TextInput(attrs={'maxlength': 20, 'required': True, 'pattern': r'^[A-Za-z]{1,20}$', 'title': 'One word, letters only'}),
            'origin_address': forms.TextInput(attrs={'maxlength': 20, 'required': 'required'}),
            'origin_zip': forms.TextInput(attrs={'maxlength': 5, 'pattern': '^\d{5}$', 'required': 'required'}),
            'pickup_date': forms.DateInput(attrs={'type': 'date', 'required': 'required'}),
            'pickup_time_from': forms.Select(attrs={'required': 'required'}),
            'destination': forms.TextInput(attrs={'maxlength': 20, 'required': True, 'pattern': r'^[A-Za-z]{1,20}$', 'title': 'One word, letters only'}),
            'destination_address': forms.TextInput(attrs={'maxlength': 20, 'required': 'required'}),
            'destination_zip': forms.TextInput(attrs={'maxlength': 5, 'pattern': '^\d{5}$', 'required': 'required'}),
            'delivery_deadline': forms.DateInput(attrs={'type': 'date', 'required': 'required'}),
            'pickup_time_to': forms.Select(attrs={'required': 'required'}),
            'special_requirements': forms.Textarea(attrs={'rows': 2, 'maxlength': 100}),
            'reference_code': forms.TextInput(attrs={'maxlength': 100}),
        }

@login_required
def request_job(request):
    if request.user.is_staff:
        return redirect('logistics:admin_dashboard')
    if request.method == 'POST':
        form = JobRequestForm(request.POST)
        if form.is_valid():
            job_request = form.save(commit=False)
            job_request.requested_by = request.user
            job_request.status = 'pending'
            job_request.save()
            messages.success(request, 'Your job request has been successfully submitted! We will review it and get back to you soon. You can check your request status in "My Job Requests" section.')
            return redirect('logistics:dashboard')
    else:
        form = JobRequestForm()
    return render(request, 'request_job.html', {'form': form})

@login_required
def my_job_requests(request):
    job_requests_qs = JobRequest.objects.filter(requested_by=request.user).order_by('-created_at')
    paginator = Paginator(job_requests_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    job_requests = page_obj.object_list

    # Build a mapping from job request id to declared_value (if approved and job exists)
    approved_titles = [req.title for req in job_requests if req.status == 'approved']
    job_posts = JobPost.objects.filter(title__in=approved_titles)
    jobpost_value_map = {jp.title: jp.declared_value for jp in job_posts}

    return render(request, 'my_job_requests.html', {
        'job_requests': job_requests,
        'jobpost_value_map': jobpost_value_map,
        'paginator': paginator,
        'page_obj': page_obj,
    })

@login_required
def my_bookings(request):
    bookings = BookedJob.objects.filter(user=request.user, job__hidden=False).select_related('job').order_by('-booked_at')
    return render(request, 'my_bookings.html', {'bookings': bookings})

@login_required
@require_POST
def approve_job_request(request, req_id):
    print(f"DEBUG: Approve job request called for req_id: {req_id}")
    print(f"DEBUG: POST data: {request.POST}")
    if not request.user.is_staff:
        print("DEBUG: User is not staff")
        return HttpResponseForbidden()
    job_request = get_object_or_404(JobRequest, id=req_id, status='pending')
    print(f"DEBUG: Found job request: {job_request.title}")
    declared_value_raw = request.POST.get('declared_value')
    print(f"DEBUG: Raw declared_value: {declared_value_raw}")
    
    declared_value = None
    if declared_value_raw and declared_value_raw.strip():
        try:
            declared_value = Decimal(declared_value_raw)
            print(f"DEBUG: Converted declared_value: {declared_value}")
        except (InvalidOperation, TypeError):
            print(f"DEBUG: Invalid value error for: {declared_value_raw}")
            messages.error(request, 'Invalid value. Please enter a valid number for the value.')
            return redirect('logistics:admin_dashboard')
    else:
        print(f"DEBUG: No declared_value provided, setting to None")
    
    # Create JobPost from JobRequest
    try:
        # Convert time windows to actual time objects
        pickup_time_from, pickup_time_to = convert_time_window_to_time(job_request.pickup_time_from)
        delivery_time_from, delivery_time_to = convert_time_window_to_time(job_request.pickup_time_to)
        
        job_post = JobPost.objects.create(
            title=job_request.title,
            description=job_request.description,
            origin=job_request.origin,
            destination=job_request.destination,
            cargo_type=job_request.cargo_type,
            weight_kg=job_request.weight_kg,
            pickup_date=job_request.pickup_date,
            pickup_time_from=pickup_time_from,
            pickup_time_to=pickup_time_to,
            delivery_deadline=job_request.delivery_deadline,
            origin_address=job_request.origin_address,
            origin_zip=job_request.origin_zip,
            destination_address=job_request.destination_address,
            destination_zip=job_request.destination_zip,
            length_cm=job_request.length_cm,
            width_cm=job_request.width_cm,
            height_cm=job_request.height_cm,
            special_requirements=job_request.special_requirements,
            reference_code=job_request.reference_code,
            created_by=request.user,
            declared_value=declared_value
        )
        print(f"DEBUG: Created job post: {job_post.id}")
        job_request.status = 'approved'
        job_request.save()
        print(f"DEBUG: Updated job request status to approved")
        messages.success(request, 'Job request approved and posted!')
        return redirect('logistics:admin_dashboard')
    except Exception as e:
        print(f"DEBUG: Error creating job post: {e}")
        messages.error(request, f'Error approving job request: {e}')
        return redirect('logistics:admin_dashboard')

@login_required
@require_POST
def reject_job_request(request, req_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    job_request = get_object_or_404(JobRequest, id=req_id, status='pending')
    job_request.status = 'rejected'
    job_request.save()
    messages.info(request, 'Job request rejected.')
    return redirect('logistics:admin_dashboard')

@login_required
@require_POST
def flag_job(request, job_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    job = get_object_or_404(JobPost, id=job_id)
    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, 'A reason is required to flag a job.')
        return redirect('logistics:job_detail', job_id=job_id)
    JobFlag.objects.create(job=job, flagged_by=request.user, reason=reason)
    messages.success(request, 'Job flagged for review.')
    return redirect('logistics:admin_dashboard')

@login_required
@require_POST
def hide_job(request, job_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    job = get_object_or_404(JobPost, id=job_id)
    job.hidden = True
    job.save()
    # Log to RecentActivity
    RecentActivity.objects.create(
        user=request.user,
        action='hide',
        target_type='job',
        target_ids=str(job_id),
        details=f"Hid job: {job.title}"
    )
    messages.success(request, 'Job has been hidden from public view.')
    return redirect('logistics:admin_dashboard')

@login_required
@require_POST
def unhide_job(request, job_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    job = get_object_or_404(JobPost, id=job_id)
    job.hidden = False
    job.save()
    # Log to RecentActivity
    RecentActivity.objects.create(
        user=request.user,
        action='unhide',
        target_type='job',
        target_ids=str(job_id),
        details=f"Unhid job: {job.title}"
    )
    messages.success(request, 'Job is now visible to users.')
    return redirect('logistics:admin_dashboard')

@login_required
@require_POST
def remove_job(request, job_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    job = get_object_or_404(JobPost, id=job_id)
    was_hidden = job.hidden
    job_title = job.title
    job.delete()
    # Log to RecentActivity
    RecentActivity.objects.create(
        user=request.user,
        action='single_remove',
        target_type='job',
        target_ids=str(job_id),
        details=f"Removed job: {job_title} (hidden={was_hidden})"
    )
    messages.success(request, 'Job has been removed.')
    return redirect('logistics:admin_dashboard')

@login_required
@require_POST
def close_flag(request, flag_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    flag = get_object_or_404(JobFlag, id=flag_id, status='open')
    flag.status = 'closed'
    flag.save()
    messages.success(request, 'Flag has been closed.')
    return redirect('logistics:admin_dashboard')

@login_required
@require_POST
def bulk_job_request_action(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    action = request.POST.get('bulk_action')
    selected = request.POST.getlist('selected_requests')
    acted_ids = []
    if action == 'approve':
        for req_id in selected:
            job_request = JobRequest.objects.filter(id=req_id, status='pending').first()
            if job_request:
                # Convert time windows to actual time objects
                pickup_time_from, pickup_time_to = convert_time_window_to_time(job_request.pickup_time_from)
                delivery_time_from, delivery_time_to = convert_time_window_to_time(job_request.pickup_time_to)
                
                JobPost.objects.create(
                    title=job_request.title,
                    description=job_request.description,
                    origin=job_request.origin,
                    destination=job_request.destination,
                    cargo_type=job_request.cargo_type,
                    weight_kg=job_request.weight_kg,
                    pickup_date=job_request.pickup_date,
                    pickup_time_from=pickup_time_from,
                    pickup_time_to=pickup_time_to,
                    delivery_deadline=job_request.delivery_deadline,
                    origin_address=job_request.origin_address,
                    origin_zip=job_request.origin_zip,
                    destination_address=job_request.destination_address,
                    destination_zip=job_request.destination_zip,
                    length_cm=job_request.length_cm,
                    width_cm=job_request.width_cm,
                    height_cm=job_request.height_cm,
                    special_requirements=job_request.special_requirements,
                    reference_code=job_request.reference_code,
                    created_by=request.user
                )
                job_request.status = 'approved'
                job_request.save()
                acted_ids.append(str(req_id))
        if acted_ids:
            RecentActivity.objects.create(
                user=request.user,
                action='bulk_approve',
                target_type='job_request',
                target_ids=','.join(acted_ids),
                details=f"Approved job requests: {', '.join(acted_ids)}"
            )
    elif action == 'remove':
        JobRequest.objects.filter(id__in=selected).delete()
        if selected:
            RecentActivity.objects.create(
                user=request.user,
                action='bulk_remove',
                target_type='job_request',
                target_ids=','.join(selected),
                details=f"Removed job requests: {', '.join(selected)}"
            )
    return redirect('logistics:admin_dashboard')

@login_required
@require_POST
def bulk_live_job_action(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    action = request.POST.get('bulk_action')
    selected = request.POST.getlist('selected_jobs')
    if action == 'remove':
        JobPost.objects.filter(id__in=selected).delete()
        if selected:
            RecentActivity.objects.create(
                user=request.user,
                action='bulk_remove',
                target_type='job',
                target_ids=','.join(selected),
                details=f"Removed jobs: {', '.join(selected)}"
            )
    return redirect('logistics:admin_dashboard')

@login_required
def export_jobs_csv(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    q = request.GET.get('q', '').strip()
    export_type = request.GET.get('type', 'all')
    # Log the export action
    type_label = {
        'all': 'All',
        'pending': 'Pending Requests',
        'live': 'Live Jobs',
        'hidden': 'Hidden Jobs',
        'flagged': 'Flagged Jobs',
    }.get(export_type, export_type)
    if q:
        details = f"Exported CSV: {type_label} (filtered by: {q})"
    else:
        details = f"Exported CSV: {type_label}"
    RecentActivity.objects.create(
        user=request.user,
        action='export_csv',
        target_type='export',
        target_ids=export_type,
        details=details
    )
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="jobs_export.csv"'
    writer = csv.writer(response)
    if export_type == 'pending':
        # Export pending job requests
        job_requests = JobRequest.objects.filter(status='pending').select_related('cargo_type', 'requested_by')
        if q:
            job_requests = job_requests.filter(
                Q(title__icontains=q) | Q(description__icontains=q) |
                Q(origin__icontains=q) | Q(destination__icontains=q) |
                Q(cargo_type__name__icontains=q) | Q(requested_by__username__icontains=q)
            )
        writer.writerow(['ID', 'Title', 'Description', 'Origin', 'Destination', 'Cargo Type', 'Weight (kg)', 'Pickup Date', 'Requested By', 'Status'])
        for req in job_requests:
            writer.writerow([
                req.id,
                req.title,
                req.description,
                req.origin,
                req.destination,
                req.cargo_type.name if req.cargo_type else '',
                req.weight_kg,
                req.pickup_date,
                req.requested_by.username if req.requested_by else '',
                req.get_status_display(),
            ])
    elif export_type == 'live':
        jobs = JobPost.objects.filter(hidden=False).select_related('cargo_type', 'created_by')
        if q:
            job_filter = (
                Q(title__icontains=q) | Q(description__icontains=q) |
                Q(origin__icontains=q) | Q(destination__icontains=q) |
                Q(cargo_type__name__icontains=q) | Q(created_by__username__icontains=q)
            )
            jobs = jobs.filter(job_filter)
        writer.writerow(['ID', 'Title', 'Description', 'Origin', 'Destination', 'Cargo Type', 'Weight (kg)', 'Pickup Date', 'Created By', 'Hidden', 'Likes'])
        for job in jobs:
            writer.writerow([
                job.id,
                job.title,
                job.description,
                job.origin,
                job.destination,
                job.cargo_type.name if job.cargo_type else '',
                job.weight_kg,
                job.pickup_date,
                job.created_by.username if job.created_by else '',
                job.hidden,
                job.like_count() if hasattr(job, 'like_count') else '',
            ])
    elif export_type == 'hidden':
        jobs = JobPost.objects.filter(hidden=True).select_related('cargo_type', 'created_by')
        if q:
            job_filter = (
                Q(title__icontains=q) | Q(description__icontains=q) |
                Q(origin__icontains=q) | Q(destination__icontains=q) |
                Q(cargo_type__name__icontains=q) | Q(created_by__username__icontains=q)
            )
            jobs = jobs.filter(job_filter)
        writer.writerow(['ID', 'Title', 'Description', 'Origin', 'Destination', 'Cargo Type', 'Weight (kg)', 'Pickup Date', 'Created By', 'Hidden', 'Likes'])
        for job in jobs:
            writer.writerow([
                job.id,
                job.title,
                job.description,
                job.origin,
                job.destination,
                job.cargo_type.name if job.cargo_type else '',
                job.weight_kg,
                job.pickup_date,
                job.created_by.username if job.created_by else '',
                job.hidden,
                job.like_count() if hasattr(job, 'like_count') else '',
            ])
    elif export_type == 'flagged':
        jobs = JobPost.objects.filter(flags__status='open').distinct().select_related('cargo_type', 'created_by')
        if q:
            job_filter = (
                Q(title__icontains=q) | Q(description__icontains=q) |
                Q(origin__icontains=q) | Q(destination__icontains=q) |
                Q(cargo_type__name__icontains=q) | Q(created_by__username__icontains=q)
            )
            jobs = jobs.filter(job_filter)
        writer.writerow(['ID', 'Title', 'Description', 'Origin', 'Destination', 'Cargo Type', 'Weight (kg)', 'Pickup Date', 'Created By', 'Hidden', 'Likes', 'Open Flags'])
        for job in jobs:
            open_flags = job.flags.filter(status='open').count() if hasattr(job, 'flags') else ''
            writer.writerow([
                job.id,
                job.title,
                job.description,
                job.origin,
                job.destination,
                job.cargo_type.name if job.cargo_type else '',
                job.weight_kg,
                job.pickup_date,
                job.created_by.username if job.created_by else '',
                job.hidden,
                job.like_count() if hasattr(job, 'like_count') else '',
                open_flags,
            ])
    else:  # all
        # Export all types, with a Job Type column
        jobs = JobPost.objects.all().select_related('cargo_type', 'created_by')
        job_requests = JobRequest.objects.filter(status='pending').select_related('cargo_type', 'requested_by')
        if q:
            job_filter = (
                Q(title__icontains=q) | Q(description__icontains=q) |
                Q(origin__icontains=q) | Q(destination__icontains=q) |
                Q(cargo_type__name__icontains=q)
            )
            jobs = jobs.filter(job_filter | Q(created_by__username__icontains=q))
            job_requests = job_requests.filter(job_filter | Q(requested_by__username__icontains=q))
        writer.writerow(['ID', 'Title', 'Description', 'Origin', 'Destination', 'Cargo Type', 'Weight (kg)', 'Pickup Date', 'User', 'Hidden', 'Likes', 'Job Type'])
        for job in jobs:
            job_type = 'Live Job'
            if job.hidden:
                job_type = 'Hidden Job'
            if hasattr(job, 'flags') and job.flags.filter(status='open').exists():
                job_type = 'Flagged Job' if not job.hidden else 'Hidden & Flagged Job'
            writer.writerow([
                job.id,
                job.title,
                job.description,
                job.origin,
                job.destination,
                job.cargo_type.name if job.cargo_type else '',
                job.weight_kg,
                job.pickup_date,
                job.created_by.username if job.created_by else '',
                job.hidden,
                job.like_count() if hasattr(job, 'like_count') else '',
                job_type,
            ])
        for req in job_requests:
            writer.writerow([
                req.id,
                req.title,
                req.description,
                req.origin,
                req.destination,
                req.cargo_type.name if req.cargo_type else '',
                req.weight_kg,
                req.pickup_date,
                req.requested_by.username if req.requested_by else '',
                '',  # Hidden
                '',  # Likes
                'Pending Request',
            ])
    return response

@user_passes_test(lambda u: u.is_superuser)
def manager_dashboard(request):
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    manager_users = User.objects.filter(is_superuser=True)
    normal_users = User.objects.filter(is_staff=False, is_superuser=False)
    found_users = None
    search_query = request.GET.get('search_user', '').strip()
    if search_query:
        found_users = User.objects.filter(Q(username__icontains=search_query) | Q(email__icontains=search_query))
    return render(request, 'manager_dashboard.html', {
        'staff_users': staff_users,
        'manager_users': manager_users,
        'normal_users': normal_users,
        'found_users': found_users,
        'search_query': search_query
    })



@user_passes_test(lambda u: u.is_superuser)
def manager_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    class ManagerUserEditForm(forms.ModelForm):
        class Meta:
            model = User
            fields = ['username', 'first_name', 'last_name', 'email']
    if request.method == 'POST':
        form = ManagerUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            if 'promote_to_manager' in request.POST:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                messages.success(request, f'User {user.username} promoted to manager.')
            elif 'demote_to_user' in request.POST:
                user.is_staff = False
                user.is_superuser = False
                user.save()
                messages.success(request, f'User {user.username} demoted to normal user.')
            elif 'promote_to_staff' in request.POST:
                user.is_staff = True
                user.save()
                messages.success(request, f'User {user.username} updated and promoted to staff.')
            else:
                messages.success(request, f'User {user.username} updated.')
            return redirect('logistics:manager_dashboard')
    else:
        form = ManagerUserEditForm(instance=user)
    return render(request, 'manager_edit_user.html', {'form': form, 'edit_user': user})

@login_required
@require_POST
def book_job(request, job_id):
    """Book a job via AJAX"""
    job = get_object_or_404(JobPost, id=job_id)
    # Check if job is already booked by this user
    existing_booking = BookedJob.objects.filter(user=request.user, job=job).first()
    if existing_booking:
        return JsonResponse({
            'success': False,
            'message': 'You have already booked this job.'
        })
    # Create the booking (do NOT set job.hidden = True)
    BookedJob.objects.create(user=request.user, job=job)
    return JsonResponse({
        'success': True,
        'message': f'Job "{job.title}" has been booked successfully!'
    })

@login_required
def hidden_jobs(request):
    # Show all booked jobs (not just hidden ones), paginated
    booked_jobs_qs = BookedJob.objects.select_related('job', 'user').order_by('-job__created_at')
    paginator = Paginator(booked_jobs_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hidden_jobs.html', {
        'booked_jobs': page_obj.object_list,
        'paginator': paginator,
        'page_obj': page_obj,
    })

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    success = False
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        if name and email and message:
            ContactMessage.objects.create(name=name, email=email, message=message)
            success = True
    return render(request, 'contact.html', {'success': success})

@staff_member_required
def staff_contact_messages(request):
    if request.method == 'POST':
        msg_id = request.POST.get('msg_id')
        answer = request.POST.get('answer')
        if msg_id and answer is not None:
            try:
                msg = ContactMessage.objects.get(id=msg_id)
                msg.answered = True
                msg.answer_text = answer
                msg.save()
            except ContactMessage.DoesNotExist:
                pass
    messages = ContactMessage.objects.all().order_by('answered', '-created_at')
    return render(request, 'staff_contact_messages.html', {'messages': messages})

@login_required
def dashboard(request):
    # Get user's job requests
    job_requests = JobRequest.objects.filter(requested_by=request.user).order_by('-created_at')
    
    # Get user's booked jobs (only live jobs, i.e., not hidden)
    booked_jobs = BookedJob.objects.filter(user=request.user, job__hidden=False).select_related('job', 'job__cargo_type', 'job__created_by')
    
    # Get user's liked jobs
    liked_jobs = JobPost.objects.filter(joblike__user=request.user).select_related('cargo_type', 'created_by')
    
    # Restore recommended_jobs logic
    recommended_jobs = []
    if liked_jobs.exists():
        liked_cargo_types = liked_jobs.values_list('cargo_type', flat=True).distinct()
        liked_origins = liked_jobs.values_list('origin', flat=True).distinct()
        liked_destinations = liked_jobs.values_list('destination', flat=True).distinct()
        all_booked_job_ids = set(BookedJob.objects.values_list('job_id', flat=True))
        recommended_jobs = JobPost.objects.filter(
            hidden=False,
            cargo_type__in=liked_cargo_types
        ).exclude(
            id__in=liked_jobs.values_list('id', flat=True)
        ).exclude(
            id__in=booked_jobs.values_list('job_id', flat=True)
        ).exclude(
            id__in=all_booked_job_ids
        ).select_related('cargo_type', 'created_by').order_by('-created_at')[:6]
        if recommended_jobs.count() < 6:
            additional_jobs = JobPost.objects.filter(
                hidden=False,
                origin__in=liked_origins
            ).exclude(
                id__in=liked_jobs.values_list('id', flat=True)
            ).exclude(
                id__in=booked_jobs.values_list('job_id', flat=True)
            ).exclude(
                id__in=all_booked_job_ids
            ).exclude(
                id__in=recommended_jobs.values_list('id', flat=True)
            ).select_related('cargo_type', 'created_by').order_by('-created_at')[:6-recommended_jobs.count()]
            recommended_jobs = list(recommended_jobs) + list(additional_jobs)
    else:
        all_booked_job_ids = set(BookedJob.objects.values_list('job_id', flat=True))
        recommended_jobs = JobPost.objects.filter(
            hidden=False
        ).exclude(
            id__in=booked_jobs.values_list('job_id', flat=True)
        ).exclude(
            id__in=all_booked_job_ids
        ).select_related('cargo_type', 'created_by').order_by('-created_at')[:6]
    # live_jobs_count should match jobs shown in browse jobs (not hidden and not booked by any user)
    booked_job_ids = set(BookedJob.objects.values_list('job_id', flat=True))
    live_jobs_count = JobPost.objects.filter(hidden=False).exclude(id__in=booked_job_ids).count()
    active_requests_count = JobRequest.objects.filter(requested_by=request.user, status='pending').count()
    jobs_booked_count = BookedJob.objects.filter(user=request.user).count()
    liked_jobs_count = JobLike.objects.filter(user=request.user).count()
    context = {
        'job_requests': job_requests,
        'booked_jobs': booked_jobs,
        'liked_jobs': liked_jobs,
        'recommended_jobs': recommended_jobs,
        'live_jobs_count': live_jobs_count,
        'active_requests_count': active_requests_count,
        'jobs_booked_count': jobs_booked_count,
        'liked_jobs_count': liked_jobs_count,
    }
    return render(request, 'dashboard.html', context)

@login_required
def job_request_detail_json(request, request_id):
    try:
        req = JobRequest.objects.get(id=request_id, requested_by=request.user)
    except JobRequest.DoesNotExist:
        raise Http404
    # Try to find a related JobPost (approved job)
    job_post = JobPost.objects.filter(title=req.title, origin=req.origin, destination=req.destination).order_by('-created_at').first()
    approved_value = job_post.declared_value if job_post else None
    data = {
        'id': req.id,
        'title': req.title,
        'description': req.description,
        'origin': req.origin,
        'origin_address': req.origin_address,
        'origin_zip': req.origin_zip,
        'destination': req.destination,
        'destination_address': req.destination_address,
        'destination_zip': req.destination_zip,
        'pickup_date': req.pickup_date.strftime('%Y-%m-%d') if req.pickup_date else '',
        'pickup_time_from': req.pickup_time_from,
        'pickup_time_to': req.pickup_time_to,
        'delivery_deadline': req.delivery_deadline.strftime('%Y-%m-%d') if req.delivery_deadline else '',
        'cargo_type': req.cargo_type.name if req.cargo_type else '',
        'weight_kg': req.weight_kg,
        'length_cm': req.length_cm,
        'width_cm': req.width_cm,
        'height_cm': req.height_cm,
        'special_requirements': req.special_requirements,
        'declared_value': req.declared_value,
        'approved_value': approved_value,
        'reference_code': req.reference_code,
        'status': req.status,
        'staff_note': req.staff_note,
        'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
        'num_boxes': req.num_boxes,
        'weight_per_box_kg': req.weight_per_box_kg,
        'length_per_box_cm': req.length_per_box_cm,
        'width_per_box_cm': req.width_per_box_cm,
        'height_per_box_cm': req.height_per_box_cm,
    }
    return JsonResponse(data)

@login_required
@require_GET
def ajax_check_username(request):
    username = request.GET.get('username', '').strip()
    user_id = request.user.id
    exists = User.objects.exclude(pk=user_id).filter(username__iexact=username).exists()
    return JsonResponse({'exists': exists, 'message': 'Username already exists.' if exists else 'Username is available.'})

@login_required
@require_GET
def ajax_check_email(request):
    email = request.GET.get('email', '').strip()
    user_id = request.user.id
    exists = User.objects.exclude(pk=user_id).filter(email__iexact=email).exists()
    return JsonResponse({'exists': exists, 'message': 'Email already in use.' if exists else 'Email is available.'})

@login_required
@require_POST
def ajax_check_password(request):
    password = request.POST.get('password', '')
    is_correct = request.user.check_password(password)
    return JsonResponse({'valid': is_correct, 'message': 'Password is correct.' if is_correct else 'Password is incorrect.'})

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': 25, 'required': True}),
            'email': forms.EmailInput(attrs={'maxlength': 25, 'required': True}),
            'message': forms.Textarea(attrs={'maxlength': 100, 'required': True, 'rows': 4}),
        }
