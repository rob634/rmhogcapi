# Technical Architecture - rmhogcapi

**OGC Features + STAC API Azure Function App**

---

## System Overview

rmhogcapi is a serverless Azure Function App that provides read-only access to geospatial data stored in Azure PostgreSQL with PostGIS and pgSTAC extensions. The application implements two standards-compliant APIs:

1. **OGC API - Features Core 1.0**: Vector feature access from PostGIS (`geo` schema)
2. **STAC API v1.0.0**: SpatioTemporal Asset Catalog for raster and vector metadata (`pgstac` schema)

Both APIs are served from a single Function App deployment with 13 total HTTP endpoints (6 OGC + 6 STAC + 1 health).

### Design Principles

1. **Standards Compliance**: Strict adherence to OGC API - Features Core 1.0 and STAC API v1.0.0
2. **Read-Only Operations**: No write access to database
3. **Stateless Architecture**: Each request is independent
4. **Microservices Pattern**: Dedicated service for geospatial data access
5. **Cloud-Native**: Built for Azure Functions consumption model
6. **Dual Schema Architecture**: `geo` schema for PostGIS vectors, `pgstac` schema for STAC catalog

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Client Applications                            │
│  (Web Browsers, GIS Tools, pystac-client, Static Websites)          │
└──────────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                 Azure Function App (rmhgeoapifn)                     │
│                        13 HTTP Endpoints Total                       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    OGC Features API (6 endpoints)              │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  HTTP Triggers (ogc_features/triggers.py)                │ │ │
│  │  │  - Landing Page  - Conformance  - Collections           │ │ │
│  │  │  - Collection    - Items        - Single Feature        │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │            ▼                                                   │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  Service Layer (ogc_features/service.py)                 │ │ │
│  │  │  Repository Layer (ogc_features/repository.py)           │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     STAC API (6 endpoints)                     │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  HTTP Triggers (stac_api/triggers.py)                    │ │ │
│  │  │  - Landing Page  - Conformance  - Collections           │ │ │
│  │  │  - Collection    - Items        - Single Item           │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │            ▼                                                   │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  Service Layer (stac_api/service.py)                     │ │ │
│  │  │  Query Functions (infrastructure/stac_queries.py)        │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Shared Infrastructure Layer                       │ │
│  │  PostgreSQLRepository (infrastructure/postgresql.py)           │ │
│  │  - Per-request connections  - Managed identity support        │ │
│  │  - psycopg3 driver          - SQL injection prevention        │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                                │
                                │ PostgreSQL Protocol (TLS)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│           Azure Database for PostgreSQL (rmhpgflex)                  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    geo Schema (PostGIS)                        │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │
│  │  │  Table 1     │  │  Table 2     │  │  Table 20    │        │ │
│  │  │  (geom col)  │  │  (geom col)  │  │  (geom col)  │        │ │
│  │  │  GiST index  │  │  GiST index  │  │  GiST index  │        │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   pgstac Schema (pgSTAC v0.9.8)                │ │
│  │  ┌─────────────────┐  ┌─────────────────┐                     │ │
│  │  │  collections    │  │  items          │                     │ │
│  │  │  (JSONB)        │  │  (JSONB+geom)   │                     │ │
│  │  └─────────────────┘  └─────────────────┘                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### OGC Features API Components

#### Layer 1: HTTP Triggers

**File**: `ogc_features/triggers.py`

**Purpose**: Handle HTTP requests and route to appropriate service methods

**Components**:
- `OGCLandingPageTrigger`: API entry point with metadata
- `OGCConformanceTrigger`: Conformance class declaration
- `OGCCollectionsTrigger`: List all collections
- `OGCCollectionTrigger`: Single collection metadata
- `OGCItemsTrigger`: Feature query with filters
- `OGCItemTrigger`: Single feature retrieval

**Key Responsibilities**:
- Parse HTTP query parameters
- Validate request format
- Extract route parameters (collection_id, feature_id)
- Generate base URL from request context
- Error handling and HTTP status codes
- Return OGC-compliant responses

**Design Pattern**: Factory pattern for trigger registration

---

#### Layer 2: Service Layer

**File**: `ogc_features/service.py`

**Purpose**: Implement business logic and OGC specification compliance

**Key Class**: `OGCFeaturesService`

