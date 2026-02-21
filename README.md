# Moniepoint DreamDev Hackathon 2025 - Analytics API

**Author:** Basssey John
**Date**: 21/02/2026

## Overview

This is a REST API built with Django that analyzes merchant activity data across all Moniepoint products. The API provides analytics endpoints to extract key business insights from merchant transaction logs.

## Assumptions

### Configuration & Infrastructure

1. **Database**: PostgreSQL is used as the database. The application expects a PostgreSQL database to be set up and configured via environment variables.

2. **Port**: The API runs on port 8080 as specified in the requirements.

3. **Time Zone**: All timestamps are stored and processed in UTC timezone.

4. **Server Resources**: Database connection settings are optimized for a 2GB RAM server (connection max age: 300 seconds, query timeout: 30 seconds).

### Data Format & Schema

5. **Merchant ID Format**: Assumes format `MRC-XXXXXX` (documented in models and comments).

6. **CSV File Location**: Defaults to `../data` relative to `src/` or `./data` in project root. Can also be in `candidate_package/candidate_package/data/sample_data/` directory by default, but can be specified via command-line argument.

7. **CSV Encoding**: Assumes UTF-8 encoding.

8. **Missing Data Handling**:
   - Empty `channel` → defaults to `'UNKNOWN'`
   - Empty `region` → defaults to `'UNKNOWN'`
   - Empty `merchant_tier` → defaults to `'STARTER'`
   - Empty `event_timestamp` → allowed to be `NULL`
   - Invalid amounts → default to `0.00`

9. **Batch Processing**: Batch size of 5000 records for bulk inserts.

### Business Logic

10. **Top Merchant**: Only considers transactions with `status='SUCCESS'` (excludes FAILED and PENDING).

11. **Monthly Active Merchants**:
    - Only counts merchants with `status='SUCCESS'`
    - Excludes records with `NULL` timestamps

12. **Product Adoption**: Counts all events regardless of status (not just successful ones).

13. **KYC Funnel**: Only counts events with `status='SUCCESS'` for each stage.

14. **Failure Rates**:
    - Excludes `PENDING` transactions from calculation
    - Formula: `(FAILED / (SUCCESS + FAILED)) × 100`
    - Products with zero transactions are excluded from results

### Data Import

15. **Transaction Atomicity**: Entire import is wrapped in a transaction (all-or-nothing).

16. **Error Handling**: Malformed CSV rows are skipped with warnings rather than failing the entire import process. First 10 errors are logged to avoid spam.

17. **Duplicate Handling**: Uses `ignore_conflicts=True` for bulk inserts (assumes `event_id` uniqueness).

18. **Data Validation**: Assumes CSV has exact column names matching model fields.

### Product & Domain

19. **Product Types**: Fixed list: `POS`, `AIRTIME`, `BILLS`, `CARD_PAYMENT`, `SAVINGS`, `MONIEBOOK`, `KYC`.

20. **Status Values**: Only three statuses: `SUCCESS`, `FAILED`, `PENDING`.

21. **Merchant Tiers**: Only three tiers: `STARTER`, `VERIFIED`, `PREMIUM`.

22. **Channels**: Fixed list: `POS`, `APP`, `USSD`, `WEB`, `OFFLINE`.

23. **KYC Event Types**: Specific mapping:
    - `DOCUMENT_SUBMITTED` → documents_submitted
    - `VERIFICATION_COMPLETED` → verifications_completed
    - `TIER_UPGRADE` → tier_upgrades

### Precision & Formatting

24. **Monetary Amounts**: 2 decimal places (NGN currency).

25. **Percentages**: 1 decimal place for failure rates.

26. **Date Formatting**: Monthly data formatted as `YYYY-MM` strings.

## Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 12 or higher
- **pip**: Python package manager

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/jbassie/Moniepoint_DreamDev
cd src
```

### 2. Create and Activate Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

1. Create a PostgreSQL database:
```sql
CREATE DATABASE moniepoint_db;
```

2. Create a `.env` file in the project root with your database credentials:
```env
SECRET_KEY=django-secret-key
DEBUG=True

# Database Configuration
# Update these values with your PostgreSQL credentials
LOCAL_DATABASE_NAME=database_name
LOCAL_DATABASE_USERNAM=database_username
LOCAL_DATABASE_PASSWORD=your_password_here
LOCAL_DATABASE_HOST=database_host
LOCAL_DATABASE_PORT=port


### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Import CSV Data

The CSV files should be located in `/data/` by default.(The root directory)

To import the data:
```bash
python manage.py loads
```
if the data is not in the data directory of the projects root directory please specify a custom data directory:
```bash
python manage.py loads --data-dir=path/to/your/data
```

