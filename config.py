# ============================================================================
# CLAUDE CONTEXT - APPLICATION CONFIGURATION
# ============================================================================
# STATUS: Core Infrastructure - Configuration Management
# PURPOSE: Centralized configuration for PostgreSQL connection with managed identity support
# LAST_REVIEWED: 19 NOV 2025
# EXPORTS: get_postgres_connection_string, AppConfig
# DEPENDENCIES: pydantic-settings, azure-identity
# SOURCE: Environment variables, Azure managed identity
# PATTERNS: Singleton pattern for config, lazy initialization for credentials
# ============================================================================

"""
Application Configuration Module

Provides centralized configuration management for rmhogcapi including:
- PostgreSQL connection string generation
- Support for both password and managed identity authentication
- Environment-based configuration with validation

Authentication Modes:
    1. Password-based (local development):
       - Requires: POSTGIS_HOST, POSTGIS_USER, POSTGIS_PASSWORD
       - Use when: USE_MANAGED_IDENTITY=false or not set

    2. Managed Identity (Azure production):
       - Requires: System-assigned managed identity enabled
       - Use when: USE_MANAGED_IDENTITY=true
       - Eliminates need for password storage

Usage:
    from config import get_postgres_connection_string

    conn_string = get_postgres_connection_string()
    conn = psycopg.connect(conn_string)
"""

import os
import logging
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field, validator

logger = logging.getLogger(__name__)

# ============================================================================
# Application Configuration
# ============================================================================