**Key Methods**:
- `get_landing_page()`: Generate API landing page with links
- `get_conformance()`: Return conformance classes
- `list_collections()`: Aggregate collection metadata
- `get_collection()`: Single collection with extent
- `query_features()`: Feature query with pagination
- `get_feature()`: Single feature retrieval

**Key Responsibilities**:
- OGC API specification compliance
- Link generation (self, next, prev, alternate)
- Pagination logic (limit, offset)
- URL construction for responses
- Data transformation (repository → OGC models)
- Response serialization

**Design Pattern**: Service pattern with dependency injection

---

#### Layer 3: Repository Layer

**File**: `ogc_features/repository.py`

**Purpose**: Direct data access to PostgreSQL with PostGIS

**Key Class**: `OGCFeaturesRepository`

**Key Methods**:
- `list_collections()`: Query geometry_columns view
- `get_collection_metadata()`: Compute extent, count, datetime columns
- `query_features()`: Execute spatial and attribute filters
- `get_feature_by_id()`: Single feature lookup
- `_detect_geometry_column()`: Auto-detect geom/geometry/shape
- `_detect_datetime_columns()`: Find timestamp columns
- `_has_spatial_index()`: Validate GiST indexes

**Key Responsibilities**:
- SQL query composition (injection-safe)
- PostGIS function calls (ST_AsGeoJSON, ST_Intersects, ST_Extent)
- Geometry optimization (simplification, precision)
- Spatial filter construction (bbox)
- Temporal filter construction (datetime)
- Attribute filter construction (key=value)
- Connection management (per-request connections)

**Design Pattern**: Repository pattern with SQL composition

**SQL Safety**:
```python
from psycopg import sql

# SAFE - uses SQL composition
query = sql.SQL("SELECT * FROM {schema}.{table} WHERE {column} = %s").format(
    schema=sql.Identifier(schema_name),
    table=sql.Identifier(table_name),
    column=sql.Identifier(column_name)
)
cursor.execute(query, (value,))

# UNSAFE - string concatenation (NEVER used)
query = f"SELECT * FROM {schema}.{table}"  # ❌ SQL injection risk
```

---

#### Layer 4: Data Models

**File**: `ogc_features/models.py`

**Purpose**: Pydantic models for request/response validation

**Key Models**:
- `OGCLandingPage`: API root response
- `OGCConformance`: Conformance declaration
- `OGCCollection`: Collection metadata
- `OGCCollectionList`: List of collections
- `OGCFeatureCollection`: GeoJSON FeatureCollection
- `OGCQueryParameters`: Request parameter validation
- `OGCLink`: RFC 8288 Web Links

**Key Responsibilities**:
- Request parameter validation
- Response serialization
- Type safety
- JSON schema generation
- Default value handling

**Design Pattern**: Pydantic BaseModel with validators

---

### STAC API Components

#### Infrastructure Layer: STAC Queries

**File**: `infrastructure/stac_queries.py`

**Purpose**: Read-only query functions for pgSTAC database schema

**Key Functions**:
- `get_all_collections()`: Query all STAC collections with item counts
- `get_collection(collection_id)`: Get single STAC collection by ID
- `get_collection_items(collection_id, limit, bbox, datetime)`: Query items in collection
- `get_item_by_id(item_id, collection_id)`: Get single STAC item by ID

**Key Responsibilities**:
- Direct SQL queries to `pgstac.collections` and `pgstac.items` tables
- JSONB content extraction and merging
- Geometry reconstruction from separate columns
- Item count aggregation
- GeoJSON serialization via `ST_AsGeoJSON()`

**Design Pattern**: Functional approach with PostgreSQLRepository injection

**Data Structure**:
```python
# pgSTAC v0.9.8 stores STAC data in JSONB columns
# Collections: content JSONB contains full STAC collection
# Items: content JSONB + separate id, collection, geometry columns

# Reconstruction query:
content || jsonb_build_object(
    'id', id,
    'collection', collection,
    'geometry', ST_AsGeoJSON(geometry)::jsonb,
    'type', 'Feature'
)
```

---

#### STAC HTTP Triggers

**File**: `stac_api/triggers.py`

**Purpose**: HTTP endpoint handlers for STAC API

