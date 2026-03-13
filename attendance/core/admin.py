from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, StudentProfile, TeacherProfile, Attendance


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Contact', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Contact', {'fields': ('role', 'phone')}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'registration_number']
    search_fields = ['user__username', 'registration_number']


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user']
    search_fields = ['user__username']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'teacher']
    list_filter = ['status', 'date']
    search_fields = ['student__registration_number', 'student__user__first_name']


admin.site.register(CustomUser, CustomUserAdmin)
