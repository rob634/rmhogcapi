# OGC Features API - Local Testing Guide

**Date**: 29 OCT 2025
**Purpose**: Complete guide for local development and testing with PostGIS

---

## Overview

The OGC Features API can be **fully tested locally** with a PostgreSQL/PostGIS instance. This guide covers setup, test data creation, and comprehensive testing procedures.

---

## What Can Be Tested Locally?

### ✅ **100% Testable** (No Azure Required)

| Component | Local Testing | Notes |
|-----------|---------------|-------|
| **PostGIS Queries** | ✅ Full | All SQL queries work identically |
| **Spatial Filtering** | ✅ Full | ST_Intersects, bbox queries |
| **Temporal Queries** | ✅ Full | Datetime filtering |
| **Attribute Filtering** | ✅ Full | Property filters |
| **Sorting** | ✅ Full | ORDER BY clauses |
| **Simplification** | ✅ Full | ST_Simplify works locally |
| **Pagination** | ✅ Full | LIMIT/OFFSET |
| **HTTP Endpoints** | ✅ Full | Azure Functions local runtime |
| **Response Formatting** | ✅ Full | GeoJSON serialization |
| **Validation** | ✅ Full | Index checks, warnings |

### ⚠️ **Partially Testable** (Azure-specific features)

| Feature | Local | Notes |
|---------|-------|-------|
| **Easy Auth** | ❌ | Azure Portal only - test with `ANONYMOUS` |
| **Application Insights** | ⚠️ | Mock locally, real in Azure |
| **Managed Identity** | ❌ | Azure only - use password auth locally |

### 🎯 **Testing Coverage**: 95%+

Everything except Azure-specific auth/logging can be tested locally.

---

## Prerequisites

### 1. Install PostgreSQL + PostGIS

#### macOS (Homebrew)
```bash
# Install PostgreSQL 15 with PostGIS
brew install postgresql@15 postgis

# Start PostgreSQL
brew services start postgresql@15

# Verify installation
psql --version  # Should show PostgreSQL 15.x
```

#### Linux (Ubuntu/Debian)
```bash
# Install PostgreSQL + PostGIS
sudo apt update
sudo apt install postgresql-15 postgis postgresql-15-postgis-3

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Windows
```bash
# Download and install:
# - PostgreSQL 15: https://www.postgresql.org/download/windows/
# - PostGIS: http://postgis.net/install/
# Follow installer wizards
```

#### Docker (Cross-platform)
```bash
# Run PostGIS in Docker (easiest!)
docker run -d \
  --name postgis-local \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=geodata \
  -p 5432:5432 \
  postgis/postgis:15-3.4

# Verify running
docker ps | grep postgis-local
```

### 2. Install Azure Functions Core Tools

```bash
# macOS
brew tap azure/functions
brew install azure-functions-core-tools@4

# Linux
wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4

# Windows
# Download MSI: https://github.com/Azure/azure-functions-core-tools/releases
```

### 3. Install Python Dependencies

```bash
# In your project directory
pip install -r requirements.txt

# Or manually:
pip install azure-functions psycopg[binary] pydantic
```

---

## Local Database Setup

### Step 1: Create Database and Enable PostGIS

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE geodata;

# Connect to new database
\c geodata

# Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

# Create geo schema
CREATE SCHEMA IF NOT EXISTS geo;

# Verify PostGIS version
SELECT PostGIS_Version();
-- Should show: 3.4.x or higher
```

### Step 2: Create Test Tables

