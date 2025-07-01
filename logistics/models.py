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
    weight_kg = models.FloatField()
    pickup_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)
    
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
    weight_kg = models.FloatField()
    pickup_date = models.DateField()
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    staff_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
