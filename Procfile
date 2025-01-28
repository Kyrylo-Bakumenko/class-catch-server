web: gunicorn backend.wsgi --log-file - --preload
worker-check-availability: python manage.py check_availability
worker-refresh-proxies: python manage.py refresh_proxies
worker-scrape-classes: python manage.py scrape_classes