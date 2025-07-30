"""
Test settings for the Sanusi project.
This file overrides settings for testing purposes.
"""

from .settings import *

# Use SQLite for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable email sending during tests
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# Set default values for required environment variables
SECRET_KEY = "test-secret-key-for-testing-only"
DEBUG = True
FRONTEND_BASE_URL = "http://localhost:3000"
OPENAI_KEY = "test-openai-key"

# Email settings for testing
EMAIL_HOST = "localhost"
EMAIL_PORT = 587
EMAIL_HOST_USER = "test@example.com"
EMAIL_HOST_PASSWORD = "test-password"

# Database settings for testing
DB_NAME = "test_db"
DB_USER = "test_user"
DB_PASSWORD = "test_password"
DB_HOST = "localhost"
DB_PORT = 5432

# Disable telemetry during tests
TELEMETRY_ENABLED = False

# Use in-memory cache for testing
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Disable static files collection during tests
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage" 