```sql
-- Example 1: Point features (restaurants)
CREATE TABLE geo.restaurants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    rating NUMERIC(2,1),
    date_opened DATE,
    date_updated TIMESTAMP DEFAULT NOW(),
    geom GEOMETRY(Point, 4326)
);

-- Create spatial index
CREATE INDEX idx_restaurants_geom ON geo.restaurants USING GIST(geom);

-- Insert test data (San Francisco area)
INSERT INTO geo.restaurants (name, category, rating, date_opened, geom) VALUES
    ('The Mission', 'Mexican', 4.5, '2020-01-15', ST_SetSRID(ST_MakePoint(-122.419, 37.759), 4326)),
    ('North Beach Pizza', 'Italian', 4.2, '2019-06-20', ST_SetSRID(ST_MakePoint(-122.409, 37.803), 4326)),
    ('Chinatown Express', 'Chinese', 4.7, '2021-03-10', ST_SetSRID(ST_MakePoint(-122.407, 37.795), 4326)),
    ('Golden Gate Cafe', 'American', 3.9, '2018-11-05', ST_SetSRID(ST_MakePoint(-122.478, 37.819), 4326)),
    ('Fishermans Wharf', 'Seafood', 4.3, '2022-02-28', ST_SetSRID(ST_MakePoint(-122.417, 37.808), 4326));

-- Update statistics
ANALYZE geo.restaurants;


-- Example 2: Polygon features (neighborhoods)
CREATE TABLE geo.neighborhoods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    district VARCHAR(100),
    population INTEGER,
    year_established INTEGER,
    last_census DATE,
    geom GEOMETRY(Polygon, 4326)
);

-- Create spatial index
CREATE INDEX idx_neighborhoods_geom ON geo.neighborhoods USING GIST(geom);

-- Insert test data (simple polygons)
INSERT INTO geo.neighborhoods (name, district, population, year_established, last_census, geom) VALUES
    ('Mission District',
     'District 9',
     60000,
     1776,
     '2020-01-01',
     ST_SetSRID(ST_GeomFromText('POLYGON((-122.42 37.75, -122.42 37.77, -122.40 37.77, -122.40 37.75, -122.42 37.75))'), 4326)),

    ('North Beach',
     'District 3',
     15000,
     1850,
     '2020-01-01',
     ST_SetSRID(ST_GeomFromText('POLYGON((-122.41 37.80, -122.41 37.81, -122.40 37.81, -122.40 37.80, -122.41 37.80))'), 4326)),

    ('Chinatown',
     'District 3',
     25000,
     1848,
     '2020-01-01',
     ST_SetSRID(ST_GeomFromText('POLYGON((-122.41 37.79, -122.41 37.80, -122.40 37.80, -122.40 37.79, -122.41 37.79))'), 4326));

-- Update statistics
ANALYZE geo.neighborhoods;


-- Verify tables
SELECT
    f_table_name as table_name,
    f_geometry_column as geom_column,
    type as geom_type,
    srid
FROM geometry_columns
WHERE f_table_schema = 'geo';
```

### Step 3: Verify Spatial Indexes

```sql
-- Check that GIST indexes exist
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'geo'
  AND indexdef LIKE '%USING gist%';

-- Should show:
-- idx_restaurants_geom
-- idx_neighborhoods_geom
```

---

## Local Configuration

### Create `local.settings.json`

In your project root (same directory as `function_app.py`):

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",

    "POSTGIS_HOST": "localhost",
    "POSTGIS_PORT": "5432",
    "POSTGIS_DATABASE": "geodata",
    "POSTGIS_USER": "postgres",
    "POSTGIS_PASSWORD": "password",

    "OGC_SCHEMA": "geo",
    "OGC_GEOMETRY_COLUMN": "geom",
    "OGC_DEFAULT_LIMIT": "100",
    "OGC_MAX_LIMIT": "10000",
    "OGC_DEFAULT_PRECISION": "6",
    "OGC_BASE_URL": "http://localhost:7071",
    "OGC_QUERY_TIMEOUT": "30",
    "OGC_ENABLE_VALIDATION": "true"
  }
}
```

**Docker PostgreSQL**:
If using Docker, keep `POSTGIS_HOST=localhost` (Docker port forwarding handles it).

---

## Running Locally

### Start Azure Functions Runtime

```bash
# In project directory (where function_app.py is)
func start

