#!/bin/bash
pip install -r requirements.txt
python attendance/manage.py collectstatic --noinput --clear
