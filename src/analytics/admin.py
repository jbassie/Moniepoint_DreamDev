"""
Django admin configuration for the Analytics app.

This module registers the MerchantActivity model with the Django admin interface,
allowing administrators to view and manage merchant activity data.
"""

from django.contrib import admin
from .models import MerchantActivity


@admin.register(MerchantActivity)
class MerchantActivityAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for MerchantActivity model.

    Provides a user-friendly interface for viewing and managing merchant activities
    with search, filtering, and list display capabilities.
    """

    list_display: list[str] = [
        'event_id',
        'merchant_id',
        'event_timestamp',
        'product',
        'event_type',
        'amount',
        'status',
        'channel',
        'region',
        'merchant_tier'
    ]
    """Fields to display in the admin list view."""

    list_filter: list[str] = [
        'product',
        'status',
        'channel',
        'merchant_tier',
        'region'
    ]
    """Fields available for filtering in the admin interface."""

    search_fields: list[str] = [
        'merchant_id',
        'event_id',
        'event_type'
    ]
    """Fields searchable in the admin interface."""

    readonly_fields: list[str] = ['event_id']
    """Fields that are read-only in the admin interface."""

    date_hierarchy: str = 'event_timestamp'
    """Enable date-based navigation by event timestamp."""

    ordering: list[str] = ['-event_timestamp']
    """Default ordering for the list view (newest first)."""
