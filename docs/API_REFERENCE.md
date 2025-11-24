# API Reference

Complete reference for all rmhogcapi endpoints.

---

## Base URLs

| Environment | Base URL |
|-------------|----------|
| **Production** | `https://<your-function-app>.azurewebsites.net` |
| **Local Development** | `http://localhost:7071` |

---

## Endpoint Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| [`/api/health`](#health-endpoint) | GET | Service health check |
| [`/api/features`](#ogc-features-landing-page) | GET | OGC Features landing page |
| [`/api/features/conformance`](#ogc-conformance) | GET | OGC conformance classes |
| [`/api/features/collections`](#list-ogc-collections) | GET | List all vector collections |
| [`/api/features/collections/{collectionId}`](#get-ogc-collection) | GET | Collection metadata |
| [`/api/features/collections/{collectionId}/items`](#query-ogc-features) | GET | Query features from collection |
| [`/api/features/collections/{collectionId}/items/{featureId}`](#get-single-ogc-feature) | GET | Retrieve single feature |
| [`/api/stac`](#stac-catalog-landing-page) | GET | STAC catalog landing page |
| [`/api/stac/conformance`](#stac-conformance) | GET | STAC conformance classes |
| [`/api/stac/collections`](#list-stac-collections) | GET | List all STAC collections |
| [`/api/stac/collections/{collectionId}`](#get-stac-collection) | GET | STAC collection metadata |
| [`/api/stac/collections/{collectionId}/items`](#query-stac-items) | GET | Query STAC items |
| [`/api/stac/collections/{collectionId}/items/{itemId}`](#get-single-stac-item) | GET | Retrieve single STAC item |

**Total**: 13 endpoints (1 health + 6 OGC + 6 STAC)

---

## Health Endpoint

### GET /api/health

Service health check and status information for both APIs.

**Response** (200 OK):
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

**Example**:
```bash
curl https://<your-function-app>.azurewebsites.net/api/health
```

---

## OGC Features API

### OGC Features Landing Page

**GET** `/api/features`

Landing page with API metadata and links.

**Response** (200 OK):
```json
{
  "title": "OGC Features API",
  "description": "Standards-compliant OGC API - Features Core 1.0 implementation",
  "links": [
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/features",
      "rel": "self",
      "type": "application/json",
      "title": "This document"
    },
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/features/conformance",
      "rel": "conformance",
      "type": "application/json",
      "title": "OGC API conformance classes"
    },
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/features/collections",
      "rel": "data",
      "type": "application/json",
      "title": "Feature collections"
    }
  ]
}
```

---

### OGC Conformance

**GET** `/api/features/conformance`

OGC API conformance classes implemented by this server.

**Response** (200 OK):
```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
  ]
}
```

---

### List OGC Collections

**GET** `/api/features/collections`

List all available vector feature collections.

**Response** (200 OK):
```json
{
  "collections": [
    {
      "id": "acled_serial_001",
      "title": "Acled Serial 001",
      "description": "Vector features from acled_serial_001",
      "links": [
        {
          "href": "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001",
          "rel": "self",
          "type": "application/json"
        },
        {
          "href": "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items",
          "rel": "items",
          "type": "application/geo+json"
        }
      ],
      "extent": {
        "spatial": {
          "bbox": [[-180, -90, 180, 90]],
          "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
        }
      },
      "itemType": "feature",
      "crs": ["http://www.opengis.net/def/crs/EPSG/0/4326"]
    }
  ],
  "links": [
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/features/collections",
      "rel": "self",
      "type": "application/json"
    }
  ]
}
```

---

### Get OGC Collection

**GET** `/api/features/collections/{collectionId}`

Get metadata for a specific collection.

**Path Parameters**:
- `collectionId` (string) - Collection identifier

**Response** (200 OK):
```json
{
  "id": "acled_serial_001",
  "title": "Acled Serial 001",
  "description": "Vector features from acled_serial_001",
  "links": [...],
  "extent": {
    "spatial": {
      "bbox": [[-180, -90, 180, 90]],
      "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
    }
  },
  "itemType": "feature",
  "crs": ["http://www.opengis.net/def/crs/EPSG/0/4326"]
}
```

**Example**:
```bash
curl https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001
```

---

### Query OGC Features

**GET** `/api/features/collections/{collectionId}/items`

Query features from a collection with optional filters.

**Path Parameters**:
- `collectionId` (string) - Collection identifier

**Query Parameters**:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `limit` | integer | Max features to return (default: 100, max: 10000) | `limit=50` |
| `offset` | integer | Skip N features (pagination) | `offset=100` |
| `bbox` | string | Bounding box filter (minx,miny,maxx,maxy) | `bbox=30,45,35,50` |
| `datetime` | string | Temporal filter (ISO 8601 interval) | `datetime=2022-01-01/2022-12-31` |
| `{property}` | string | Filter by property value | `year=2022&country=Ukraine` |

**Response** (200 OK - GeoJSON FeatureCollection):
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "1",
      "geometry": {
        "type": "Point",
        "coordinates": [34.5, 48.5]
      },
      "properties": {
        "year": 2022,
        "country": "Ukraine",
        "event_type": "Battle"
      }
    }
  ],
  "links": [
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items?limit=100&offset=0",
      "rel": "self",
      "type": "application/geo+json"
    },
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items?limit=100&offset=100",
      "rel": "next",
      "type": "application/geo+json"
    }
  ],
  "timeStamp": "2025-11-24T10:00:00Z",
  "numberMatched": 5000,
  "numberReturned": 100
}
```

**Examples**:

```bash
# Basic query (first 100 features)
curl "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items"

# Pagination
curl "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items?limit=50&offset=100"

# Spatial filter (bounding box)
curl "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items?bbox=30,45,35,50"

# Temporal filter
curl "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items?datetime=2022-01-01/2022-12-31"

# Property filter
curl "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items?year=2022&country=Ukraine"

# Combined filters
curl "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items?bbox=30,45,35,50&datetime=2022-01-01/2022-12-31&limit=200"
```

---

### Get Single OGC Feature

**GET** `/api/features/collections/{collectionId}/items/{featureId}`

Retrieve a single feature by ID.

**Path Parameters**:
- `collectionId` (string) - Collection identifier
- `featureId` (string) - Feature identifier

**Response** (200 OK - GeoJSON Feature):
```json
{
  "type": "Feature",
  "id": "12345",
  "geometry": {
    "type": "Point",
    "coordinates": [34.5, 48.5]
  },
  "properties": {
    "year": 2022,
    "country": "Ukraine",
    "event_type": "Battle"
  },
  "links": [
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items/12345",
      "rel": "self",
      "type": "application/geo+json"
    },
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001",
      "rel": "collection",
      "type": "application/json"
    }
  ]
}
```

**Example**:
```bash
curl https://<your-function-app>.azurewebsites.net/api/features/collections/acled_serial_001/items/12345
```

---

## STAC API

### STAC Catalog Landing Page

**GET** `/api/stac`

STAC catalog landing page with metadata and links.

**Response** (200 OK):
```json
{
  "id": "rmh-geospatial-stac",
  "type": "Catalog",
  "title": "RMH Geospatial STAC API",
  "description": "STAC catalog for geospatial raster and vector data",
  "stac_version": "1.0.0",
  "conformsTo": [
    "https://api.stacspec.org/v1.0.0/core",
    "https://api.stacspec.org/v1.0.0/collections"
  ],
  "links": [
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/stac",
      "rel": "self",
      "type": "application/json"
    },
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/stac/conformance",
      "rel": "conformance",
      "type": "application/json"
    },
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/stac/collections",
      "rel": "data",
      "type": "application/json"
    }
  ]
}
```

---

### STAC Conformance

**GET** `/api/stac/conformance`

STAC API conformance classes.

**Response** (200 OK):
```json
{
  "conformsTo": [
    "https://api.stacspec.org/v1.0.0/core",
    "https://api.stacspec.org/v1.0.0/collections",
    "https://api.stacspec.org/v1.0.0/ogcapi-features"
  ]
}
```

---

### List STAC Collections

**GET** `/api/stac/collections`

List all STAC collections.

**Response** (200 OK):
```json
{
  "collections": [
    {
      "id": "namangan_test_1",
      "type": "Collection",
      "title": "Namangan Test Collection",
      "description": "Test STAC collection for Namangan region",
      "stac_version": "1.0.0",
      "license": "proprietary",
      "extent": {
        "spatial": {
          "bbox": [[70.0, 40.0, 72.0, 42.0]]
        },
        "temporal": {
          "interval": [["2020-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]]
        }
      },
      "links": [
        {
          "href": "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1",
          "rel": "self",
          "type": "application/json"
        },
        {
          "href": "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items",
          "rel": "items",
          "type": "application/geo+json"
        }
      ]
    }
  ],
  "links": [
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/stac/collections",
      "rel": "self",
      "type": "application/json"
    }
  ]
}
```

---

### Get STAC Collection

**GET** `/api/stac/collections/{collectionId}`

Get metadata for a specific STAC collection.

**Path Parameters**:
- `collectionId` (string) - Collection identifier

**Response** (200 OK):
```json
{
  "id": "namangan_test_1",
  "type": "Collection",
  "title": "Namangan Test Collection",
  "description": "Test STAC collection for Namangan region",
  "stac_version": "1.0.0",
  "license": "proprietary",
  "extent": {
    "spatial": {
      "bbox": [[70.0, 40.0, 72.0, 42.0]]
    },
    "temporal": {
      "interval": [["2020-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]]
    }
  },
  "links": [...]
}
```

**Example**:
```bash
curl https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1
```

---

### Query STAC Items

**GET** `/api/stac/collections/{collectionId}/items`

Query STAC items from a collection.

**Path Parameters**:
- `collectionId` (string) - Collection identifier

**Query Parameters**:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `limit` | integer | Max items to return (default: 100) | `limit=50` |
| `offset` | integer | Skip N items (pagination) | `offset=100` |
| `bbox` | string | Bounding box filter (minx,miny,maxx,maxy) | `bbox=70,40,72,42` |
| `datetime` | string | Temporal filter (ISO 8601 interval) | `datetime=2022-01-01/2022-12-31` |

**Response** (200 OK - STAC ItemCollection):
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "stac_version": "1.0.0",
      "id": "namangan_20220615_s2",
      "collection": "namangan_test_1",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[...]]
      },
      "bbox": [70.5, 40.5, 71.5, 41.5],
      "properties": {
        "datetime": "2022-06-15T10:30:00Z",
        "platform": "sentinel-2",
        "instruments": ["msi"]
      },
      "assets": {
        "visual": {
          "href": "https://storage.example.com/namangan_20220615.tif",
          "type": "image/tiff; application=geotiff; profile=cloud-optimized",
          "roles": ["visual"]
        }
      },
      "links": [...]
    }
  ],
  "links": [
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items?limit=100&offset=0",
      "rel": "self",
      "type": "application/geo+json"
    },
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items?limit=100&offset=100",
      "rel": "next",
      "type": "application/geo+json"
    }
  ]
}
```

**Examples**:

```bash
# Basic query
curl "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items"

# Pagination
curl "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items?limit=50&offset=100"

# Spatial filter
curl "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items?bbox=70,40,72,42"

# Temporal filter
curl "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items?datetime=2022-01-01/2022-12-31"
```

---

### Get Single STAC Item

**GET** `/api/stac/collections/{collectionId}/items/{itemId}`

Retrieve a single STAC item by ID.

**Path Parameters**:
- `collectionId` (string) - Collection identifier
- `itemId` (string) - Item identifier

**Response** (200 OK - STAC Item):
```json
{
  "type": "Feature",
  "stac_version": "1.0.0",
  "id": "namangan_20220615_s2",
  "collection": "namangan_test_1",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[...]]
  },
  "bbox": [70.5, 40.5, 71.5, 41.5],
  "properties": {
    "datetime": "2022-06-15T10:30:00Z",
    "platform": "sentinel-2",
    "instruments": ["msi"]
  },
  "assets": {
    "visual": {
      "href": "https://storage.example.com/namangan_20220615.tif",
      "type": "image/tiff; application=geotiff; profile=cloud-optimized",
      "roles": ["visual"]
    }
  },
  "links": [
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items/namangan_20220615_s2",
      "rel": "self",
      "type": "application/geo+json"
    },
    {
      "href": "https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1",
      "rel": "collection",
      "type": "application/json"
    }
  ]
}
```

**Example**:
```bash
curl https://<your-function-app>.azurewebsites.net/api/stac/collections/namangan_test_1/items/namangan_20220615_s2
```

---

## Error Responses

### 404 Not Found

Resource not found (collection or item doesn't exist).

```json
{
  "code": "NotFound",
  "description": "Collection 'invalid_collection' not found"
}
```

### 400 Bad Request

Invalid query parameters.

```json
{
  "code": "BadRequest",
  "description": "Invalid bbox format. Expected: minx,miny,maxx,maxy"
}
```

### 500 Internal Server Error

Server-side error (database connection, query timeout, etc.).

```json
{
  "code": "InternalServerError",
  "description": "Database query failed"
}
```

---

## Response Headers

All endpoints return standard headers:

```
Content-Type: application/json
Access-Control-Allow-Origin: *
X-Request-Id: <unique-request-id>
```

---

## Rate Limiting

Currently no rate limiting is enforced. This may change in future versions.

---

## Standards Compliance

### OGC API - Features Core 1.0
- **Specification**: [OGC 17-069r4](https://docs.ogc.org/is/17-069r4/17-069r4.html)
- **GeoJSON**: [RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946)
- **CRS**: EPSG:4326 (WGS 84)

### STAC API v1.0.0
- **Specification**: [STAC API Spec](https://github.com/radiantearth/stac-api-spec)
- **STAC Version**: 1.0.0
- **Backend**: pgSTAC 0.9.8

---

## Client Libraries

### Python

**OGC Features API**:
```python
import requests

# List collections
response = requests.get("https://<your-function-app>.azurewebsites.net/api/features/collections")
collections = response.json()["collections"]

# Query features
features_url = f"https://<your-function-app>.azurewebsites.net/api/features/collections/{collection_id}/items"
params = {"limit": 100, "bbox": "30,45,35,50"}
response = requests.get(features_url, params=params)
features = response.json()["features"]
```

**STAC API**:
```python
from pystac_client import Client

# Open STAC catalog
catalog = Client.open("https://<your-function-app>.azurewebsites.net/api/stac")

# List collections
collections = list(catalog.get_collections())

# Get items from collection
collection = catalog.get_collection("namangan_test_1")
items = list(collection.get_items())
```

### JavaScript

```javascript
// OGC Features API
const response = await fetch('https://<your-function-app>.azurewebsites.net/api/features/collections');
const data = await response.json();
console.log(data.collections);

// STAC API
const stacResponse = await fetch('https://<your-function-app>.azurewebsites.net/api/stac/collections');
const stacData = await stacResponse.json();
console.log(stacData.collections);
```

---

## Next Steps

- **[Configuration](CONFIGURATION.md)** - Environment variable reference
- **[Deployment](DEPLOYMENT.md)** - Deploy to Azure
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues
