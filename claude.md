# 📁 rmhogcapi - OGC Features & STAC API Azure Function App

**Mission**: Standalone Azure Function App serving OGC Features API and STAC search/query APIs

---

## 🎯 Project Overview

This project creates a dedicated Azure Function App for serving **two standardized geospatial APIs**:

### 1. **OGC Features API** (OGC API - Features Core 1.0)
- Standards-compliant vector feature access
- Direct PostGIS queries with GeoJSON serialization
- Spatial filtering via bounding box queries
- Pagination support (limit/offset)
- RESTful endpoints for collections and features

### 2. **STAC API** (SpatioTemporal Asset Catalog v1.0)
- Metadata catalog for spatial data discovery
- Collection and item management
- Search functionality with spatial/temporal filters
- Asset management for raster/vector datasets

---

## 🏗️ Source ETL System Context

The geospatial data served by these APIs is created by the **rmhgeoapi** ETL pipeline located at:
```
/Users/robertharrison/python_builds/rmhgeoapi/
```

### rmhgeoapi Architecture Summary

**Two-Layer System:**

#### **Platform Layer** (Orchestration)
- API request handling and workflow orchestration
- Dataset management and metadata tracking
- User-facing endpoints for data submission
- Service Bus-based job queuing

#### **CoreMachine Layer** (Processing)
- Job → Stage → Task abstraction for complex workflows
- Parallel task execution with sequential stage advancement
- "Last task turns out the lights" completion detection
- Queue-driven orchestration with PostgreSQL state management

**Key ETL Workflows:**

1. **Raster Processing Pipeline:**
   - Stage 1: Metadata extraction and validation
   - Stage 2: Tiling scheme creation (for large rasters)
   - Stage 3: Fan-out parallel reprojection/validation
   - Stage 4: Fan-out parallel COG conversion
   - Stage 5: STAC metadata creation and indexing

2. **Vector Processing Pipeline:**
   - Shapefile/GeoPackage ingestion
   - PostGIS schema deployment
   - Geometry validation and transformation
   - Spatial indexing
   - OGC Features collection registration

**Data Tiers:**
- **Bronze**: Raw user uploads (`rmhazuregeobronze` container)
- **Silver**: Processed COGs + PostGIS tables (production ready)
- **Gold**: GeoParquet exports (future)

**Database Schema (PostgreSQL - rmhpostgres.postgres.database.azure.com):**
- `app` schema: CoreMachine jobs and tasks
- `platform` schema: Orchestration and dataset tracking
- `geo` schema: PostGIS vector features (served by OGC Features API)
- `pgstac` schema: STAC collections and items (served by STAC API)

---

## 🚀 This Project's Mission

### Current Status
Production

The rmhgeoapi system currently serves ALL APIs from a monolithic Function App:
```
Azure Function App: rmhazuregeoapi (B3 Basic tier)
├── OGC Features (ogc_features/ - 2,600+ lines, standalone)
├── STAC API (pgstac/ + infrastructure/stac.py)
├── Platform Layer (platform schema + triggers)
└── CoreMachine (jobs/tasks + app schema)
```

### Goal: Microservices Architecture

**Extract OGC Features + STAC APIs into standalone Function App** for:
- ✅ **Independent Scaling**: Scale read APIs separately from ETL processing
- ✅ **Separate Deployments**: Deploy API fixes without touching ETL pipeline
- ✅ **Cleaner Architecture**: Dedicated apps for specific concerns
- ✅ **Future APIM Integration**: Prepare for Azure API Management routing

**Future Vision (with Azure API Management):**
```
APIM Gateway (geospatial.rmh.org)
├─→ rmhogcapi Function App (THIS PROJECT)
│   ├── /api/features/* → OGC Features API
│   └── /api/collections/* → STAC API
│
└─→ rmhazuregeoapi Function App (ETL System)
    ├── /api/platform/* → Data ingestion orchestration
    └── /api/jobs/* → CoreMachine processing

All connect to: PostgreSQL (shared database, separate schemas)
```

---

## 📋 Implementation Tasks

### Phase 1: Project Setup
- [ ] Initialize Azure Function App project structure
- [ ] Configure Python runtime and dependencies
- [ ] Set up connection to PostgreSQL (rmhpostgres)
- [ ] Configure environment variables and secrets

### Phase 2: OGC Features API Migration
- [ ] Extract ogc_features/ module from rmhgeoapi
- [ ] Implement OGC Features Core 1.0 endpoints:
  - [ ] `/api/features` - Landing page
  - [ ] `/api/features/conformance` - Conformance classes
  - [ ] `/api/features/collections` - List collections
  - [ ] `/api/features/collections/{collectionId}` - Collection metadata
  - [ ] `/api/features/collections/{collectionId}/items` - Query features
  - [ ] `/api/features/collections/{collectionId}/items/{featureId}` - Single feature
- [ ] Test with existing `geo` schema PostGIS tables
- [ ] Implement spatial query support (bbox filtering)
- [ ] Configure CORS for static website integration

