"""
Management command to load merchant activity data from CSV files.

This command reads CSV files from the data directory and imports them into
the PostgreSQL database. It handles malformed data gracefully and uses
bulk operations for performance.
"""
import csv
import os
from datetime import datetime
from typing import List, Optional, Tuple
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from analytics.models import MerchantActivity
from analytics.constants import BATCH_SIZE


class Command(BaseCommand):
    """
    Management command to load merchant activities from CSV files.
    
    Usage:
        python manage.py loads [--data-dir=<path>]
    
    The command will:
    1. Scan the specified data directory for CSV files
    2. Parse each CSV file and validate data
    3. Import data in batches for performance
    4. Handle malformed rows gracefully (skip with warning)
    """
    help = "Load merchant activities from CSV files into the database"

    def add_arguments(self, parser):
        """
        Add command-line arguments.
        
        Args:
            parser: ArgumentParser instance
        """
        parser.add_argument(
            '--data-dir',
            type=str,
            default='candidate_package/candidate_package/data/sample_data',
            help='Directory containing CSV files (default: candidate_package/candidate_package/data/sample_data)'
        )

    def handle(self, *args, **options) -> None:
        """
        Main command handler.
        
        Args:
            *args: Positional arguments
            **options: Keyword arguments from command line
        """
        data_dir: str = options['data_dir']
        batch_size: int = BATCH_SIZE
        
        # Validate data directory exists
        if not os.path.isdir(data_dir):
            raise CommandError(f"Data directory does not exist: {data_dir}")
        
        self.stdout.write(self.style.SUCCESS(f'Loading data from: {data_dir}'))
        
        # Get all CSV files in the directory
        csv_files: List[str] = [
            f for f in os.listdir(data_dir)
            if f.endswith('.csv') and f.startswith('activities_')
        ]
        
        if not csv_files:
            raise CommandError(f"No CSV files found in {data_dir}")
        
        total_imported: int = 0
        total_skipped: int = 0
        
        # Process each CSV file
        for filename in sorted(csv_files):
            filepath: str = os.path.join(data_dir, filename)
            imported, skipped = self._process_file(filepath, batch_size)
            total_imported += imported
            total_skipped += skipped
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded {filename}: {imported} records, {skipped} skipped'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nTotal: {total_imported} records imported, {total_skipped} records skipped'
            )
        )

    def _process_file(
        self,
        filepath: str,
        batch_size: int
    ) -> Tuple[int, int]:
        """
        Process a single CSV file and import its data.
        
        Args:
            filepath: Path to the CSV file
            batch_size: Number of records to batch before inserting
        
        Returns:
            Tuple of (imported_count, skipped_count)
        """
        activities_to_create: List[MerchantActivity] = []
        imported_count: int = 0
        skipped_count: int = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        activity = self._parse_row(row)
                        if activity:
                            activities_to_create.append(activity)
                            
                            # Bulk insert when batch size is reached
                            if len(activities_to_create) >= batch_size:
                                with transaction.atomic():
                                    MerchantActivity.objects.bulk_create(
                                        activities_to_create,
                                        ignore_conflicts=True
                                    )
                                imported_count += len(activities_to_create)
                                activities_to_create = []
                        else:
                            skipped_count += 1
                    except Exception as e:
                        # Log error but continue processing
                        self.stdout.write(
                            self.style.WARNING(
                                f'Error processing row {row_num} in {os.path.basename(filepath)}: {str(e)}'
                            )
                        )
                        skipped_count += 1
                        continue
            
            # Insert remaining records
            if activities_to_create:
                with transaction.atomic():
                    MerchantActivity.objects.bulk_create(
                        activities_to_create,
                        ignore_conflicts=True
                    )
                imported_count += len(activities_to_create)
        
        except FileNotFoundError:
            raise CommandError(f"File not found: {filepath}")
        except Exception as e:
            raise CommandError(f"Error processing file {filepath}: {str(e)}")
        
        return imported_count, skipped_count

    def _parse_row(self, row: dict[str, str]) -> Optional[MerchantActivity]:
        """
        Parse a CSV row into a MerchantActivity instance.
        
        Handles data cleaning and validation:
        - Strips whitespace and normalizes case
        - Handles empty timestamps (uses current time as fallback)
        - Validates required fields
        - Converts data types appropriately
        
        Args:
            row: Dictionary representing a CSV row
        
        Returns:
            MerchantActivity instance or None if row is invalid
        """
        try:
            # Clean and validate product
            clean_product: str = str(row.get('product', '')).strip().upper()
            if not clean_product:
                return None
            
            # Clean and validate event_type (should be uppercase)
            clean_event_type: str = str(row.get('event_type', '')).strip().upper()
            if not clean_event_type:
                return None
            
            # Clean and validate status
            clean_status: str = str(row.get('status', '')).strip().upper()
            if not clean_status:
                return None
            
            # Parse event_timestamp (handle empty values)
            event_timestamp_str: str = str(row.get('event_timestamp', '')).strip()
            if event_timestamp_str:
                event_timestamp: Optional[datetime] = parse_datetime(event_timestamp_str)
                if event_timestamp is None:
                    # Try alternative parsing
                    try:
                        event_timestamp = datetime.fromisoformat(event_timestamp_str.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        event_timestamp = datetime.now()
            else:
                # Use current time if timestamp is missing
                event_timestamp = datetime.now()
            
            # Parse amount
            try:
                amount: float = float(row.get('amount', 0))
            except (ValueError, TypeError):
                amount = 0.0
            
            # Validate required fields
            event_id: str = str(row.get('event_id', '')).strip()
            merchant_id: str = str(row.get('merchant_id', '')).strip()
            
            if not event_id or not merchant_id:
                return None
            
            # Create MerchantActivity instance
            return MerchantActivity(
                event_id=event_id,
                merchant_id=merchant_id,
                event_timestamp=event_timestamp,
                product=clean_product,
                event_type=clean_event_type,
                amount=amount,
                status=clean_status,
                channel=str(row.get('channel', '')).strip(),
                region=str(row.get('region', '')).strip(),
                merchant_tier=str(row.get('merchant_tier', '')).strip()
            )
        
        except Exception as e:
            # Return None for any parsing errors
            return None