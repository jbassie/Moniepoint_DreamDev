"""
Django app configuration for the analytics application.
"""
from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """
    Configuration class for the analytics Django app.
    
    This app provides models, views, and management commands for
    analyzing merchant activity data.
    """
    default_auto_field: str = 'django.db.models.BigAutoField'
    name: str = 'analytics'
    verbose_name: str = 'Analytics'
