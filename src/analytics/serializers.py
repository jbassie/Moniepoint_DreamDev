"""
Django REST Framework serializers for Analytics API.

This module defines strict serializers for all API response types,
ensuring consistent and validated output formats.
"""

from rest_framework import serializers
from typing import Dict, List, Any
from decimal import Decimal


class TopMerchantSerializer(serializers.Serializer):
    """
    Serializer for top merchant endpoint response.
    
    Fields:
        merchant_id: Merchant identifier (required, string)
        total_volume: Total transaction volume (required, decimal with 2 decimal places)
    """
    merchant_id = serializers.CharField(required=True, max_length=50)
    total_volume = serializers.DecimalField(
        required=True,
        max_digits=15,
        decimal_places=2,
        coerce_to_string=False
    )


class MonthlyActiveMerchantsSerializer(serializers.Serializer):
    """
    Serializer for monthly active merchants endpoint response.
    
    Returns a dictionary with month-year keys and merchant counts as values.
    """
    def to_representation(self, instance: Dict[str, int]) -> Dict[str, int]:
        """
        Convert the monthly data dictionary to the response format.
        
        Args:
            instance: Dictionary with month-year keys and merchant counts
            
        Returns:
            Dictionary with validated month-year keys and integer counts
        """
        result: Dict[str, int] = {}
        for month_key, count in instance.items():
            # Validate month format (YYYY-MM)
            if isinstance(month_key, str) and len(month_key) == 7:
                result[month_key] = int(count) if isinstance(count, (int, float, Decimal)) else 0
        return result


class ProductAdoptionSerializer(serializers.Serializer):
    """
    Serializer for product adoption endpoint response.
    
    Returns a dictionary with product names as keys and merchant counts as values.
    """
    def to_representation(self, instance: Dict[str, int]) -> Dict[str, int]:
        """
        Convert the product adoption data dictionary to the response format.
        
        Args:
            instance: Dictionary with product names and merchant counts
            
        Returns:
            Dictionary with validated product names and integer counts
        """
        result: Dict[str, int] = {}
        for product, count in instance.items():
            if isinstance(product, str):
                result[product] = int(count) if isinstance(count, (int, float, Decimal)) else 0
        return result


class KYCFunnelSerializer(serializers.Serializer):
    """
    Serializer for KYC funnel endpoint response.
    
    Fields:
        documents_submitted: Number of merchants who submitted documents (required, integer)
        verifications_completed: Number of merchants who completed verification (required, integer)
        tier_upgrades: Number of merchants who upgraded tier (required, integer)
    """
    documents_submitted = serializers.IntegerField(required=True, min_value=0)
    verifications_completed = serializers.IntegerField(required=True, min_value=0)
    tier_upgrades = serializers.IntegerField(required=True, min_value=0)


class FailureRateItemSerializer(serializers.Serializer):
    """
    Serializer for a single failure rate item in the failure rates list.
    
    Fields:
        product: Product name (required, string)
        failure_rate: Failure rate percentage (required, decimal with 1 decimal place)
    """
    product = serializers.CharField(required=True, max_length=50)
    failure_rate = serializers.DecimalField(
        required=True,
        max_digits=5,
        decimal_places=1,
        min_value=Decimal('0'),
        max_value=Decimal("100"), #
        coerce_to_string=False
    )


class FailureRatesSerializer(serializers.Serializer):
    """
    Serializer for failure rates endpoint response.
    
    Returns a list of failure rate items.
    """
    def to_representation(self, instance: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert the failure rates list to the response format.
        
        Args:
            instance: List of dictionaries with product and failure_rate
            
        Returns:
            List of validated failure rate dictionaries
        """
        serializer = FailureRateItemSerializer(many=True)
        return serializer.to_representation(instance)

