"""
Django app configuration for the Analytics application.

This module defines the AnalyticsConfig class which configures the analytics app
for Django's application registry.
"""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """
    Configuration class for the Analytics Django application.
    
    This class is used by Django to configure the analytics app, including
    its name and any app-specific settings.
    """
    
    default_auto_field: str = 'django.db.models.BigAutoField'
    """Default primary key field type for models in this app."""
    
    name: str = 'analytics'
    """Full Python path to the application (e.g., 'analytics')."""
