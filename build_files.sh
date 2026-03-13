#!/bin/bash
pip install -r requirements.txt --break-system-packages
python attendance/manage.py collectstatic --noinput --clear
