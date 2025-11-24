# Quick Start Guide

Get rmhogcapi running locally in 5 minutes.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Azure Functions Core Tools 4.x** ([install guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local))
- **Azure CLI** (optional, for deployment)
- **Access to PostgreSQL** with PostGIS extension

---

## Step 1: Clone and Install

```bash
# Clone the repository
git clone <repository-url>
cd rmhogcapi

# Create virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Configure Local Settings

```bash
# Copy the example settings file
cp local.settings.example.json local.settings.json
```

Edit `local.settings.json` with your database credentials:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",

    "POSTGIS_HOST": "your-server.postgres.database.azure.com",
    "POSTGIS_PORT": "5432",
    "POSTGIS_DATABASE": "<your-database>",
    "POSTGIS_USER": "your-username",
    "POSTGIS_PASSWORD": "your-password",
    "USE_MANAGED_IDENTITY": "false",

    "OGC_SCHEMA": "geo",
    "OGC_GEOMETRY_COLUMN": "geom"
  }
}
```

**Important**: Use `USE_MANAGED_IDENTITY=false` for local development with password authentication.

---

## Step 3: Start Local Server

```bash
func start
```

You should see output like:

```
Azure Functions Core Tools
Core Tools Version:       4.x.x
Function Runtime Version: 4.x.x

Functions:

	health: [GET] http://localhost:7071/api/health

	ogc_features_landing: [GET] http://localhost:7071/api/features
	ogc_features_conformance: [GET] http://localhost:7071/api/features/conformance
	ogc_features_collections: [GET] http://localhost:7071/api/features/collections
	... (and more)
```

---

## Step 4: Test Endpoints

### Health Check

```bash
curl http://localhost:7071/api/health | jq '.'
```

Expected response:

```json
{
  "status": "healthy",
  "app": "rmhogcapi",
  "description": "OGC Features & STAC API Service",
  "apis": {
    "ogc_features": {
      "available": true,
      "schema": "geo",
      "endpoints": 6
    },
    "stac": {
      "available": true,
      "schema": "pgstac",
      "endpoints": 6
    }
  }
}
```

### List OGC Collections

```bash
curl http://localhost:7071/api/features/collections | jq '.collections | length'
```

### List STAC Collections

```bash
curl http://localhost:7071/api/stac/collections | jq '.collections | length'
```

---

## Step 5: Explore the APIs

### OGC Features API

```bash
# Get collection metadata
curl http://localhost:7071/api/features/collections/{collection-id} | jq '.'

# Query features (first 10)
curl "http://localhost:7071/api/features/collections/{collection-id}/items?limit=10" | jq '.features | length'

# Spatial filter (bounding box)
curl "http://localhost:7071/api/features/collections/{collection-id}/items?bbox=-180,-90,180,90&limit=100"
```

### STAC API

```bash
# Get STAC catalog
curl http://localhost:7071/api/stac | jq '.'

# Get collection metadata
curl http://localhost:7071/api/stac/collections/{collection-id} | jq '.'

# Query items
curl "http://localhost:7071/api/stac/collections/{collection-id}/items?limit=20" | jq '.features | length'
```

---

## Common Issues

### Issue: "Connection refused" error

**Solution**: Ensure PostgreSQL server is accessible from your local machine. Check firewall rules if using Azure PostgreSQL.

### Issue: "No collections found"

**Solution**: Verify that your database has tables in the `geo` schema (for OGC) or `pgstac.collections` table (for STAC).

### Issue: "Password authentication failed"

**Solution**: Check that credentials in `local.settings.json` are correct. For special characters in passwords, ensure they're properly formatted.

---

## Next Steps

- **[Configuration Guide](CONFIGURATION.md)** - Learn about all environment variables
- **[API Reference](API_REFERENCE.md)** - Complete endpoint documentation
- **[Deployment Guide](DEPLOYMENT.md)** - Deploy to Azure
- **[Authentication](AUTHENTICATION.md)** - Set up managed identity

---

## Development Tips

### Hot Reload

Azure Functions Core Tools supports hot reload. Just edit your code and save - the function will restart automatically.

### Debugging

Use VS Code with the Azure Functions extension for breakpoint debugging:

1. Open project in VS Code
2. Press F5 to start debugging
3. Set breakpoints in your code
4. Test endpoints with curl or browser

### Testing

```bash
# Run unit tests (if available)
pytest tests/

# Test specific endpoint
curl -v http://localhost:7071/api/features/collections
```

---

**Need Help?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.
