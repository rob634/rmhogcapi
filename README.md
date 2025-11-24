# rmhogcapi - Geospatial API Service

**Standards-compliant OGC Features & STAC APIs for Azure PostgreSQL**

[![Azure Functions](https://img.shields.io/badge/Azure-Functions-blue)](https://azure.microsoft.com/en-us/services/functions/)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![OGC API](https://img.shields.io/badge/OGC-API--Features-green)](https://docs.ogc.org/is/17-069r4/17-069r4.html)
[![STAC](https://img.shields.io/badge/STAC-v1.0.0-green)](https://github.com/radiantearth/stac-api-spec)

---

## What is rmhogcapi?

rmhogcapi is a dedicated Azure Function App that serves geospatial data through two standards-compliant REST APIs:

- **OGC API - Features Core 1.0**: Query vector features from PostGIS with GeoJSON responses
- **STAC API v1.0.0**: Discover and access raster/vector metadata catalogs

Designed for **read-only** access with managed identity authentication, independent scaling, and microservices architecture.

---

## Key Features

- **Dual API Architecture**: OGC Features + STAC in a single deployment
- **Standards Compliance**: Fully conformant with OGC and STAC specifications
- **Azure Managed Identity**: Secure, passwordless PostgreSQL authentication
- **PostGIS & pgSTAC**: Native support for spatial queries and STAC catalogs
- **GeoJSON Output**: Standards-compliant spatial data responses
- **Spatial Filtering**: Bounding box and temporal queries
- **Pagination**: Efficient handling of large datasets
- **Production Ready**: Active deployment serving 5 OGC collections + 4 STAC collections

---

## Quick Start

### Prerequisites

- Python 3.11+
- Azure Functions Core Tools 4.x
- Access to Azure PostgreSQL with PostGIS

### Local Development

```bash
# Clone and install dependencies
git clone <repository>
cd rmhogcapi
pip install -r requirements.txt

# Configure local settings
cp local.settings.example.json local.settings.json
# Edit local.settings.json with your PostgreSQL credentials

# Start local server
func start

# Test endpoints
curl http://localhost:7071/api/health
curl http://localhost:7071/api/features/collections
curl http://localhost:7071/api/stac/collections
```

---

## API Endpoints

### Production Base URL
```
https://<your-function-app>.azurewebsites.net
```

### Available Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Public health check (minimal response) |
| `GET /api/health/detailed` | Detailed health metrics (for APIM probes) |
| `GET /api/features` | OGC Features landing page |
| `GET /api/features/conformance` | OGC conformance classes |
| `GET /api/features/collections` | List OGC vector collections |
| `GET /api/features/collections/{id}` | Collection metadata |
| `GET /api/features/collections/{id}/items` | Query features with filters |
| `GET /api/features/collections/{id}/items/{featureId}` | Single feature by ID |
| `GET /api/stac` | STAC API landing page |
| `GET /api/stac/conformance` | STAC conformance classes |
| `GET /api/stac/collections` | List STAC catalogs |
| `GET /api/stac/collections/{id}` | Collection metadata |
| `GET /api/stac/collections/{id}/items` | Query STAC items |
| `GET /api/stac/collections/{id}/items/{itemId}` | Single STAC item |
| `GET/POST /api/stac/search` | STAC search endpoint |

**Total**: 15 HTTP endpoints (6 OGC + 7 STAC + 2 health)

---

## Usage Examples

### List OGC Features Collections

```bash
curl "https://<your-function-app>.azurewebsites.net/api/features/collections"
```

### Query Features with Filters

```bash
# Spatial filter (bounding box)
curl "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items?bbox=30,45,35,50&limit=100"

# Temporal filter
curl "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items?datetime=2022-01-01/2022-12-31"
```

### Access STAC Catalog

```bash
# List STAC collections
curl "https://<your-function-app>.azurewebsites.net/api/stac/collections"

# Query STAC items
curl "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items?limit=50"
```

---

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Configuration](docs/CONFIGURATION.md)** - Environment variables and settings
- **[API Reference](docs/API_REFERENCE.md)** - Complete endpoint documentation
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Azure deployment instructions
- **[Authentication](docs/AUTHENTICATION.md)** - Managed identity setup
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Database Setup

- **[DB_READER_SQL.md](DB_READER_SQL.md)** - Read-only managed identity setup (rmhpgflexreader)
- **[DB_ADMIN_SQL.md](DB_ADMIN_SQL.md)** - Admin managed identity setup (rmhpgflexadmin)

---

## Architecture

### Technology Stack

- **Runtime**: Python 3.11, Azure Functions v4
- **Database**: Azure PostgreSQL Flexible Server (PostGIS + pgSTAC)
- **Authentication**: Azure User-Assigned Managed Identity
- **API Framework**: Azure Functions HTTP triggers
- **Data Validation**: Pydantic v2

### Project Structure

```
rmhogcapi/
├── function_app.py        # Azure Functions entry point (15 HTTP endpoints)
├── health.py              # Production health monitoring (public + detailed)
├── config.py              # Configuration with managed identity support
├── requirements.txt       # Python dependencies
├── infrastructure/        # PostgreSQL repository and STAC queries
├── ogc_features/          # OGC Features API module (6 endpoints)
├── stac_api/              # STAC API module (7 endpoints)
└── docs/                  # Documentation
```

---

## Security & Authentication

This application uses **Azure User-Assigned Managed Identity** for secure, passwordless PostgreSQL authentication:

- **Identity**: `rmhpgflexreader` (Client ID: `1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f`)
- **Database Role**: Read-only access to `geo`, `pgstac`, and `h3` schemas
- **No Secrets**: No passwords stored in application settings
- **Token-Based**: Automatic Azure AD token refresh (1-hour expiry)
- **SSL/TLS**: Enforced for all PostgreSQL connections

See [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) for detailed setup instructions.

---

## Standards Compliance

### OGC API - Features Core 1.0
- **OGC 17-069r4** specification
- **GeoJSON** (RFC 7946)
- **EPSG:4326** coordinate reference system

### STAC API v1.0.0
- **STAC API Core** specification
- **STAC Collections** extension
- **pgSTAC v0.9.8** backend

---

## Support

- **Issues**: Report bugs or request features via GitHub issues
- **Documentation**: See [docs/](docs/) directory
- **OGC Specification**: https://docs.ogc.org/is/17-069r4/17-069r4.html
- **STAC Specification**: https://github.com/radiantearth/stac-api-spec

---

**Version**: 1.0.0
**Last Updated**: 24 NOV 2025
**Status**: Production Ready
