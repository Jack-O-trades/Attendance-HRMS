import uuid
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import CustomUser, StudentProfile, TeacherProfile, Attendance, PendingRegistration, AttendanceRequest


# ─── Helpers ───────────────────────────────────────────────────────────────────

def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('login')
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator


def _redirect_by_role(user):
    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    return redirect('student_dashboard')


def _send_verification_email(request, pending):
    """Send email verification link to the registrant."""
    if not pending.email:
        return
    verify_url = request.build_absolute_uri(f'/verify-email/{pending.verification_token}/')
    subject = 'EduTrack — Verify Your Email'
    message = (
        f"Hello {pending.first_name},\n\n"
        f"Thank you for registering on EduTrack as a {pending.role.capitalize()}.\n\n"
        f"Please click the link below to verify your email address:\n"
        f"{verify_url}\n\n"
        f"Once verified, your registration will be sent to the admin for approval.\n\n"
        f"— EduTrack Team"
    )
    send_mail(subject, message, 'EduTrack <noreply@edutrack.com>', [pending.email], fail_silently=True)


def _send_approval_email(pending):
    """Send congratulations email when admin approves a registration."""
    if not pending.email:
        return
    subject = 'EduTrack — Registration Approved!'
    message = (
        f"Hello {pending.first_name},\n\n"
        f"Congratulations! Your registration as a {pending.role.capitalize()} on EduTrack "
        f"has been approved by the administrator.\n\n"
        f"You can now log in using your credentials:\n"
        f"  Username: {pending.username}\n"
        f"  Password: (the one you set during registration)\n\n"
        f"Please visit the EduTrack portal to sign in.\n\n"
        f"— EduTrack Team"
    )
    send_mail(subject, message, 'EduTrack <noreply@edutrack.com>', [pending.email], fail_silently=True)


def _send_denial_email(pending):
    """Send notification email when admin denies a registration."""
    if not pending.email:
        return
    subject = 'EduTrack — Registration Update'
    message = (
        f"Hello {pending.first_name},\n\n"
        f"We regret to inform you that your registration request as a {pending.role.capitalize()} "
        f"on EduTrack has been reviewed and was not approved at this time.\n\n"
        f"Please contact the school administration for further assistance.\n\n"
        f"— EduTrack Team"
    )
    send_mail(subject, message, 'EduTrack <noreply@edutrack.com>', [pending.email], fail_silently=True)


# ─── Register (Front Page) ──────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        role = request.POST.get('role', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        confirm = request.POST.get('confirm_password', '').strip()
        reg_no = request.POST.get('registration_number', '').strip()

        if role not in ('teacher', 'student'):
            messages.error(request, 'Please select a valid role (Student or Teacher).')
            return render(request, 'core/register.html')

        if not all([first_name, last_name, username, password]):
            messages.error(request, 'First name, last name, username and password are required.')
            return render(request, 'core/register.html')

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/register.html')

        if role == 'student' and not reg_no:
            messages.error(request, 'Registration number is required for students.')
            return render(request, 'core/register.html')

        if not email:
            messages.error(request, 'An email address is required for verification.')
            return render(request, 'core/register.html')

        if CustomUser.objects.filter(username=username).exists() or \
           PendingRegistration.objects.filter(username=username, status='pending').exists():
            messages.error(request, 'Username already taken. Please choose another.')
            return render(request, 'core/register.html')

        token = uuid.uuid4()
        pending = PendingRegistration.objects.create(
            first_name=first_name, last_name=last_name, username=username,
            email=email, phone=phone, role=role,
            registration_number=reg_no,
            password=make_password(password),
            email_verified=False,
            verification_token=token,
        )
        _send_verification_email(request, pending)
        messages.success(
            request,
            f'Registration submitted! A verification email has been sent to {email}. '
            f'Please verify your email before admin can review your application.'
        )
        return render(request, 'core/register.html')

    return render(request, 'core/register.html')