### Phase 3: STAC API Migration
- [ ] Extract pgstac/ module from rmhgeoapi
- [ ] Implement STAC v1.0 endpoints:
  - [ ] `/api/stac` - Landing page
  - [ ] `/api/stac/conformance` - Conformance classes
  - [ ] `/api/stac/collections` - List collections
  - [ ] `/api/stac/collections/{collectionId}` - Collection metadata
  - [ ] `/api/stac/collections/{collectionId}/items` - Collection items
  - [ ] `/api/stac/search` - Search endpoint (POST/GET)
  - [ ] `/api/stac/queryables` - Queryable properties
- [ ] Test with existing `pgstac` schema
- [ ] Implement spatial/temporal search filters
- [ ] Configure pagination and result limits

### Phase 4: Deployment & Testing
- [ ] Deploy to Azure Function App
- [ ] Configure application insights logging
- [ ] Test OGC Features API endpoints
- [ ] Test STAC API endpoints
- [ ] Update static website to use new API URLs
- [ ] Performance testing and optimization

### Phase 5: Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Deployment guide
- [ ] Architecture diagrams
- [ ] Update FILE_CATALOG.md equivalent for this project

---

## 🔧 Technical Stack

**Runtime:**
- Python 3.11
- Azure Functions runtime v4
- Consumption or Basic tier (TBD)

**Database:**
- PostgreSQL (rmhpostgres.postgres.database.azure.com)
- PostGIS extension (geo schema)
- pgstac extension (pgstac schema)
- psycopg3 for connection management

**Key Dependencies:**
- `azure-functions` - Azure Functions SDK
- `psycopg[binary]` - PostgreSQL adapter
- `pydantic` - Data validation
- `geojson` - GeoJSON serialization
- `shapely` - Geometry operations (optional)

**Standards Compliance:**
- OGC API - Features Core 1.0
- STAC v1.0 API specification
- GeoJSON RFC 7946

---

## 🔑 Key URLs & Resources

**Database Connection:**
- Host: `rmhpostgres.postgres.database.azure.com`
- Database: `geopgflex`
- Schemas: `geo` (PostGIS), `pgstac` (STAC)
- User: `rmhpgflexreader` (managed identity) or `rob634` (password auth)

**Resource Group:**
- `rmhazure_rg`

**Related Function App (ETL System):**
- Name: `rmhazuregeoapi`
- URL: https://rmhazuregeoapi-a3dma3ctfdgngwf6.eastus-01.azurewebsites.net

**Static Website (Consumer):**
- URL: https://rmhazuregeo.z13.web.core.windows.net/
- Uses OGC Features API for interactive map

---

## 📝 Development Guidelines

### File Naming Conventions
Follow rmhgeoapi patterns:
- `ogc_*.py` - OGC Features API modules
- `stac_*.py` - STAC API modules
- `model_*.py` - Pydantic models
- `util_*.py` - Utility modules
- `config.py` - Configuration management

### File Headers
Use Claude Context Config header template:
```python
# ============================================================================
# CLAUDE CONTEXT - [DESCRIPTIVE_TITLE]
# ============================================================================
# STATUS: [Component type] - [Brief description]
# PURPOSE: [One sentence description of what this file does]
# LAST_REVIEWED: [DD MMM YYYY]
# EXPORTS: [Main classes, functions, or constants exposed]
# DEPENDENCIES: [Key external libraries]
# ============================================================================
```

### Git Workflow
- **Main branch**: Production-ready code only
- **Commit frequently** with descriptive messages
- Use standard commit format with Claude Code attribution

### Documentation
- Update this claude.md as architecture evolves
- Maintain accurate dependency list
- Document all API endpoints with examples

---

## 🎓 References

**Source System Documentation:**
- `/Users/robertharrison/python_builds/rmhgeoapi/docs_claude/CLAUDE_CONTEXT.md`
- `/Users/robertharrison/python_builds/rmhgeoapi/docs_claude/ARCHITECTURE_REFERENCE.md`

**Standards Documentation:**
- OGC API - Features Core 1.0: https://docs.ogc.org/is/17-069r4/17-069r4.html
- STAC API Spec: https://github.com/radiantearth/stac-api-spec
- GeoJSON RFC 7946: https://datatracker.ietf.org/doc/html/rfc7946

**Azure Documentation:**
- Azure Functions Python: https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python
- Azure PostgreSQL: https://learn.microsoft.com/en-us/azure/postgresql/

---

## 🚨 Important Notes

- **READ-ONLY APIs**: This app serves data, never writes to database (ETL handled by rmhgeoapi)
- **Shared Database**: Coordinate schema changes with rmhgeoapi team
- **Standards Compliance**: Follow OGC and STAC specifications exactly
- **Performance**: Optimize PostGIS queries, use connection pooling
- **Security**: Use managed identity for database access (future)
- **CORS**: Configure for static website domain

---

**Status**: Project initialization - ready for Phase 1 implementation
**Next Step**: Initialize Azure Function App project structure
