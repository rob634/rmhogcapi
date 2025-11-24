# ============================================================================
# CLAUDE CONTEXT - HEALTH CHECK MODULE
# ============================================================================
# STATUS: Core Infrastructure - Health Monitoring
# PURPOSE: Production-grade health checks for APIM integration and monitoring
# LAST_REVIEWED: 24 NOV 2025
# EXPORTS: get_public_health, get_detailed_health, HealthStatus
# DEPENDENCIES: psycopg, config, util_logger
# PATTERNS: Two-tier health checks (public/detailed) for APIM
# ============================================================================

"""
Health Check Module for rmhogcapi

Provides two-tier health monitoring optimized for Azure APIM integration:

1. Public Health (/api/health):
   - Minimal response for external callers (Cloudflare, public users)
   - Returns only status and timestamp
   - Always returns 200 (status in body indicates health)

2. Detailed Health (/api/health/detailed):
   - Full metrics for APIM probes and operations teams
   - Database connectivity with latency metrics
   - Schema validation (geo, pgstac)
   - API module status
   - Returns 503 if unhealthy

APIM Configuration:
    Block /health/detailed from external gateway to prevent information disclosure.
    Point APIM backend health probe at /health/detailed for circuit breaker.

Usage:
    from health import get_public_health, get_detailed_health

    # Public endpoint
    result = get_public_health()
    # {"status": "healthy", "timestamp": "2025-11-24T12:00:00Z"}

    # Detailed endpoint (APIM only)
    result = get_detailed_health()
    # Full metrics with latency, counts, etc.
"""

import time
import uuid
import psycopg
from enum import Enum
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

from config import get_postgres_connection_string, get_app_config
from util_logger import LoggerFactory, ComponentType

# Create module logger
logger = LoggerFactory.create_logger(ComponentType.SERVICE, "HealthService")


# ============================================================================
# Health Status Enum
# ============================================================================

class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"      # Non-critical components failing
    UNHEALTHY = "unhealthy"    # Critical components failing


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CheckResult:
    """Result of a single health check."""
    status: str              # "pass" or "fail"
    latency_ms: float        # Time taken for check
    message: str             # Human-readable status message
    details: Optional[Dict[str, Any]] = None  # Additional details

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {
            "status": self.status,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message
        }
        if self.details:
            result["details"] = self.details
        return result


# ============================================================================
# Health Check Functions
# ============================================================================