# Output should show:
# Azure Functions Core Tools
# Core Tools Version: 4.x.x
# Function Runtime Version: 4.x.x
#
# Functions:
#   features: [GET] http://localhost:7071/api/features
#   features/conformance: [GET] http://localhost:7071/api/features/conformance
#   features/collections: [GET] http://localhost:7071/api/features/collections
#   ... (6 endpoints total)
```

### Verify Endpoints Load

```bash
# Health check (if you have one)
curl http://localhost:7071/api/health

# OGC landing page
curl http://localhost:7071/api/features
```

---

## Testing Procedures

### 1. Landing Page & Conformance

```bash
# Landing page
curl http://localhost:7071/api/features | jq

# Expected: JSON with links to collections, conformance

# Conformance
curl http://localhost:7071/api/features/conformance | jq

# Expected: conformsTo array with OGC URIs
```

### 2. Collections Discovery

```bash
# List all collections
curl http://localhost:7071/api/features/collections | jq

# Expected: Array with "restaurants" and "neighborhoods"

# Single collection metadata
curl http://localhost:7071/api/features/collections/restaurants | jq

# Expected: Collection metadata with bbox, feature count
```

### 3. Basic Feature Query

```bash
# Get all restaurants (limit 100)
curl "http://localhost:7071/api/features/collections/restaurants/items?limit=100" | jq

# Expected: GeoJSON FeatureCollection with 5 features
```

### 4. Spatial Filtering (Bbox)

```bash
# Restaurants in specific area
curl "http://localhost:7071/api/features/collections/restaurants/items?\
bbox=-122.42,37.75,-122.40,37.77&\
limit=100" | jq

# Expected: Only restaurants within bbox (Mission District area)

# Check numberMatched vs numberReturned
# numberMatched = total matching features
# numberReturned = features in this response
```

### 5. Temporal Filtering

```bash
# Restaurants opened in 2020
curl "http://localhost:7071/api/features/collections/restaurants/items?\
datetime=2020-01-01/2020-12-31&\
datetime_property=date_opened" | jq

# Expected: Only "The Mission" (opened 2020-01-15)

# Restaurants opened before 2020
curl "http://localhost:7071/api/features/collections/restaurants/items?\
datetime=../2020-01-01&\
datetime_property=date_opened" | jq

# Expected: Features with date_opened < 2020-01-01
```

### 6. Attribute Filtering

```bash
# Italian restaurants
curl "http://localhost:7071/api/features/collections/restaurants/items?\
category=Italian" | jq

# Expected: "North Beach Pizza"

# High-rated restaurants (rating >= 4.5)
# Note: Simple filters only support equality in Phase 1
curl "http://localhost:7071/api/features/collections/restaurants/items?\
rating=4.5" | jq

# For range queries, use database views or wait for Phase 2
```

### 7. Sorting

```bash
# Restaurants sorted by rating (descending)
curl "http://localhost:7071/api/features/collections/restaurants/items?\
sortby=-rating" | jq

# Expected: Chinatown Express (4.7) first, Golden Gate Cafe (3.9) last

# Multiple sort columns
curl "http://localhost:7071/api/features/collections/restaurants/items?\
sortby=+category,-rating" | jq

# Expected: Sorted by category ASC, then rating DESC within each category
```

### 8. Geometry Optimization

```bash
# Low precision (3 decimals = ~111m resolution)
curl "http://localhost:7071/api/features/collections/neighborhoods/items?\
precision=3" | jq

# Check coordinates - should have 3 decimal places

# High precision (8 decimals = ~1cm resolution)
curl "http://localhost:7071/api/features/collections/neighborhoods/items?\
precision=8" | jq

# Simplification (100m tolerance)
curl "http://localhost:7071/api/features/collections/neighborhoods/items?\
simplify=100&\
precision=3" | jq

