"""
URL configuration for moniepoint project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path
from analytics.views import (
    TopMerchantView,
    MonthlyActiveMerchantsView,
    ProductAdoptionView,
    KYCFunnelView,
    FailureRatesView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Analytics API endpoints using Django REST Framework
    path('analytics/top-merchant', TopMerchantView.as_view(), name='top-merchant'),
    path('analytics/monthly-active-merchants', MonthlyActiveMerchantsView.as_view(), name='monthly-active-merchants'),
    path('analytics/product-adoption', ProductAdoptionView.as_view(), name='product-adoption'),
    path('analytics/kyc-funnel', KYCFunnelView.as_view(), name='kyc-funnel'),
    path('analytics/failure-rates', FailureRatesView.as_view(), name='failure-rates'),
]
