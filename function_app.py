# ============================================================================
# CLAUDE CONTEXT - AZURE FUNCTIONS ENTRY POINT
# ============================================================================
# STATUS: Core Infrastructure - Function App Entry Point
# PURPOSE: Main entry point for Azure Functions runtime with OGC Features and STAC APIs
# LAST_REVIEWED: 19 NOV 2025
# EXPORTS: app (FunctionApp instance)
# DEPENDENCIES: azure-functions, ogc_features, stac_api
# ============================================================================

"""
Azure Functions Entry Point for rmhogcapi

This module serves as the main entry point for the Azure Functions runtime.
It registers all HTTP triggers for both OGC Features API and STAC API.

Architecture:
    - OGC Features API: 6 endpoints serving PostGIS vector data (geo schema)
    - STAC API: 6 endpoints serving STAC catalog metadata (pgstac schema)
    - Health check: 1 endpoint for monitoring and deployment verification

Total: 13 HTTP endpoints (12 API + 1 health check)

Deployment:
    - Local: func start
    - Azure: func azure functionapp publish rmhogcapi --python --build remote
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
# STAC API - 6 Endpoints
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

    # Collections list
    @app.route(route="stac/collections", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_collections(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[2]['handler'](req)

    # Single collection
    @app.route(route="stac/collections/{collection_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_collection(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[3]['handler'](req)

    # Collection items (STAC items query)
    @app.route(route="stac/collections/{collection_id}/items", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_items(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[4]['handler'](req)

    # Single item
    @app.route(route="stac/collections/{collection_id}/items/{item_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def stac_item(req: func.HttpRequest) -> func.HttpResponse:
        return stac_triggers[5]['handler'](req)

    logger.info("✅ STAC API registered successfully (6 endpoints)")

except ImportError as e:
    logger.warning(f"⚠️ STAC API module not available: {e}")
    logger.warning("STAC API will not be available")

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint for monitoring and deployment verification.

    Returns:
        JSON response with status and available APIs
    """
    import json

    try:
        from ogc_features import get_ogc_config
        ogc_available = True
        ogc_config = get_ogc_config()
        ogc_status = {
            "available": True,
            "schema": ogc_config.ogc_schema,
            "endpoints": 6
        }
    except Exception as e:
        ogc_available = False
        ogc_status = {
            "available": False,
            "error": str(e)
        }

    try:
        from stac_api import get_stac_config
        stac_available = True
        stac_config = get_stac_config()
        stac_status = {
            "available": True,
            "schema": "pgstac",
            "endpoints": 6
        }
    except Exception as e:
        stac_available = False
        stac_status = {
            "available": False,
            "error": str(e)
        }

    response = {
        "status": "healthy",
        "app": "rmhogcapi",
        "description": "OGC Features & STAC API Service",
        "apis": {
            "ogc_features": ogc_status,
            "stac": stac_status
        }
    }

    return func.HttpResponse(
        json.dumps(response, indent=2),
        mimetype="application/json",
        status_code=200
    )

# ============================================================================
# Application Startup
# ============================================================================

logger.info("="*60)
logger.info("🚀 rmhogcapi - OGC Features & STAC API Service")
logger.info("="*60)
logger.info("Function App initialized successfully")
logger.info("Available endpoints:")
logger.info("  - GET /api/health - Health check")
logger.info("")
logger.info("OGC Features API (6 endpoints):")
logger.info("  - GET /api/features - Landing page")
logger.info("  - GET /api/features/conformance - Conformance")
logger.info("  - GET /api/features/collections - List collections")
logger.info("  - GET /api/features/collections/{id} - Collection metadata")
logger.info("  - GET /api/features/collections/{id}/items - Query features")
logger.info("  - GET /api/features/collections/{id}/items/{fid} - Single feature")
logger.info("")
logger.info("STAC API (6 endpoints):")
logger.info("  - GET /api/stac - Landing page")
logger.info("  - GET /api/stac/conformance - Conformance")
logger.info("  - GET /api/stac/collections - List collections")
logger.info("  - GET /api/stac/collections/{id} - Collection metadata")
logger.info("  - GET /api/stac/collections/{id}/items - Query items")
logger.info("  - GET /api/stac/collections/{id}/items/{item_id} - Single item")
logger.info("="*60)
