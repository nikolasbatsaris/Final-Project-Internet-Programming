from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, SetPasswordForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from .models import JobPost, SavedJob, JobLike, JobRequest, JobFlag
from django import forms
from django.utils import timezone
from django.contrib.auth.models import User

# Create your views here.

def home(request):
    """Home page view"""
    return render(request, 'home.html')

def job_list(request):
    """Display list of all job posts"""
    jobs = JobPost.objects.select_related('cargo_type', 'created_by').filter(hidden=False)
    return render(request, 'job_list.html', {'jobs': jobs})

def job_detail(request, job_id):
    """Display detailed view of a specific job post"""
    job = get_object_or_404(JobPost, id=job_id)
    is_liked = job.is_liked_by(request.user) if request.user.is_authenticated else False
    return render(request, 'job_detail.html', {
        'job': job, 
        'is_liked': is_liked,
        'like_count': job.like_count()
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
    return render(request, 'dashboard.html', {
        'saved_jobs': saved_jobs,
        'profile': profile,
        'recent_saved': recent_saved,
        'job_statuses': job_statuses,
        'show_change_password': show_change_password,
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
    # Jobs
    live_jobs = JobPost.objects.filter(hidden=False).order_by('-created_at')
    hidden_jobs = JobPost.objects.filter(hidden=True).order_by('-created_at')
    flagged_jobs = JobPost.objects.filter(flags__status='open').distinct().order_by('-created_at')
    # Requests
    job_requests = JobRequest.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'admin_dashboard.html', {
        'job_requests': job_requests,
        'live_jobs': live_jobs,
        'hidden_jobs': hidden_jobs,
        'flagged_jobs': flagged_jobs,
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

    class Meta:
        model = JobRequest
        fields = ['title', 'description', 'origin', 'destination', 'cargo_type', 'weight_kg', 'pickup_date']

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
    messages.success(request, 'Job has been hidden from public view.')
    return redirect('logistics:job_detail', job_id=job_id)

@login_required
@require_POST
def unhide_job(request, job_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    job = get_object_or_404(JobPost, id=job_id)
    job.hidden = False
    job.save()
    messages.success(request, 'Job is now visible to users.')
    return redirect('logistics:job_detail', job_id=job_id)

@login_required
@require_POST
def remove_job(request, job_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    job = get_object_or_404(JobPost, id=job_id)
    job.delete()
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