# Compare payload size - should be smaller with simplification
```

### 9. Pagination

```bash
# First page (offset 0, limit 2)
curl "http://localhost:7071/api/features/collections/restaurants/items?\
limit=2&\
offset=0" | jq

# Expected:
# - numberMatched: 5 (total)
# - numberReturned: 2 (in this response)
# - links: includes "next" link

# Second page (offset 2, limit 2)
curl "http://localhost:7071/api/features/collections/restaurants/items?\
limit=2&\
offset=2" | jq

# Expected:
# - numberReturned: 2
# - links: includes "prev" and "next"

# Last page (offset 4, limit 2)
curl "http://localhost:7071/api/features/collections/restaurants/items?\
limit=2&\
offset=4" | jq

# Expected:
# - numberReturned: 1 (only 1 remaining)
# - links: includes "prev" but NO "next"
```

### 10. Combined Query (All Features)

```bash
# Complex query combining all filters
curl "http://localhost:7071/api/features/collections/restaurants/items?\
bbox=-122.42,37.75,-122.40,37.82&\
datetime=2019-01-01/2021-12-31&\
datetime_property=date_opened&\
category=Italian&\
sortby=-rating&\
precision=5&\
limit=10&\
offset=0" | jq

# Expected: Italian restaurants in bbox, opened 2019-2021, sorted by rating
```

### 11. Single Feature Retrieval

```bash
# Get specific restaurant by ID
curl "http://localhost:7071/api/features/collections/restaurants/items/1" | jq

# Expected: Single GeoJSON Feature (not FeatureCollection)

# Non-existent feature
curl "http://localhost:7071/api/features/collections/restaurants/items/999" | jq

# Expected: 404 error with message
```

### 12. Validation Checks (if enabled)

```bash
# Get collection with validation
curl "http://localhost:7071/api/features/collections/restaurants" | jq

# If OGC_ENABLE_VALIDATION=true, response includes:
# {
#   "id": "restaurants",
#   "validation": {
#     "validation_enabled": true,
#     "warnings": [],  # Empty if all indexes exist
#     "recommendations": []
#   }
# }
```

---

## Testing with Real GIS Clients

### QGIS

1. **Layer** → **Add Layer** → **Add WFS Layer**
2. **New Connection**:
   - Name: `Local OGC API`
   - URL: `http://localhost:7071/api/features`
3. **Connect** → Should show `restaurants` and `neighborhoods`
4. **Add Layer** → Features load in QGIS

### Python Script

```python
import requests

# Query features
response = requests.get(
    "http://localhost:7071/api/features/collections/restaurants/items",
    params={
        "bbox": "-122.42,37.75,-122.40,37.77",
        "category": "Mexican",
        "limit": 100
    }
)

geojson = response.json()
print(f"Found {geojson['numberReturned']} features")

# Access features
for feature in geojson['features']:
    props = feature['properties']
    coords = feature['geometry']['coordinates']
    print(f"{props['name']}: {coords}")
```

---

## Performance Testing

### Test with Larger Datasets

```sql
-- Generate 10,000 random points in San Francisco
INSERT INTO geo.restaurants (name, category, rating, date_opened, geom)
SELECT
    'Restaurant ' || i,
    CASE (i % 5)
        WHEN 0 THEN 'Mexican'
        WHEN 1 THEN 'Italian'
        WHEN 2 THEN 'Chinese'
        WHEN 3 THEN 'American'
        ELSE 'Seafood'
    END,
    3.0 + (random() * 2.0),  -- Rating 3.0-5.0
    '2020-01-01'::date + (random() * 1000)::int,  -- Random date 2020-2023
    ST_SetSRID(
        ST_MakePoint(
            -122.52 + (random() * 0.15),  -- SF longitude range
            37.70 + (random() * 0.15)     -- SF latitude range
        ),
        4326
    )
FROM generate_series(6, 10000) AS i;

-- Update statistics
ANALYZE geo.restaurants;

-- Test query performance
EXPLAIN ANALYZE
SELECT COUNT(*)
FROM geo.restaurants
WHERE ST_Intersects(
    geom,
    ST_MakeEnvelope(-122.42, 37.75, -122.40, 37.77, 4326)
);

-- Should show "Index Scan using idx_restaurants_geom" (fast!)
```

