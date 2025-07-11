from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class JobCategory(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Job Categories"

class JobPost(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    cargo_type = models.ForeignKey(JobCategory, on_delete=models.CASCADE)
    weight_kg = models.FloatField(null=True, blank=True)
    pickup_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)
    # Extra fields for full job info
    origin_zip = models.CharField(max_length=20, blank=True)
    destination_zip = models.CharField(max_length=20, blank=True)
    origin_address = models.CharField(max_length=255, blank=True)
    destination_address = models.CharField(max_length=255, blank=True)
    length_cm = models.FloatField(null=True, blank=True)
    width_cm = models.FloatField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    volume_m3 = models.FloatField(null=True, blank=True)
    special_requirements = models.TextField(blank=True)
    pickup_time_from = models.TimeField(null=True, blank=True)
    pickup_time_to = models.TimeField(null=True, blank=True)
    delivery_deadline = models.DateField(null=True, blank=True)
    declared_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reference_code = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.title
    
    def like_count(self):
        return self.joblike_set.count()
    
    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return self.joblike_set.filter(user=user).exists()
    
    class Meta:
        ordering = ['-created_at']

class JobLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} likes {self.job.title}"
    
    class Meta:
        unique_together = ['user', 'job']
        verbose_name_plural = "Job Likes"

class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.user.username} - {self.job.title}"
    
    class Meta:
        unique_together = ['user', 'job']
        verbose_name_plural = "Saved Jobs"

class JobRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    cargo_type = models.ForeignKey(JobCategory, on_delete=models.CASCADE)
    weight_kg = models.FloatField(null=True, blank=True)
    pickup_date = models.DateField()
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    staff_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    origin_zip = models.CharField(max_length=20, blank=True)
    destination_zip = models.CharField(max_length=20, blank=True)
    length_cm = models.FloatField(null=True, blank=True)
    width_cm = models.FloatField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    volume_m3 = models.FloatField(null=True, blank=True)
    special_requirements = models.TextField(blank=True)
    pickup_time_from = models.TimeField(null=True, blank=True)
    pickup_time_to = models.TimeField(null=True, blank=True)
    delivery_deadline = models.DateField(null=True, blank=True)
    declared_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reference_code = models.CharField(max_length=100, blank=True)
    origin_address = models.CharField(max_length=255, blank=True)
    destination_address = models.CharField(max_length=255, blank=True)
    num_boxes = models.PositiveIntegerField(default=1)
    weight_per_box_kg = models.FloatField(null=True, blank=True)
    length_per_box_cm = models.FloatField(null=True, blank=True)
    width_per_box_cm = models.FloatField(null=True, blank=True)
    height_per_box_cm = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} (requested by {self.requested_by.username})"

class JobFlag(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='flags')
    flagged_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Flag on {self.job.title} by {self.flagged_by.username} ({self.status})"

class RecentActivity(models.Model):
    ACTION_CHOICES = [
        ('bulk_approve', 'Bulk Approve'),
        ('bulk_remove', 'Bulk Remove'),
        ('single_remove', 'Single Remove'),
        ('hide', 'Hide'),
        ('unhide', 'Unhide'),
        ('export_csv', 'Export CSV'),
    ]
    TARGET_CHOICES = [
        ('job_request', 'Job Request'),
        ('job', 'Job'),
        ('export', 'Export'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    target_ids = models.CharField(max_length=255)  # Comma-separated IDs
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} {self.get_action_display()} {self.target_type} [{self.target_ids}] at {self.timestamp}"

class BookedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'job']
        verbose_name_plural = 'Booked Jobs'

    def __str__(self):
        return f"{self.user.username} booked {self.job.title} at {self.booked_at}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    answered = models.BooleanField(default=False)
    answer_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.created_at:%Y-%m-%d %H:%M}"
