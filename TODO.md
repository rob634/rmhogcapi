# 📋 TODO - rmhogcapi Development Plan

**Date**: 24 NOV 2025
**Status**: Phase 1 ✅ | Phase 2 ✅ | Phase 3 (Conformance Fixes) 🎯

---

## 🎯 Project Goal

Create standalone Azure Function App serving two read-only geospatial APIs:
1. **OGC Features API** - Vector feature access (PostGIS `geo` schema)
2. **STAC API** - Spatiotemporal asset catalog (PostgreSQL `pgstac` schema)

---

## 📊 Current Status

### Phase 1: OGC Features API - ✅ COMPLETE
- 6 endpoints operational
- OGC API - Features Core 1.0 compliant
- Production deployed

### Phase 2: STAC API - ✅ COMPLETE
- 6 endpoints operational
- Basic STAC v1.0.0 structure
- Production deployed

### Phase 3: STAC Conformance Fixes - 🎯 NEXT
- OpenAPI endpoint missing
- Pagination `next` links missing
- Minor link relation fixes

---

## 🎯 Phase 3: STAC API Conformance Fixes

### Context

Code review on 24 NOV 2025 identified conformance gaps between the current STAC API implementation and the official STAC API v1.0.0 specification. The API is functional but claims conformance classes it doesn't fully implement.

**Conformance Classes Declared** (in `stac_api/service.py`):
```python
"conformsTo": [
    "https://api.stacspec.org/v1.0.0/core",
    "https://api.stacspec.org/v1.0.0/collections",
    "https://api.stacspec.org/v1.0.0/ogcapi-features",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
]
```

**Reference Specifications**:
- STAC API Core: https://github.com/radiantearth/stac-api-spec/tree/main/core
- STAC API OGC Features: https://github.com/radiantearth/stac-api-spec/tree/main/ogcapi-features
- OGC API Features Core 1.0: https://docs.ogc.org/is/17-069r4/17-069r4.html

---

### Production Verification (24 NOV 2025)

**Production URL**: `https://rmhgeoapifn-dydhe8dddef4f7bd.eastus-01.azurewebsites.net`

**Verified Gaps from Live Testing**:

| Test | Result | Gap Confirmed |
|------|--------|---------------|
| `GET /api/stac/api` | HTTP 404 | ✅ OpenAPI endpoint missing |
| Landing page `service-desc` link | Points to `https://stacspec.org/en/api/` | ✅ Should point to local `/api/stac/api` |
| Items with `?limit=2` (collection has 4 items) | Returns 2 items, no `next` link | ✅ Pagination links missing |
| Items response `numberMatched` | NOT PRESENT | ✅ Pagination metadata missing |
| Items response `numberReturned` | NOT PRESENT | ✅ Pagination metadata missing |
| Items with `?limit=2&offset=2` | Returns same 2 items (offset ignored) | ✅ Offset parameter not implemented |

**Working Features Verified**:
- ✅ Landing page returns valid STAC Catalog
- ✅ Collections list returns 4 collections with proper links
- ✅ Single collection detail with `items`, `parent`, `root` links
- ✅ Items endpoint returns valid GeoJSON FeatureCollection
- ✅ Single item with `self`, `parent`, `collection`, `root` links
- ✅ Rich STAC Item metadata (proj:*, raster:bands, assets)
- ✅ TiTiler integration links (preview, tilejson, thumbnail)
- ✅ `mosaic:search_id` in collection summaries (for TiTiler-pgSTAC)

---

### 3.1 Add OpenAPI Endpoint (REQUIRED - STAC Core Conformance)

**Problem**: STAC API Core requires a `GET /api` endpoint returning an OpenAPI 3.0/3.1 specification document. Currently missing entirely.

**Spec Requirement** (STAC API Core):
> "The STAC API landing page... MUST include a link with rel="service-desc" that links to an OpenAPI definition of the service."

**Current State**:
- No `/api/stac/api` endpoint exists
- The `service-desc` link in landing page points to external URL (`https://stacspec.org/en/api/`)
- This violates the spec which expects the link to point to the API's own OpenAPI definition

**Files to Modify**:
1. `stac_api/triggers.py` - Add new trigger class
2. `stac_api/service.py` - Add method to generate/return OpenAPI spec
3. `function_app.py` - Register new endpoint

