# ============================================================================
# CLAUDE CONTEXT - STAC API OPENAPI SPECIFICATION
# ============================================================================
# STATUS: Core Infrastructure - OpenAPI 3.0 specification for STAC API
# PURPOSE: Provide OpenAPI spec document required by STAC API Core conformance
# CREATED: 24 NOV 2025
# EXPORTS: get_openapi_spec
# DEPENDENCIES: None (pure Python dict generation)
# SPEC_REF: https://github.com/radiantearth/stac-api-spec/tree/main/core
# ============================================================================

"""
OpenAPI 3.0 Specification for STAC API

This module provides the OpenAPI specification document required by STAC API Core
conformance class. The spec requires a service-desc link pointing to an OpenAPI
definition of the service.

Usage:
    from stac_api.openapi import get_openapi_spec

    spec = get_openapi_spec("https://example.com")
    # Returns OpenAPI 3.0 dict
"""

from typing import Dict, Any


def get_openapi_spec(base_url: str) -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification for STAC API.

    Args:
        base_url: Base URL for server definition (e.g., https://example.com)

    Returns:
        OpenAPI 3.0 specification dict

    Example:
        spec = get_openapi_spec("https://myapi.com")
        # spec["openapi"] == "3.0.3"
    """
    from stac_api.config import get_stac_config
    config = get_stac_config()

    return {
        "openapi": "3.0.3",
        "info": {
            "title": config.catalog_title,
            "description": f"STAC API v1.0.0 - {config.catalog_description}. "
                          "Provides standards-compliant access to SpatioTemporal Asset Catalog collections and items.",
            "version": "1.0.0",
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
            {"name": "Collections", "description": "STAC Collection access"},
            {"name": "Items", "description": "STAC Item access"}
        ],
        "paths": {
            "/": {
                "get": {
                    "tags": ["Core"],
                    "summary": "Landing Page",
                    "description": "Returns the STAC Catalog root with links to available resources",
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
                    "description": "Returns the list of conformance classes implemented by this API",
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
            "/api": {
                "get": {
                    "tags": ["Core"],
                    "summary": "OpenAPI Specification",
                    "description": "Returns this OpenAPI 3.0 specification document",
                    "operationId": "getOpenAPI",
                    "responses": {
                        "200": {
                            "description": "OpenAPI specification",
                            "content": {
                                "application/vnd.oai.openapi+json;version=3.0": {
                                    "schema": {"type": "object"}
                                },
                                "application/json": {
                                    "schema": {"type": "object"}
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
                    "description": "Returns all available STAC collections",
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
                    "description": "Returns a single STAC collection by ID",
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
                            "description": "Collection not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
                                }
                            }
                        }
                    }
                }
            },
            "/collections/{collectionId}/items": {
                "get": {
                    "tags": ["Items"],
                    "summary": "Get Collection Items",
                    "description": "Returns items in a collection with pagination support",
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
                            "schema": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 1000
                            },
                            "description": "Maximum number of items to return"
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "default": 0,
                                "minimum": 0
                            },
                            "description": "Number of items to skip for pagination"
                        },
                        {
                            "name": "bbox",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Bounding box filter (minx,miny,maxx,maxy in WGS84)",
                            "example": "-180,-90,180,90"
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
                            "description": "Collection not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
                                }
                            }
                        }
                    }
                }
            },
            "/collections/{collectionId}/items/{itemId}": {
                "get": {
                    "tags": ["Items"],
                    "summary": "Get Item",
                    "description": "Returns a single STAC item by ID",
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
                            "description": "Item not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
                                }
                            }
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
                        "id": {"type": "string", "description": "Catalog identifier"},
                        "type": {"type": "string", "enum": ["Catalog"]},
                        "stac_version": {"type": "string", "example": "1.0.0"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "conformsTo": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Conformance classes implemented"
                        },
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"}
                        }
                    }
                },
                "Conformance": {
                    "type": "object",
                    "required": ["conformsTo"],
                    "properties": {
                        "conformsTo": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of conformance class URIs"
                        }
                    }
                },
                "Collections": {
                    "type": "object",
                    "required": ["collections", "links"],
                    "properties": {
                        "collections": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Collection"}
                        },
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"}
                        }
                    }
                },
                "Collection": {
                    "type": "object",
                    "required": ["id", "type", "stac_version", "description", "license", "extent", "links"],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["Collection"]},
                        "stac_version": {"type": "string"},
                        "stac_extensions": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "license": {"type": "string"},
                        "extent": {"$ref": "#/components/schemas/Extent"},
                        "summaries": {"type": "object"},
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"}
                        },
                        "assets": {"type": "object"}
                    }
                },
                "ItemCollection": {
                    "type": "object",
                    "required": ["type", "features"],
                    "properties": {
                        "type": {"type": "string", "enum": ["FeatureCollection"]},
                        "features": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Item"}
                        },
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"}
                        },
                        "numberMatched": {
                            "type": "integer",
                            "description": "Total number of items matching the query"
                        },
                        "numberReturned": {
                            "type": "integer",
                            "description": "Number of items in this response"
                        }
                    }
                },
                "Item": {
                    "type": "object",
                    "required": ["id", "type", "geometry", "bbox", "properties", "links", "assets"],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["Feature"]},
                        "stac_version": {"type": "string"},
                        "stac_extensions": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "geometry": {
                            "type": "object",
                            "description": "GeoJSON geometry"
                        },
                        "bbox": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 4,
                            "description": "Bounding box [minx, miny, maxx, maxy]"
                        },
                        "properties": {
                            "type": "object",
                            "required": ["datetime"],
                            "properties": {
                                "datetime": {
                                    "type": "string",
                                    "format": "date-time",
                                    "nullable": True
                                }
                            }
                        },
                        "links": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Link"}
                        },
                        "assets": {
                            "type": "object",
                            "additionalProperties": {"$ref": "#/components/schemas/Asset"}
                        },
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
                "Asset": {
                    "type": "object",
                    "required": ["href"],
                    "properties": {
                        "href": {"type": "string", "format": "uri"},
                        "type": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "roles": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "Extent": {
                    "type": "object",
                    "properties": {
                        "spatial": {
                            "type": "object",
                            "properties": {
                                "bbox": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "number"}
                                    }
                                }
                            }
                        },
                        "temporal": {
                            "type": "object",
                            "properties": {
                                "interval": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {
                                            "type": "string",
                                            "format": "date-time",
                                            "nullable": True
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "Error": {
                    "type": "object",
                    "required": ["code", "description"],
                    "properties": {
                        "code": {"type": "string"},
                        "description": {"type": "string"}
                    }
                }
            }
        }
    }
