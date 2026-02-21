"""
API views for the Analytics endpoints.

This module contains all the view functions that handle the analytics API endpoints,
providing business insights from merchant activity data.
"""

from django.http import JsonResponse, HttpRequest
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncMonth
from typing import Dict, Any, List
from decimal import Decimal

from .models import MerchantActivity
from .constants import (
    STATUS_SUCCESS,
    STATUS_FAILED,
    STATUS_PENDING,
    DECIMAL_PLACES_AMOUNT,
    DECIMAL_PLACES_PERCENTAGE,
    KYC_DOCUMENT_SUBMITTED,
    KYC_VERIFICATION_COMPLETED,
    KYC_TIER_UPGRADE,
)


def top_merchant(request: HttpRequest) -> JsonResponse:
    """
    Get the merchant with the highest total successful transaction amount.
    
    Endpoint: GET /analytics/top-merchant
    
    Returns the merchant with the highest total volume across all products,
    considering only successful transactions.
    
    Args:
        request: HTTP request object (unused but required by Django)
    
    Returns:
        JsonResponse with merchant_id and total_volume (rounded to 2 decimal places),
        or 404 if no data found
    """
    top_merchant_data = (
        MerchantActivity.objects
        .filter(status=STATUS_SUCCESS)
        .values('merchant_id')
        .annotate(total_volume=Sum('amount'))
        .order_by('-total_volume')
        .first()
    )
    
    if top_merchant_data:
        # Format to 2 decimal places per requirements
        total_volume: float = round(float(top_merchant_data['total_volume']), DECIMAL_PLACES_AMOUNT)
        return JsonResponse({
            "merchant_id": top_merchant_data['merchant_id'],
            "total_volume": total_volume
        })
    
    return JsonResponse({"error": "No data found"}, status=404)


def monthly_active_merchants(request: HttpRequest) -> JsonResponse:
    """
    Get the count of unique merchants with at least one successful event per month.
    
    Endpoint: GET /analytics/monthly-active-merchants
    
    Returns a dictionary with month-year as keys and unique merchant counts as values.
    Only includes merchants with at least one successful event in that month.
    
    Args:
        request: HTTP request object (unused but required by Django)
    
    Returns:
        JsonResponse with monthly active merchant counts in format {"YYYY-MM": count}
    """
    monthly_data = (
        MerchantActivity.objects
        .filter(status=STATUS_SUCCESS)
        .exclude(event_timestamp__isnull=True)
        .annotate(month=TruncMonth('event_timestamp'))
        .values('month')
        .annotate(unique_merchants=Count('merchant_id', distinct=True))
        .order_by('month')
    )
    
    # Format response as {"YYYY-MM": count}
    result: Dict[str, int] = {}
    for item in monthly_data:
        month_str: str = item['month'].strftime('%Y-%m')
        result[month_str] = item['unique_merchants']
    
    return JsonResponse(result)


def product_adoption(request: HttpRequest) -> JsonResponse:
    """
    Get unique merchant count per product, sorted by count (highest first).
    
    Endpoint: GET /analytics/product-adoption
    
    Returns the number of unique merchants that have used each product,
    sorted in descending order by adoption count.
    
    Args:
        request: HTTP request object (unused but required by Django)
    
    Returns:
        JsonResponse with product names as keys and unique merchant counts as values,
        sorted by count descending
    """
    product_data = (
        MerchantActivity.objects
        .values('product')
        .annotate(unique_merchants=Count('merchant_id', distinct=True))
        .order_by('-unique_merchants')
    )
    
    # Convert to dictionary format
    result: Dict[str, int] = {}
    for item in product_data:
        result[item['product']] = item['unique_merchants']
    
    return JsonResponse(result)


def kyc_funnel(request: HttpRequest) -> JsonResponse:
    """
    Get the KYC conversion funnel metrics.
    
    Endpoint: GET /analytics/kyc-funnel
    
    Returns unique merchant counts at each stage of the KYC process:
    - documents_submitted: Merchants who submitted KYC documents
    - verifications_completed: Merchants who completed verification
    - tier_upgrades: Merchants who upgraded their tier
    
    Only counts successful KYC events.
    
    Args:
        request: HTTP request object (unused but required by Django)
    
    Returns:
        JsonResponse with KYC funnel metrics
    """
    # Count unique merchants at each stage (only successful events)
    documents_submitted = (
        MerchantActivity.objects
        .filter(
            product='KYC',
            event_type=KYC_DOCUMENT_SUBMITTED,
            status=STATUS_SUCCESS
        )
        .values('merchant_id')
        .distinct()
        .count()
    )
    
    verifications_completed = (
        MerchantActivity.objects
        .filter(
            product='KYC',
            event_type=KYC_VERIFICATION_COMPLETED,
            status=STATUS_SUCCESS
        )
        .values('merchant_id')
        .distinct()
        .count()
    )
    
    tier_upgrades = (
        MerchantActivity.objects
        .filter(
            product='KYC',
            event_type=KYC_TIER_UPGRADE,
            status=STATUS_SUCCESS
        )
        .values('merchant_id')
        .distinct()
        .count()
    )
    
    return JsonResponse({
        "documents_submitted": documents_submitted,
        "verifications_completed": verifications_completed,
        "tier_upgrades": tier_upgrades
    })


def failure_rates(request: HttpRequest) -> JsonResponse:
    """
    Get failure rate per product: (FAILED / (SUCCESS + FAILED)) × 100.
    
    Endpoint: GET /analytics/failure-rates
    
    Calculates the failure rate for each product, excluding PENDING transactions.
    Results are sorted by failure rate in descending order.
    Percentages are rounded to 1 decimal place.
    
    Args:
        request: HTTP request object (unused but required by Django)
    
    Returns:
        JsonResponse with list of products and their failure rates,
        sorted by rate descending
    """
    # Get counts of SUCCESS and FAILED per product (exclude PENDING)
    product_stats = (
        MerchantActivity.objects
        .filter(status__in=[STATUS_SUCCESS, STATUS_FAILED])
        .values('product')
        .annotate(
            success_count=Count('id', filter=Q(status=STATUS_SUCCESS)),
            failed_count=Count('id', filter=Q(status=STATUS_FAILED))
        )
    )
    
    # Calculate failure rates
    result: List[Dict[str, Any]] = []
    for item in product_stats:
        success: int = item['success_count']
        failed: int = item['failed_count']
        total: int = success + failed
        
        if total > 0:
            failure_rate: float = (failed / total) * 100
            # Round to 1 decimal place per requirements
            failure_rate = round(failure_rate, DECIMAL_PLACES_PERCENTAGE)
            
            result.append({
                "product": item['product'],
                "failure_rate": failure_rate
            })
    
    # Sort by failure rate descending
    result.sort(key=lambda x: x['failure_rate'], reverse=True)
    
    return JsonResponse(result, safe=False)
