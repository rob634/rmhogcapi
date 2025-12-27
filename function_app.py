# ============================================================================
# CLAUDE CONTEXT - AZURE FUNCTIONS ENTRY POINT
# ============================================================================
# STATUS: Core Infrastructure - Function App Entry Point
# PURPOSE: Main entry point for Azure Functions runtime with OGC Features and STAC APIs
# LAST_REVIEWED: Current
# EXPORTS: app (FunctionApp instance)
# DEPENDENCIES: azure-functions, ogc_features, stac_api
# ============================================================================

"""
Azure Functions Entry Point for rmhogcapi

This module serves as the main entry point for the Azure Functions runtime.
It registers all HTTP triggers for OGC Features, STAC, Raster, and xarray APIs.

Architecture:
    - OGC Features API: 6 endpoints serving PostGIS vector data (geo schema)
    - STAC API: 7 endpoints serving STAC catalog metadata (pgstac schema)
    - Raster API: 4 endpoints for raster operations via TiTiler
    - xarray API: 3 endpoints for Zarr time-series operations
    - Health checks: 2 endpoints for monitoring and APIM integration
        - /api/health - Public (minimal response for external callers)
        - /api/health/detailed - Internal (full metrics for APIM probes)

Total: 22 HTTP endpoints (20 API + 2 health check)

Deployment:
    - Local: func start
    - Azure: func azure functionapp publish rmhogcapi --python --build remote

Updated: 19 DEC 2025 - Added Raster API and xarray API (Reader Migration)
"""

import azure.functions as func
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Azure Function App
app = func.FunctionApp()

# ============================================================================
# OGC Features API - 6 Endpoints
# ============================================================================

