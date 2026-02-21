"""
Tests for Analytics API views.

This module contains comprehensive tests for all analytics API endpoints,
including success cases, edge cases, and error handling.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from analytics.models import MerchantActivity
from analytics.constants import (
    STATUS_SUCCESS,
    STATUS_FAILED,
    STATUS_PENDING,
    KYC_DOCUMENT_SUBMITTED,
    KYC_VERIFICATION_COMPLETED,
    KYC_TIER_UPGRADE,
)


class TopMerchantViewTest(TestCase):
    """Test cases for TopMerchantView endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        self.client = APIClient()
        self.url = '/analytics/top-merchant'

    def test_top_merchant_with_data(self):
        """Test top merchant endpoint returns merchant with highest volume."""
        # Create test data
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('5000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='AIRTIME',
            event_type='PURCHASE',
            amount=Decimal('2000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Abuja',
            merchant_tier='STARTER',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['merchant_id'], 'MRC-001')
        self.assertEqual(Decimal(str(response.data['total_volume'])), Decimal('6000.00'))

    def test_top_merchant_excludes_failed_transactions(self):
        """Test that failed transactions are excluded from top merchant calculation."""
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('10000.00'),
            status=STATUS_FAILED,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('5000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['merchant_id'], 'MRC-002')
        self.assertEqual(Decimal(str(response.data['total_volume'])), Decimal('5000.00'))

    def test_top_merchant_excludes_pending_transactions(self):
        """Test that pending transactions are excluded from top merchant calculation."""
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('10000.00'),
            status=STATUS_PENDING,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('5000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['merchant_id'], 'MRC-002')
        self.assertEqual(Decimal(str(response.data['total_volume'])), Decimal('5000.00'))

    def test_top_merchant_no_data(self):
        """Test top merchant endpoint returns 204 when no data exists."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data['error'], 'No data found')

    def test_top_merchant_decimal_precision(self):
        """Test that total volume is rounded to 2 decimal places."""
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.123'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('2000.456'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be rounded to 2 decimal places
        total_volume = Decimal(str(response.data['total_volume']))
        self.assertEqual(total_volume.as_tuple().exponent, -2)


class MonthlyActiveMerchantsViewTest(TestCase):
    """Test cases for MonthlyActiveMerchantsView endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        self.client = APIClient()
        self.url = '/analytics/monthly-active-merchants'

    def test_monthly_active_merchants_with_data(self):
        """Test monthly active merchants endpoint returns correct counts."""
        now = timezone.now()
        jan_date = now.replace(month=1, day=15)
        feb_date = now.replace(month=2, day=15)

        # January data
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=jan_date
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('2000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=jan_date
        )
        # Same merchant in January (should count as 1)
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='AIRTIME',
            event_type='PURCHASE',
            amount=Decimal('500.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=jan_date
        )

        # February data
        MerchantActivity.objects.create(
            merchant_id='MRC-003',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('3000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=feb_date
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jan_key = jan_date.strftime('%Y-%m')
        feb_key = feb_date.strftime('%Y-%m')
        self.assertEqual(response.data[jan_key], 2)  # MRC-001 and MRC-002
        self.assertEqual(response.data[feb_key], 1)  # MRC-003

    def test_monthly_active_merchants_excludes_failed(self):
        """Test that failed transactions are excluded from monthly active merchants."""
        now = timezone.now()
        jan_date = now.replace(month=1, day=15)

        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_FAILED,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=jan_date
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('2000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=jan_date
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jan_key = jan_date.strftime('%Y-%m')
        self.assertEqual(response.data[jan_key], 1)  # Only MRC-002

    def test_monthly_active_merchants_excludes_null_timestamps(self):
        """Test that records with null timestamps are excluded."""
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=None
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_monthly_active_merchants_no_data(self):
        """Test monthly active merchants endpoint with no data."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_monthly_active_merchants_date_format(self):
        """Test that dates are formatted as YYYY-MM."""
        now = timezone.now()
        jan_date = now.replace(month=1, day=15)

        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=jan_date
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jan_key = jan_date.strftime('%Y-%m')
        self.assertIn(jan_key, response.data)
        # Verify format is YYYY-MM
        self.assertEqual(len(jan_key), 7)
        self.assertEqual(jan_key[4], '-')


class ProductAdoptionViewTest(TestCase):
    """Test cases for ProductAdoptionView endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        self.client = APIClient()
        self.url = '/analytics/product-adoption'

    def test_product_adoption_with_data(self):
        """Test product adoption endpoint returns correct counts."""
        # Create merchants for different products
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('2000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='AIRTIME',
            event_type='PURCHASE',
            amount=Decimal('500.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['POS'], 2)  # MRC-001 and MRC-002
        self.assertEqual(response.data['AIRTIME'], 1)  # MRC-001

    def test_product_adoption_includes_all_statuses(self):
        """Test that product adoption counts all events regardless of status."""
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('2000.00'),
            status=STATUS_FAILED,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-003',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('3000.00'),
            status=STATUS_PENDING,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['POS'], 3)  # All three merchants

    def test_product_adoption_sorted_by_count(self):
        """Test that products are sorted by count in descending order."""
        # Create data with different counts
        # POS: 3 merchants
        for i in range(1, 4):
            MerchantActivity.objects.create(
                merchant_id=f'MRC-00{i}',
                product='POS',
                event_type='TRANSACTION',
                amount=Decimal('1000.00'),
                status=STATUS_SUCCESS,
                channel='APP',
                region='Lagos',
                merchant_tier='VERIFIED',
                event_timestamp=timezone.now()
            )

        # AIRTIME: 2 merchants
        for i in range(1, 3):
            MerchantActivity.objects.create(
                merchant_id=f'MRC-00{i}',
                product='AIRTIME',
                event_type='PURCHASE',
                amount=Decimal('500.00'),
                status=STATUS_SUCCESS,
                channel='APP',
                region='Lagos',
                merchant_tier='VERIFIED',
                event_timestamp=timezone.now()
            )

        # BILLS: 1 merchant
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='BILLS',
            event_type='PAYMENT',
            amount=Decimal('2000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that POS comes first (highest count)
        products = list(response.data.keys())
        self.assertEqual(products[0], 'POS')
        self.assertEqual(response.data['POS'], 3)
        self.assertEqual(response.data['AIRTIME'], 2)
        self.assertEqual(response.data['BILLS'], 1)

    def test_product_adoption_no_data(self):
        """Test product adoption endpoint with no data."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class KYCFunnelViewTest(TestCase):
    """Test cases for KYCFunnelView endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        self.client = APIClient()
        self.url = '/analytics/kyc-funnel'

    def test_kyc_funnel_with_data(self):
        """Test KYC funnel endpoint returns correct counts for all stages."""
        # Documents submitted
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='KYC',
            event_type=KYC_DOCUMENT_SUBMITTED,
            amount=Decimal('0.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='STARTER',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='KYC',
            event_type=KYC_DOCUMENT_SUBMITTED,
            amount=Decimal('0.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='STARTER',
            event_timestamp=timezone.now()
        )

        # Verifications completed
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='KYC',
            event_type=KYC_VERIFICATION_COMPLETED,
            amount=Decimal('0.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        # Tier upgrades
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='KYC',
            event_type=KYC_TIER_UPGRADE,
            amount=Decimal('0.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='PREMIUM',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['documents_submitted'], 2)
        self.assertEqual(response.data['verifications_completed'], 1)
        self.assertEqual(response.data['tier_upgrades'], 1)

    def test_kyc_funnel_excludes_failed_events(self):
        """Test that failed KYC events are excluded from funnel counts."""
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='KYC',
            event_type=KYC_DOCUMENT_SUBMITTED,
            amount=Decimal('0.00'),
            status=STATUS_FAILED,
            channel='APP',
            region='Lagos',
            merchant_tier='STARTER',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='KYC',
            event_type=KYC_DOCUMENT_SUBMITTED,
            amount=Decimal('0.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='STARTER',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['documents_submitted'], 1)  # Only successful

    def test_kyc_funnel_counts_unique_merchants(self):
        """Test that KYC funnel counts unique merchants per stage."""
        # Same merchant submitting documents multiple times
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='KYC',
            event_type=KYC_DOCUMENT_SUBMITTED,
            amount=Decimal('0.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='STARTER',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='KYC',
            event_type=KYC_DOCUMENT_SUBMITTED,
            amount=Decimal('0.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='STARTER',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['documents_submitted'], 1)  # Unique count

    def test_kyc_funnel_no_data(self):
        """Test KYC funnel endpoint with no data."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['documents_submitted'], 0)
        self.assertEqual(response.data['verifications_completed'], 0)
        self.assertEqual(response.data['tier_upgrades'], 0)

    def test_kyc_funnel_only_kyc_product(self):
        """Test that only KYC product events are counted."""
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type=KYC_DOCUMENT_SUBMITTED,
            amount=Decimal('0.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='STARTER',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='KYC',
            event_type=KYC_DOCUMENT_SUBMITTED,
            amount=Decimal('0.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='STARTER',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['documents_submitted'], 1)  # Only KYC product


class FailureRatesViewTest(TestCase):
    """Test cases for FailureRatesView endpoint."""

    def setUp(self):
        """Set up test client and sample data."""
        self.client = APIClient()
        self.url = '/analytics/failure-rates'

    def test_failure_rates_with_data(self):
        """Test failure rates endpoint returns correct calculations."""
        # Product A: 2 success, 1 failed = 33.3% failure rate
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('2000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-003',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('3000.00'),
            status=STATUS_FAILED,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        # Product B: 1 success, 0 failed = 0% failure rate
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='AIRTIME',
            event_type='PURCHASE',
            amount=Decimal('500.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Find POS and AIRTIME in response
        pos_data = next(item for item in response.data if item['product'] == 'POS')
        airtime_data = next(item for item in response.data if item['product'] == 'AIRTIME')

        # POS: 1 failed / 3 total = 33.3%
        self.assertEqual(Decimal(str(pos_data['failure_rate'])), Decimal('33.3'))
        # AIRTIME: 0 failed / 1 total = 0%
        self.assertEqual(Decimal(str(airtime_data['failure_rate'])), Decimal('0.0'))

    def test_failure_rates_excludes_pending(self):
        """Test that pending transactions are excluded from failure rate calculation."""
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('2000.00'),
            status=STATUS_FAILED,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-003',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('3000.00'),
            status=STATUS_PENDING,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pos_data = next(item for item in response.data if item['product'] == 'POS')
        # Should be 1 failed / 2 total = 50.0% (pending excluded)
        self.assertEqual(Decimal(str(pos_data['failure_rate'])), Decimal('50.0'))

    def test_failure_rates_sorted_by_rate(self):
        """Test that failure rates are sorted in descending order."""
        # Product A: 50% failure rate
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('2000.00'),
            status=STATUS_FAILED,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        # Product B: 33.3% failure rate
        MerchantActivity.objects.create(
            merchant_id='MRC-003',
            product='AIRTIME',
            event_type='PURCHASE',
            amount=Decimal('500.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-004',
            product='AIRTIME',
            event_type='PURCHASE',
            amount=Decimal('600.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-005',
            product='AIRTIME',
            event_type='PURCHASE',
            amount=Decimal('700.00'),
            status=STATUS_FAILED,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # First item should be POS (50.0%)
        self.assertEqual(response.data[0]['product'], 'POS')
        self.assertEqual(Decimal(str(response.data[0]['failure_rate'])), Decimal('50.0'))
        # Second item should be AIRTIME (33.3%)
        self.assertEqual(response.data[1]['product'], 'AIRTIME')
        self.assertEqual(Decimal(str(response.data[1]['failure_rate'])), Decimal('33.3'))

    def test_failure_rates_decimal_precision(self):
        """Test that failure rates are rounded to 1 decimal place."""
        # Create scenario that results in 33.333...%
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-002',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('2000.00'),
            status=STATUS_SUCCESS,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )
        MerchantActivity.objects.create(
            merchant_id='MRC-003',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('3000.00'),
            status=STATUS_FAILED,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pos_data = next(item for item in response.data if item['product'] == 'POS')
        failure_rate = Decimal(str(pos_data['failure_rate']))
        # Should be rounded to 1 decimal place
        self.assertEqual(failure_rate.as_tuple().exponent, -1)
        self.assertEqual(failure_rate, Decimal('33.3'))

    def test_failure_rates_no_data(self):
        """Test failure rates endpoint with no data."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_failure_rates_excludes_zero_total(self):
        """Test that products with only pending transactions are excluded."""
        MerchantActivity.objects.create(
            merchant_id='MRC-001',
            product='POS',
            event_type='TRANSACTION',
            amount=Decimal('1000.00'),
            status=STATUS_PENDING,
            channel='APP',
            region='Lagos',
            merchant_tier='VERIFIED',
            event_timestamp=timezone.now()
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # POS should not be in results since it has no SUCCESS or FAILED transactions
        products = [item['product'] for item in response.data]
        self.assertNotIn('POS', products)

