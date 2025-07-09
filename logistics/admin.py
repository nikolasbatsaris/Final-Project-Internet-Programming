from django.contrib import admin
from .models import JobCategory, JobPost, JobLike, ContactMessage

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



admin.site.register(ContactMessage)