class AppConfig(BaseSettings):
    """
    Application-wide configuration loaded from environment variables.

    Attributes:
        postgis_host: PostgreSQL server hostname
        postgis_port: PostgreSQL server port
        postgis_database: Database name
        postgis_user: Database username
        postgis_password: Database password (optional with managed identity)
        use_managed_identity: Enable Azure managed identity authentication
    """

    # PostgreSQL Connection
    postgis_host: str = Field(..., description="PostgreSQL hostname")
    postgis_port: int = Field(default=5432, description="PostgreSQL port")
    postgis_database: str = Field(..., description="Database name")
    postgis_user: str = Field(..., description="Database username")
    postgis_password: Optional[str] = Field(default=None, description="Database password")

    # Authentication Mode
    use_managed_identity: bool = Field(
        default=False,
        description="Use Azure managed identity for authentication"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator('postgis_password')
    def validate_password(cls, v, values):
        """Ensure password is provided when not using managed identity."""
        use_managed_identity = values.get('use_managed_identity', False)
        if not use_managed_identity and not v:
            raise ValueError(
                "POSTGIS_PASSWORD is required when USE_MANAGED_IDENTITY=false"
            )
        return v


@lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    """
    Get singleton application configuration instance.

    Returns:
        AppConfig: Validated configuration object

    Raises:
        ValidationError: If required environment variables are missing
    """
    return AppConfig()


# ============================================================================
# PostgreSQL Connection String Generation
# ============================================================================

def get_postgres_connection_string() -> str:
    """
    Generate PostgreSQL connection string based on authentication mode.

    Supports two authentication modes:
        1. Password-based: Uses POSTGIS_PASSWORD environment variable
        2. Managed Identity: Uses Azure AD token from system-assigned identity

    Returns:
        str: PostgreSQL connection string (psycopg format)

    Raises:
        ValueError: If required configuration is missing
        Exception: If managed identity token acquisition fails

    Example:
        >>> conn_string = get_postgres_connection_string()
        >>> conn = psycopg.connect(conn_string)
    """
    config = get_app_config()

    if config.use_managed_identity:
        return _build_managed_identity_connection_string(config)
    else:
        return _build_password_connection_string(config)


def _build_password_connection_string(config: AppConfig) -> str:
    """
    Build password-based connection string.

    Args:
        config: Application configuration

    Returns:
        str: Connection string with embedded password

    Note:
        SSL is enforced (sslmode=require) for Azure PostgreSQL
        Password is URL-encoded to handle special characters like @ symbols
    """
    from urllib.parse import quote_plus

    logger.info(f"Building password-based connection string for {config.postgis_host}")

    # URL-encode password to handle special characters (e.g., @ symbols)
    encoded_password = quote_plus(config.postgis_password)

    conn_string = (
        f"postgresql://{config.postgis_user}:{encoded_password}"
        f"@{config.postgis_host}:{config.postgis_port}"
        f"/{config.postgis_database}"
        f"?sslmode=require"
    )

    return conn_string


def _build_managed_identity_connection_string(config: AppConfig) -> str:
    """
    Build managed identity connection string with Azure AD token.

    This function acquires an Azure AD access token using the system-assigned
    managed identity and constructs a connection string with the token as password.

    Args:
        config: Application configuration

    Returns:
        str: Connection string with Azure AD token as password

    Raises:
        Exception: If token acquisition fails

    Note:
        Token is acquired synchronously and has limited lifetime (~1 hour).
        For long-running connections, consider implementing token refresh.
    """
    logger.info(f"Building managed identity connection string for {config.postgis_host}")

    try:
        from azure.identity import DefaultAzureCredential

        # Acquire Azure AD token for PostgreSQL
        # Scope for Azure Database for PostgreSQL: https://ossrdbms-aad.database.windows.net/.default
        credential = DefaultAzureCredential()
        token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")

        logger.info("✅ Successfully acquired managed identity token")

        # Build connection string with token as password
        conn_string = (
            f"postgresql://{config.postgis_user}:{token.token}"
            f"@{config.postgis_host}:{config.postgis_port}"
            f"/{config.postgis_database}"
            f"?sslmode=require"
        )

        return conn_string

    except ImportError:
        logger.error("azure-identity package not installed")
        raise ValueError(
            "Managed identity requires azure-identity package. "
            "Install with: pip install azure-identity"
        )
    except Exception as e:
        logger.error(f"Failed to acquire managed identity token: {e}")
        raise Exception(
            f"Managed identity authentication failed: {e}. "
            "Ensure system-assigned managed identity is enabled and has database permissions."
        )


# ============================================================================
# Connection String Caching
# ============================================================================

# Cache connection string to avoid repeated token acquisition
# Note: For managed identity, tokens expire after ~1 hour
# Consider implementing token refresh for long-running processes
_cached_connection_string: Optional[str] = None


@lru_cache(maxsize=1)
def get_cached_postgres_connection_string() -> str:
    """
    Get cached PostgreSQL connection string.

    For password-based auth: Safe to cache indefinitely
    For managed identity: Token expires after ~1 hour, may need refresh

    Returns:
        str: Cached connection string

    Note:
        Use get_postgres_connection_string() directly if you need
        fresh token for managed identity authentication
    """
    return get_postgres_connection_string()


# ============================================================================
# Configuration Validation
# ============================================================================

def validate_configuration() -> bool:
    """
    Validate configuration on application startup.

    Returns:
        bool: True if configuration is valid

    Raises:
        Exception: If configuration validation fails
    """
    try:
        config = get_app_config()
        logger.info("Configuration validation:")
        logger.info(f"  PostgreSQL Host: {config.postgis_host}")
        logger.info(f"  PostgreSQL Port: {config.postgis_port}")
        logger.info(f"  Database: {config.postgis_database}")
        logger.info(f"  User: {config.postgis_user}")
        logger.info(f"  Managed Identity: {config.use_managed_identity}")

        # Test connection string generation
        conn_string = get_postgres_connection_string()
        logger.info("✅ Connection string generated successfully")

        return True

    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        raise


# ============================================================================
# Module Initialization
# ============================================================================

if __name__ == "__main__":
    # For testing configuration
    logging.basicConfig(level=logging.INFO)
    validate_configuration()
