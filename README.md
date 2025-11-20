# rmhogcapi - Geospatial API Service

**Azure Function App for Standards-Compliant Geospatial Data Access**

---

## Overview

rmhogcapi is a dedicated Azure Function App serving two standards-compliant geospatial APIs for read-only data access:

1. **OGC API - Features Core 1.0**: Vector feature access from PostGIS
2. **STAC API v1.0.0**: SpatioTemporal Asset Catalog for raster and vector metadata

### Key Features

- **Dual API Architecture**: OGC Features + STAC in single deployment
- **Standards Compliance**: OGC API - Features Core 1.0 & STAC API v1.0.0
- **PostgreSQL Integration**: Direct queries to Azure PostgreSQL with PostGIS and pgSTAC
- **GeoJSON Responses**: Standards-compliant GeoJSON for both APIs
- **Spatial Filtering**: Bounding box queries for geographic subsetting
- **Pagination Support**: Efficient handling of large datasets
- **Read-Only Architecture**: No write operations to database
- **Microservices Ready**: Independent scaling and deployment

---

## API Endpoints

### Base URL

- **Production**: https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net
- **Local Development**: http://localhost:7071

### Available Endpoints

**Health Check**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service health check and status (both APIs) |

**OGC Features API** (6 endpoints):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/features` | GET | Landing page with API metadata |
| `/api/features/conformance` | GET | OGC conformance classes |
| `/api/features/collections` | GET | List all vector collections |
| `/api/features/collections/{collectionId}` | GET | Collection metadata and extent |
| `/api/features/collections/{collectionId}/items` | GET | Query features from collection |
| `/api/features/collections/{collectionId}/items/{featureId}` | GET | Retrieve single feature |

**STAC API** (6 endpoints):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stac` | GET | STAC catalog landing page |
| `/api/stac/conformance` | GET | STAC conformance classes |
| `/api/stac/collections` | GET | List all STAC collections |
| `/api/stac/collections/{collectionId}` | GET | STAC collection metadata |
| `/api/stac/collections/{collectionId}/items` | GET | Query STAC items (with pagination) |
| `/api/stac/collections/{collectionId}/items/{itemId}` | GET | Retrieve single STAC item |

**Total**: 13 HTTP endpoints (6 OGC + 6 STAC + 1 health)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Azure Functions Core Tools 4.x
- Azure CLI (for deployment)
- Access to Azure PostgreSQL with PostGIS

### Local Development

1. **Clone and setup**:
   ```bash
   cd rmhogcapi
   pip install -r requirements.txt
   ```

2. **Configure local settings**:
   ```bash
   cp local.settings.example.json local.settings.json
   # Edit local.settings.json with your PostgreSQL credentials
   ```

3. **Start local server**:
   ```bash
   func start
   ```

4. **Test endpoints**:
   ```bash
   curl http://localhost:7071/api/health
   curl http://localhost:7071/api/features/collections
   ```

---

## Configuration

### Environment Variables

All configuration is managed through environment variables (Azure App Settings in production):

#### PostgreSQL Connection (Required)

```
POSTGIS_HOST=rmhpgflex.postgres.database.azure.com
POSTGIS_PORT=5432
POSTGIS_DATABASE=geopgflex
POSTGIS_USER=rob634
POSTGIS_PASSWORD=<password>
USE_MANAGED_IDENTITY=false
```

#### OGC Features Settings (Optional)

```
OGC_SCHEMA=geo
OGC_GEOMETRY_COLUMN=geom
OGC_DEFAULT_LIMIT=100
OGC_MAX_LIMIT=10000
OGC_DEFAULT_PRECISION=6
OGC_ENABLE_VALIDATION=true
OGC_QUERY_TIMEOUT=30
```

#### STAC API Settings (Optional)