**Implementation Steps**:

#### Step 1: Create OpenAPI Specification Document

Create a new file `stac_api/openapi.py` containing the OpenAPI 3.0 specification as a Python dict:

```python
# stac_api/openapi.py
"""
OpenAPI 3.0 Specification for STAC API

This is a static OpenAPI document describing the STAC API endpoints.
Required by STAC API Core conformance class.
"""

def get_openapi_spec(base_url: str) -> dict:
    """
    Generate OpenAPI 3.0 specification for STAC API.

    Args:
        base_url: Base URL for server definition (e.g., https://example.com)

    Returns:
        OpenAPI 3.0 specification dict
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "RMH Geospatial STAC API",
            "description": "STAC API for geospatial raster and vector metadata catalog",
            "version": "1.0.0",
            "contact": {
                "name": "RMH Geospatial"
            },
            "license": {
                "name": "Proprietary"
            }
        },
        "servers": [
            {
                "url": f"{base_url}/api/stac",
                "description": "STAC API Server"
            }
        ],
        "tags": [
            {"name": "Core", "description": "STAC API Core endpoints"},
            {"name": "Collections", "description": "Collection management"},
            {"name": "Items", "description": "Item access"}
        ],
        "paths": {
            "/": {
                "get": {
                    "tags": ["Core"],
                    "summary": "Landing Page",
                    "description": "Returns the STAC Catalog root",
                    "operationId": "getLandingPage",
                    "responses": {
                        "200": {
                            "description": "STAC Catalog",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Catalog"}
                                }
                            }
                        }
                    }
                }
            },
            "/conformance": {
                "get": {
                    "tags": ["Core"],
                    "summary": "Conformance Classes",
                    "description": "Returns conformance classes implemented by this API",
                    "operationId": "getConformance",
                    "responses": {
                        "200": {
                            "description": "Conformance declaration",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Conformance"}
                                }
                            }
                        }
                    }
                }
            },
            "/collections": {
                "get": {
                    "tags": ["Collections"],
                    "summary": "List Collections",
                    "description": "Returns all STAC collections",
                    "operationId": "getCollections",
                    "responses": {
                        "200": {
                            "description": "Collections list",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Collections"}
                                }
                            }
                        }
                    }
                }
            },
            "/collections/{collectionId}": {
                "get": {
                    "tags": ["Collections"],
                    "summary": "Get Collection",
                    "description": "Returns a single STAC collection",
                    "operationId": "getCollection",
                    "parameters": [
                        {
                            "name": "collectionId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Collection identifier"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "STAC Collection",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Collection"}
                                }
                            }
                        },
                        "404": {
                            "description": "Collection not found"
                        }
                    }
                }
            },
            "/collections/{collectionId}/items": {
                "get": {
                    "tags": ["Items"],
                    "summary": "Get Collection Items",
                    "description": "Returns items in a collection",
                    "operationId": "getItems",
                    "parameters": [
                        {
                            "name": "collectionId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Collection identifier"
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 10, "minimum": 1, "maximum": 1000},
                            "description": "Maximum number of items to return"
                        },
                        {
                            "name": "bbox",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Bounding box filter (minx,miny,maxx,maxy)"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "STAC ItemCollection (GeoJSON FeatureCollection)",
                            "content": {
                                "application/geo+json": {
                                    "schema": {"$ref": "#/components/schemas/ItemCollection"}
                                }
                            }
                        },
                        "404": {
                            "description": "Collection not found"
                        }
                    }
                }
            },
            "/collections/{collectionId}/items/{itemId}": {
                "get": {
                    "tags": ["Items"],
                    "summary": "Get Item",
                    "description": "Returns a single STAC item",
                    "operationId": "getItem",
                    "parameters": [
                        {
                            "name": "collectionId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Collection identifier"
                        },
                        {
                            "name": "itemId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Item identifier"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "STAC Item (GeoJSON Feature)",
                            "content": {
                                "application/geo+json": {
                                    "schema": {"$ref": "#/components/schemas/Item"}
                                }
                            }
                        },
                        "404": {
                            "description": "Item not found"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Catalog": {
                    "type": "object",
                    "required": ["id", "type", "stac_version", "links"],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["Catalog"]},
                        "stac_version": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "conformsTo": {"type": "array", "items": {"type": "string"}},
                        "links": {"type": "array", "items": {"$ref": "#/components/schemas/Link"}}
                    }
                },
                "Conformance": {
                    "type": "object",
                    "required": ["conformsTo"],
                    "properties": {
                        "conformsTo": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "Collections": {
                    "type": "object",
                    "required": ["collections", "links"],
                    "properties": {
                        "collections": {"type": "array", "items": {"$ref": "#/components/schemas/Collection"}},
                        "links": {"type": "array", "items": {"$ref": "#/components/schemas/Link"}}
                    }
                },
                "Collection": {
                    "type": "object",
                    "required": ["id", "type", "stac_version", "links"],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["Collection"]},
                        "stac_version": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "extent": {"$ref": "#/components/schemas/Extent"},
                        "links": {"type": "array", "items": {"$ref": "#/components/schemas/Link"}}
                    }
                },
                "ItemCollection": {
                    "type": "object",
                    "required": ["type", "features"],
                    "properties": {
                        "type": {"type": "string", "enum": ["FeatureCollection"]},
                        "features": {"type": "array", "items": {"$ref": "#/components/schemas/Item"}},
                        "links": {"type": "array", "items": {"$ref": "#/components/schemas/Link"}},
                        "numberMatched": {"type": "integer"},
                        "numberReturned": {"type": "integer"}
                    }
                },
                "Item": {
                    "type": "object",
                    "required": ["id", "type", "geometry", "properties", "links", "assets"],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["Feature"]},
                        "stac_version": {"type": "string"},
                        "geometry": {"type": "object"},
                        "bbox": {"type": "array", "items": {"type": "number"}},
                        "properties": {"type": "object"},
                        "links": {"type": "array", "items": {"$ref": "#/components/schemas/Link"}},
                        "assets": {"type": "object"},
                        "collection": {"type": "string"}
                    }
                },
                "Link": {
                    "type": "object",
                    "required": ["href", "rel"],
                    "properties": {
                        "href": {"type": "string", "format": "uri"},
                        "rel": {"type": "string"},
                        "type": {"type": "string"},
                        "title": {"type": "string"}
                    }
                },
                "Extent": {
                    "type": "object",
                    "properties": {
                        "spatial": {
                            "type": "object",
                            "properties": {
                                "bbox": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}
                            }
                        },
                        "temporal": {
                            "type": "object",
                            "properties": {
                                "interval": {"type": "array", "items": {"type": "array", "items": {"type": "string", "nullable": True}}}
                            }
                        }
                    }
                }
            }
        }
    }
```

