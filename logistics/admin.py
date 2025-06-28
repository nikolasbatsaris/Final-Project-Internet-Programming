from django.contrib import admin
from .models import JobCategory, JobPost, SavedJob, JobLike

# Register your models here.

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'origin', 'created_by', 'like_count']
    list_filter = ['cargo_type', 'pickup_date', 'created_at']
    search_fields = ['title', 'description', 'origin', 'destination']
    list_select_related = ['cargo_type', 'created_by']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    def like_count(self, obj):
        return obj.like_count()
    like_count.short_description = 'Likes'

@admin.register(JobLike)
class JobLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'created_at']
    list_filter = ['created_at', 'job__cargo_type']
    search_fields = ['user__username', 'job__title']
    list_select_related = ['user', 'job']
    date_hierarchy = 'created_at'

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'job_title', 'job_origin', 'job_destination']
    list_filter = ['job__cargo_type']
    search_fields = ['user__username', 'user__email', 'job__title']
    list_select_related = ['user', 'job']
    
    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = 'Job Title'
    
    def job_origin(self, obj):
        return obj.job.origin
    job_origin.short_description = 'Origin'
    
    def job_destination(self, obj):
        return obj.job.destination
    job_destination.short_description = 'Destination'
