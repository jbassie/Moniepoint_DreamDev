"""
API views for analytics endpoints.

This module provides REST API endpoints for analyzing merchant activity data
across all Moniepoint products.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal

from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncMonth
from django.http import HttpRequest
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from analytics.models import MerchantActivity, ProductTypes, EventTypes, StatusTypes


@api_view(["GET"])
def top_merchant(request: HttpRequest) -> Response:
    """
    Get the merchant with the highest total successful transaction amount.
    
    This endpoint aggregates all successful transactions across all products
    for each merchant and returns the merchant with the highest total volume.
    
    Returns:
        Response with JSON containing:
        - merchant_id: Merchant identifier
        - total_volume: Total transaction amount (2 decimal places)
    
    Example response:
        {
            "merchant_id": "MRC-001234",
            "total_volume": 98765432.10
        }
    """
    try:
        # Aggregate successful transactions by merchant
        top_merchant_data = (
            MerchantActivity.objects
            .filter(status=StatusTypes.SUCCESS)
            .values('merchant_id')
            .annotate(total_volume=Sum('amount'))
            .order_by('-total_volume')
            .first()
        )
        
        if not top_merchant_data:
            return Response(
                {"merchant_id": None, "total_volume": 0.00},
                status=status.HTTP_200_OK
            )
        
        # Format response with 2 decimal places
        return Response({
            "merchant_id": top_merchant_data['merchant_id'],
            "total_volume": float(round(Decimal(str(top_merchant_data['total_volume'])), 2))
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def monthly_active_merchants(request: HttpRequest) -> Response:
    """
    Get the count of unique merchants with at least one successful event per month.
    
    This endpoint groups merchants by month and counts unique merchants
    who had at least one successful transaction in that month.
    
    Returns:
        Response with JSON containing monthly counts:
        {
            "2024-01": 8234,
            "2024-02": 8456,
            ...
        }
    
    Example response:
        {
            "2024-01": 8234,
            "2024-02": 8456,
            "2024-03": 8621
        }
    """
    try:
        # Group by month and count distinct merchants with successful events
        monthly_counts = (
            MerchantActivity.objects
            .filter(status=StatusTypes.SUCCESS)
            .annotate(month=TruncMonth('event_timestamp'))
            .values('month')
            .annotate(merchant_count=Count('merchant_id', distinct=True))
            .order_by('month')
        )
        
        # Format response as dictionary with YYYY-MM keys
        result: Dict[str, int] = {}
        for item in monthly_counts:
            month_str: str = item['month'].strftime('%Y-%m')
            result[month_str] = item['merchant_count']
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def product_adoption(request: HttpRequest) -> Response:
    """
    Get unique merchant count per product, sorted by count (highest first).
    
    This endpoint counts how many unique merchants have used each product,
    regardless of transaction status. Results are sorted by count in descending order.
    
    Returns:
        Response with JSON containing product adoption counts:
        {
            "POS": 15234,
            "AIRTIME": 12456,
            "BILLS": 10234,
            ...
        }
    
    Example response:
        {
            "POS": 15234,
            "AIRTIME": 12456,
            "BILLS": 10234,
            "CARD_PAYMENT": 8934,
            "SAVINGS": 7821,
            "MONIEBOOK": 6543,
            "KYC": 5432
        }
    """
    try:
        # Count distinct merchants per product
        product_counts = (
            MerchantActivity.objects
            .values('product')
            .annotate(merchant_count=Count('merchant_id', distinct=True))
            .order_by('-merchant_count')
        )
        
        # Format response as dictionary
        result: Dict[str, int] = {}
        for item in product_counts:
            result[item['product']] = item['merchant_count']
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def kyc_funnel(request: HttpRequest) -> Response:
    """
    Get the KYC conversion funnel metrics.
    
    This endpoint tracks unique merchants at each stage of the KYC process:
    1. Documents submitted (DOCUMENT_SUBMITTED events)
    2. Verifications completed (VERIFICATION_COMPLETED events)
    3. Tier upgrades (TIER_UPGRADE events)
    
    Only successful events are counted.
    
    Returns:
        Response with JSON containing funnel metrics:
        {
            "documents_submitted": 5432,
            "verifications_completed": 4521,
            "tier_upgrades": 3890
        }
    
    Example response:
        {
            "documents_submitted": 5432,
            "verifications_completed": 4521,
            "tier_upgrades": 3890
        }
    """
    try:
        # Filter for KYC product and successful events only
        kyc_activities = MerchantActivity.objects.filter(
            product=ProductTypes.KYC,
            status=StatusTypes.SUCCESS
        )
        
        # Count distinct merchants at each stage
        documents_submitted: int = (
            kyc_activities
            .filter(event_type=EventTypes.DOCUMENT_SUBMITTED)
            .values('merchant_id')
            .distinct()
            .count()
        )
        
        verifications_completed: int = (
            kyc_activities
            .filter(event_type=EventTypes.VERIFICATION_COMPLETED)
            .values('merchant_id')
            .distinct()
            .count()
        )
        
        tier_upgrades: int = (
            kyc_activities
            .filter(event_type=EventTypes.TIER_UPGRADE)
            .values('merchant_id')
            .distinct()
            .count()
        )
        
        return Response({
            "documents_submitted": documents_submitted,
            "verifications_completed": verifications_completed,
            "tier_upgrades": tier_upgrades
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def failure_rates(request: HttpRequest) -> Response:
    """
    Get failure rate per product.
    
    Calculates failure rate as: (FAILED / (SUCCESS + FAILED)) × 100
    PENDING transactions are excluded from the calculation.
    Results are sorted by failure rate in descending order.
    
    Returns:
        Response with JSON array containing failure rates:
        [
            {"product": "BILLS", "failure_rate": 5.2},
            {"product": "AIRTIME", "failure_rate": 4.1},
            ...
        ]
    
    Example response:
        [
            {"product": "BILLS", "failure_rate": 5.2},
            {"product": "AIRTIME", "failure_rate": 4.1},
            {"product": "POS", "failure_rate": 3.5},
            {"product": "CARD_PAYMENT", "failure_rate": 2.8},
            {"product": "SAVINGS", "failure_rate": 1.2},
            {"product": "MONIEBOOK", "failure_rate": 0.5},
            {"product": "KYC", "failure_rate": 0.3}
        ]
    """
    try:
        # Filter out PENDING status
        relevant_activities = MerchantActivity.objects.exclude(
            status=StatusTypes.PENDING
        )
        
        # Calculate failure rates per product
        product_stats = (
            relevant_activities
            .values('product')
            .annotate(
                total=Count('id'),
                failed=Count('id', filter=Q(status=StatusTypes.FAILED)),
                success=Count('id', filter=Q(status=StatusTypes.SUCCESS))
            )
        )
        
        # Calculate failure rate for each product
        result: List[Dict[str, Any]] = []
        for stat in product_stats:
            total: int = stat['total']
            failed: int = stat['failed']
            
            if total > 0:
                # Calculate failure rate: (FAILED / (SUCCESS + FAILED)) × 100
                failure_rate: float = (failed / total) * 100
                result.append({
                    "product": stat['product'],
                    "failure_rate": round(failure_rate, 1)  # 1 decimal place
                })
        
        # Sort by failure rate descending
        result.sort(key=lambda x: x['failure_rate'], reverse=True)
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

