"""
URL configuration for moniepoint project.

This module defines all URL routes for the Analytics API.
All analytics endpoints are prefixed with /analytics/.
"""
from django.contrib import admin
from django.urls import path

from analytics import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Analytics API endpoints
    path('analytics/top-merchant', views.top_merchant, name='top-merchant'),
    path('analytics/monthly-active-merchants', views.monthly_active_merchants, name='monthly-active-merchants'),
    path('analytics/product-adoption', views.product_adoption, name='product-adoption'),
    path('analytics/kyc-funnel', views.kyc_funnel, name='kyc-funnel'),
    path('analytics/failure-rates', views.failure_rates, name='failure-rates'),
]
