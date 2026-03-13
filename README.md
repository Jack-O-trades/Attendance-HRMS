# 🎓 EduTrack — Student Attendance & HRMS

A full-featured **Django web application** for managing student attendance, teacher workflows, and organisation administration — all in one place.

---

## ✨ Features

### 👤 Role-Based Access
| Role | Capabilities |
|------|-------------|
| **Admin / Organisation** | Approve registrations, add/remove teachers & students, full dashboard |
| **Teacher** | Mark attendance, add students directly, approve student attendance requests |
| **Student** | View personal attendance, submit attendance requests |

### 🔐 Authentication & Registration
- Role-aware login page (Student / Teacher / Organisation)
- Self-registration with **email verification** — accounts are held pending until admin approves
- Admin can directly create teacher or student accounts
- Teachers can directly add students to their class

### 📋 Attendance System
- Teachers mark attendance (present/absent) per date per student
- Students can **request attendance** for a specific date; teacher approves/denies
- Attendance records are unique per student per date

### 📬 Email Notifications
- Email verification on self-registration
- Configurable between console output (dev) and Gmail SMTP (production)

---

## 🛠️ Tech Stack

- **Backend:** Python 3 · Django 4+
- **Database:** SQLite (default) — easily swappable for PostgreSQL
- **Frontend:** Django Templates · HTML/CSS
- **Auth:** Custom user model (`core.CustomUser`) with role field

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/Student-System.git
cd Student-System
```

### 2. Create & activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install django
```
> If a `requirements.txt` exists, use `pip install -r requirements.txt` instead.

### 4. Apply migrations
```bash
cd attendance
python manage.py migrate
```

### 5. Seed initial data *(optional)*
```bash
python manage.py seed_data
```

### 6. Create a superuser
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 📁 Project Structure

```
Student-System/
├── attendance/                 # Django project root
│   ├── attendance/             # Project settings & URL config
│   │   ├── settings.py
│   │   └── urls.py
│   ├── core/                   # Main application
│   │   ├── models.py           # CustomUser, Attendance, PendingRegistration, etc.
│   │   ├── views.py            # All business logic & views
│   │   ├── urls.py             # URL routing
│   │   ├── admin.py            # Django admin registrations
│   │   ├── templates/core/     # HTML templates
│   │   └── management/         # Custom management commands (seed_data)
│   └── manage.py
├── venv/                       # Virtual environment (not committed)
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

### Email
By default, emails print to the terminal. To send real emails via Gmail SMTP, update `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'   # Gmail App Password, not your real password
DEFAULT_FROM_EMAIL = 'EduTrack <your@gmail.com>'
```

> **Tip:** Generate a Gmail App Password at [myaccount.google.com → Security → App passwords](https://myaccount.google.com/apppasswords).

### Time Zone
Set to `Asia/Kolkata` by default. Change `TIME_ZONE` in `settings.py` as needed.

---

## 🔒 Security Notes

> [!WARNING]
> Before deploying to production:
> - Replace `SECRET_KEY` in `settings.py` with a strong, randomly generated key
> - Set `DEBUG = False`
> - Move credentials to environment variables (e.g., via `python-decouple` or `.env`)
> - Configure `ALLOWED_HOSTS` with your actual domain

---

## 📜 License

This project is for educational purposes. Feel free to fork and extend it.
