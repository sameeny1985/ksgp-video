web: gunicorn ksgp_video.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
release: python manage.py migrate --noinput