**Components**:
- Landing page trigger: STAC catalog root
- Conformance trigger: STAC conformance classes
- Collections list trigger: List all STAC collections
- Single collection trigger: Collection metadata
- Items query trigger: Query STAC items with pagination
- Single item trigger: Retrieve single STAC item

**Key Responsibilities**:
- Parse HTTP query parameters (limit, bbox, datetime)
- Extract route parameters (collection_id, item_id)
- Call service layer methods
- Return STAC-compliant JSON responses
- Error handling and HTTP status codes

**Design Pattern**: Factory pattern for trigger registration

---

#### STAC Service Layer

**File**: `stac_api/service.py`

**Purpose**: STAC specification compliance and business logic

**Key Class**: `STACService`

**Key Methods**:
- `get_landing_page()`: Generate STAC catalog root with links
- `get_conformance()`: Return STAC conformance classes
- `list_collections()`: Get all collections with links
- `get_collection()`: Single collection with links
- `query_items()`: Query items with pagination
- `get_item()`: Single item retrieval

**Key Responsibilities**:
- STAC API v1.0.0 specification compliance
- Link generation (self, root, parent, items, collection)
- Pagination logic
- URL construction for STAC links
- Response formatting

**Design Pattern**: Service pattern with dependency injection

---

#### Shared Infrastructure: PostgreSQL Repository

**File**: `infrastructure/postgresql.py`

**Purpose**: Shared database connection management for both APIs

**Key Class**: `PostgreSQLRepository`

**Key Features**:
- **Per-Request Connections**: No connection pooling (serverless-friendly)
- **Schema Support**: Configurable schema (geo or pgstac)
- **Managed Identity**: Support for Azure AD authentication
- **Connection Context Managers**: Safe resource cleanup
- **SQL Composition**: Injection-safe queries via psycopg.sql

**Connection Strategy**:
```python
# Each request creates new connection
with repo._get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()
    conn.commit()
# Connection automatically closed
```

**Dual Schema Usage**:
- OGC Features: `PostgreSQLRepository(schema_name='geo')`
- STAC API: `PostgreSQLRepository(schema_name='pgstac')`

---

## Data Flow

### Request Flow: Query Features

```
1. HTTP Request
   GET /api/features/collections/acled_serial_001/items?bbox=30,45,35,50&limit=100

2. HTTP Trigger (triggers.py)
   ├─ Parse query parameters (bbox, limit)
   ├─ Extract route parameter (collection_id)
   ├─ Validate with OGCQueryParameters model
   └─ Call service.query_features()

3. Service Layer (service.py)
   ├─ Call repository.query_features()
   ├─ Generate pagination links (self, next, prev)
   ├─ Construct absolute URLs
   └─ Return OGCFeatureCollection model

4. Repository Layer (repository.py)
   ├─ Build SQL query with psycopg.sql composition
   ├─ Add spatial filter (ST_Intersects with bbox)
   ├─ Add LIMIT/OFFSET for pagination
   ├─ Execute query with parameters
   ├─ Serialize geometry as GeoJSON (ST_AsGeoJSON)
   └─ Return list of features + total count

5. PostgreSQL (PostGIS)
   ├─ Execute query with spatial index (GiST)
   ├─ Apply filters
   ├─ Generate GeoJSON geometry
   └─ Return result set

6. HTTP Response
   ├─ Serialize OGCFeatureCollection to JSON
   ├─ Set Content-Type: application/geo+json
   ├─ Set HTTP status code 200
   └─ Return to client
```

---

## Database Schema

### PostgreSQL Configuration

**Database**: `geopgflex`
**Schemas**:
- `geo` - PostGIS vector features (OGC Features API)
- `pgstac` - pgSTAC v0.9.8 catalog (STAC API)

**Extensions**:
- PostGIS 3.0+ (`geo` schema)
- pgSTAC 0.9.8+ (`pgstac` schema)

---

### OGC Features Schema (`geo`)

#### Table Requirements

Each vector table in the `geo` schema must have:

1. **Geometry Column**:
   - Name: `geom`, `geometry`, or `shape` (auto-detected)
   - Type: GEOMETRY (any PostGIS geometry type)
   - SRID: Typically 4326 (WGS84)
   - Registered in `geometry_columns` view

2. **Primary Key** (recommended):
   - Name: typically `id` or `objectid`
   - Type: INTEGER or SERIAL
   - Used for single feature retrieval

