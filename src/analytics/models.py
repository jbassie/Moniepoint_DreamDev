"""
Django models for the Analytics API.

This module defines the data models for storing merchant activity data
from various Moniepoint products.
"""
from typing import Tuple
from django.db import models


class ProductTypes(models.TextChoices):
    """
    Enumeration of product types available in the Moniepoint ecosystem.
    
    Attributes:
        POS: POS terminal card transactions
        AIRTIME: Airtime vending for customers
        BILLS: Bill payments (electricity, cable TV, internet, etc.)
        CARD_PAYMENT: Merchant's own card payments to suppliers
        SAVINGS: Merchant savings account
        MONIEBOOK: Inventory and sales tracking
        KYC: Know Your Customer verification
    """
    POS: Tuple[str, str] = 'POS', 'POS'
    AIRTIME: Tuple[str, str] = 'AIRTIME', 'Airtime'
    BILLS: Tuple[str, str] = 'BILLS', 'Bills'
    CARD_PAYMENT: Tuple[str, str] = 'CARD_PAYMENT', 'Card Payment'
    SAVINGS: Tuple[str, str] = 'SAVINGS', 'Savings'
    MONIEBOOK: Tuple[str, str] = 'MONIEBOOK', 'Moniebook'
    KYC: Tuple[str, str] = 'KYC', 'KYC'


class EventTypes(models.TextChoices):
    """
    Enumeration of event types by product category.
    
    Each product has specific event types that can occur:
    - POS: Card transactions, cash withdrawals, transfers
    - AIRTIME: Airtime and data purchases
    - BILLS: Various bill payment types
    - CARD_PAYMENT: Supplier and invoice payments
    - SAVINGS: Deposits, withdrawals, interest credits, auto-save
    - MONIEBOOK: Sales, inventory updates, expense logging
    - KYC: Document submission, verification, tier upgrades
    """
    # POS events
    CARD_TRANSACTION: Tuple[str, str] = 'CARD_TRANSACTION', 'Card Transaction'
    CASH_WITHDRAWAL: Tuple[str, str] = 'CASH_WITHDRAWAL', 'Cash Withdrawal'
    TRANSFER: Tuple[str, str] = 'TRANSFER', 'Transfer'
    
    # AIRTIME events
    AIRTIME_PURCHASE: Tuple[str, str] = 'AIRTIME_PURCHASE', 'Airtime Purchase'
    DATA_PURCHASE: Tuple[str, str] = 'DATA_PURCHASE', 'Data Purchase'
    
    # BILLS events
    ELECTRICITY: Tuple[str, str] = 'ELECTRICITY', 'Electricity'
    CABLE_TV: Tuple[str, str] = 'CABLE_TV', 'Cable TV'
    INTERNET: Tuple[str, str] = 'INTERNET', 'Internet'
    WATER: Tuple[str, str] = 'WATER', 'Water'
    BETTING: Tuple[str, str] = 'BETTING', 'Betting'
    
    # CARD_PAYMENT events
    SUPPLIER_PAYMENT: Tuple[str, str] = 'SUPPLIER_PAYMENT', 'Supplier Payment'
    INVOICE_PAYMENT: Tuple[str, str] = 'INVOICE_PAYMENT', 'Invoice Payment'
    
    # SAVINGS events
    DEPOSIT: Tuple[str, str] = 'DEPOSIT', 'Deposit'
    WITHDRAWAL: Tuple[str, str] = 'WITHDRAWAL', 'Withdrawal'
    INTEREST_CREDIT: Tuple[str, str] = 'INTEREST_CREDIT', 'Interest Credit'
    AUTO_SAVE: Tuple[str, str] = 'AUTO_SAVE', 'Auto Save'
    
    # MONIEBOOK events
    SALE_RECORDED: Tuple[str, str] = 'SALE_RECORDED', 'Sale Recorded'
    INVENTORY_UPDATE: Tuple[str, str] = 'INVENTORY_UPDATE', 'Inventory Update'
    EXPENSE_LOGGED: Tuple[str, str] = 'EXPENSE_LOGGED', 'Expense Logged'
    
    # KYC events
    DOCUMENT_SUBMITTED: Tuple[str, str] = 'DOCUMENT_SUBMITTED', 'Document Submitted'
    VERIFICATION_COMPLETED: Tuple[str, str] = 'VERIFICATION_COMPLETED', 'Verification Completed'
    TIER_UPGRADE: Tuple[str, str] = 'TIER_UPGRADE', 'Tier Upgrade'


class StatusTypes(models.TextChoices):
    """
    Enumeration of transaction status types.
    
    Attributes:
        SUCCESS: Transaction completed successfully
        FAILED: Transaction failed
        PENDING: Transaction is pending completion
    """
    SUCCESS: Tuple[str, str] = 'SUCCESS', 'Success'
    FAILED: Tuple[str, str] = 'FAILED', 'Failed'
    PENDING: Tuple[str, str] = 'PENDING', 'Pending'


class MerchantActivity(models.Model):
    """
    Model representing a merchant activity event across all Moniepoint products.
    
    This model stores all merchant interactions including transactions,
    KYC events, and other activities. It serves as the primary data source
    for analytics endpoints.
    
    Attributes:
        event_id: Unique UUID identifier for the event
        merchant_id: Merchant identifier in format MRC-XXXXXX
        event_timestamp: ISO 8601 timestamp when the event occurred
        product: Product category (POS, AIRTIME, BILLS, etc.)
        event_type: Specific type of activity within the product
        amount: Transaction amount in NGN (0 for non-monetary events)
        status: Event status (SUCCESS, FAILED, PENDING)
        channel: Channel through which event occurred (POS, APP, USSD, WEB, OFFLINE)
        region: Merchant's operating region
        merchant_tier: KYC tier (STARTER, VERIFIED, PREMIUM)
    """
    event_id = models.UUIDField(
        primary_key=True,
        help_text="Unique identifier for the event"
    )
    merchant_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Merchant identifier in format MRC-XXXXXX"
    )
    event_timestamp = models.DateTimeField(
        db_index=True,
        help_text="ISO 8601 timestamp when the event occurred"
    )
    product = models.CharField(
        max_length=50,
        choices=ProductTypes.choices,
        db_index=True,
        help_text="Product category"
    )
    event_type = models.CharField(
        max_length=50,
        choices=EventTypes.choices,
        help_text="Type of activity within the product"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Transaction amount in NGN (0 for non-monetary events)"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusTypes.choices,
        db_index=True,
        help_text="Event status: SUCCESS, FAILED, or PENDING"
    )
    channel = models.CharField(
        max_length=20,
        help_text="Channel: POS, APP, USSD, WEB, or OFFLINE"
    )
    region = models.CharField(
        max_length=50,
        help_text="Merchant's operating region"
    )
    merchant_tier = models.CharField(
        max_length=20,
        help_text="KYC tier: STARTER, VERIFIED, or PREMIUM"
    )

    class Meta:
        """
        Meta configuration for the MerchantActivity model.
        
        Includes database indexes for commonly queried fields to improve
        query performance for analytics endpoints.
        """
        db_table = 'merchant_activity'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['product']),
            models.Index(fields=['event_timestamp']),
            models.Index(fields=['merchant_id']),
            models.Index(fields=['merchant_id', 'status']),  # Composite index for common queries
            models.Index(fields=['product', 'status']),  # Composite index for product analytics
        ]
        ordering = ['-event_timestamp']

    def __str__(self) -> str:
        """
        String representation of the MerchantActivity instance.
        
        Returns:
            Formatted string with merchant_id, product, and event_type
        """
        return f"{self.merchant_id} - {self.product} - {self.event_type}"