def verify_email(request, token):
    """Handle email verification link click."""
    try:
        pending = PendingRegistration.objects.get(verification_token=token, email_verified=False)
    except PendingRegistration.DoesNotExist:
        messages.error(request, 'This verification link is invalid or has already been used.')
        return render(request, 'core/verify_result.html', {'success': False})

    pending.email_verified = True
    pending.save()
    return render(request, 'core/verify_result.html', {'success': True, 'pending': pending})


# ─── Login ──────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        selected_role = request.POST.get('role', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'core/login.html')

        if selected_role == 'admin' and user.role != 'admin':
            messages.error(request, 'Please contact administrator for access.')
            return render(request, 'core/login.html')

        if selected_role != 'admin' and user.role == 'admin':
            messages.error(request, 'Please select "Organisation" to log in as admin.')
            return render(request, 'core/login.html')

        if selected_role and selected_role != user.role and selected_role != 'admin':
            messages.error(request, f'Your account is not registered as a {selected_role}.')
            return render(request, 'core/login.html')

        login(request, user)
        return _redirect_by_role(user)

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('register')


# ─── Admin Dashboard ────────────────────────────────────────────────────────────

@login_required
@role_required('admin')
def admin_dashboard(request):
    tab = request.GET.get('tab', 'overview')

    student_query = request.GET.get('sq', '')
    students = StudentProfile.objects.select_related('user').all()
    if student_query:
        students = students.filter(
            Q(registration_number__icontains=student_query) |
            Q(user__first_name__icontains=student_query) |
            Q(user__last_name__icontains=student_query) |
            Q(user__email__icontains=student_query)
        )

    teachers = TeacherProfile.objects.select_related('user').all()

    records = Attendance.objects.select_related('student__user', 'teacher__user').all()
    date_filter = request.GET.get('date', '')
    att_query = request.GET.get('aq', '')
    if date_filter:
        records = records.filter(date=date_filter)
    if att_query:
        records = records.filter(
            Q(student__registration_number__icontains=att_query) |
            Q(student__user__first_name__icontains=att_query)
        )

    # Only show email-verified pending registrations to admin
    pending_students = PendingRegistration.objects.filter(
        role='student', email_verified=True
    ).order_by('-created_at')
    pending_teachers = PendingRegistration.objects.filter(
        role='teacher', email_verified=True
    ).order_by('-created_at')

    context = {
        'tab': tab,
        'students': students,
        'teachers': teachers,
        'records': records,
        'student_query': student_query,
        'date_filter': date_filter,
        'att_query': att_query,
        'total_students': StudentProfile.objects.count(),
        'total_teachers': TeacherProfile.objects.count(),
        'total_attendance': Attendance.objects.count(),
        'present_count': Attendance.objects.filter(status='present').count(),
        'pending_students': pending_students,
        'pending_teachers': pending_teachers,
        'pending_count': PendingRegistration.objects.filter(status='pending', email_verified=True).count(),
    }
    return render(request, 'core/admin.html', context)


@login_required
@role_required('admin')
def admin_approve_registration(request, reg_id):
    pending = get_object_or_404(PendingRegistration, id=reg_id)
    action = request.POST.get('action')

    if action == 'approve' and pending.status == 'pending':
        user = CustomUser.objects.create(
            username=pending.username,
            first_name=pending.first_name,
            last_name=pending.last_name,
            email=pending.email,
            phone=pending.phone,
            role=pending.role,
            password=pending.password,
        )
        if pending.role == 'student':
            StudentProfile.objects.create(user=user, registration_number=pending.registration_number)
        else:
            TeacherProfile.objects.create(user=user)
        pending.status = 'approved'
        pending.save()
        _send_approval_email(pending)
        messages.success(request, f'{pending.username} approved. Congratulations email sent to {pending.email}.')

    elif action == 'deny' and pending.status == 'pending':
        pending.status = 'denied'
        pending.save()
        _send_denial_email(pending)
        messages.success(request, f'{pending.username} registration denied. Notification sent.')
    else:
        messages.error(request, 'Invalid action.')

    return redirect(f'/manage/?tab={"students" if pending.role == "student" else "teachers"}')


