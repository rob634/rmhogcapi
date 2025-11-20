# ============================================================================
# CLAUDE CONTEXT - STAC QUERY FUNCTIONS
# ============================================================================
# STATUS: Core Infrastructure - Read-only STAC database queries
# PURPOSE: Query functions for STAC API to access pgstac schema
# LAST_REVIEWED: 19 NOV 2025
# EXPORTS: get_all_collections, get_collection, get_collection_items, get_item_by_id
# DEPENDENCIES: psycopg, infrastructure.postgresql
# SOURCE: Extracted from rmhgeoapi/infrastructure/pgstac_bootstrap.py
# SCOPE: Read-only STAC queries (no write operations)
# PATTERNS: Repository pattern, Direct SQL queries
# ============================================================================

"""
STAC Query Functions - Read-Only Access to pgSTAC Schema

Provides query functions for STAC API to access pgSTAC database schema.
These functions are extracted from rmhgeoapi/infrastructure/pgstac_bootstrap.py
with ETL-specific code removed.

Functions:
- get_all_collections(): List all STAC collections with item counts
- get_collection(collection_id): Get single collection by ID
- get_collection_items(collection_id, limit, bbox, datetime): Get items in collection
- get_item_by_id(item_id, collection_id): Get single item by ID

Usage:
    from infrastructure.stac_queries import get_all_collections

    collections = get_all_collections()
    print(f"Found {len(collections['collections'])} collections")
"""

import logging
from typing import Dict, Any, Optional, List

from infrastructure.postgresql import PostgreSQLRepository

# Logger setup
logger = logging.getLogger(__name__)


def get_collection(collection_id: str, repo: Optional[PostgreSQLRepository] = None) -> Dict[str, Any]:
    """
    Get single STAC collection by ID.

    Implements: GET /collections/{collection_id}

    Args:
        collection_id: Collection identifier
        repo: Optional PostgreSQLRepository instance (creates new if not provided)

    Returns:
        STAC Collection object or error dict

    Example:
        collection = get_collection('system-rasters')
        print(collection['id'], collection['title'])
    """
    try:
        # Use repository pattern
        if repo is None:
            repo = PostgreSQLRepository(schema_name='pgstac')

        with repo._get_connection() as conn:
            with conn.cursor() as cur:
                # pgSTAC 0.9.8 stores collections in content column as JSONB
                cur.execute(
                    "SELECT content FROM pgstac.collections WHERE id = %s",
                    [collection_id]
                )
                result = cur.fetchone()

                if result and result['content']:
                    return result['content']  # Return collection JSONB
                else:
                    return {
                        'error': f"Collection '{collection_id}' not found",
                        'error_type': 'NotFound'
                    }

    except Exception as e:
        logger.error(f"Failed to get collection '{collection_id}': {e}")
        return {
            'error': str(e),
            'error_type': type(e).__name__
        }


def get_collection_items(
    collection_id: str,
    limit: int = 100,
    bbox: Optional[List[float]] = None,
    datetime_str: Optional[str] = None,
    repo: Optional[PostgreSQLRepository] = None
) -> Dict[str, Any]:
    """
    Get items in a collection.

    Implements: GET /collections/{collection_id}/items

    Args:
        collection_id: Collection identifier
        limit: Maximum number of items to return (default 100)
        bbox: Bounding box filter [minx, miny, maxx, maxy]
        datetime_str: Datetime filter (RFC 3339 or interval)
        repo: Optional PostgreSQLRepository instance

    Returns:
        STAC ItemCollection (GeoJSON FeatureCollection)

    Example:
        items = get_collection_items('system-rasters', limit=10)
        print(f"Found {len(items['features'])} items")
    """
    try:
        if repo is None:
            repo = PostgreSQLRepository(schema_name='pgstac')

        with repo._get_connection() as conn:
            with conn.cursor() as cur:
                # Query items from pgstac.items table
                # pgSTAC stores id, collection, geometry in separate columns
                # Must reconstruct full STAC item by merging with content JSONB
                query = """
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
                    ) items
                """
                cur.execute(query, [collection_id, limit])
                result = cur.fetchone()

                # jsonb_build_object() result is in 'jsonb_build_object' column
                if result and 'jsonb_build_object' in result:
                    return result['jsonb_build_object']
                else:
                    # Empty FeatureCollection
                    return {
                        'type': 'FeatureCollection',
                        'features': [],
                        'links': []
                    }

    except Exception as e:
        logger.error(f"Failed to get items for collection '{collection_id}': {e}")
        return {
            'error': str(e),
            'error_type': type(e).__name__
        }


