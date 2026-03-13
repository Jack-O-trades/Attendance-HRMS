"""
WSGI config for attendance project.
"""

import os
import sys
from pathlib import Path

# Add the Django project root (the folder containing manage.py) to sys.path
# so that 'attendance.settings' can be found when Vercel runs this file
# from the repo root as a serverless function.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance.settings')

application = get_wsgi_application()