@login_required
@role_required('admin')
def admin_add_student(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        reg_no = request.POST.get('registration_number', '').strip()

        if not all([first_name, last_name, username, password, reg_no]):
            messages.error(request, 'All fields are required.')
            return redirect('/manage/?tab=students')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return redirect('/manage/?tab=students')

        user = CustomUser.objects.create_user(
            username=username, password=password,
            first_name=first_name, last_name=last_name,
            email=email, phone=phone, role='student'
        )
        StudentProfile.objects.create(user=user, registration_number=reg_no)
        messages.success(request, f'Student {user.get_full_name()} added successfully.')
    return redirect('/manage/?tab=students')


@login_required
@role_required('admin')
def admin_add_teacher(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([first_name, last_name, username, password]):
            messages.error(request, 'All fields are required.')
            return redirect('/manage/?tab=teachers')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return redirect('/manage/?tab=teachers')

        user = CustomUser.objects.create_user(
            username=username, password=password,
            first_name=first_name, last_name=last_name,
            email=email, phone=phone, role='teacher'
        )
        TeacherProfile.objects.create(user=user)
        messages.success(request, f'Teacher {user.get_full_name()} added successfully.')
    return redirect('/manage/?tab=teachers')


@login_required
@role_required('admin')
def admin_remove_user(request, uid):
    user = get_object_or_404(CustomUser, id=uid)
    if user.role == 'admin':
        messages.error(request, 'Cannot remove admin users.')
        return redirect('admin_dashboard')
    name = user.get_full_name()
    role = user.role
    user.delete()
    messages.success(request, f'{name} ({role}) removed successfully.')
    return redirect(f'/manage/?tab={"students" if role == "student" else "teachers"}')


# ─── Teacher Dashboard ──────────────────────────────────────────────────────────

@login_required
@role_required('teacher')
def teacher_dashboard(request):
    teacher = get_object_or_404(TeacherProfile, user=request.user)
    tab = request.GET.get('tab', 'mark')
    today = timezone.localdate()

    all_students = StudentProfile.objects.select_related('user').all()
    today_marked = set(Attendance.objects.filter(date=today).values_list('student_id', flat=True))
    recent_records = Attendance.objects.filter(teacher=teacher).select_related('student__user').order_by('-date')[:12]

    search_query = request.GET.get('q', '').strip()
    search_results = []
    if search_query:
        search_results = all_students.filter(
            Q(registration_number__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )

    detail_student = None
    detail_records = []
    today_record = None
    if tab == 'detail':
        sid = request.GET.get('sid')
        if sid:
            detail_student = get_object_or_404(StudentProfile, id=sid)
            detail_records = Attendance.objects.filter(student=detail_student).order_by('-date')
            today_record = detail_records.filter(date=today).first()

    attendance_requests = AttendanceRequest.objects.filter(
        status='pending'
    ).select_related('student__user').order_by('-submitted_at')

    context = {
        'teacher': teacher, 'tab': tab, 'today': today,
        'all_students': all_students, 'today_marked': today_marked,
        'recent_records': recent_records, 'search_query': search_query,
        'search_results': search_results, 'detail_student': detail_student,
        'detail_records': detail_records, 'today_record': today_record,
        'attendance_requests': attendance_requests,
        'pending_requests_count': attendance_requests.count(),
    }
    return render(request, 'core/teacher.html', context)


@login_required
@role_required('teacher')
def mark_attendance(request):
    if request.method == 'POST':
        teacher = get_object_or_404(TeacherProfile, user=request.user)
        student_id = request.POST.get('student_id')
        date_str = request.POST.get('date')
        status = request.POST.get('status')
        redirect_tab = request.POST.get('redirect_tab', 'mark')
        sid = request.POST.get('sid', '')

        if not all([student_id, date_str, status]):
            messages.error(request, 'All fields are required.')
            return redirect('teacher_dashboard')

        student = get_object_or_404(StudentProfile, id=student_id)
        record, created = Attendance.objects.update_or_create(
            student=student, date=date_str,
            defaults={'teacher': teacher, 'status': status}
        )
        action = 'marked' if created else 'updated'
        messages.success(request, f'Attendance {action} for {student.user.get_full_name()} on {date_str}.')

        if redirect_tab == 'detail' and sid:
            return redirect(f'/teacher/?tab=detail&sid={sid}')
    return redirect('teacher_dashboard')


@login_required
@role_required('teacher')
def teacher_add_student(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        reg_no = request.POST.get('registration_number', '').strip()

        if not all([first_name, last_name, username, password, reg_no]):
            messages.error(request, 'All fields are required.')
            return redirect('/teacher/?tab=add_student')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return redirect('/teacher/?tab=add_student')
        if StudentProfile.objects.filter(registration_number=reg_no).exists():
            messages.error(request, f'Registration number "{reg_no}" already exists.')
            return redirect('/teacher/?tab=add_student')

        user = CustomUser.objects.create_user(
            username=username, password=password,
            first_name=first_name, last_name=last_name,
            email=email, phone=phone, role='student'
        )
        StudentProfile.objects.create(user=user, registration_number=reg_no)
        messages.success(request, f'Student {user.get_full_name()} ({reg_no}) added successfully.')
    return redirect('/teacher/?tab=add_student')


@login_required
@role_required('teacher')
def teacher_handle_attendance_request(request, req_id):
    att_req = get_object_or_404(AttendanceRequest, id=req_id)
    action = request.POST.get('action')
    teacher = get_object_or_404(TeacherProfile, user=request.user)

    if action == 'approve':
        Attendance.objects.update_or_create(
            student=att_req.student, date=att_req.date,
            defaults={'teacher': teacher, 'status': 'present'}
        )
        att_req.status = 'approved'
        att_req.approved_by = teacher
        att_req.save()
        messages.success(request, f'Approved attendance for {att_req.student.user.get_full_name()} on {att_req.date}.')
    elif action == 'deny':
        att_req.status = 'denied'
        att_req.approved_by = teacher
        att_req.save()
        messages.success(request, f'Denied attendance request for {att_req.student.user.get_full_name()}.')

    return redirect('/teacher/?tab=requests')


# ─── Student Dashboard ──────────────────────────────────────────────────────────

@login_required
@role_required('student')
def student_dashboard(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    records = Attendance.objects.filter(student=student).order_by('-date')
    total = records.count()
    present = records.filter(status='present').count()
    absent = records.filter(status='absent').count()
    percentage = round((present / total * 100), 1) if total > 0 else 0
    my_requests = AttendanceRequest.objects.filter(student=student).order_by('-submitted_at')

    context = {
        'student': student, 'records': records,
        'total': total, 'present': present, 'absent': absent,
        'percentage': percentage, 'my_requests': my_requests,
    }
    return render(request, 'core/student.html', context)


@login_required
@role_required('student')
def student_request_attendance(request):
    if request.method == 'POST':
        student = get_object_or_404(StudentProfile, user=request.user)
        date_str = request.POST.get('date', '').strip()

        if not date_str:
            messages.error(request, 'Please select a date.')
            return redirect('student_dashboard')

        if Attendance.objects.filter(student=student, date=date_str, status='present').exists():
            messages.error(request, 'You are already marked Present for this date.')
            return redirect('student_dashboard')

        _, created = AttendanceRequest.objects.get_or_create(
            student=student, date=date_str,
            defaults={'status': 'pending'}
        )
        if created:
            messages.success(request, f'Attendance request submitted for {date_str}. Waiting for teacher approval.')
        else:
            messages.error(request, 'You have already submitted a request for this date.')

    return redirect('student_dashboard')