#### Step 2: Add Service Method

Update `stac_api/service.py` to add a method for the OpenAPI spec:

```python
# Add to STACAPIService class in stac_api/service.py

def get_openapi_spec(self, base_url: str) -> Dict[str, Any]:
    """
    Get OpenAPI 3.0 specification for this API.

    Required by STAC API Core conformance class.
    The spec requires a service-desc link pointing to an OpenAPI document.

    Args:
        base_url: Base URL for server definition

    Returns:
        OpenAPI 3.0 specification dict
    """
    from .openapi import get_openapi_spec
    return get_openapi_spec(base_url)
```

#### Step 3: Add HTTP Trigger

Update `stac_api/triggers.py` to add the OpenAPI endpoint trigger:

```python
# Add new trigger class after STACConformanceTrigger

class STACOpenAPITrigger(BaseSTACTrigger):
    """
    OpenAPI specification trigger.

    Endpoint: GET /api/stac/api

    Required by STAC API Core conformance class.
    Returns OpenAPI 3.0 specification document.
    """

    def handle(self, req: func.HttpRequest) -> func.HttpResponse:
        """
        Handle OpenAPI specification request.

        Args:
            req: Azure Functions HTTP request

        Returns:
            OpenAPI 3.0 JSON response
        """
        try:
            logger.info("STAC API OpenAPI spec requested")

            base_url = self._get_base_url(req)
            openapi_spec = self.service.get_openapi_spec(base_url)

            logger.info("STAC API OpenAPI spec generated successfully")
            return self._json_response(openapi_spec)

        except Exception as e:
            logger.error(f"Error generating STAC API OpenAPI spec: {e}", exc_info=True)
            return self._error_response(
                message=str(e),
                status_code=500,
                error_type="InternalServerError"
            )
```

