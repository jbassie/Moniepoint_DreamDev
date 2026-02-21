"""
Django models for the Analytics API.

This module defines the database models used to store merchant activity data.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class MerchantActivity(models.Model):
    """
    Model representing a merchant activity event.
    
    Stores all merchant activities across different products including POS transactions,
    airtime purchases, bill payments, card payments, savings, MonieBook operations, and KYC events.
    
    Attributes:
        event_id: Unique identifier for the event (UUID)
        merchant_id: Merchant identifier in format MRC-XXXXXX
        event_timestamp: When the event occurred (ISO 8601 format)
        product: Product category (POS, AIRTIME, BILLS, CARD_PAYMENT, SAVINGS, MONIEBOOK, KYC)
        event_type: Type of activity specific to the product
        amount: Transaction amount in NGN (0 for non-monetary events)
        status: Event status (SUCCESS, FAILED, PENDING)
        channel: Channel through which event occurred (POS, APP, USSD, WEB, OFFLINE)
        region: Merchant's operating region
        merchant_tier: KYC tier (STARTER, VERIFIED, PREMIUM)
    """
    
    event_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the event"
    )
    
    merchant_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Merchant identifier in format MRC-XXXXXX"
    )
    
    event_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the event occurred (ISO 8601 format)"
    )
    
    product = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Product category: POS, AIRTIME, BILLS, CARD_PAYMENT, SAVINGS, MONIEBOOK, KYC"
    )
    
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Type of activity specific to the product"
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Transaction amount in NGN (0 for non-monetary events)"
    )
    
    status = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Event status: SUCCESS, FAILED, PENDING"
    )
    
    channel = models.CharField(
        max_length=20,
        help_text="Channel: POS, APP, USSD, WEB, OFFLINE"
    )
    
    region = models.CharField(
        max_length=100,
        help_text="Merchant's operating region"
    )
    
    merchant_tier = models.CharField(
        max_length=20,
        help_text="KYC tier: STARTER, VERIFIED, PREMIUM"
    )
    
    class Meta:
        """Meta configuration for the MerchantActivity model."""
        
        db_table = 'merchant_activities'
        indexes = [
            models.Index(fields=['merchant_id', 'status']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['event_timestamp', 'status']),
            models.Index(fields=['product', 'event_type']),
        ]
        ordering = ['-event_timestamp']
    
   

