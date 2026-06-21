release: python manage.py migrate && python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@admin.com', 'JAZ051236') if not User.objects.filter(username='admin').exists() else print('Admin exists')"
web: gunicorn pharmaerp.wsgi --log-file -
