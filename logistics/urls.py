from django.urls import path
from . import views

app_name = 'logistics'

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/save/', views.save_job, name='save_job'),
    path('jobs/<int:job_id>/like/', views.like_job, name='like_job'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('post-job/', views.post_job, name='post_job'),
    path('saved-jobs/<int:job_id>/remove/', views.remove_saved_job, name='remove_saved_job'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('request-job/', views.request_job, name='request_job'),
    path('my-job-requests/', views.my_job_requests, name='my_job_requests'),
    path('job-request/<int:req_id>/approve/', views.approve_job_request, name='approve_job_request'),
    path('job-request/<int:req_id>/reject/', views.reject_job_request, name='reject_job_request'),
    path('jobs/<int:job_id>/flag/', views.flag_job, name='flag_job'),
    path('jobs/<int:job_id>/hide/', views.hide_job, name='hide_job'),
    path('jobs/<int:job_id>/unhide/', views.unhide_job, name='unhide_job'),
    path('jobs/<int:job_id>/remove/', views.remove_job, name='remove_job'),
    path('flags/<int:flag_id>/close/', views.close_flag, name='close_flag'),
    path('admin-dashboard/bulk-job-requests/', views.bulk_job_request_action, name='bulk_job_request_action'),
    path('admin-dashboard/bulk-live-jobs/', views.bulk_live_job_action, name='bulk_live_job_action'),
    path('admin-dashboard/export-jobs-csv/', views.export_jobs_csv, name='export_jobs_csv'),
    path('manager-home/', views.manager_home, name='manager_home'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager-logs/staff/', views.manager_logs_staff, name='manager_logs_staff'),
    path('manager-logs/users/', views.manager_logs_users, name='manager_logs_users'),
    path('manager-edit-user/<int:user_id>/', views.manager_edit_user, name='manager_edit_user'),
    path('jobs/<int:job_id>/book/', views.book_job, name='book_job'),
] 