#### Step 4: Update Trigger Registry

Update `get_stac_triggers()` in `stac_api/triggers.py` to include the new endpoint:

```python
def get_stac_triggers() -> List[Dict[str, Any]]:
    """Get list of STAC API trigger configurations."""
    return [
        {
            'route': 'stac',
            'methods': ['GET'],
            'handler': STACLandingPageTrigger().handle
        },
        {
            'route': 'stac/conformance',
            'methods': ['GET'],
            'handler': STACConformanceTrigger().handle
        },
        {
            'route': 'stac/api',  # NEW - OpenAPI endpoint
            'methods': ['GET'],
            'handler': STACOpenAPITrigger().handle
        },
        # ... rest of existing triggers
    ]
```

#### Step 5: Register in function_app.py

Add the new endpoint registration in `function_app.py`:

```python
# OpenAPI specification (NEW)
@app.route(route="stac/api", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def stac_openapi(req: func.HttpRequest) -> func.HttpResponse:
    return stac_triggers[2]['handler'](req)  # Index depends on position in list
```

**Note**: After adding to `get_stac_triggers()`, update the index numbers for subsequent triggers.

#### Step 6: Fix service-desc Link

Update the landing page in `stac_api/service.py` `get_catalog()` method:

```python
# Change this link in get_catalog():
{
    "rel": "service-desc",
    "type": "text/html",  # WRONG
    "href": "https://stacspec.org/en/api/",  # WRONG - external
    "title": "STAC API specification"
}

# To this:
{
    "rel": "service-desc",
    "type": "application/vnd.oai.openapi+json;version=3.0",  # CORRECT
    "href": f"{base_url}/api/stac/api",  # CORRECT - local
    "title": "OpenAPI specification"
}
```

**Testing**:
```bash
# Test OpenAPI endpoint
curl http://localhost:7071/api/stac/api | python3 -m json.tool

# Verify landing page links to it
curl http://localhost:7071/api/stac | jq '.links[] | select(.rel=="service-desc")'
```

---

### 3.2 Add Pagination to Items Endpoint (REQUIRED - OGC Features Conformance)

**Problem**: The items endpoint doesn't return `next` link when more items are available. This violates OGC API Features conformance.

**Spec Requirement** (OGC API Features / STAC OGC Features):
> "If the response is a partial result, the response MUST include a link with rel="next" pointing to the next page."

**Current State**:
- `stac_api/service.py:get_items()` accepts `offset` parameter but doesn't pass it to infrastructure
- `infrastructure/stac_queries.py:get_collection_items()` doesn't implement offset pagination
- No `next` link is ever returned
- No `numberMatched`/`numberReturned` metadata in response

**Files to Modify**:
1. `infrastructure/stac_queries.py` - Add offset support and total count
2. `stac_api/service.py` - Generate pagination links
3. `stac_api/triggers.py` - No changes needed (already parses offset)

**Implementation Steps**:

#### Step 1: Update stac_queries.py

Modify `get_collection_items()` to support offset pagination and return total count:

