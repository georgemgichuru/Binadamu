from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth'          # Python package path (keeps current folder)
    label = 'accounts'     # app label used by Django (avoids conflict with 'auth')
    verbose_name = "Local Accounts"