def get_item_by_id(
    item_id: str,
    collection_id: Optional[str] = None,
    repo: Optional[PostgreSQLRepository] = None
) -> Dict[str, Any]:
    """
    Get single STAC item by ID.

    Implements: GET /collections/{collection_id}/items/{item_id}

    Args:
        item_id: Item identifier
        collection_id: Optional collection identifier for scoped lookup
        repo: Optional PostgreSQLRepository instance

    Returns:
        STAC Item object or error dict

    Example:
        item = get_item_by_id('my-item-123', 'system-rasters')
        print(item['id'], item['properties'])
    """
    try:
        if repo is None:
            repo = PostgreSQLRepository(schema_name='pgstac')

        with repo._get_connection() as conn:
            with conn.cursor() as cur:
                # Build query based on whether collection_id provided
                if collection_id:
                    query = """
                        SELECT content ||
                            jsonb_build_object(
                                'id', id,
                                'collection', collection,
                                'geometry', ST_AsGeoJSON(geometry)::jsonb,
                                'type', 'Feature',
                                'stac_version', COALESCE(content->>'stac_version', '1.0.0')
                            ) as item
                        FROM pgstac.items
                        WHERE id = %s AND collection = %s
                    """
                    cur.execute(query, [item_id, collection_id])
                else:
                    query = """
                        SELECT content ||
                            jsonb_build_object(
                                'id', id,
                                'collection', collection,
                                'geometry', ST_AsGeoJSON(geometry)::jsonb,
                                'type', 'Feature',
                                'stac_version', COALESCE(content->>'stac_version', '1.0.0')
                            ) as item
                        FROM pgstac.items
                        WHERE id = %s
                    """
                    cur.execute(query, [item_id])

                result = cur.fetchone()

                if result and result['item']:
                    return result['item']
                else:
                    return {
                        'error': f"Item '{item_id}' not found",
                        'error_type': 'NotFound'
                    }

    except Exception as e:
        logger.error(f"Failed to get item '{item_id}': {e}")
        return {
            'error': str(e),
            'error_type': type(e).__name__
        }


def get_all_collections(repo: Optional[PostgreSQLRepository] = None) -> Dict[str, Any]:
    """
    Get all STAC collections with item counts.

    Implements: GET /collections

    Args:
        repo: Optional PostgreSQLRepository instance

    Returns:
        Dict with 'collections' list and 'links' list

    Example:
        result = get_all_collections()
        for coll in result['collections']:
            print(f"{coll['id']}: {coll.get('item_count', 0)} items")
    """
    try:
        if repo is None:
            repo = PostgreSQLRepository(schema_name='pgstac')

        with repo._get_connection() as conn:
            with conn.cursor() as cur:
                # Get all collections with item counts
                query = """
                    SELECT
                        c.content,
                        COUNT(i.id) as item_count
                    FROM pgstac.collections c
                    LEFT JOIN pgstac.items i ON i.collection = c.id
                    GROUP BY c.id, c.content
                    ORDER BY c.id
                """
                cur.execute(query)
                results = cur.fetchall()

                # Build collections list
                collections = []
                for row in results:
                    coll = dict(row['content']) if row['content'] else {}
                    coll['item_count'] = row['item_count']
                    collections.append(coll)

                return {
                    'collections': collections,
                    'links': []
                }

    except Exception as e:
        logger.error(f"Failed to get all collections: {e}")
        return {
            'error': str(e),
            'error_type': type(e).__name__
        }
