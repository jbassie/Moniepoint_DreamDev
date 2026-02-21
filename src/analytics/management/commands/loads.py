import csv
import os


from django.core.management.base import BaseCommand
from analytics.models import MerchantActivity

class Command(BaseCommand):
    help = 'Load merchant activities from CSV'

    def handle(self, *args, **kwargs):
        data_dir = './data' # Point this to your unzipped data folder
        batch_size = 5000
        
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(data_dir, filename)
                activities_to_create = []
                
                with open(filepath, 'r') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        try:
                            # Aggressive data cleaning for malformed rows
                            clean_product = str(row['product']).strip().upper()
                            clean_event_type = str(row['event_type']).strip().upper()
                            clean_status = str(row['status']).strip().upper()

                            activities_to_create.append(MerchantActivity(
                                event_id=row['event_id'],
                                merchant_id=row['merchant_id'],
                                event_timestamp=row['event_timestamp'],
                                product=clean_product,           # Cleaned!
                                event_type=clean_event_type,     # Cleaned!
                                amount=float(row['amount']),
                                status=clean_status,             # Cleaned!
                                channel=row['channel'],
                                region=row['region'],
                                merchant_tier=row['merchant_tier']
                            ))
                        except Exception as e:
                            # Log it if you want, but skip the malformed row
                            continue
                        # Insert in batches for Performance evaluation
                        if len(activities_to_create) >= batch_size:
                            MerchantActivity.objects.bulk_create(activities_to_create, ignore_conflicts=True)
                            activities_to_create = []
                
                # Insert remaining
                if activities_to_create:
                    MerchantActivity.objects.bulk_create(activities_to_create, ignore_conflicts=True)
                
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {filename}'))