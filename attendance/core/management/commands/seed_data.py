from django.core.management.base import BaseCommand
from core.models import CustomUser, StudentProfile, TeacherProfile, Attendance
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Seeds the database with sample data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # ── Admin ──────────────────────────────────────────────────────────────
        admin_user, created = CustomUser.objects.get_or_create(
            username='admin1',
            defaults={
                'first_name': 'Alice', 'last_name': 'Admin',
                'email': 'alice@example.com', 'phone': '9000000001',
                'role': 'admin', 'is_staff': True, 'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('  [+] Admin created: admin1 / admin123')
        else:
            self.stdout.write('  [=] Admin already exists: admin1')

        # ── Teachers ───────────────────────────────────────────────────────────
        teachers_data = [
            {'username': 'teacher1', 'first_name': 'Bob', 'last_name': 'Smith',
             'email': 'bob@example.com', 'phone': '9000000002'},
            {'username': 'teacher2', 'first_name': 'Carol', 'last_name': 'Jones',
             'email': 'carol@example.com', 'phone': '9000000003'},
        ]

        teacher_profiles = []
        for tdata in teachers_data:
            user, created = CustomUser.objects.get_or_create(
                username=tdata['username'],
                defaults={**tdata, 'role': 'teacher'}
            )
            if created:
                user.set_password('teacher123')
                user.save()
                self.stdout.write(f"  [+] Teacher created: {tdata['username']} / teacher123")
            profile, _ = TeacherProfile.objects.get_or_create(user=user)
            teacher_profiles.append(profile)

        # ── Students ───────────────────────────────────────────────────────────
        students_data = [
            {'username': 'student1', 'first_name': 'David', 'last_name': 'Lee',
             'email': 'david@example.com', 'phone': '9001000001', 'reg_no': 'REG2024001'},
            {'username': 'student2', 'first_name': 'Emma', 'last_name': 'Brown',
             'email': 'emma@example.com', 'phone': '9001000002', 'reg_no': 'REG2024002'},
            {'username': 'student3', 'first_name': 'Frank', 'last_name': 'Wilson',
             'email': 'frank@example.com', 'phone': '9001000003', 'reg_no': 'REG2024003'},
            {'username': 'student4', 'first_name': 'Grace', 'last_name': 'Taylor',
             'email': 'grace@example.com', 'phone': '9001000004', 'reg_no': 'REG2024004'},
            {'username': 'student5', 'first_name': 'Henry', 'last_name': 'Martin',
             'email': 'henry@example.com', 'phone': '9001000005', 'reg_no': 'REG2024005'},
        ]

        student_profiles = []
        for sdata in students_data:
            reg_no = sdata.pop('reg_no')
            user, created = CustomUser.objects.get_or_create(
                username=sdata['username'],
                defaults={**sdata, 'role': 'student'}
            )
            if created:
                user.set_password('student123')
                user.save()
                self.stdout.write(f"  [+] Student created: {sdata['username']} / student123")
            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={'registration_number': reg_no}
            )
            student_profiles.append(profile)

        # ── Attendance Records (last 14 days) ──────────────────────────────────
        today = date.today()
        created_count = 0
        for student in student_profiles:
            for i in range(14):
                att_date = today - timedelta(days=i)
                if att_date.weekday() >= 5:  # skip weekends
                    continue
                status = random.choices(['present', 'absent'], weights=[80, 20])[0]
                teacher = random.choice(teacher_profiles)
                _, created = Attendance.objects.get_or_create(
                    student=student,
                    date=att_date,
                    defaults={'teacher': teacher, 'status': status}
                )
                if created:
                    created_count += 1

        self.stdout.write(f'\nDone! Created {created_count} attendance records.')
        self.stdout.write('\nTest Credentials:')
        self.stdout.write('  Admin:   admin1   / admin123')
        self.stdout.write('  Teacher: teacher1 / teacher123')
        self.stdout.write('  Student: student1 / student123')