3. **Spatial Index** (recommended):
   - Type: GiST
   - Column: geometry column
   - Dramatically improves spatial query performance

4. **Timestamp Columns** (optional):
   - Auto-detected for temporal filtering
   - Names containing: date, time, created, updated

### Example Table Definition

```sql
CREATE TABLE geo.my_collection (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    year INTEGER,
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    geom GEOMETRY(Point, 4326)
);

-- Create spatial index
CREATE INDEX idx_my_collection_geom
ON geo.my_collection
USING GiST (geom);

-- Register in geometry_columns (automatic with PostGIS)
```

---

### STAC Schema (`pgstac`)

#### Table Structure

The `pgstac` schema is managed by the pgSTAC extension v0.9.8. This project uses **read-only** access to pgSTAC tables - all write operations are performed by the rmhgeoapi ETL system.

**Key Tables**:

1. **`pgstac.collections`**:
   - Stores STAC collection metadata as JSONB
   - Columns: `id` (text), `content` (jsonb)
   - `content` contains complete STAC Collection object

2. **`pgstac.items`**:
   - Stores STAC items with separate columns for efficient querying
   - Columns: `id` (text), `collection` (text), `geometry` (geometry), `datetime` (timestamptz), `content` (jsonb)
   - `content` contains STAC Item properties and assets
   - Geometry stored separately for spatial indexing

#### Data Structure

```sql
-- pgstac.collections table
SELECT id, content FROM pgstac.collections LIMIT 1;
-- Returns:
-- id: 'namangan_test_1'
-- content: {"id": "namangan_test_1", "type": "Collection", "links": [...], ...}

-- pgstac.items table (simplified)
SELECT id, collection, ST_AsText(geometry), content->>'properties'
FROM pgstac.items LIMIT 1;
-- Returns:
-- id: 'item-123'
-- collection: 'namangan_test_1'
-- geometry: 'POLYGON((...))'
-- properties: '{"datetime": "2024-01-01T00:00:00Z", ...}'
```

#### STAC Item Reconstruction

Since pgSTAC stores items with split fields, queries must reconstruct complete STAC items:

```sql
-- Reconstruct full STAC item
SELECT content ||
    jsonb_build_object(
        'id', id,
        'collection', collection,
        'geometry', ST_AsGeoJSON(geometry)::jsonb,
        'type', 'Feature',
        'stac_version', COALESCE(content->>'stac_version', '1.0.0')
    ) as item
FROM pgstac.items
WHERE collection = 'namangan_test_1';
```

**Why this approach?**:
- Enables efficient spatial queries on geometry column
- Enables temporal queries on datetime column
- Enables collection filtering on collection column
- Maintains full STAC spec compliance in content JSONB

---

## PostGIS Query Optimization

### Spatial Queries

**Bounding Box Filter**:
```sql
SELECT
    id,
    ST_AsGeoJSON(geom, 6) as geometry,
    name,
    description
FROM geo.my_collection
WHERE ST_Intersects(
    geom,
    ST_MakeEnvelope(minx, miny, maxx, maxy, 4326)
)
LIMIT 100 OFFSET 0;
```

**Geometry Simplification**:
```sql
SELECT
    id,
    ST_AsGeoJSON(
        ST_Simplify(geom, 0.001),  -- Tolerance in degrees
        6                          -- Precision
    ) as geometry,
    name
FROM geo.my_collection;
```

**Performance Considerations**:
- GiST indexes enable efficient spatial filtering (O(log n) vs O(n))
- `ST_AsGeoJSON` generates GeoJSON directly in database
- Pagination prevents memory issues with large datasets
- Query timeout prevents long-running queries

---

## Configuration Architecture

### Configuration Hierarchy

```
┌────────────────────────────────────────────────────────────────┐
│              Application Configuration (config.py)             │
│  - PostgreSQL connection string generation                    │
│  - Password URL encoding                                      │
│  - Managed identity support                                   │
└────────────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┴──────────────┐
           ▼                             ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  OGC Features Config     │  │  STAC API Config         │
│  (ogc_features/config)   │  │  (stac_api/config.py)    │
│  - geo schema            │  │  - pgstac schema         │
│  - Geometry columns      │  │  - Catalog metadata      │
│  - Query limits          │  │  - Item limits           │
└──────────────────────────┘  └──────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│            Environment Variables / Azure App Settings          │
│  - POSTGIS_HOST, POSTGIS_PORT, POSTGIS_DATABASE               │
│  - OGC_SCHEMA, OGC_DEFAULT_LIMIT (OGC Features)               │
│  - STAC_CATALOG_ID, STAC_BASE_URL (STAC API)                  │
└────────────────────────────────────────────────────────────────┘
```

