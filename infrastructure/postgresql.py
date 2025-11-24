# ============================================================================
# CLAUDE CONTEXT - POSTGRESQL REPOSITORY
# ============================================================================
# STATUS: Core Infrastructure - PostgreSQL connection management
# PURPOSE: PostgreSQL database access for read-only STAC and OGC APIs
# LAST_REVIEWED: Current
# EXPORTS: PostgreSQLRepository
# DEPENDENCIES: psycopg, config, util_logger
# SOURCE: Extracted from rmhgeoapi/infrastructure/postgresql.py
# SCOPE: Read-only database operations for API serving
# PATTERNS: Repository pattern, Per-request connections, Managed identity
# ============================================================================

"""
PostgreSQL Repository - Read-Only Database Access

Provides PostgreSQL connection management for rmhogcapi with support for:
- Password-based authentication (local development)
- Azure Managed Identity authentication (production)
- Per-request connection creation (no pooling)
- Safe SQL execution with psycopg.sql composition
- Schema verification

This is a simplified extraction from rmhgeoapi that removes Job/Task-specific
repository classes, keeping only the core PostgreSQLRepository base class needed
for STAC and OGC API database access.

Usage:
    from infrastructure.postgresql import PostgreSQLRepository

    repo = PostgreSQLRepository(schema_name='pgstac')
    with repo._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM pgstac.collections")
            collections = cursor.fetchall()
"""

import os
import logging
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from typing import Optional, Tuple, Any
from contextlib import contextmanager

from config import get_postgres_connection_string

# Logger setup
logger = logging.getLogger(__name__)


