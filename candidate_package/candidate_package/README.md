# DreamDev Hackathon 2025

## Challenge Overview

Build a **REST API** that analyzes merchant activity data and exposes analytics endpoints.


---

## Quick Start

### 1. Create Your Repository

Create a public GitHub repository with:
```
your-repo/
├── src/                # Your source code
├── README.md           # Your name, assumptions & instructions on how to run your service
└── requirements.txt / package.json / pom.xml / build.gradle.kts
```

### 2. Choose Your Language

You can use any of the following languages/frameworks:
- **Python** (Flask, FastAPI, Django)
- **JavaScript** (Express, NestJS, Fastify)
- **Java** (Spring Boot, Quarkus)
- **Kotlin** (Ktor, Spring Boot)

### 3. Download Sample Data

Download the sample CSV files for local development:

**[DOWNLOAD_LINK_HERE]**

*(Organizer will provide the actual Google Drive link)*

Extract to a `data/` folder in your repo:
```
your-repo/
├── data/
│   ├── activities_20240101.csv
│   ├── activities_20240102.csv
│   └── ...
```

### 4. Import CSV Data into a Database

Your first task is to **import the CSV data into a database** of your choice before processing for analytics.

**Data Source:** CSV files located at `data/activities_YYYYMMDD.csv`

Your application should:
1. Read the CSV files from the `data/` directory
2. Import the data into your chosen database (PostgreSQL, MySQL, SQLite, etc.)
3. Query the database to serve the analytics endpoints

---

### 5. Build & Run

Provide clear instructions in your README on how to run your microservice. Include:
- Prerequisites (e.g., Java 17, Node.js 18, Python 3.11)
- How to install dependencies
- How to start the application
- Any environment variables needed

Your API must run on **port 8080**.

### 6. Test Your API

```bash
curl http://localhost:8080/analytics/top-merchant
curl http://localhost:8080/analytics/monthly-active-merchants
curl http://localhost:8080/analytics/product-adoption
curl http://localhost:8080/analytics/kyc-funnel
curl http://localhost:8080/analytics/failure-rates
```

---

## API Endpoints (Port 8080)

| Endpoint | Description |
|----------|-------------|
| `GET /analytics/top-merchant` | Merchant with highest total volume |
| `GET /analytics/monthly-active-merchants` | Unique merchants per month |
| `GET /analytics/product-adoption` | Unique merchants per product |
| `GET /analytics/kyc-funnel` | KYC conversion funnel |
| `GET /analytics/failure-rates` | Failure rate by product |

---

## Data Schema

| Column | Type | Description |
|--------|------|-------------|
| event_id | UUID | Unique identifier |
| merchant_id | VARCHAR | Format: MRC-XXXXXX |
| event_timestamp | TIMESTAMP | ISO 8601 format |
| product | VARCHAR | POS, AIRTIME, BILLS, CARD_PAYMENT, SAVINGS, MONIEBOOK, KYC |
| event_type | VARCHAR | Activity type |
| amount | DECIMAL | Amount in NGN |
| status | VARCHAR | SUCCESS, FAILED, PENDING |
| channel | VARCHAR | POS, APP, USSD, WEB, OFFLINE |
| region | VARCHAR | Operating region |
| merchant_tier | VARCHAR | STARTER, VERIFIED, PREMIUM |

---

## Submission Checklist

- [ ] Repository is **public** on GitHub
- [ ] README includes **instructions on how to run your microservice**
- [ ] API responds on **port 8080**
- [ ] All 5 endpoints return valid JSON
- [ ] README includes your name and assumptions
- [ ] Submit your repository URL before deadline

---

**Good luck!**
