from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [('admin', 'Admin'), ('teacher', 'Teacher'), ('student', 'Student')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    registration_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.registration_number}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')

    def __str__(self):
        return self.user.get_full_name()


class Attendance(models.Model):
    STATUS_CHOICES = [('present', 'Present'), ('absent', 'Absent')]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} — {self.date} — {self.status}"


class PendingRegistration(models.Model):
    """Stores self-registration requests awaiting admin approval."""
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')]
    ROLE_CHOICES = [('teacher', 'Teacher'), ('student', 'Student')]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    registration_number = models.CharField(max_length=50, blank=True)  # students only
    password = models.CharField(max_length=128)  # stores hashed password
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role}) — {self.status}"


class AttendanceRequest(models.Model):
    """Student-submitted attendance requests awaiting teacher approval."""
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_requests')
    date = models.DateField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests'
    )

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.user.get_full_name()} — {self.date} — {self.status}"
