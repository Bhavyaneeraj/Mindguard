import sys
import os

# Point to your Django project
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "browser_tracker.settings")

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
