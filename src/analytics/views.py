"""
API views for the Analytics endpoints using Django REST Framework.

This module contains all the view classes that handle the analytics API endpoints,
providing business insights from merchant activity data with strict serialization.
"""

import logging
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from typing import Dict, Any, List
from decimal import Decimal

from .models import MerchantActivity

# Configure logger for analytics views
logger = logging.getLogger(__name__)
from .serializers import (
    TopMerchantSerializer,
    MonthlyActiveMerchantsSerializer,
    ProductAdoptionSerializer,
    KYCFunnelSerializer,
    FailureRateItemSerializer,
)
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


class TopMerchantView(APIView):
    """
    Get the merchant with the highest total successful transaction amount.

    Endpoint: GET /analytics/top-merchant

    Returns the merchant with the highest total volume across all products,
    considering only successful transactions.
    """

    def get(self, request) -> Response:
        """
        Handle GET request for top merchant endpoint.

        Returns:
            Response with merchant_id and total_volume (rounded to 2 decimal places),
            or 404 if no data found
        """
        start_time = time.time()
        logger.info("TOPMERCHANTVIEW: REQUEST RECEIVED")
        
        try:
            top_merchant_data = (
                MerchantActivity.objects
                .filter(status=STATUS_SUCCESS)
                .values('merchant_id')
                .annotate(total_volume=Sum('amount'))
                .order_by('-total_volume')
                .first()
            )
            
            query_time = time.time() - start_time
            logger.debug(f"TopMerchantView: Query executed in {query_time:.3f}s")

            if top_merchant_data:
                # Format to 2 decimal places per requirements
                total_volume: Decimal = Decimal(str(top_merchant_data['total_volume'])).quantize(
                    Decimal('0.01')
                )

                serializer = TopMerchantSerializer({
                    "merchant_id": top_merchant_data['merchant_id'],
                    "total_volume": total_volume
                })
                
                total_time = time.time() - start_time
                logger.info(
                    f"TOPMERCHANTVIEW: SUCCESS | merchant_id={top_merchant_data['merchant_id']} | "
                    f"total_volume={total_volume} | response_time={total_time:.3f}s"
                )
                return Response(serializer.data, status=status.HTTP_200_OK)

            total_time = time.time() - start_time
            logger.warning(f"TopMerchantView: No data found | response_time={total_time:.3f}s")
            return Response(
                {"error": "No data found"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"TopMerchantView: Error occurred | {str(e)} | response_time={total_time:.3f}s",
                exc_info=True
            )
            return Response(
                {"error": "An error occurred while processing the request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MonthlyActiveMerchantsView(APIView):
    """
    Get the count of unique merchants with at least one successful event per month.

    Endpoint: GET /analytics/monthly-active-merchants

    Returns a dictionary with month-year as keys and unique merchant counts as values.
    Only includes merchants with at least one successful event in that month.
    """

    def get(self, request) -> Response:
        """
        Handle GET request for monthly active merchants endpoint.

        Returns:
            Response with monthly active merchant counts in format {"YYYY-MM": count}
        """
        start_time = time.time()
        logger.info("MONTHLYACTIVEMERCHANTSVIEW: REQUEST RECEIVED")
        
        try:
            monthly_data = (
                MerchantActivity.objects
                .filter(status=STATUS_SUCCESS)
                .exclude(event_timestamp__isnull=True)
                .annotate(month=TruncMonth('event_timestamp'))
                .values('month')
                .annotate(unique_merchants=Count('merchant_id', distinct=True))
                .order_by('month')
            )

            query_time = time.time() - start_time
            logger.debug(f"MonthlyActiveMerchantsView: Query executed in {query_time:.3f}s")

            # Format response as {"YYYY-MM": count}
            result: Dict[str, int] = {}
            for item in monthly_data:
                month_str: str = item['month'].strftime('%Y-%m')
                result[month_str] = item['unique_merchants']

            serializer = MonthlyActiveMerchantsSerializer(result)
            
            total_time = time.time() - start_time
            logger.info(
                f"MONTHLYACTIVEMERCHANTSVIEW: SUCCESS | {len(result)} months returned | "
                f"response_time={total_time:.3f}s"
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"MonthlyActiveMerchantsView: Error occurred | {str(e)} | response_time={total_time:.3f}s",
                exc_info=True
            )
            return Response(
                {"error": "An error occurred while processing the request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductAdoptionView(APIView):
    """
    Get unique merchant count per product, sorted by count (highest first).

    Endpoint: GET /analytics/product-adoption

    Returns the number of unique merchants that have used each product,
    sorted in descending order by adoption count.
    """

    def get(self, request) -> Response:
        """
        Handle GET request for product adoption endpoint.

        Returns:
            Response with product names as keys and unique merchant counts as values,
            sorted by count descending
        """
        start_time = time.time()
        logger.info("PRODUCTADOPTIONVIEW: REQUEST RECEIVED")
        
        try:
            product_data = (
                MerchantActivity.objects
                .values('product')
                .annotate(unique_merchants=Count('merchant_id', distinct=True))
                .order_by('-unique_merchants')
            )

            query_time = time.time() - start_time
            logger.debug(f"ProductAdoptionView: Query executed in {query_time:.3f}s")

            # Convert to dictionary format
            result: Dict[str, int] = {}
            for item in product_data:
                result[item['product']] = item['unique_merchants']

            serializer = ProductAdoptionSerializer(result)
            
            total_time = time.time() - start_time
            logger.info(
                f"PRODUCTADOPTIONVIEW: SUCCESS | {len(result)} products returned | "
                f"response_time={total_time:.3f}s"
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"ProductAdoptionView: Error occurred | {str(e)} | response_time={total_time:.3f}s",
                exc_info=True
            )
            return Response(
                {"error": "An error occurred while processing the request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KYCFunnelView(APIView):
    """
    Get the KYC conversion funnel metrics.


    Returns unique merchant counts at each stage of the KYC process:
    - documents_submitted: Merchants who submitted KYC documents
    - verifications_completed: Merchants who completed verification
    - tier_upgrades: Merchants who upgraded their tier

    Only counts successful KYC events.
    """

    def get(self, request) -> Response:
        """
        Handle GET request for KYC funnel endpoint.

        Returns:
            Response with KYC funnel metrics
        """
        start_time = time.time()
        logger.info("KYCFUNNELVIEW: REQUEST RECEIVED")
        
        try:
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

            query_time = time.time() - start_time
            logger.debug(f"KYCFunnelView: Queries executed in {query_time:.3f}s")

            serializer = KYCFunnelSerializer({
                "documents_submitted": documents_submitted,
                "verifications_completed": verifications_completed,
                "tier_upgrades": tier_upgrades
            })
            
            total_time = time.time() - start_time
            logger.info(
                f"KYCFUNNELVIEW: SUCCESS | documents_submitted={documents_submitted} | "
                f"verifications_completed={verifications_completed} | tier_upgrades={tier_upgrades} | "
                f"response_time={total_time:.3f}s"
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"KYCFunnelView: Error occurred | {str(e)} | response_time={total_time:.3f}s",
                exc_info=True
            )
            return Response(
                {"error": "An error occurred while processing the request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FailureRatesView(APIView):
    """
    Get failure rate per product: (FAILED / (SUCCESS + FAILED)) × 100.

    Endpoint: GET /analytics/failure-rates

    Calculates the failure rate for each product, excluding PENDING transactions.
    Results are sorted by failure rate in descending order.
    Percentages are rounded to 1 decimal place.
    """

    def get(self, request) -> Response:
        """
        Handle GET request for failure rates endpoint.

        Returns:
            Response with list of products and their failure rates,
            sorted by rate descending
        """
        start_time = time.time()
        logger.info("FAILURERATESVIEW: REQUEST RECEIVED")
        
        try:
            # Get counts of SUCCESS and FAILED per product (exclude PENDING)
            product_stats = (
                MerchantActivity.objects
                .filter(status__in=[STATUS_SUCCESS, STATUS_FAILED])
                .values('product')
                .annotate(
                    success_count=Count('event_id', filter=Q(status=STATUS_SUCCESS)),
                    failed_count=Count('event_id', filter=Q(status=STATUS_FAILED))
                )
            )

            query_time = time.time() - start_time
            logger.debug(f"FailureRatesView: Query executed in {query_time:.3f}s")

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
                        "failure_rate": Decimal(str(failure_rate)).quantize(Decimal('0.1'))
                    })

            # Sort by failure rate descending
            result.sort(key=lambda x: x['failure_rate'], reverse=True)

            serializer = FailureRateItemSerializer(result, many=True)
            
            total_time = time.time() - start_time
            logger.info(
                f"FAILURERATESVIEW: SUCCESS | {len(result)} products with failure rates calculated | "
                f"response_time={total_time:.3f}s"
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                f"FailureRatesView: Error occurred | {str(e)} | response_time={total_time:.3f}s",
                exc_info=True
            )
            return Response(
                {"error": "An error occurred while processing the request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
