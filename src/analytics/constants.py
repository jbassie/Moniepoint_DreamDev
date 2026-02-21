"""
Constants used throughout the analytics application.
"""
from typing import Final

# Batch size for bulk database operations
# Larger batches improve performance but consume more memory
BATCH_SIZE: Final[int] = 5000