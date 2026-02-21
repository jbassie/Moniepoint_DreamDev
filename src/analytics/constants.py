"""
Constants used throughout the Analytics API.

This module contains application-wide constants including batch sizes,
data validation values, and configuration parameters.
"""

from typing import Final

# Batch processing configuration
BATCH_SIZE: Final[int] = 5000
"""Batch size for bulk database operations to optimize performance."""

# Product types
PRODUCTS: Final[list[str]] = [
    'POS',
    'AIRTIME',
    'BILLS',
    'CARD_PAYMENT',
    'SAVINGS',
    'MONIEBOOK',
    'KYC'
]
"""List of valid product categories."""

# Status values
STATUS_SUCCESS: Final[str] = 'SUCCESS'
STATUS_FAILED: Final[str] = 'FAILED'
STATUS_PENDING: Final[str] = 'PENDING'

STATUSES: Final[list[str]] = [
    STATUS_SUCCESS,
    STATUS_FAILED,
    STATUS_PENDING
]
"""List of valid event statuses."""

# KYC Event types for funnel analysis
KYC_DOCUMENT_SUBMITTED: Final[str] = 'DOCUMENT_SUBMITTED'
KYC_VERIFICATION_COMPLETED: Final[str] = 'VERIFICATION_COMPLETED'
KYC_TIER_UPGRADE: Final[str] = 'TIER_UPGRADE'

# Merchant tiers
MERCHANT_TIERS: Final[list[str]] = [
    'STARTER',
    'VERIFIED',
    'PREMIUM'
]
"""List of valid merchant KYC tiers."""

# Channels
CHANNELS: Final[list[str]] = [
    'POS',
    'APP',
    'USSD',
    'WEB',
    'OFFLINE'
]
"""List of valid channels."""

# Decimal precision
DECIMAL_PLACES_AMOUNT: Final[int] = 2
"""Number of decimal places for monetary amounts."""
DECIMAL_PLACES_PERCENTAGE: Final[int] = 1
"""Number of decimal places for percentages."""