class PostgreSQLRepository:
    """
    PostgreSQL repository base class with connection management.

    Provides core database access functionality for read-only API operations.
    Supports both password-based and managed identity authentication via the
    config module's get_postgres_connection_string() function.

    Features:
    - Connection string from config module (managed identity or password)
    - Connection context managers for safe resource cleanup
    - SQL composition for injection safety
    - Schema verification on initialization
    - Cursor context managers with auto-commit options

    Connection Strategy:
    -------------------
    Each operation creates a NEW connection and closes it immediately after use.
    No connection pooling is used - suitable for serverless Azure Functions
    where connection reuse across requests is not beneficial.

    Example:
    -------
    ```python
    repo = PostgreSQLRepository(schema_name='pgstac')

    # Single query with auto-commit
    with repo._get_cursor() as cursor:
        cursor.execute("SELECT * FROM pgstac.collections")
        collections = cursor.fetchall()

    # Multi-statement transaction
    with repo._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM pgstac.collections")
            collections = cursor.fetchall()
        conn.commit()
    ```
    """

    def __init__(self, connection_string: Optional[str] = None,
                 schema_name: str = 'pgstac'):
        """
        Initialize PostgreSQL repository.

        Parameters:
        ----------
        connection_string : Optional[str]
            Explicit PostgreSQL connection string. If not provided,
            uses get_postgres_connection_string() from config module.

        schema_name : str
            Database schema name. Defaults to 'pgstac' for STAC API.
            Use 'geo' for OGC Features API.

        Side Effects:
        ------------
        - Acquires connection string (may fetch managed identity token)
        - Validates schema existence (warning if missing)
        - Logs initialization status
        """
        # Set schema name
        self.schema_name = schema_name

        # Get connection string (from parameter or config)
        if connection_string:
            self.conn_string = connection_string
        else:
            self.conn_string = get_postgres_connection_string()

        # Validate that schema exists (non-blocking warning if missing)
        self._ensure_schema_exists()

        logger.info(f"✅ PostgreSQLRepository initialized with schema: {self.schema_name}")

    @contextmanager
    def _get_connection(self):
        """
        Context manager for PostgreSQL database connections.

        Provides safe connection lifecycle management:
        1. Create connection using connection string
        2. Yield connection to caller
        3. On error: rollback transaction
        4. Always: close connection

        Yields:
        ------
        psycopg.Connection
            Active PostgreSQL connection with dict_row factory.
            Autocommit is OFF by default (explicit commit needed).

        Raises:
        ------
        psycopg.Error
            On connection failures (network, auth, etc.)

        Usage:
        -----
        ```python
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
            conn.commit()
        ```
        """
        conn = None
        try:
            logger.debug(f"🔗 Attempting PostgreSQL connection to schema: {self.schema_name}")

            # Create connection with dict_row factory for easy result access
            conn = psycopg.connect(self.conn_string, row_factory=dict_row)
            logger.debug(f"✅ PostgreSQL connection established")

            yield conn

        except psycopg.Error as e:
            logger.error(f"❌ PostgreSQL connection error: {e}")
            logger.error(f"  Error type: {type(e).__name__}")

            # Rollback any pending transaction
            if conn:
                try:
                    conn.rollback()
                except:
                    pass

            raise

        finally:
            # Always close connection to free resources
            if conn:
                try:
                    conn.close()
                    logger.debug("🔒 Connection closed")
                except:
                    pass

    @contextmanager
    def _get_cursor(self, conn=None):
        """
        Context manager for PostgreSQL cursors with auto-transaction handling.

        Provides two modes:
        1. Use existing connection (for multi-statement transactions)
        2. Create new connection (auto-commits on success)

        Parameters:
        ----------
        conn : Optional[psycopg.Connection]
            Existing connection to use. If None, creates new connection
            with auto-commit behavior.

        Yields:
        ------
        psycopg.Cursor
            Database cursor for executing queries.

        Transaction Behavior:
        --------------------
        - With conn: Caller controls transaction (no auto-commit)
        - Without conn: Auto-commits on success, auto-rollback on error

        Usage:
        -----
        ```python
        # Single operation (auto-commit)
        with self._get_cursor() as cursor:
            cursor.execute("SELECT * FROM table")
            result = cursor.fetchall()

        # Multi-statement transaction
        with self._get_connection() as conn:
            with self._get_cursor(conn) as cursor:
                cursor.execute("SELECT * FROM table")
            conn.commit()
        ```
        """
        if conn:
            # Use existing connection - caller controls transaction
            with conn.cursor() as cursor:
                yield cursor
        else:
            # Create new connection with auto-commit
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    yield cursor
                    conn.commit()

    def _ensure_schema_exists(self) -> None:
        """
        Verify that the target database schema exists.

        Checks if the configured schema exists in the database. Logs a warning
        if missing but doesn't fail - actual operations will fail with specific
        errors if the schema is genuinely missing.

        Side Effects:
        ------------
        - Creates temporary database connection
        - Logs schema status (exists/missing/error)

        Error Handling:
        --------------
        - Schema missing: WARNING logged, continues
        - Connection fails: ERROR logged, continues
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check schema existence in information_schema
                    cursor.execute(
                        sql.SQL("SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s"),
                        (self.schema_name,)
                    )

                    if not cursor.fetchone():
                        logger.warning(
                            f"⚠️ Schema '{self.schema_name}' does not exist. "
                            f"Database operations may fail."
                        )
                    else:
                        logger.debug(f"✅ Schema '{self.schema_name}' exists")

        except Exception as e:
            logger.error(f"❌ Error checking schema existence: {e}")

    def _execute_query(self, query: sql.Composed, params: Optional[Tuple] = None,
                      fetch: Optional[str] = None) -> Optional[Any]:
        """
        Execute a PostgreSQL query with automatic commit and error handling.

        This is a convenience method for simple read operations. For more complex
        scenarios, use _get_connection() or _get_cursor() directly.

        Parameters:
        ----------
        query : sql.Composed
            SQL query built using psycopg.sql composition for injection safety.

        params : Optional[Tuple]
            Query parameters for %s placeholders.

        fetch : Optional[str]
            Fetch mode: None | 'one' | 'all'

        Returns:
        -------
        Optional[Any]
            - fetch='one': Single row or None
            - fetch='all': List of rows
            - fetch=None: Row count for DML, None for DDL

        Raises:
        ------
        TypeError
            If query is not sql.Composed (security requirement)

        ValueError
            If fetch parameter is invalid

        RuntimeError
            For any database operation failure

        Example:
        -------
        ```python
        query = sql.SQL("SELECT * FROM {schema}.collections WHERE id = %s").format(
            schema=sql.Identifier(self.schema_name)
        )
        result = self._execute_query(query, ('my-collection',), fetch='one')
        ```
        """
        # Validate query type for security
        if not isinstance(query, sql.Composed):
            raise TypeError(f"Query must be sql.Composed, got {type(query)}")

        # Validate fetch mode
        if fetch and fetch not in ['one', 'all']:
            raise ValueError(f"Invalid fetch mode: {fetch}")

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Execute query
                    cursor.execute(query, params)
                    logger.debug("✅ Query executed successfully")

                    # Handle fetch operations
                    result = None
                    if fetch == 'one':
                        result = cursor.fetchone()
                    elif fetch == 'all':
                        result = cursor.fetchall()

                    # Commit transaction
                    conn.commit()
                    logger.debug("✅ Transaction committed")

                    # Return result based on operation type
                    if fetch:
                        return result
                    else:
                        return cursor.rowcount if cursor.rowcount >= 0 else None

        except psycopg.Error as e:
            logger.error(f"❌ Query execution failed: {e}")
            raise RuntimeError(f"Database query failed: {e}") from e

    def _table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the schema.

        Parameters:
        ----------
        table_name : str
            Name of the table to check (without schema prefix)

        Returns:
        -------
        bool
            True if table exists in configured schema, False otherwise

        Example:
        -------
        ```python
        repo = PostgreSQLRepository(schema_name='pgstac')
        if repo._table_exists('collections'):
            print("Collections table exists")
        ```
        """
        # Use simple query without sql.Composed - just direct execution
        try:
            with self._get_cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = %s
                        AND table_name = %s
                    ) as exists
                """, (self.schema_name, table_name))
                result = cursor.fetchone()
                return result['exists'] if result else False
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
