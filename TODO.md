# 📋 TODO - rmhogcapi Development Plan

**Date**: 19 NOV 2025
**Status**: Phase 1 Complete ✅ | Phase 2 Planning 🎯

---

## 🎯 Project Goal

Create standalone Azure Function App serving two read-only geospatial APIs:
1. **OGC Features API** - Vector feature access (PostGIS `geo` schema)
2. **STAC API** - Spatiotemporal asset catalog (PostgreSQL `pgstac` schema)

Extract from monolithic rmhazuregeoapi into microservices architecture with independent deployment, scaling, and maintenance.

---

## 📊 Current Status

### Phase 1: OGC Features API - ✅ COMPLETE
- ✅ Project structure created
- ✅ OGC Features module copied and integrated
- ✅ Configuration with password + managed identity support
- ✅ Local testing successful (all 7 endpoints working)
- ✅ Azure deployment successful (rmhgeoapifn Function App)
- ✅ Professional documentation created (README.md, ARCHITECTURE.md)

### Phase 2: STAC API - 🎯 NEXT
- ✅ Source code analysis completed
- ✅ Implementation plan created
- ⏳ Ready to begin migration

---

## ✅ Phase 1: OGC Features API - COMPLETE

All tasks completed successfully. See README.md and ARCHITECTURE.md for full documentation.

**Key Achievements:**
- ✅ Project infrastructure created (function_app.py, host.json, requirements.txt, config.py)
- ✅ OGC Features module copied and integrated (7 endpoints)
- ✅ Password URL encoding fix for special characters
- ✅ Local testing successful with 20 PostGIS collections
- ✅ Azure deployment to rmhgeoapifn Function App
- ✅ Professional documentation (README.md, ARCHITECTURE.md)

---

## 🎯 Phase 2: STAC API Implementation

### Overview
Extract STAC API from rmhgeoapi as standalone read-only module. Total effort: ~7-11 hours across 5 phases.

**Source Location**: `/Users/robertharrison/python_builds/rmhgeoapi/`

**Database Schema**: `pgstac` (PostgreSQL with pgSTAC extension v0.9.8)

**Files to Extract**:
- `stac_api/` module (902 lines) - COPY AS-IS
- PostgreSQL repository pattern (~300 lines) - EXTRACT
- 4 query functions from pgstac_bootstrap.py (~200 lines) - EXTRACT
- Logger module - COPY AS-IS

### 2.1 Infrastructure Layer - PostgreSQL Repository (2-3 hours)

**Goal**: Extract PostgreSQLRepository class for database access without ETL dependencies.

**Tasks**:
- [ ] Create `infrastructure/` directory
- [ ] Create `infrastructure/__init__.py`
- [ ] Create `infrastructure/postgresql.py`:
  - [ ] Extract `PostgreSQLRepository` class from rmhgeoapi
  - [ ] Remove Job/Task-specific repository classes
  - [ ] Keep core connection management (~300 lines)
  - [ ] Keep managed identity support
  - [ ] Keep connection pooling logic
  - [ ] Test with existing config.py connection string
- [ ] Copy `util_logger.py` to root:
  - [ ] Copy LoggerFactory class as-is
  - [ ] Copy JSON formatter for Application Insights
  - [ ] No modifications needed (self-contained)
- [ ] Test PostgreSQLRepository connection:
  - [ ] Test password-based authentication
  - [ ] Test connection pooling
  - [ ] Test error handling
  - [ ] Verify works with pgstac schema

**Source Files**:
- `/Users/robertharrison/python_builds/rmhgeoapi/infrastructure/postgresql.py`
- `/Users/robertharrison/python_builds/rmhgeoapi/util_logger.py`

**Implementation Notes**:
```python
# infrastructure/postgresql.py
from config import get_postgres_connection_string
from util_logger import LoggerFactory

class PostgreSQLRepository:
    """Shared PostgreSQL connection management for read-only access."""

    def __init__(self, connection_string=None, schema_name='pgstac'):
        self.connection_string = connection_string or get_postgres_connection_string()
        self.schema_name = schema_name
        self.logger = LoggerFactory.get_logger(__name__)

    def _get_connection(self):
        """Get database connection with error handling."""
        # Connection pooling logic
        # Managed identity token refresh
        # Error handling
```

