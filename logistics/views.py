from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from .models import JobPost, SavedJob, JobLike
from django import forms
from django.utils import timezone

# Create your views here.

def home(request):
    """Home page view"""
    return render(request, 'home.html')

def job_list(request):
    """Display list of all job posts"""
    jobs = JobPost.objects.select_related('cargo_type', 'created_by').all()
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
    """User dashboard showing saved jobs"""
    saved_jobs = SavedJob.objects.filter(user=request.user).select_related('job', 'job__cargo_type', 'job__created_by')
    return render(request, 'dashboard.html', {'saved_jobs': saved_jobs})

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
    """Admin-only dashboard view"""
    if not request.user.is_staff:
        return render(request, 'admin_error.html', status=403)
    # Example admin data: all jobs, all users, etc.
    all_jobs = JobPost.objects.all()
    all_users = SavedJob.objects.values('user').distinct().count()
    return render(request, 'admin_dashboard.html', {
        'all_jobs': all_jobs,
        'user_count': all_users,
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