```python
# infrastructure/stac_queries.py

def get_collection_items(
    collection_id: str,
    limit: int = 100,
    offset: int = 0,  # ADD THIS PARAMETER
    bbox: Optional[str] = None,
    datetime_str: Optional[str] = None,
    repo: Optional[PostgreSQLRepository] = None
) -> Dict[str, Any]:
    """
    Get items in a collection with pagination support.

    Args:
        collection_id: Collection identifier
        limit: Maximum items to return (default 100)
        offset: Number of items to skip for pagination (default 0)  # ADD
        bbox: Bounding box filter [minx, miny, maxx, maxy]
        datetime_str: Datetime filter
        repo: Optional PostgreSQLRepository instance

    Returns:
        STAC ItemCollection with pagination metadata:
        {
            "type": "FeatureCollection",
            "features": [...],
            "numberMatched": <total_count>,  # ADD
            "numberReturned": <returned_count>,  # ADD
            "links": []
        }
    """
    try:
        if repo is None:
            repo = PostgreSQLRepository(schema_name='pgstac')

        with repo._get_connection() as conn:
            with conn.cursor() as cur:
                # STEP 1: Get total count for pagination
                count_query = """
                    SELECT COUNT(*) as total
                    FROM pgstac.items
                    WHERE collection = %s
                """
                cur.execute(count_query, [collection_id])
                count_result = cur.fetchone()
                total_count = count_result['total'] if count_result else 0

                # STEP 2: Get paginated items with OFFSET
                items_query = """
                    SELECT jsonb_build_object(
                        'type', 'FeatureCollection',
                        'features', COALESCE(jsonb_agg(
                            content ||
                            jsonb_build_object(
                                'id', id,
                                'collection', collection,
                                'geometry', ST_AsGeoJSON(geometry)::jsonb,
                                'type', 'Feature',
                                'stac_version', COALESCE(content->>'stac_version', '1.0.0')
                            )
                        ), '[]'::jsonb),
                        'links', '[]'::jsonb
                    )
                    FROM (
                        SELECT id, collection, geometry, content
                        FROM pgstac.items
                        WHERE collection = %s
                        ORDER BY datetime DESC
                        LIMIT %s
                        OFFSET %s
                    ) items
                """
                cur.execute(items_query, [collection_id, limit, offset])
                result = cur.fetchone()

                if result and 'jsonb_build_object' in result:
                    response = result['jsonb_build_object']
                else:
                    response = {
                        'type': 'FeatureCollection',
                        'features': [],
                        'links': []
                    }

                # ADD pagination metadata
                response['numberMatched'] = total_count
                response['numberReturned'] = len(response.get('features', []))

                return response

    except Exception as e:
        logger.error(f"Failed to get items for collection '{collection_id}': {e}")
        return {
            'error': str(e),
            'error_type': type(e).__name__
        }
```

#### Step 2: Update Service Layer

Modify `stac_api/service.py:get_items()` to pass offset and generate pagination links:

```python
# stac_api/service.py

def get_items(
    self,
    collection_id: str,
    base_url: str,
    limit: int = 10,
    offset: int = 0,
    bbox: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get items from collection (paginated).

    Now includes proper pagination links per OGC API Features spec.
    """
    from infrastructure.stac_queries import get_collection_items

    # Pass offset to infrastructure layer
    response = get_collection_items(
        collection_id=collection_id,
        limit=limit,
        offset=offset,  # NOW PASSED THROUGH
        bbox=bbox
    )

    if 'error' not in response:
        # Extract pagination metadata
        total_count = response.get('numberMatched', 0)
        returned_count = response.get('numberReturned', 0)

        # Build pagination links
        links = [
            {
                "rel": "self",
                "type": "application/geo+json",
                "href": f"{base_url}/api/stac/collections/{collection_id}/items?limit={limit}&offset={offset}",
                "title": "This page"
            },
            {
                "rel": "collection",
                "type": "application/json",
                "href": f"{base_url}/api/stac/collections/{collection_id}",
                "title": f"Collection {collection_id}"
            },
            {
                "rel": "root",
                "type": "application/json",
                "href": f"{base_url}/api/stac",
                "title": "Root catalog"
            }
        ]

        # ADD 'next' link if more items exist
        if offset + returned_count < total_count:
            next_offset = offset + limit
            links.append({
                "rel": "next",
                "type": "application/geo+json",
                "href": f"{base_url}/api/stac/collections/{collection_id}/items?limit={limit}&offset={next_offset}",
                "title": "Next page"
            })

        # ADD 'prev' link if not on first page
        if offset > 0:
            prev_offset = max(0, offset - limit)
            links.append({
                "rel": "prev",
                "type": "application/geo+json",
                "href": f"{base_url}/api/stac/collections/{collection_id}/items?limit={limit}&offset={prev_offset}",
                "title": "Previous page"
            })

        response['links'] = links

    return response
```

**Testing**:
```bash
# Test pagination
curl "http://localhost:7071/api/stac/collections/{collection_id}/items?limit=5" | jq '.links'

# Verify 'next' link exists when more items available
curl "http://localhost:7071/api/stac/collections/{collection_id}/items?limit=2" | jq '.links[] | select(.rel=="next")'

# Verify numberMatched/numberReturned
curl "http://localhost:7071/api/stac/collections/{collection_id}/items?limit=5" | jq '{matched: .numberMatched, returned: .numberReturned}'

# Follow pagination
NEXT_URL=$(curl -s "http://localhost:7071/api/stac/collections/{collection_id}/items?limit=2" | jq -r '.links[] | select(.rel=="next") | .href')
curl "$NEXT_URL" | jq '.features | length'
```