The import process will:
- Read all CSV files matching the pattern `activities_*.csv`
- Parse and validate each row
- Handle malformed data gracefully (skip with warnings)
- Import data in batches for performance
- Display progress and summary statistics

### 7. Start the Development Server

```bash
python manage.py runserver 8080
```

The API will be available at `http://localhost:8080`

## API Endpoints

All endpoints return JSON responses and are available at `http://localhost:8080/analytics/`

### 1. Top Merchant
**GET** `/analytics/top-merchant`

Returns the merchant with the highest total successful transaction amount across all products.

**Response:**
```json
{
    "merchant_id": "MRC-001234",
    "total_volume": 98765432.10
}
```

### 2. Monthly Active Merchants
**GET** `/analytics/monthly-active-merchants`

Returns the count of unique merchants with at least one successful event per month.

**Response:**
```json
{
    "2024-01": 8234,
    "2024-02": 8456,
    "2024-03": 8621
}
```

### 3. Product Adoption
**GET** `/analytics/product-adoption`

Returns unique merchant count per product, sorted by count (highest first).

**Response:**
```json
{
    "POS": 15234,
    "AIRTIME": 12456,
    "BILLS": 10234,
    "CARD_PAYMENT": 8934,
    "SAVINGS": 7821,
    "MONIEBOOK": 6543,
    "KYC": 5432
}
```

### 4. KYC Funnel
**GET** `/analytics/kyc-funnel`

Returns the KYC conversion funnel metrics (unique merchants at each stage).

**Response:**
```json
{
    "documents_submitted": 5432,
    "verifications_completed": 4521,
    "tier_upgrades": 3890
}
```

### 5. Failure Rates
**GET** `/analytics/failure-rates`

Returns failure rate per product: (FAILED / (SUCCESS + FAILED)) × 100. PENDING transactions are excluded.

**Response:**
```json
[
    {"product": "BILLS", "failure_rate": 5.2},
    {"product": "AIRTIME", "failure_rate": 4.1},
    {"product": "POS", "failure_rate": 3.5}
]
```

## Testing the API

### Running Automated Tests

The project includes comprehensive unit tests for all API endpoints. To run the test suite:

```bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test analytics

# Run tests for a specific test file
python manage.py test analytics.tests.test_views

# Run tests with verbose output
python manage.py test --verbosity=2


```

The test suite includes:
- **TopMerchantView**
  - Tests for top merchant calculation, status filtering, and decimal precision
- **MonthlyActiveMerchantsView**
  - Tests for monthly counts, date formatting, and null timestamp handling
- **ProductAdoptionView**
  - Tests for product adoption counts, sorting, and status inclusion
- **KYCFunnelView**
  - Tests for KYC funnel stages, unique merchant counting, and event filtering
- **FailureRatesView**
  - Tests for failure rate calculations, sorting, and decimal precision

### Manual API Testing

You can also test the endpoints manually using `curl`:

```bash
# Top Merchant
curl http://localhost:8080/analytics/top-merchant

# Monthly Active Merchants
curl http://localhost:8080/analytics/monthly-active-merchants

# Product Adoption
curl http://localhost:8080/analytics/product-adoption

# KYC Funnel
curl http://localhost:8080/analytics/kyc-funnel

# Failure Rates
curl http://localhost:8080/analytics/failure-rates
```

## Project Structure

```
Moniepoint_DreamDev/
├──src/
│   ├── analytics/
│   │   ├── models.py          # Database models
│   │   ├── views.py           # API endpoints
│   │   ├── constants.py       # Application constants
│   │   └── management/
│   │       └── commands/
│   │           └── loads.py  # CSV import command
│   ├─ moniepoint/
│   |    ├── settings.py        # Django settings
│   |    └── urls.py            # URL routing
    └──manage.py
├── data/
│   └── activities_20240101.csv
|   └── 2.csv # CSV data files
                # Django management script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Code Quality Features

- **Static Typing**: All code uses Python type hints for better code clarity and IDE support
- **Comprehensive Docstrings**: All functions and classes are documented with detailed docstrings
- **Error Handling**: Graceful error handling for malformed data and edge cases
- **Database Indexing**: Optimized database indexes for query performance
- **Batch Processing**: Efficient bulk operations for data import

## Notes

- The API uses Django REST Framework for JSON responses
- All monetary values are formatted to 2 decimal places
- Percentages are formatted to 1 decimal place
- The application handles malformed CSV data gracefully
- Database connections are optimized for performance

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Verify database credentials in `.env` file
- Check that the database exists

### Import Errors
- Verify CSV files are in the correct directory
- Check file permissions
- Review error messages in the console output

### Port Already in Use
- Ensure port 8080 is not already in use


## License

This project is created for the Moniepoint DreamDev Hackathon 2026.
