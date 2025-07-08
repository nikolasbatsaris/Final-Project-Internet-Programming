from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, SetPasswordForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_POST
from .models import JobPost, SavedJob, JobLike, JobRequest, JobFlag, RecentActivity, JobCategory, BookedJob
from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
import csv
from django.db.models import Q

# Create your views here.

def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('logistics:manager_dashboard')
        elif request.user.is_staff:
            return redirect('logistics:admin_dashboard')
    return render(request, 'home.html')

def job_list(request):
    """Display list of all job posts with filtering"""
    jobs = JobPost.objects.select_related('cargo_type', 'created_by').filter(hidden=False)
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
    booked_job_ids = set()
    if request.user.is_authenticated:
        booked_job_ids = set(BookedJob.objects.filter(user=request.user, job__in=jobs).values_list('job_id', flat=True))
    return render(request, 'job_list.html', {
        'jobs': jobs,
        'categories': categories,
        'q': q,
        'cargo_type': cargo_type,
        'origin': origin,
        'destination': destination,
        'pickup_date': pickup_date,
        'booked_job_ids': booked_job_ids,
    })

def job_detail(request, job_id):
    """Display detailed view of a specific job post"""
    job = get_object_or_404(JobPost, id=job_id)
    is_liked = job.is_liked_by(request.user) if request.user.is_authenticated else False
    # Recommended jobs: same cargo_type, exclude current job, order by created_at desc
    recommended_jobs = JobPost.objects.filter(cargo_type=job.cargo_type, hidden=False).exclude(id=job.id).order_by('-created_at')[:5]
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

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('logistics:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def login_view(request):
    """User login view"""
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
    messages.success(request, 'You have been logged out successfully.')
    return redirect('logistics:home')

@login_required
def dashboard(request):
    user = request.user
    if user.is_staff:
        return redirect('logistics:admin_dashboard')
    saved_jobs = SavedJob.objects.filter(user=user).select_related('job', 'job__cargo_type', 'job__created_by')
    # Profile summary
    profile = {
        'email': user.email,
        'date_joined': user.date_joined,
        'saved_count': saved_jobs.count(),
    }
    # Recent activity: last 5 saved jobs
    recent_saved = saved_jobs.order_by('-id')[:5]
    # Saved job status: active if job still exists, closed if not
    job_statuses = {sj.job.id: sj.job for sj in saved_jobs}
    # Show change password link (always True for now)
    show_change_password = True
    # Booked jobs
    booked_jobs = BookedJob.objects.filter(user=user).select_related('job', 'job__cargo_type', 'job__created_by')
    return render(request, 'dashboard.html', {
        'saved_jobs': saved_jobs,
        'profile': profile,
        'recent_saved': recent_saved,
        'job_statuses': job_statuses,
        'show_change_password': show_change_password,
        'booked_jobs': booked_jobs,
    })

@login_required
def save_job(request, job_id):
    """Save a job to user's saved jobs"""
    job = get_object_or_404(JobPost, id=job_id)
    
    # Check if job is already saved by this user
    saved_job, created = SavedJob.objects.get_or_create(
        user=request.user,
        job=job
    )
    
    if created:
        messages.success(request, f'Job "{job.title}" has been saved to your dashboard!')
    else:
        messages.info(request, f'Job "{job.title}" is already in your saved jobs.')
    
    return redirect('logistics:job_detail', job_id=job_id)

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
    # Jobs
    live_jobs = JobPost.objects.filter(hidden=False).order_by('-created_at')
    hidden_jobs = JobPost.objects.filter(hidden=True).order_by('-created_at')
    flagged_jobs = JobPost.objects.filter(flags__status='open').distinct().order_by('-created_at')
    # Requests
    job_requests = JobRequest.objects.filter(status='pending').order_by('-created_at')
    # Booked jobs
    booked_jobs = BookedJob.objects.select_related('job', 'user').order_by('-booked_at')
    # Users (for user management)
    users = User.objects.all()
    if q:
        job_filter = (
            Q(title__icontains=q) | Q(description__icontains=q) |
            Q(origin__icontains=q) | Q(destination__icontains=q) |
            Q(cargo_type__name__icontains=q) | Q(created_by__username__icontains=q)
        )
        live_jobs = live_jobs.filter(job_filter)
        hidden_jobs = hidden_jobs.filter(job_filter)
        flagged_jobs = flagged_jobs.filter(job_filter)
        job_requests = job_requests.filter(
            Q(title__icontains=q) | Q(description__icontains=q) |
            Q(origin__icontains=q) | Q(destination__icontains=q) |
            Q(cargo_type__name__icontains=q) | Q(requested_by__username__icontains=q)
        )
        users = users.filter(
            Q(username__icontains=q) | Q(email__icontains=q) |
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    # Quick stats
    stats = {
        'pending_requests': job_requests.count(),
        'live_jobs': live_jobs.count(),
        'flagged_jobs': flagged_jobs.count(),
        'hidden_jobs': hidden_jobs.count(),
        'user_count': User.objects.filter(savedjob__isnull=False).distinct().count(),
        'total_jobs': JobPost.objects.count(),
    }
    # Recent activity (last 10 actions)
    recent_requests = JobRequest.objects.order_by('-created_at')[:5]
    recent_flags = JobFlag.objects.order_by('-created_at')[:5]
    recent_jobs = JobPost.objects.order_by('-created_at')[:5]
    recent_bulk = RecentActivity.objects.order_by('-timestamp')[:5]
    return render(request, 'admin_dashboard.html', {
        'job_requests': job_requests,
        'live_jobs': live_jobs,
        'hidden_jobs': hidden_jobs,
        'flagged_jobs': flagged_jobs,
        'stats': stats,
        'recent_requests': recent_requests,
        'recent_flags': recent_flags,
        'recent_jobs': recent_jobs,
        'recent_bulk': recent_bulk,
        'users': users,
        'q': q,
        'booked_jobs': booked_jobs,
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
            return redirect('logistics:dashboard')
    else:
        form = JobPostForm()
    return render(request, 'post_job.html', {'form': form})

@login_required
def remove_saved_job(request, job_id):
    saved_job = get_object_or_404(SavedJob, user=request.user, job_id=job_id)
    saved_job.delete()
    messages.success(request, 'Job removed from your saved jobs.')
    return redirect('logistics:dashboard')

class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

    def clean_username(self):
        username = self.cleaned_data['username']
        if len(username) < 2:
            raise forms.ValidationError('Username must be at least 2 characters long.')
        qs = User.objects.exclude(pk=self.instance.pk).filter(username__iexact=username)
        if qs.exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email)
        if qs.exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if len(first_name.strip()) < 2:
            raise forms.ValidationError('First name must be at least 2 characters long.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if len(last_name.strip()) < 2:
            raise forms.ValidationError('Last name must be at least 2 characters long.')
        return last_name

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('logistics:dashboard')
    else:
        form = UserProfileForm(instance=request.user)
    date_joined = request.user.date_joined
    return render(request, 'edit_profile.html', {'form': form, 'date_joined': date_joined})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('logistics:dashboard')
    else:
        form = SetPasswordForm(request.user)
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
        self.fields['pickup_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'min': tomorrow.isoformat(),
        })
    def clean_pickup_date(self):
        date = self.cleaned_data['pickup_date']
        tomorrow = (timezone.now() + timezone.timedelta(days=1)).date()
        if date < tomorrow:
            raise forms.ValidationError('Pickup date must be from tomorrow onwards.')
        return date
    def clean(self):
        cleaned_data = super().clean()
        # No need for 3-hour window validation, as windows are fixed
        return cleaned_data

    class Meta:
        model = JobRequest
        fields = [
            'title', 'description', 'origin', 'origin_address', 'origin_zip', 'destination', 'destination_address', 'destination_zip',
            'cargo_type', 'weight_kg',
            'length_cm', 'width_cm', 'height_cm', 'volume_m3',
            'special_requirements',
            'pickup_date', 'pickup_time_from', 'pickup_time_to',
            'delivery_deadline',
            'declared_value', 'reference_code',
        ]
        widgets = {
            'pickup_date': forms.DateInput(attrs={'type': 'date'}),
            'delivery_deadline': forms.DateInput(attrs={'type': 'date'}),
            'pickup_time_from': forms.TimeInput(attrs={'type': 'time', 'min': '06:00', 'max': '22:00'}),
            'pickup_time_to': forms.TimeInput(attrs={'type': 'time', 'min': '06:00', 'max': '22:00'}),
            'special_requirements': forms.Textarea(attrs={'rows': 2}),
            'declared_value': forms.NumberInput(attrs={'step': '0.01'}),
            'origin_address': forms.TextInput(),
            'destination_address': forms.TextInput(),
        }

@login_required
def request_job(request):
    if request.user.is_staff:
        return redirect('logistics:dashboard')
    if request.method == 'POST':
        form = JobRequestForm(request.POST)
        if form.is_valid():
            job_request = form.save(commit=False)
            job_request.requested_by = request.user
            job_request.status = 'pending'
            job_request.save()
            messages.success(request, 'Your job request has been submitted!')
            return redirect('logistics:my_job_requests')
    else:
        form = JobRequestForm()
    return render(request, 'request_job.html', {'form': form})

@login_required
def my_job_requests(request):
    job_requests = JobRequest.objects.filter(requested_by=request.user).order_by('-created_at')
    return render(request, 'my_job_requests.html', {'job_requests': job_requests})

@login_required
@require_POST
def approve_job_request(request, req_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    job_request = get_object_or_404(JobRequest, id=req_id, status='pending')
    # Create JobPost from JobRequest
    job_post = JobPost.objects.create(
        title=job_request.title,
        description=job_request.description,
        origin=job_request.origin,
        destination=job_request.destination,
        cargo_type=job_request.cargo_type,
        weight_kg=job_request.weight_kg,
        pickup_date=job_request.pickup_date,
        created_by=request.user
    )
    job_request.status = 'approved'
    job_request.save()
    messages.success(request, 'Job request approved and posted!')
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
    return redirect('logistics:job_detail', job_id=job_id)

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
                JobPost.objects.create(
                    title=job_request.title,
                    description=job_request.description,
                    origin=job_request.origin,
                    destination=job_request.destination,
                    cargo_type=job_request.cargo_type,
                    weight_kg=job_request.weight_kg,
                    pickup_date=job_request.pickup_date,
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
def manager_home(request):
    # Deprecated: redirect to manager_dashboard
    return redirect('logistics:manager_dashboard')

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
def manager_logs_staff(request):
    staff_activities = RecentActivity.objects.filter(user__is_staff=True).order_by('-timestamp')[:100]
    return render(request, 'manager_logs_staff.html', {'activities': staff_activities})

@user_passes_test(lambda u: u.is_superuser)
def manager_logs_users(request):
    user_activities = RecentActivity.objects.filter(user__is_staff=False).order_by('-timestamp')[:100]
    return render(request, 'manager_logs_users.html', {'activities': user_activities})

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
            if 'promote_to_staff' in request.POST:
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
def book_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id)
    already_booked = BookedJob.objects.filter(user=request.user, job=job).exists()
    if not already_booked:
        BookedJob.objects.create(user=request.user, job=job)
        job.hidden = True
        job.save()
        messages.success(request, 'Job booked successfully!')
    else:
        messages.info(request, 'You have already booked this job.')
    return redirect('logistics:job_detail', job_id=job.id)

@login_required
def hidden_jobs(request):
    jobs = JobPost.objects.filter(hidden=True).select_related('cargo_type', 'created_by')
    booked = BookedJob.objects.filter(job__in=jobs).select_related('user', 'job')
    booked_map = {b.job_id: b.user for b in booked}
    return render(request, 'hidden_jobs.html', {'jobs': jobs, 'booked_map': booked_map})
