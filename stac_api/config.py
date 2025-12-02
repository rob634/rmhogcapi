# ============================================================================
# CLAUDE CONTEXT - STAC API CONFIGURATION
# ============================================================================
# STATUS: Standalone Configuration - STAC API
# PURPOSE: Environment-based configuration for STAC API module
# LAST_REVIEWED: 02 DEC 2025
# EXPORTS: STACAPIConfig, get_stac_config
# DEPENDENCIES: pydantic, os
# SOURCE: Environment variables
# ============================================================================

"""
STAC API Configuration

Environment-based configuration for STAC API module.
All settings can be customized via environment variables for multi-tenant deployment.

Environment Variables:
    Optional:
    - STAC_CATALOG_ID: Catalog identifier (default: "geospatial-stac")
    - STAC_CATALOG_TITLE: Human-readable catalog title (default: "Geospatial STAC API")
    - STAC_CATALOG_DESCRIPTION: Catalog description (default: generic)
    - STAC_BASE_URL: Base URL for STAC links (default: auto-detect)

Date: 02 DEC 2025
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class STACAPIConfig(BaseModel):
    """STAC API module configuration - fully configurable via environment variables."""

    catalog_id: str = Field(
        default_factory=lambda: os.getenv("STAC_CATALOG_ID", "geospatial-stac"),
        description="STAC catalog ID"
    )

    catalog_title: str = Field(
        default_factory=lambda: os.getenv("STAC_CATALOG_TITLE", "Geospatial STAC API"),
        description="Human-readable catalog title"
    )

    catalog_description: str = Field(
        default_factory=lambda: os.getenv(
            "STAC_CATALOG_DESCRIPTION",
            "STAC catalog for geospatial raster and vector data"
        ),
        description="Catalog description"
    )

    stac_version: str = Field(
        default="1.0.0",
        description="STAC specification version"
    )

    stac_base_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("STAC_BASE_URL"),
        description="Base URL for STAC API (auto-detected if None)"
    )


# Singleton instance cache
_stac_config_cache: Optional[STACAPIConfig] = None


def get_stac_config() -> STACAPIConfig:
    """
    Get STAC API configuration (singleton pattern).

    Returns:
        Cached configuration instance
    """
    global _stac_config_cache

    if _stac_config_cache is None:
        _stac_config_cache = STACAPIConfig()

    return _stac_config_cache