```
STAC_CATALOG_ID=rmh-geospatial-stac
STAC_CATALOG_TITLE=RMH Geospatial STAC API
STAC_DESCRIPTION=STAC catalog for geospatial raster and vector data
STAC_BASE_URL=https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `OGC_SCHEMA` | geo | PostgreSQL schema containing vector tables |
| `OGC_GEOMETRY_COLUMN` | geom | Default geometry column name (use "shape" for ArcGIS) |
| `OGC_DEFAULT_LIMIT` | 100 | Default number of features returned |
| `OGC_MAX_LIMIT` | 10000 | Maximum features allowed per request |
| `OGC_DEFAULT_PRECISION` | 6 | Coordinate decimal precision |
| `OGC_ENABLE_VALIDATION` | true | Enable spatial index validation |
| `OGC_QUERY_TIMEOUT` | 30 | Query timeout in seconds |

---

## Usage Examples

### List Available Collections

```bash
curl https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/features/collections
```

**Response**:
```json
{
  "collections": [
    {
      "id": "acled_serial_001",
      "title": "Acled Serial 001",
      "description": "Vector features from acled_serial_001",
      "links": [...],
      "itemType": "feature",
      "crs": ["http://www.opengis.net/def/crs/EPSG/0/4326"]
    }
  ]
}
```

### Query Features with Pagination

```bash
curl "https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/features/collections/acled_serial_001/items?limit=10&offset=0"
```

### Spatial Filter (Bounding Box)

```bash
# bbox format: minx,miny,maxx,maxy (EPSG:4326)
curl "https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/features/collections/acled_serial_001/items?bbox=30,45,35,50&limit=100"
```

### Temporal Filter

```bash
curl "https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/features/collections/acled_serial_001/items?datetime=2022-01-01/2022-12-31&limit=50"
```

### Attribute Filters

```bash
curl "https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/features/collections/acled_serial_001/items?year=2022&country=Ukraine&limit=20"
```

### Combined Filters

```bash
curl "https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/features/collections/acled_serial_001/items?bbox=30,45,35,50&datetime=2022-01-01/2022-12-31&year=2022&limit=100"
```

---

## STAC API Usage Examples

### Get STAC Catalog

```bash
curl https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/stac
```

**Response**:
```json
{
  "id": "rmh-geospatial-stac",
  "type": "Catalog",
  "title": "RMH Geospatial STAC API",
  "stac_version": "1.0.0",
  "conformsTo": [
    "https://api.stacspec.org/v1.0.0/core",
    "https://api.stacspec.org/v1.0.0/collections"
  ],
  "links": [...]
}
```

### List STAC Collections

```bash
curl https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/stac/collections
```

### Get Collection Metadata

```bash
curl https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/stac/collections/namangan_test_1
```

### Query STAC Items with Pagination

```bash
curl "https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/stac/collections/namangan_test_1/items?limit=50&offset=0"
```

### Get Single STAC Item

```bash
curl https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/stac/collections/namangan_test_1/items/{item-id}
```

### Using pystac-client

```python
from pystac_client import Client

# Open STAC catalog
catalog = Client.open("https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/stac")

# List collections
collections = list(catalog.get_collections())
print(f"Found {len(collections)} collections")

# Get items from collection
collection = catalog.get_collection("namangan_test_1")
items = collection.get_items()
for item in items:
    print(f"Item: {item.id}")
```

---

## Deployment

### Azure Deployment

1. **Configure Azure Function App**:
   ```bash
   az functionapp config appsettings set \
     --name rmhgeoapifn \
     --resource-group rmhazure_rg \
     --settings \
       POSTGIS_HOST="rmhpgflex.postgres.database.azure.com" \
       POSTGIS_PORT="5432" \
       POSTGIS_DATABASE="geopgflex" \
       POSTGIS_USER="rob634" \
       POSTGIS_PASSWORD="<password>" \
       USE_MANAGED_IDENTITY="false" \
       OGC_SCHEMA="geo"
   ```

2. **Deploy application**:
   ```bash
   func azure functionapp publish rmhgeoapifn
   ```

3. **Verify deployment**:
   ```bash
   curl https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/health
   ```

### Deployment Checklist

- [ ] Azure Function App created (Linux, Python 3.11)
- [ ] PostgreSQL firewall rules configured
- [ ] Environment variables configured in Azure
- [ ] Application deployed successfully
- [ ] Health endpoint returns "healthy" status
- [ ] Collections endpoint returns data
- [ ] CORS configured if needed

---

## Architecture

### Technology Stack

- **Runtime**: Python 3.11, Azure Functions v4
- **Database**: Azure PostgreSQL with PostGIS extension
- **API Framework**: Azure Functions HTTP triggers
- **Data Validation**: Pydantic v2
- **PostgreSQL Driver**: psycopg3 with binary extensions

### Project Structure

```
rmhogcapi/
├── function_app.py        # Azure Functions entry point (13 HTTP endpoints)
├── config.py              # Configuration management
├── host.json              # Azure Functions runtime config
├── requirements.txt       # Python dependencies
├── local.settings.json    # Local development settings
├── infrastructure/        # Shared infrastructure layer
│   ├── postgresql.py      # PostgreSQL repository (per-request connections)
│   └── stac_queries.py    # Read-only STAC query functions
├── ogc_features/          # OGC Features API module (6 endpoints)
│   ├── __init__.py        # Module exports
│   ├── config.py          # OGC-specific configuration
│   ├── models.py          # Pydantic response models
│   ├── repository.py      # PostGIS data access layer
│   ├── service.py         # Business logic layer
│   └── triggers.py        # HTTP endpoint handlers
├── stac_api/              # STAC API module (6 endpoints)
│   ├── __init__.py        # Module exports
│   ├── config.py          # STAC-specific configuration
│   ├── models.py          # STAC response models
│   ├── service.py         # STAC business logic
│   └── triggers.py        # STAC HTTP endpoint handlers
└── docs/
    ├── README.md          # This file
    └── ARCHITECTURE.md    # Technical architecture
