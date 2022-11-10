import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vehicle_ads.settings")
app = Celery("vehicle_ads")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