### 2.2 STAC Query Functions (2-3 hours)

**Goal**: Extract 4 read-only query functions from pgstac_bootstrap.py into new stac_queries.py module.

**Tasks**:
- [ ] Create `infrastructure/stac_queries.py`
- [ ] Extract `get_all_collections()` function:
  - [ ] Source: rmhgeoapi/infrastructure/pgstac_bootstrap.py line ~1951
  - [ ] Remove ETL-specific dependencies
  - [ ] Accept PostgreSQLRepository as parameter
  - [ ] Test with pgstac.collections table
- [ ] Extract `get_collection(collection_id)` function:
  - [ ] Source: rmhgeoapi/infrastructure/pgstac_bootstrap.py line ~1095
  - [ ] Returns single collection JSON
  - [ ] Test with existing collections
- [ ] Extract `get_collection_items(collection_id, limit, offset)` function:
  - [ ] Source: rmhgeoapi/infrastructure/pgstac_bootstrap.py line ~1143
  - [ ] Returns GeoJSON FeatureCollection
  - [ ] Test pagination
  - [ ] Test with geometry serialization
- [ ] Extract `get_item_by_id(collection_id, item_id)` function:
  - [ ] Source: rmhgeoapi/infrastructure/pgstac_bootstrap.py line ~1722
  - [ ] Returns single STAC Item
  - [ ] Test with existing items
- [ ] Add comprehensive error handling:
  - [ ] Collection not found (404)
  - [ ] Item not found (404)
  - [ ] Database connection errors (500)
  - [ ] Query timeouts (503)
- [ ] Test all 4 functions independently with live database

**Source File**:
- `/Users/robertharrison/python_builds/rmhgeoapi/infrastructure/pgstac_bootstrap.py`

**Function Signatures**:
```python
# infrastructure/stac_queries.py
from infrastructure.postgresql import PostgreSQLRepository
from util_logger import LoggerFactory

def get_all_collections(repo: PostgreSQLRepository = None) -> dict:
    """Query all collections from pgstac.collections with item counts."""

def get_collection(collection_id: str, repo: PostgreSQLRepository = None) -> dict:
    """Get single collection by ID."""

def get_collection_items(
    collection_id: str,
    limit: int = 100,
    offset: int = 0,
    repo: PostgreSQLRepository = None
) -> dict:
    """Get items from collection with pagination."""

def get_item_by_id(
    collection_id: str,
    item_id: str,
    repo: PostgreSQLRepository = None
) -> dict:
    """Get single item by ID."""
```

### 2.3 STAC API Module Migration (1-2 hours)

**Goal**: Copy entire stac_api/ module and update imports to use new infrastructure.

**Tasks**:
- [ ] Copy `stac_api/` directory from rmhgeoapi:
  - [ ] `__init__.py` (23 lines)
  - [ ] `config.py` (46 lines)
  - [ ] `service.py` (315 lines)
  - [ ] `triggers.py` (518 lines)
- [ ] Update `stac_api/service.py` imports:
  ```python
  # OLD:
  from infrastructure.pgstac_bootstrap import get_all_collections, ...

  # NEW:
  from infrastructure.stac_queries import get_all_collections, ...
  ```
- [ ] Update `stac_api/config.py` if needed:
  - [ ] Verify environment variable reading
  - [ ] Add STAC catalog metadata to root config.py
- [ ] Update `stac_api/__init__.py`:
  - [ ] Export get_stac_triggers function
  - [ ] Export STACService class
  - [ ] Export STACConfig class
- [ ] Test service layer methods:
  - [ ] test_get_catalog()
  - [ ] test_get_collections()
  - [ ] test_get_collection_items()

**Source Directory**:
- `/Users/robertharrison/python_builds/rmhgeoapi/stac_api/`

### 2.4 Azure Functions Integration (1 hour)

**Goal**: Register STAC API endpoints in function_app.py alongside OGC Features.

