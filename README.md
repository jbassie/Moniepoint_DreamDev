# Moniepoint DreamDev Hackathon 2025 - Analytics API

**Author:** Basssey John
**Date**: 21/02/2026

## Overview

This is a REST API built with Django that analyzes merchant activity data across all Moniepoint products. The API provides analytics endpoints to extract key business insights from merchant transaction logs.

## Assumptions

1. **Database**: PostgreSQL is used as the database. The application expects a PostgreSQL database to be set up and configured via environment variables.

2. **Data Format**: CSV files follow the exact schema specified in the requirements. Some rows may have missing or malformed data (e.g., empty timestamps), which are handled gracefully.

3. **Port**: The API runs on port 8080 as specified in the requirements.

4. **Time Zone**: All timestamps are stored and processed in UTC timezone.

5. **Data Import**: CSV files are expected to be in the `candidate_package/candidate_package/data/sample_data/` directory by default, but can be specified via command-line argument.

6. **Error Handling**: Malformed CSV rows are skipped with warnings rather than failing the entire import process.

## Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 12 or higher
- **pip**: Python package manager

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Moniepoint_DreamDev
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
API_database_name=moniepoint_db
API_database_username=**REMOVED**
API_database_password=your_password
API_database_host=localhost
API_database_port=5432
```

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Import CSV Data

The CSV files should be located in `candidate_package/candidate_package/data/sample_data/` by default.

To import the data:
```bash
python manage.py loads
```

Or specify a custom data directory:
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

You can test the endpoints using `curl`:

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
├── v1/
│   ├── analytics/
│   │   ├── models.py          # Database models
│   │   ├── views.py           # API endpoints
│   │   ├── constants.py       # Application constants
│   │   └── management/
│   │       └── commands/
│   │           └── loads.py  # CSV import command
│   └── moniepoint/
│       ├── settings.py        # Django settings
│       └── urls.py            # URL routing
├── candidate_package/
│   └── candidate_package/
│       └── data/
│           └── sample_data/   # CSV data files
├── manage.py                  # Django management script
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
- Use `netstat -ano | findstr :8080` (Windows) or `lsof -i :8080` (Linux/Mac) to check

## License

This project is created for the Moniepoint DreamDev Hackathon 2025.

