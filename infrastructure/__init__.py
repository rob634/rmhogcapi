# ============================================================================
# CLAUDE CONTEXT - INFRASTRUCTURE MODULE
# ============================================================================
# STATUS: Core Infrastructure - Database and Utilities
# PURPOSE: Shared infrastructure components for STAC and OGC APIs
# LAST_REVIEWED: 19 NOV 2025
# EXPORTS: PostgreSQLRepository, STAC query functions
# DEPENDENCIES: psycopg, config
# ============================================================================

"""
Infrastructure Module

Provides shared infrastructure components for rmhogcapi:
- PostgreSQL connection management (PostgreSQLRepository)
- STAC query functions (read-only access to pgstac schema)
- Database utilities

This module supports both OGC Features API and STAC API with
read-only database access patterns.
"""

__version__ = "1.0.0"
__all__ = []