**Tasks**:
- [ ] Update `function_app.py`:
  ```python
  from stac_api import get_stac_triggers

  # Register STAC API endpoints
  stac_triggers = get_stac_triggers()

  @app.route(route="stac", methods=["GET"])
  def stac_landing_page(req):
      return stac_triggers[0]['handler'](req)

  @app.route(route="stac/conformance", methods=["GET"])
  def stac_conformance(req):
      return stac_triggers[1]['handler'](req)

  # ... register all 6 STAC endpoints
  ```
- [ ] Set auth_level=ANONYMOUS for all STAC endpoints
- [ ] Verify unique function names (no conflicts with OGC)
- [ ] Update local.settings.json with STAC config:
  ```json
  "STAC_CATALOG_ID": "rmh-geospatial-stac",
  "STAC_CATALOG_TITLE": "Geospatial STAC API",
  "STAC_DESCRIPTION": "SpatioTemporal Asset Catalog for raster and vector datasets"
  ```

**STAC Endpoints to Register** (6 total):
1. `GET /api/stac` - Landing page (catalog root)
2. `GET /api/stac/conformance` - Conformance classes
3. `GET /api/stac/collections` - Collections list
4. `GET /api/stac/collections/{collection_id}` - Collection detail
5. `GET /api/stac/collections/{collection_id}/items` - Items list
6. `GET /api/stac/collections/{collection_id}/items/{item_id}` - Item detail

### 2.5 Testing & Documentation (2-3 hours)

**Local Testing**:
- [ ] Start local Functions runtime
- [ ] Verify all 13 endpoints register (7 OGC + 6 STAC)
- [ ] Test STAC landing page: `curl http://localhost:7071/api/stac`
- [ ] Test STAC conformance: `curl http://localhost:7071/api/stac/conformance`
- [ ] Test STAC collections: `curl http://localhost:7071/api/stac/collections`
- [ ] Test STAC collection detail: `curl http://localhost:7071/api/stac/collections/{id}`
- [ ] Test STAC items: `curl http://localhost:7071/api/stac/collections/{id}/items`
- [ ] Test STAC single item: `curl http://localhost:7071/api/stac/collections/{id}/items/{item_id}`
- [ ] Test pagination: `?limit=50&offset=100`
- [ ] Verify STAC JSON response structure
- [ ] Verify link relations (self, root, parent, etc.)

**Standards Compliance**:
- [ ] Test with STAC Validator CLI:
  ```bash
  pip install stac-validator
  stac-validator http://localhost:7071/api/stac
  ```
- [ ] Test with pystac-client:
  ```python
  from pystac_client import Client
  catalog = Client.open("http://localhost:7071/api/stac")
  collections = list(catalog.get_collections())
  ```
- [ ] Verify STAC API v1.0.0 compliance

**Azure Deployment**:
- [ ] Update environment variables in rmhgeoapifn:
  ```bash
  az functionapp config appsettings set \
    --name rmhgeoapifn \
    --resource-group rmhazure_rg \
    --settings \
      STAC_CATALOG_ID="rmh-geospatial-stac" \
      STAC_CATALOG_TITLE="Geospatial STAC API"
  ```
- [ ] Deploy to Azure: `func azure functionapp publish rmhgeoapifn`
- [ ] Test all 6 STAC endpoints in production
- [ ] Verify Application Insights logging

**Documentation Updates**:
- [ ] Update README.md with STAC API endpoints
- [ ] Update ARCHITECTURE.md with STAC components:
  - [ ] Add stac_api/ module description
  - [ ] Add infrastructure/stac_queries.py description
  - [ ] Add PostgreSQLRepository description
  - [ ] Update database schema section (pgstac schema)
  - [ ] Add STAC API data flow diagram
- [ ] Add STAC API examples to README:
  - [ ] List collections example
  - [ ] Search items example
  - [ ] Pagination example
  - [ ] pystac-client usage example
- [ ] Document STAC Browser integration (future)

---

## 📋 Phase 2 Checklist Summary

**Infrastructure** (2-3 hours):
- [ ] Create infrastructure/ directory
- [ ] Extract PostgreSQLRepository class
- [ ] Copy util_logger.py module
- [ ] Test database connectivity

**STAC Queries** (2-3 hours):
- [ ] Create infrastructure/stac_queries.py
- [ ] Extract 4 query functions from pgstac_bootstrap.py
- [ ] Remove ETL dependencies
- [ ] Test all queries independently