```

---

## Performance Considerations

### Database Optimization

- **Spatial Indexes**: GiST indexes on geometry columns recommended
- **Primary Keys**: Required for feature ID lookups
- **Per-Request Connections**: No connection pooling (suitable for serverless)
- **Query Timeout**: 30-second default timeout prevents long-running queries
- **Dual Schema**: `geo` schema for PostGIS vectors, `pgstac` schema for STAC catalog

### Response Optimization

- **Geometry Simplification**: Optional via `simplify` parameter (meters)
- **Coordinate Precision**: Configurable via `precision` parameter (decimal places)
- **Pagination**: Default limit of 100 features, maximum 10,000
- **Caching**: Consider Azure Front Door or CDN for static responses

---

## Security

### Authentication

- **Current**: Anonymous access (public read API)
- **Future**: Azure AD authentication via API Management

### Database Access

- **Current**: Password-based authentication (URL-encoded)
- **Future**: Managed Identity authentication

### Network Security

- **SSL/TLS**: Enforced for all PostgreSQL connections (`sslmode=require`)
- **Firewall**: PostgreSQL firewall rules control access
- **CORS**: Configurable via `local.settings.json` or Azure portal

---

## Monitoring

### Health Endpoint

```bash
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "app": "rmhogcapi",
  "description": "OGC Features & STAC API Service",
  "apis": {
    "ogc_features": {
      "available": true,
      "schema": "geo",
      "endpoints": 6
    },
    "stac": {
      "available": true,
      "schema": "pgstac",
      "endpoints": 6
    }
  }
}
```

### Application Insights

- Function execution times
- Request/response metrics
- Error tracking and diagnostics
- Database query performance

---

## Troubleshooting

### Common Issues

**Issue**: Collections endpoint returns empty array

**Solution**: Verify PostgreSQL connection and ensure `geo` schema contains tables with geometry columns

---

**Issue**: Connection timeout errors

**Solution**: Check PostgreSQL firewall rules and network connectivity

---

**Issue**: Password authentication fails

**Solution**: Ensure password is correctly URL-encoded in environment variables (special characters like @ must be encoded)

---

**Issue**: No features returned for valid collection

**Solution**: Verify geometry column name matches `OGC_GEOMETRY_COLUMN` setting or exists in `geometry_columns` view

---

## Standards Compliance

### OGC API - Features Core 1.0

This implementation conforms to:
- **OGC API - Features - Part 1: Core** (OGC 17-069r4)
- **GeoJSON** (RFC 7946)
- **CRS84 and EPSG:4326** coordinate reference systems

**Conformance Classes:**
- Core
- GeoJSON
- HTML (not implemented)
- OpenAPI 3.0 (not implemented)

### STAC API v1.0.0

This implementation conforms to:
- **STAC API v1.0.0** specification
- **STAC Core** (required)
- **STAC Collections** (required)
- **STAC Items** (required)
- **pgSTAC v0.9.8** backend

**Conformance Classes:**
- STAC API - Core
- STAC API - Collections
- STAC API - Features (GeoJSON)
- STAC Search (not yet implemented)

---

## Support and Maintenance

### Resources

- **OGC Specification**: https://docs.ogc.org/is/17-069r4/17-069r4.html
- **STAC API Specification**: https://github.com/radiantearth/stac-api-spec
- **GeoJSON Specification**: https://datatracker.ietf.org/doc/html/rfc7946
- **pgSTAC Documentation**: https://github.com/stac-utils/pgstac
- **Azure Functions Python**: https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python

### Database Schema Requirements

#### OGC Features (`geo` schema)
- PostgreSQL 12+ with PostGIS 3.0+
- Tables in `geo` schema
- Geometry columns registered in `geometry_columns` view
- Spatial indexes (GiST) recommended for performance

#### STAC API (`pgstac` schema)
- PostgreSQL 12+ with pgSTAC 0.9.8+
- pgSTAC schema installed
- Collections in `pgstac.collections` table
- Items in `pgstac.items` table

---

## License

Internal corporate use only.

---

**Version**: 1.0.0
**Last Updated**: 19 NOV 2025
**Status**: Production Ready