---

### 3.3 Update Health Endpoint (OPTIONAL)

**Problem**: Health endpoint reports 6 STAC endpoints but there will be 7 after adding OpenAPI.

**File to Modify**: `function_app.py`

```python
# Update health_check() function
stac_status = {
    "available": True,
    "schema": "pgstac",
    "endpoints": 7  # Changed from 6
}
```

---

## 📋 Phase 3 Checklist Summary

### 3.1 OpenAPI Endpoint - ✅ COMPLETE (24 NOV 2025)
- [x] Create `stac_api/openapi.py` with OpenAPI 3.0 spec
- [x] Add `get_openapi_spec()` method to `STACAPIService`
- [x] Add `STACOpenAPITrigger` class to `stac_api/triggers.py`
- [x] Update `get_stac_triggers()` to include new endpoint
- [x] Register `GET /api/stac/api` in `function_app.py`
- [x] Fix `service-desc` link in landing page to point to `/api/stac/api`
- [ ] Test OpenAPI endpoint returns valid JSON
- [ ] Test landing page `service-desc` link is correct

### 3.2 Pagination - ✅ COMPLETE (24 NOV 2025)
- [x] Update `get_collection_items()` to accept `offset` parameter
- [x] Add COUNT query for total items
- [x] Add `numberMatched` and `numberReturned` to response
- [x] Update `STACAPIService.get_items()` to pass `offset`
- [x] Generate `next` link when `offset + returned < total`
- [x] Generate `prev` link when `offset > 0`
- [ ] Test pagination with various limit/offset values
- [ ] Verify `next` link works correctly

### 3.3 Documentation & Testing (1 hour)
- [x] Update health endpoint count (6 → 7)
- [ ] Update README.md endpoint count
- [ ] Update ARCHITECTURE.md endpoint count
- [ ] Test with stac-validator CLI
- [ ] Test with pystac-client
- [ ] Deploy to Azure and verify

**Total Estimated Time**: 5-7 hours
**Actual Implementation Time**: ~2 hours (code changes complete, testing pending)

---

## 🎯 Success Criteria for Phase 3

After completing Phase 3:

1. **STAC Core Conformance**:
   - [ ] `GET /api/stac/api` returns valid OpenAPI 3.0 JSON
   - [ ] Landing page `service-desc` link points to `/api/stac/api`
   - [ ] OpenAPI spec validates against OpenAPI 3.0 schema

2. **OGC Features Conformance**:
   - [ ] Items endpoint returns `next` link when more items exist
   - [ ] Items endpoint returns `prev` link when not on first page
   - [ ] `numberMatched` shows total matching items
   - [ ] `numberReturned` shows items in current page
   - [ ] Following `next` link returns correct next page

3. **Validation**:
   - [ ] `stac-validator` passes on all endpoints
   - [ ] `pystac-client` can successfully iterate all items
   - [ ] No errors in Application Insights after deployment

---

## 📊 Completed Phases

### Phase 1: OGC Features API - ✅ COMPLETE
- 6 endpoints operational
- Full OGC API - Features Core 1.0 compliance
- Production deployed to rmhgeoapifn

### Phase 2: STAC API - ✅ COMPLETE
- 6 endpoints operational (will be 7 after Phase 3)
- Basic STAC v1.0.0 structure
- Production deployed to rmhgeoapifn

---

## 🚨 Notes for Implementation

### Do NOT Implement (Not Required)
- ❌ `POST /search` endpoint - Not needed for static mosaic use case
- ❌ `GET /search` endpoint - Not claiming Item Search conformance
- ❌ CQL2 filters - Static mosaics don't need complex queries
- ❌ Connection pooling - Intentionally deferred

### Design Decisions
- **Static OpenAPI**: Generate OpenAPI spec as static Python dict (not dynamic generation)
- **Offset Pagination**: Use simple offset/limit (not cursor-based) - sufficient for pgSTAC
- **No Search**: Only claiming Core + Collections + OGC Features conformance classes

---

**Current Status**: Phase 3 Implementation Complete ✅
**Next Step**: Local testing, then deploy to Azure
