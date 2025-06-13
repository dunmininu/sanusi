# import os
# from celery import Celery

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sanusi_backend.settings")
# app = Celery("sanusi_backend")
# app.config_from_object("django.conf:settings", namespace="CELERY")
# app.autodiscover_tasks()


# import os

# from celery import Celery
# from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sanusi_backend.settings")

# app = TenantAwareCeleryApp("sanusi_backend")

# app.config_from_object("django.conf:settings", namespace="CELERY")

# app.autodiscover_tasks()