### Configuration Loading

**Local Development**:
- Azure Functions runtime reads `local.settings.json`
- Values exposed as environment variables
- Pydantic validates and parses values

**Azure Production**:
- Azure App Settings exposed as environment variables
- Same Pydantic validation
- Managed identity support available

---

## Security Architecture

### Authentication Flow (Current)

```
Client Request
     │
     ▼
Azure Functions (Anonymous)
     │
     ▼
PostgreSQL (Password Auth)
     │
     └─ SSL/TLS Required
     └─ Firewall Rules
```

### Authentication Flow (Future with Managed Identity)

```
Client Request
     │
     ▼
Azure AD Token Validation
     │
     ▼
Azure Functions
     │
     ▼
Azure Managed Identity
     │
     ▼
PostgreSQL (AAD Token)
```

### Security Measures

1. **SQL Injection Prevention**:
   - All queries use `psycopg.sql.SQL()` composition
   - Parameters passed separately (never concatenated)

2. **TLS Encryption**:
   - PostgreSQL connections require SSL (`sslmode=require`)
   - HTTPS enforced for all API endpoints

3. **Password Handling**:
   - URL-encoded to handle special characters
   - Never logged or exposed in responses
   - Stored in Azure App Settings (encrypted at rest)

4. **Input Validation**:
   - Pydantic models validate all inputs
   - Type checking and range validation
   - Malicious input rejected before database access

5. **Query Timeout**:
   - 30-second default prevents DOS via expensive queries
   - Configurable via `OGC_QUERY_TIMEOUT`

---

## Error Handling

### Error Response Format

All errors return OGC-compliant JSON:

```json
{
  "code": "ErrorCode",
  "description": "Human-readable error message"
}
```

### Error Types

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | InvalidParameter | Invalid query parameter value |
| 404 | NotFound | Collection or feature not found |
| 500 | InternalServerError | Database or application error |
| 503 | ServiceUnavailable | Database timeout or unavailable |

### Error Handling Strategy

**Layer 1 (Triggers)**:
- Catch all exceptions
- Log full stack trace
- Return sanitized error to client
- Set appropriate HTTP status code

**Layer 2 (Service)**:
- Validate business rules
- Raise specific exceptions
- Pass through repository exceptions

**Layer 3 (Repository)**:
- Catch database exceptions
- Wrap in domain exceptions
- Log query failures

---

## Performance Characteristics

### Latency Targets

| Operation | Target | Notes | API |
|-----------|--------|-------|-----|
| Landing Page | <100ms | Static response | Both |
| List Collections (OGC) | <500ms | Queries geometry_columns view | OGC |
| List Collections (STAC) | <1s | Queries pgstac with aggregation | STAC |
| Collection Metadata | <1s | Computes extent and count | Both |
| Query Features (100) | <2s | With spatial index | OGC |
| Query STAC Items (100) | <2s | JSONB reconstruction | STAC |
| Single Feature/Item | <500ms | Primary key lookup | Both |

### Scalability

**Horizontal Scaling**:
- Azure Functions auto-scales based on load
- Each function instance is stateless
- No shared state between instances

**Database Connections**:
- **Per-Request Strategy**: Each request creates new connection
- **No Connection Pooling**: Suitable for serverless Azure Functions
- Connections closed immediately after request completion
- Both APIs share PostgreSQLRepository infrastructure

**Caching Opportunities**:
- Collection metadata (extent, count) rarely changes
- Landing page and conformance are static
- Consider Azure Front Door or CDN for static responses

---

## Monitoring and Observability

### Application Insights Integration

**Metrics Collected**:
- Request duration (per endpoint)
- Response status codes
- Exception counts and types
- Database query execution time
- Function cold start duration

**Custom Events**:
- Collection queries (track popular collections)
- Spatial filter usage (bbox queries)
- Pagination patterns (limit/offset distribution)