try:
    from ogc_features import get_ogc_triggers

    logger.info("Registering OGC Features API endpoints...")

    # Register all OGC Features API endpoints with unique function names
    triggers = get_ogc_triggers()

    # Landing page
    @app.route(route="features", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def ogc_landing_page(req: func.HttpRequest) -> func.HttpResponse:
        return triggers[0]['handler'](req)

    # Conformance
    @app.route(route="features/conformance", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def ogc_conformance(req: func.HttpRequest) -> func.HttpResponse:
        return triggers[1]['handler'](req)

    # Collections list
    @app.route(route="features/collections", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def ogc_collections(req: func.HttpRequest) -> func.HttpResponse:
        return triggers[2]['handler'](req)

    # Single collection
    @app.route(route="features/collections/{collection_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def ogc_collection(req: func.HttpRequest) -> func.HttpResponse:
        return triggers[3]['handler'](req)

    # Collection items (features query)
    @app.route(route="features/collections/{collection_id}/items", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def ogc_items(req: func.HttpRequest) -> func.HttpResponse:
        return triggers[4]['handler'](req)

    # Single feature
    @app.route(route="features/collections/{collection_id}/items/{feature_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def ogc_item(req: func.HttpRequest) -> func.HttpResponse:
        return triggers[5]['handler'](req)

    logger.info("✅ OGC Features API registered successfully (6 endpoints)")

except ImportError as e:
    logger.warning(f"⚠️ OGC Features module not available: {e}")
    logger.warning("OGC Features API will not be available")

# ============================================================================
# STAC API - 7 Endpoints
# ============================================================================

try:
    from stac_api import get_stac_triggers

    logger.info("Registering STAC API endpoints...")

    # Register all STAC API endpoints with unique function names
    stac_triggers = get_stac_triggers()

    # Landing page (catalog root)
    @app.route(route="stac", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_landing_page(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[0]['handler'](req)

    # Conformance
    @app.route(route="stac/conformance", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_conformance(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[1]['handler'](req)

    # OpenAPI specification (required by STAC Core conformance)
    @app.route(route="stac/api", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_openapi(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[2]['handler'](req)

    # Collections list
    @app.route(route="stac/collections", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_collections(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[3]['handler'](req)

    # Single collection
    @app.route(route="stac/collections/{collection_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_collection(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[4]['handler'](req)

    # Collection items (STAC items query)
    @app.route(route="stac/collections/{collection_id}/items", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_items(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[5]['handler'](req)

    # Single item
    @app.route(route="stac/collections/{collection_id}/items/{item_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_item(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[6]['handler'](req)

    logger.info("✅ STAC API registered successfully (7 endpoints)")

except ImportError as e:
    logger.warning(f"⚠️ STAC API module not available: {e}")
    logger.warning("STAC API will not be available")

# ============================================================================
# Raster API - 4 Endpoints (Added 19 DEC 2025)
# ============================================================================

try:
    from raster_api.triggers import (
        RasterExtractTrigger,
        RasterPointTrigger,
        RasterClipTrigger,
        RasterPreviewTrigger
    )

    logger.info("Registering Raster API endpoints...")

    _raster_extract = RasterExtractTrigger()
    _raster_point = RasterPointTrigger()
    _raster_clip = RasterClipTrigger()
    _raster_preview = RasterPreviewTrigger()

    @app.route(route="raster/extract/{collection}/{item}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def raster_extract(req: func.HttpRequest) -> func.HttpResponse:
        return _raster_extract.handle(req)

    @app.route(route="raster/point/{collection}/{item}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def raster_point(req: func.HttpRequest) -> func.HttpResponse:
        return _raster_point.handle(req)

    @app.route(route="raster/clip/{collection}/{item}", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
    def raster_clip(req: func.HttpRequest) -> func.HttpResponse:
        return _raster_clip.handle(req)

    @app.route(route="raster/preview/{collection}/{item}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def raster_preview(req: func.HttpRequest) -> func.HttpResponse:
        return _raster_preview.handle(req)

    logger.info("✅ Raster API registered successfully (4 endpoints)")

except ImportError as e:
    logger.warning(f"⚠️ Raster API module not available: {e}")
    logger.warning("Raster API will not be available")

# ============================================================================
# xarray API - 3 Endpoints (Added 19 DEC 2025)
# ============================================================================

try:
    from xarray_api.triggers import (
        XarrayPointTrigger,
        XarrayStatisticsTrigger,
        XarrayAggregateTrigger
    )

    logger.info("Registering xarray API endpoints...")

    _xarray_point = XarrayPointTrigger()
    _xarray_stats = XarrayStatisticsTrigger()
    _xarray_agg = XarrayAggregateTrigger()

    @app.route(route="xarray/point/{collection}/{item}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def xarray_point(req: func.HttpRequest) -> func.HttpResponse:
        return _xarray_point.handle(req)

    @app.route(route="xarray/statistics/{collection}/{item}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def xarray_statistics(req: func.HttpRequest) -> func.HttpResponse:
        return _xarray_stats.handle(req)

    @app.route(route="xarray/aggregate/{collection}/{item}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def xarray_aggregate(req: func.HttpRequest) -> func.HttpResponse:
        return _xarray_agg.handle(req)

    logger.info("✅ xarray API registered successfully (3 endpoints)")

except ImportError as e:
    logger.warning(f"⚠️ xarray API module not available: {e}")
    logger.warning("xarray API will not be available")

# ============================================================================
# Health Check Endpoints - 2 Endpoints (Public + Detailed)
# ============================================================================

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Public health check endpoint - minimal response for external callers.

    Use for: Cloudflare health checks, public status pages, external monitoring.
    Always returns 200 - status in body indicates health.

    Returns:
        JSON: {"status": "healthy|unhealthy", "timestamp": "..."}
    """
    import json
    from health import get_public_health

    result = get_public_health()

    return func.HttpResponse(
        json.dumps(result, default=str),
        mimetype="application/json",
        status_code=200,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


@app.route(route="health/detailed", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_detailed(req: func.HttpRequest) -> func.HttpResponse:
    """
    Detailed health check endpoint - for APIM probes and operations.

    Use for: APIM backend health probes, operations dashboards, debugging.
    Returns 503 if unhealthy, 200 otherwise.

    SECURITY: Block this endpoint from external access via APIM policy.

    Returns:
        JSON with full health metrics including:
        - Database connectivity and latency
        - Schema status (geo, pgstac)
        - Collection counts
        - API module availability
    """
    import json
    from health import get_detailed_health, HealthStatus

    result = get_detailed_health()

    # Return 503 if unhealthy, 200 otherwise (healthy or degraded)
    status_code = 503 if result["status"] == HealthStatus.UNHEALTHY.value else 200

    return func.HttpResponse(
        json.dumps(result, default=str, indent=2),
        mimetype="application/json",
        status_code=status_code,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

# ============================================================================
# Application Startup
# ============================================================================

from health import get_app_identity
_app_identity = get_app_identity()

logger.info("="*60)
logger.info(f"{_app_identity['name']} - {_app_identity['description']}")
logger.info("="*60)
logger.info("Function App initialized successfully")
logger.info("Available endpoints:")
logger.info("  - GET /api/health - Public health check (minimal)")
logger.info("  - GET /api/health/detailed - Detailed health (APIM only)")
logger.info("")
logger.info("OGC Features API (6 endpoints):")
logger.info("  - GET /api/features - Landing page")
logger.info("  - GET /api/features/conformance - Conformance")
logger.info("  - GET /api/features/collections - List collections")
logger.info("  - GET /api/features/collections/{id} - Collection metadata")
logger.info("  - GET /api/features/collections/{id}/items - Query features")
logger.info("  - GET /api/features/collections/{id}/items/{fid} - Single feature")
logger.info("")
logger.info("STAC API (7 endpoints):")
logger.info("  - GET /api/stac - Landing page")
logger.info("  - GET /api/stac/conformance - Conformance")
logger.info("  - GET /api/stac/api - OpenAPI specification")
logger.info("  - GET /api/stac/collections - List collections")
logger.info("  - GET /api/stac/collections/{id} - Collection metadata")
logger.info("  - GET /api/stac/collections/{id}/items - Query items")
logger.info("  - GET /api/stac/collections/{id}/items/{item_id} - Single item")
logger.info("")
logger.info("Raster API (4 endpoints):")
logger.info("  - GET /api/raster/extract/{collection}/{item} - Extract bbox as image")
logger.info("  - GET /api/raster/point/{collection}/{item} - Point value query")
logger.info("  - GET/POST /api/raster/clip/{collection}/{item} - Clip to geometry")
logger.info("  - GET /api/raster/preview/{collection}/{item} - Preview image")
logger.info("")
logger.info("xarray API (3 endpoints):")
logger.info("  - GET /api/xarray/point/{collection}/{item} - Time-series at point")
logger.info("  - GET /api/xarray/statistics/{collection}/{item} - Regional stats")
logger.info("  - GET /api/xarray/aggregate/{collection}/{item} - Temporal aggregation")
logger.info("="*60)
