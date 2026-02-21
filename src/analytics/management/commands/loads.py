"""
Django management command to load merchant activities from CSV files.

This command reads CSV files containing merchant activity data and imports them
into the database. It handles malformed data gracefully and processes data in
batches for optimal performance.
"""

import csv
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from analytics.models import MerchantActivity
from analytics.constants import BATCH_SIZE


class Command(BaseCommand):
    """
    Management command to import merchant activities from CSV files.
    
    This command:
    - Reads CSV files from a specified directory
    - Validates and cleans data
    - Handles malformed rows gracefully
    - Imports data in batches for performance
    - Provides progress feedback
    - Wraps entire import in a transaction for atomicity (all-or-nothing)
    """
    
    help: str = 'Load merchant activities from CSV files in the specified directory'
    
    def add_arguments(self, parser: Any) -> None:
        """
        Add command-line arguments to the parser.
        
        Args:
            parser: ArgumentParser instance to add arguments to
        """
        parser.add_argument(
            '--data-dir',
            type=str,
            default=None,
            help='Directory containing CSV files (default: ../data relative to manage.py, or data/ in project root)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=BATCH_SIZE,
            help=f'Batch size for bulk inserts (default: {BATCH_SIZE})'
        )
    
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Main command handler that processes CSV files and imports data.
        
        Args:
            *args: Variable length argument list
            **options: Command options including data_dir and batch_size
        
        Raises:
            CommandError: If the data directory doesn't exist or is invalid
        """
        batch_size: int = options['batch_size']
        
        # Determine data directory path
        # If not specified, try common locations relative to manage.py
        if options['data_dir']:
            data_dir: str = options['data_dir']
        else:
            # Try ../data (parent directory of src/)
            base_dir: Path = Path(settings.BASE_DIR)
            # BASE_DIR is src/, so parent is project root
            default_path: Path = base_dir.parent / 'data'
            if default_path.exists():
                data_dir = str(default_path)
            else:
                # Fallback to ./data in current directory
                data_dir = './data'
        
        # Validate data directory
        data_path: Path = Path(data_dir).resolve()
        if not data_path.exists():
            raise CommandError(
                f'Data directory does not exist: {data_dir}\n'
                f'Please specify the correct path using --data-dir option.\n'
                f'Example: python manage.py loads --data-dir=../data'
            )
        
        if not data_path.is_dir():
            raise CommandError(f'Path is not a directory: {data_dir}')
        
        self.stdout.write(self.style.SUCCESS(f'Starting import from: {data_dir}'))
        
        # Get all CSV files
        csv_files: List[Path] = sorted([f for f in data_path.iterdir() if f.suffix == '.csv'])
        
        if not csv_files:
            self.stdout.write(self.style.WARNING(f'No CSV files found in {data_dir}'))
            return
        
        self.stdout.write(f'Found {len(csv_files)} CSV file(s) to process')
        
        # Wrap entire import process in a transaction
        # If any file fails, all changes will be rolled back
        try:
            with transaction.atomic():
                total_imported: int = 0
                total_skipped: int = 0
                
                # Process each CSV file
                for csv_file in csv_files:
                    imported, skipped = self._process_csv_file(csv_file, batch_size)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Loading {csv_file.name}"
                        )
                    )
                    total_imported += imported
                    total_skipped += skipped
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully loaded {csv_file.name}: {imported} records imported, {skipped} skipped'
                        )
                    )
                
                # Summary
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nImport complete! Total: {total_imported} imported, {total_skipped} skipped'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\nImport failed! All changes have been rolled back. Error: {str(e)}'
                )
            )
            raise CommandError(f'Import process failed: {str(e)}') from e
    
    def _process_csv_file(self, filepath: Path, batch_size: int) -> tuple[int, int]:
        """
        Process a single CSV file and import its data.
        
        This method is called within a transaction.atomic() context, so any
        exception raised here will cause the entire import to roll back.
        
        Args:
            filepath: Path to the CSV file to process
            batch_size: Number of records to insert per batch
        
        Returns:
            Tuple of (imported_count, skipped_count)
        
        Raises:
            CommandError: If the file cannot be processed or has invalid structure
        """
        activities_to_create: List[MerchantActivity] = []
        imported_count: int = 0
        skipped_count: int = 0
        
        with open(filepath, 'r', encoding='utf-8') as file:
            reader: csv.DictReader = csv.DictReader(file)
            
            # Validate required columns manually, another way to do this would be to call the models directly
            required_columns: List[str] = [
                'event_id', 'merchant_id', 'event_timestamp', 'product',
                'event_type', 'amount', 'status', 'channel', 'region', 'merchant_tier'
            ]
            
            fieldnames: Optional[List[str]] = list(reader.fieldnames) if reader.fieldnames else None
            if not fieldnames or not all(col in fieldnames for col in required_columns):
                missing: List[str] = [col for col in required_columns if col not in (fieldnames or [])]
                error_msg: str = f'Missing required columns in {filepath.name}: {missing}'
                self.stdout.write(self.style.ERROR(error_msg))
                raise CommandError(error_msg)
            
            # Process each row
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                try:
                    activity: Optional[MerchantActivity] = self._create_activity_from_row(row)
                    
                    if activity:
                        activities_to_create.append(activity)
                        
                        # Insert in batches for performance
                        # Note: These are nested within the outer transaction.atomic()
                        if len(activities_to_create) >= batch_size:
                            MerchantActivity.objects.bulk_create(
                                activities_to_create,
                                ignore_conflicts=True
                            )
                            imported_count += len(activities_to_create)
                            activities_to_create = []
                    else:
                        skipped_count += 1
                
                except Exception as e:
                    # Log malformed row but continue processing
                    skipped_count += 1
                    if row_num <= 10:  # Only log first 10 errors to avoid spam
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping malformed row {row_num} in {filepath.name}: {str(e)}'
                            )
                        )
            
            # Insert remaining records
            if activities_to_create:
                MerchantActivity.objects.bulk_create(
                    activities_to_create,
                    ignore_conflicts=True
                )
                imported_count += len(activities_to_create)
        
        return imported_count, skipped_count
    
    def _create_activity_from_row(self, row: Dict[str, str]) -> Optional[MerchantActivity]:
        """
        Create a MerchantActivity instance from a CSV row.
        
        Validates and cleans data from the CSV row, handling malformed values gracefully.
        
        Args:
            row: Dictionary representing a CSV row
        
        Returns:
            MerchantActivity instance if valid, None if row should be skipped
        """
        try:
            # Parse and validate event_id (UUID)
            event_id: str = row['event_id'].strip()
            if not event_id:
                return None
            
            # Parse and validate merchant_id
            merchant_id: str = row['merchant_id'].strip()
            if not merchant_id:
                return None
            
            # Parse event_timestamp (may be empty)
            event_timestamp: Optional[datetime] = None
            timestamp_str: str = row['event_timestamp'].strip()
            if timestamp_str:
                parsed_dt = parse_datetime(timestamp_str)
                if parsed_dt:
                    # Make timezone-aware if it's naive (required when USE_TZ=True)
                    if timezone.is_naive(parsed_dt):
                        event_timestamp = timezone.make_aware(parsed_dt)
                    else:
                        event_timestamp = parsed_dt
                # If parsing fails, event_timestamp remains None (field allows null)
            
            # Clean and validate product
            clean_product: str = str(row['product']).strip().upper()
            if not clean_product:
                return None
            
            # Clean event_type
            clean_event_type: str = str(row['event_type']).strip().upper()
            if not clean_event_type:
                return None
            
            # Parse amount (handle empty or invalid values)
            try:
                amount: Decimal = Decimal(str(row['amount']).strip() or '0.00')
                if amount < 0:
                    amount = Decimal('0.00')
            except (ValueError, TypeError):
                amount = Decimal('0.00')
            
            # Clean and validate status
            clean_status: str = str(row['status']).strip().upper()
            if not clean_status:
                return None
            
            # Clean channel
            channel: str = str(row['channel']).strip()
            if not channel:
                channel = 'UNKNOWN'
            
            # Clean region
            region: str = str(row['region']).strip()
            if not region:
                region = 'UNKNOWN'
            
            # Clean merchant_tier
            merchant_tier: str = str(row['merchant_tier']).strip()
            if not merchant_tier:
                merchant_tier = 'STARTER'
            
            # Create and return the activity instance
            return MerchantActivity(
                event_id=event_id,
                merchant_id=merchant_id,
                event_timestamp=event_timestamp,
                product=clean_product,
                event_type=clean_event_type,
                amount=amount,
                status=clean_status,
                channel=channel,
                region=region,
                merchant_tier=merchant_tier
            )
        
        except Exception:
            # Return None for any unhandled errors
            return None
