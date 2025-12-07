# ============================================================================
# CLAUDE CONTEXT - INFRASTRUCTURE MODULE
# ============================================================================
# STATUS: Core Infrastructure - Database and Utilities
# PURPOSE: Shared infrastructure components for STAC and OGC APIs
# LAST_REVIEWED: Current
# EXPORTS: PostgreSQLRepository, STAC query functions, schema availability checks
# DEPENDENCIES: psycopg, config
# ============================================================================

"""
Infrastructure Module

Provides shared infrastructure components for rmhogcapi:
- PostgreSQL connection management (PostgreSQLRepository)
- STAC query functions (read-only access to pgstac schema)
- Schema availability checks for resilient API operation
- Database utilities

This module supports both OGC Features API and STAC API with
read-only database access patterns.
"""

from .stac_queries import (
    is_pgstac_available,
    get_pgstac_unavailable_error,
    get_all_collections,
    get_collection,
    get_collection_items,
    get_item_by_id
)

__version__ = "1.0.0"
__all__ = [
    "is_pgstac_available",
    "get_pgstac_unavailable_error",
    "get_all_collections",
    "get_collection",
    "get_collection_items",
    "get_item_by_id"
]