def check_database_connectivity(timeout_seconds: float = 5.0) -> CheckResult:
    """
    Check PostgreSQL database connectivity.

    Executes SELECT 1 with timeout to verify database is reachable.
    This is a critical check - failure means UNHEALTHY status.

    Args:
        timeout_seconds: Connection timeout in seconds

    Returns:
        CheckResult with connection status and latency
    """
    start_time = time.perf_counter()

    try:
        conn_string = get_postgres_connection_string()
        config = get_app_config()

        # Connect with timeout
        with psycopg.connect(
            conn_string,
            connect_timeout=int(timeout_seconds)
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

        latency_ms = (time.perf_counter() - start_time) * 1000

        return CheckResult(
            status="pass",
            latency_ms=latency_ms,
            message="PostgreSQL connection successful",
            details={
                "host": config.postgis_host,
                "database": config.postgis_database,
                "auth_mode": "managed_identity" if config.use_managed_identity else "password"
            }
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"Database connectivity check failed: {e}")

        return CheckResult(
            status="fail",
            latency_ms=latency_ms,
            message=f"Database connection failed: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_geo_schema() -> CheckResult:
    """
    Check geo schema health for OGC Features API.

    Queries geometry_columns to count available collections.
    This is a critical check - failure means UNHEALTHY status.

    Returns:
        CheckResult with schema status and collection count
    """
    start_time = time.perf_counter()

    try:
        conn_string = get_postgres_connection_string()

        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Check schema exists
                cur.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    ('geo',)
                )
                if not cur.fetchone():
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    return CheckResult(
                        status="fail",
                        latency_ms=latency_ms,
                        message="Schema 'geo' does not exist",
                        details={"schema": "geo", "exists": False}
                    )

                # Count geometry tables
                cur.execute("""
                    SELECT f_table_name
                    FROM geometry_columns
                    WHERE f_table_schema = 'geo'
                    ORDER BY f_table_name
                    LIMIT 10
                """)
                tables = [row[0] for row in cur.fetchall()]
                collection_count = len(tables)

        latency_ms = (time.perf_counter() - start_time) * 1000

        return CheckResult(
            status="pass",
            latency_ms=latency_ms,
            message=f"{collection_count} collections available",
            details={
                "schema": "geo",
                "collection_count": collection_count,
                "sample_collections": tables[:5]  # First 5 only
            }
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"Geo schema check failed: {e}")

        return CheckResult(
            status="fail",
            latency_ms=latency_ms,
            message=f"Geo schema check failed: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_pgstac_schema() -> CheckResult:
    """
    Check pgstac schema health for STAC API.

    Counts collections and items in pgstac schema.
    This is a critical check - failure means UNHEALTHY status.

    Returns:
        CheckResult with schema status and counts
    """
    start_time = time.perf_counter()

    try:
        conn_string = get_postgres_connection_string()

        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Check schema exists
                cur.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    ('pgstac',)
                )
                if not cur.fetchone():
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    return CheckResult(
                        status="fail",
                        latency_ms=latency_ms,
                        message="Schema 'pgstac' does not exist",
                        details={"schema": "pgstac", "exists": False}
                    )

                # Count collections
                cur.execute("SELECT COUNT(*) FROM pgstac.collections")
                collections_count = cur.fetchone()[0]

                # Count items
                cur.execute("SELECT COUNT(*) FROM pgstac.items")
                items_count = cur.fetchone()[0]

        latency_ms = (time.perf_counter() - start_time) * 1000

        return CheckResult(
            status="pass",
            latency_ms=latency_ms,
            message=f"{collections_count} STAC collections, {items_count} items",
            details={
                "schema": "pgstac",
                "collections_count": collections_count,
                "items_count": items_count
            }
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"PgSTAC schema check failed: {e}")

        return CheckResult(
            status="fail",
            latency_ms=latency_ms,
            message=f"PgSTAC schema check failed: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_api_modules() -> CheckResult:
    """
    Check API module availability.

    Verifies ogc_features and stac_api modules can be imported.
    This is a non-critical check - failure means DEGRADED status.

    Returns:
        CheckResult with module availability status
    """
    start_time = time.perf_counter()

    ogc_status = {"available": False, "endpoints": 0}
    stac_status = {"available": False, "endpoints": 0}
    errors = []

    # Check OGC Features
    try:
        from ogc_features import get_ogc_triggers, get_ogc_config
        triggers = get_ogc_triggers()
        config = get_ogc_config()
        ogc_status = {
            "available": True,
            "endpoints": len(triggers),
            "schema": config.ogc_schema
        }
    except Exception as e:
        errors.append(f"ogc_features: {e}")
        ogc_status["error"] = str(e)

    # Check STAC API
    try:
        from stac_api import get_stac_triggers, get_stac_config
        triggers = get_stac_triggers()
        config = get_stac_config()
        stac_status = {
            "available": True,
            "endpoints": len(triggers),
            "catalog_id": config.catalog_id
        }
    except Exception as e:
        errors.append(f"stac_api: {e}")
        stac_status["error"] = str(e)

    latency_ms = (time.perf_counter() - start_time) * 1000

    # Determine overall status
    all_available = ogc_status["available"] and stac_status["available"]

    if all_available:
        message = "All modules loaded"
        status = "pass"
    elif ogc_status["available"] or stac_status["available"]:
        message = "Some modules unavailable"
        status = "pass"  # Partial availability is still a pass
    else:
        message = "No API modules available"
        status = "fail"

    return CheckResult(
        status=status,
        latency_ms=latency_ms,
        message=message,
        details={
            "ogc_features": ogc_status,
            "stac_api": stac_status
        }
    )


# ============================================================================
# Main Entry Points
# ============================================================================

def get_public_health() -> Dict[str, Any]:
    """
    Get minimal health status for public endpoint.

    Returns only status and timestamp - no internal details.
    Use for: Cloudflare health checks, public status pages.

    Returns:
        Dict with status and timestamp only
    """
    start_time = time.perf_counter()

    # Quick database check to determine status
    db_result = check_database_connectivity(timeout_seconds=3.0)

    # Determine overall status based on critical checks only
    if db_result.status == "pass":
        status = HealthStatus.HEALTHY
    else:
        status = HealthStatus.UNHEALTHY

    total_duration = (time.perf_counter() - start_time) * 1000

    # Log the health check
    logger.info("Public health check completed", extra={
        'custom_dimensions': {
            'status': status.value,
            'duration_ms': round(total_duration, 2),
            'check_type': 'public'
        }
    })

    return {
        "status": status.value,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_detailed_health() -> Dict[str, Any]:
    """
    Get detailed health status for APIM probes and operations.

    Includes full metrics: database latency, schema status, collection counts.
    Use for: APIM backend health probes, operations dashboards.

    SECURITY NOTE: Block this endpoint from external access via APIM policy.

    Returns:
        Dict with full health metrics
    """
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())[:8]

    checks = {}
    critical_failures = []
    non_critical_failures = []

    # Critical: Database connectivity
    db_result = check_database_connectivity()
    checks["database"] = db_result.to_dict()
    if db_result.status == "fail":
        critical_failures.append("database")

    # Critical: Geo schema (OGC Features)
    geo_result = check_geo_schema()
    checks["geo_schema"] = geo_result.to_dict()
    if geo_result.status == "fail":
        critical_failures.append("geo_schema")

    # Critical: PgSTAC schema (STAC API)
    pgstac_result = check_pgstac_schema()
    checks["pgstac_schema"] = pgstac_result.to_dict()
    if pgstac_result.status == "fail":
        critical_failures.append("pgstac_schema")

    # Non-critical: API modules
    modules_result = check_api_modules()
    checks["api_modules"] = modules_result.to_dict()
    if modules_result.status == "fail":
        non_critical_failures.append("api_modules")

    # Determine overall status
    if critical_failures:
        status = HealthStatus.UNHEALTHY
    elif non_critical_failures:
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.HEALTHY

    total_duration = (time.perf_counter() - start_time) * 1000

    # Log the health check
    logger.info("Detailed health check completed", extra={
        'custom_dimensions': {
            'status': status.value,
            'duration_ms': round(total_duration, 2),
            'check_type': 'detailed',
            'request_id': request_id,
            'critical_failures': critical_failures,
            'non_critical_failures': non_critical_failures,
            'database_latency_ms': db_result.latency_ms
        }
    })

    return {
        "status": status.value,
        "app": "rmhogcapi",
        "description": "OGC Features & STAC API Service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "checks": checks,
        "total_duration_ms": round(total_duration, 2)
    }
