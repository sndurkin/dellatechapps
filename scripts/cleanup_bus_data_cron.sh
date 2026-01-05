#!/bin/bash
# Cron script to run the BusData cleanup command daily
# This script should be executed once per day

cd /app
python manage.py cleanup_old_bus_data
