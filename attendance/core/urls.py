from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),

    # Admin
    path('manage/', views.admin_dashboard, name='admin_dashboard'),
    path('manage/approve/<int:reg_id>/', views.admin_approve_registration, name='admin_approve_registration'),
    path('manage/add-student/', views.admin_add_student, name='admin_add_student'),
    path('manage/add-teacher/', views.admin_add_teacher, name='admin_add_teacher'),
    path('manage/remove/<int:uid>/', views.admin_remove_user, name='admin_remove_user'),

    # Teacher
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/mark/', views.mark_attendance, name='mark_attendance'),
    path('teacher/add-student/', views.teacher_add_student, name='teacher_add_student'),
    path('teacher/request/<int:req_id>/', views.teacher_handle_attendance_request, name='teacher_handle_request'),

    # Student
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/request-attendance/', views.student_request_attendance, name='student_request_attendance'),
]