**STAC Module** (1-2 hours):
- [ ] Copy stac_api/ directory
- [ ] Update imports to use new infrastructure
- [ ] Test service layer methods

**Integration** (1 hour):
- [ ] Register 6 STAC endpoints in function_app.py
- [ ] Update configuration
- [ ] Verify unique function names

**Testing** (2-3 hours):
- [ ] Local endpoint testing
- [ ] STAC standards compliance validation
- [ ] Azure deployment
- [ ] Documentation updates

**Total Estimated Time**: 7-11 hours

---

## 🎯 Success Criteria

### Phase 1 Requirements (OGC Features) - ✅ COMPLETE
- ✅ All 7 OGC Features API endpoints operational (including /health)
- ✅ Returns OGC API - Features Core 1.0 compliant responses
- ✅ Serves data from PostgreSQL `geo` schema (20 collections)
- ✅ Supports all query parameters (bbox, datetime, filters, sorting)
- ✅ Handles pagination correctly (limit, offset)
- ✅ Returns valid GeoJSON with proper geometry serialization
- ✅ Managed identity authentication ready (password auth working)
- ✅ Independent deployment to rmhgeoapifn Function App
- ✅ CORS configured for static website
- ✅ Application Insights logging enabled
- ✅ Query timeout protection (30 seconds)
- ✅ Proper error handling and HTTP status codes
- ✅ Performance acceptable (<2s for typical queries)
- ✅ Comprehensive README.md and ARCHITECTURE.md

### Phase 2 Requirements (STAC API) - 🎯 TARGET
- [ ] All 6 STAC API endpoints operational
- [ ] Returns STAC API v1.0.0 compliant responses
- [ ] Serves data from PostgreSQL `pgstac` schema
- [ ] Supports pagination (limit, offset)
- [ ] Returns valid STAC Collection and Item JSON
- [ ] STAC Validator compliance verified
- [ ] pystac-client compatibility tested
- [ ] Documentation updated for dual-API architecture

---

## 📊 Progress Tracking

### Phase 1: OGC Features API
**Status**: ✅ COMPLETE (100%)
**Effort**: ~8 hours actual (vs. 14-20 estimated for full project)

### Phase 2: STAC API
**Status**: 🎯 READY TO BEGIN (0%)
**Estimated Effort**: 7-11 hours
**Tasks**:
- Infrastructure: 0/20 tasks
- STAC Queries: 0/12 tasks
- STAC Module: 0/8 tasks
- Integration: 0/5 tasks
- Testing: 0/15 tasks

**Total Tasks Remaining**: ~60 tasks

---

## 🚨 Critical Notes

### Do NOT Copy (ETL-Specific)
- ❌ CoreMachine job/task processing code
- ❌ Platform layer orchestration
- ❌ Service Bus integration
- ❌ Storage account utilities (beyond managed identity)
- ❌ ETL processing logic
- ❌ `service_stac.py` - STAC Item creation (write operations)
- ❌ `triggers/stac_*.py` - Setup, initialization, data ingestion
- ❌ `infrastructure/pgstac_repository.py` - Write operations

### Do Copy (Read-Only API Components)
- ✅ `stac_api/` module (all 4 files) - API layer
- ✅ PostgreSQLRepository class (connection management)
- ✅ 4 query functions from pgstac_bootstrap.py
- ✅ Logger module (util_logger.py)
- ✅ Configuration patterns (managed identity support)

### Key Design Decisions
- **Read-Only APIs**: No write operations to database
- **Shared Database**: Uses same PostgreSQL instance as ETL system
- **Dual Schema Access**: `geo` schema (OGC) + `pgstac` schema (STAC)
- **Independent Scaling**: Can scale separately from ETL workloads
- **Standards Compliance**: OGC API - Features Core 1.0 + STAC API v1.0.0
- **Microservices Architecture**: Preparing for Azure API Management routing
- **Single Function App**: Both APIs in rmhgeoapifn (13 endpoints total)

---

**Current Status**: Phase 1 Complete ✅ | Phase 2 Ready 🎯
**Next Step**: Begin Phase 2.1 - Infrastructure Layer (PostgreSQL Repository)