### Health Monitoring

**Health Endpoint**: `/api/health`

Returns status for both APIs:
- OGC Features module loaded and schema configured
- STAC API module loaded and schema configured
- Reports 6 endpoints per API (12 total + 1 health = 13)
- PostgreSQL connectivity (future enhancement)

---

## Future Enhancements

### Completed Features

1. ✅ **STAC API Integration** (Completed 19 NOV 2025):
   - 6 STAC endpoints operational
   - pgSTAC v0.9.8 schema integration
   - Unified OGC + STAC service (13 total endpoints)
   - Shared infrastructure layer

### Planned Features

1. **Managed Identity Authentication**:
   - Eliminate password storage
   - Use Azure AD tokens for PostgreSQL

2. **Azure API Management**:
   - Centralized routing
   - Rate limiting and throttling
   - API key management
   - Custom domain support

4. **Response Caching**:
   - Azure Front Door integration
   - CDN for static responses
   - Collection metadata caching

5. **Advanced Filters**:
   - CQL2 filter expressions
   - Sortby parameter support
   - Property selection (fields parameter)

---

## Dependencies

### Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| azure-functions | >=1.18.0 | Azure Functions runtime |
| psycopg[binary] | >=3.1.0 | PostgreSQL driver |
| pydantic | >=2.5.0 | Data validation |
| pydantic-settings | >=2.1.0 | Settings management |
| azure-identity | >=1.15.0 | Managed identity support |

### Azure Services

| Service | Purpose |
|---------|---------|
| Azure Functions | Serverless compute |
| Azure PostgreSQL | Database with PostGIS |
| Application Insights | Monitoring and logging |
| Azure Storage | Function app storage |

---

## Development Workflow

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure local settings
cp local.settings.example.json local.settings.json
# Edit with PostgreSQL credentials

# 3. Start local server
func start

# 4. Test endpoints
curl http://localhost:7071/api/health
```

### Deployment Pipeline

```bash
# 1. Authenticate
az login

# 2. Configure app settings
az functionapp config appsettings set \
  --name rmhgeoapifn \
  --resource-group rmhazure_rg \
  --settings POSTGIS_HOST="..." POSTGIS_PASSWORD="..."

# 3. Deploy
func azure functionapp publish rmhgeoapifn

# 4. Verify
curl https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net/api/health
```

---

## Technical Debt and Known Limitations

### Current Limitations

1. **No Write Operations**: Read-only API by design
2. **No Authentication**: Public anonymous access
3. **No Rate Limiting**: Relies on Azure Functions throttling
4. **No Response Caching**: Every request hits database
5. **No CQL2 Filters**: Only basic attribute filters supported

### Technical Debt

1. **Connection Strategy**: Per-request connections by design (serverless-optimized, not debt)
2. **Error Messages**: Some PostgreSQL errors exposed to clients
3. **Link Generation**: Hardcoded URL construction (could use URI templates)
4. **Collection Discovery**: Queries geometry_columns and pgstac every time (could cache)
5. **STAC Search**: POST /search endpoint not implemented yet

---

## Standards Compliance

### OGC API - Features Core 1.0

**Implemented Conformance Classes**:
- ✅ Core
- ✅ GeoJSON
- ❌ HTML (not implemented)
- ❌ OpenAPI 3.0 (not implemented)

**Compliance Notes**:
- All endpoints follow OGC specification exactly
- GeoJSON responses conform to RFC 7946
- Link relations use RFC 8288 web linking
- CRS84 and EPSG:4326 supported

---

### STAC API v1.0.0

**Implemented Conformance Classes**:
- ✅ STAC API - Core
- ✅ STAC API - Collections
- ✅ STAC API - Features (GeoJSON)
- ❌ STAC API - Item Search (POST /search not yet implemented)

**Compliance Notes**:
- All endpoints follow STAC API v1.0.0 specification
- STAC Collections and Items conform to STAC v1.0.0
- pgSTAC v0.9.8 backend for data storage
- Link relations follow STAC spec requirements
- GeoJSON geometry reconstruction from pgSTAC storage

---

**Version**: 2.0.0 (Dual API)
**Last Updated**: 19 NOV 2025
**Architecture Status**: Production Ready
**Total Endpoints**: 13 (6 OGC + 6 STAC + 1 health)