### Benchmark Queries

```bash
# Time bbox query with 10,000 features
time curl -s "http://localhost:7071/api/features/collections/restaurants/items?\
bbox=-122.42,37.75,-122.40,37.77&\
limit=1000" > /dev/null

# Expected: < 2 seconds for 1,000 features

# Time with simplification
time curl -s "http://localhost:7071/api/features/collections/restaurants/items?\
bbox=-122.52,37.70,-122.37,37.85&\
simplify=100&\
precision=3&\
limit=5000" > /dev/null

# Expected: < 3 seconds for 5,000 simplified features
```

---

## Debugging

### Enable Debug Logging

```python
# Add to local.settings.json
{
  "Values": {
    ...
    "PYTHON_ENABLE_DEBUG_LOGGING": "1",
    "PYTHON_THREADPOOL_THREAD_COUNT": "1"
  }
}
```

### Check PostgreSQL Logs

```bash
# macOS (Homebrew)
tail -f /usr/local/var/log/postgresql@15.log

# Linux
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Docker
docker logs -f postgis-local
```

### Verify SQL Queries

```sql
-- Enable query logging
ALTER DATABASE geodata SET log_statement = 'all';

-- Or edit postgresql.conf:
# log_statement = 'all'

-- Restart PostgreSQL and check logs for actual SQL
```

---

## Known Limitations (Local Testing)

### Cannot Test

1. **Easy Auth** - Azure Portal only
2. **Application Insights** - Azure only (can mock locally)
3. **Managed Identity** - Azure only

### Workarounds

- **Auth**: Test with `ANONYMOUS` locally, enable Easy Auth in Azure
- **Logging**: Use `print()` locally, Application Insights in Azure
- **Identity**: Use password auth locally, switch to managed identity in Azure

---

## Clean Up

### Remove Test Data

```sql
-- Drop test tables
DROP TABLE IF EXISTS geo.restaurants CASCADE;
DROP TABLE IF EXISTS geo.neighborhoods CASCADE;

-- Or drop entire schema
DROP SCHEMA IF EXISTS geo CASCADE;
```

### Stop PostgreSQL

```bash
# macOS (Homebrew)
brew services stop postgresql@15

# Linux
sudo systemctl stop postgresql

# Docker
docker stop postgis-local
docker rm postgis-local
```

---

## Summary

### ✅ What's Fully Testable Locally

- **100%** of OGC Features API functionality
- **100%** of PostGIS query features
- **100%** of filtering, sorting, pagination
- **95%+** of production behavior

### 🎯 Testing Coverage

| Component | Local | Azure | Notes |
|-----------|-------|-------|-------|
| **Core API** | ✅ 100% | ✅ 100% | Identical |
| **PostGIS** | ✅ 100% | ✅ 100% | Identical |
| **HTTP** | ✅ 100% | ✅ 100% | Identical |
| **Auth** | ⚠️ Anonymous | ✅ Easy Auth | Diff config |
| **Logging** | ⚠️ Console | ✅ App Insights | Diff output |

**Recommendation**: Develop and test locally first, then deploy to Azure for production validation.

---

## Next Steps

1. ✅ Set up local PostGIS
2. ✅ Create test tables
3. ✅ Configure `local.settings.json`
4. ✅ Run `func start`
5. ✅ Test all endpoints with curl
6. ✅ Performance test with 10,000+ features
7. 🚀 Deploy to Azure when ready

---

**Date**: 29 OCT 2025
