# Configuration Guide

Complete reference for rmhogcapi environment variables and configuration settings.

---

## Configuration Overview

rmhogcapi uses environment variables for all configuration. In local development, these are set in `local.settings.json`. In Azure, they're configured as Application Settings.

---

## PostgreSQL Connection Settings

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGIS_HOST` | PostgreSQL server hostname | `<your-postgresql-server>.postgres.database.azure.com` |
| `POSTGIS_PORT` | PostgreSQL server port | `5432` |
| `POSTGIS_DATABASE` | Database name | `<your-database>` |
| `POSTGIS_USER` | Database username or managed identity name | `<your-db-user>` or `rmhpgflexreader` |
| `POSTGIS_PASSWORD` | Database password (not required with managed identity) | `your-password` |

### Authentication Mode

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `USE_MANAGED_IDENTITY` | boolean | `false` | Enable Azure managed identity authentication |
| `AZURE_CLIENT_ID` | string | _(empty)_ | Client ID of user-assigned managed identity |

**Authentication Modes:**

1. **Password-based** (local development):
   ```json
   {
     "USE_MANAGED_IDENTITY": "false",
     "POSTGIS_USER": "<your-db-user>",
     "POSTGIS_PASSWORD": "your-password"
   }
   ```

2. **Managed Identity** (Azure production):
   ```json
   {
     "USE_MANAGED_IDENTITY": "true",
     "AZURE_CLIENT_ID": "1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f",
     "POSTGIS_USER": "rmhpgflexreader"
   }
   ```

See [AUTHENTICATION.md](AUTHENTICATION.md) for detailed setup instructions.

---

## OGC Features API Settings

### Schema Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OGC_SCHEMA` | string | `geo` | PostgreSQL schema containing vector tables |
| `OGC_GEOMETRY_COLUMN` | string | `geom` | Default geometry column name |

**Note**: Use `shape` for ArcGIS-generated tables, `geom` for standard PostGIS.

### Query Limits

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OGC_DEFAULT_LIMIT` | integer | `100` | Default number of features returned per request |
| `OGC_MAX_LIMIT` | integer | `10000` | Maximum features allowed per request |

**Example**:
```json
{
  "OGC_DEFAULT_LIMIT": "100",
  "OGC_MAX_LIMIT": "10000"
}
```

### Geometry Processing

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OGC_DEFAULT_PRECISION` | integer | `6` | Coordinate decimal precision (digits after decimal point) |
| `OGC_ENABLE_VALIDATION` | boolean | `true` | Enable spatial index validation on startup |

**Precision Examples:**
- `6` → 0.111 meter precision (standard)
- `7` → 0.011 meter precision (high precision)
- `5` → 1.11 meter precision (coarse)

### Performance

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OGC_QUERY_TIMEOUT` | integer | `30` | Query timeout in seconds |

---

## STAC API Settings

### Catalog Metadata

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `STAC_CATALOG_ID` | string | `rmh-geospatial-stac` | STAC catalog identifier |
| `STAC_CATALOG_TITLE` | string | `RMH Geospatial STAC API` | Human-readable catalog title |
| `STAC_DESCRIPTION` | string | _(auto)_ | Catalog description |
| `STAC_BASE_URL` | string | _(auto)_ | Base URL for STAC links |

**Example**:
```json
{
  "STAC_CATALOG_ID": "rmh-geospatial-stac",
  "STAC_CATALOG_TITLE": "RMH Geospatial STAC API",
  "STAC_DESCRIPTION": "STAC catalog for geospatial raster and vector data",
  "STAC_BASE_URL": "https://<your-function-app>.azurewebsites.net"
}
```

---

## Azure Functions Settings

### Runtime Configuration

These are standard Azure Functions settings - do not modify unless necessary.

| Variable | Value | Description |
|----------|-------|-------------|
| `AzureWebJobsStorage` | `UseDevelopmentStorage=true` | Local storage emulator (local dev only) |
| `FUNCTIONS_WORKER_RUNTIME` | `python` | Function runtime language |

---

## CORS Configuration

CORS is configured in `local.settings.json` (local) or Azure portal (production).

**Local Development** (`local.settings.json`):
```json
{
  "Host": {
    "CORS": "*",
    "CORSCredentials": false
  }
}
```

**Azure Portal**:
1. Go to Function App → CORS
2. Add allowed origins (e.g., `https://rmhazuregeo.z13.web.core.windows.net`)
3. Enable "Support Credentials" if needed

---

## Complete Configuration Example

### Local Development (`local.settings.json`)

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",

    "POSTGIS_HOST": "<your-postgresql-server>.postgres.database.azure.com",
    "POSTGIS_PORT": "5432",
    "POSTGIS_DATABASE": "<your-database>",
    "POSTGIS_USER": "<your-db-user>",
    "POSTGIS_PASSWORD": "your-password",
    "USE_MANAGED_IDENTITY": "false",
    "AZURE_CLIENT_ID": "",

    "OGC_SCHEMA": "geo",
    "OGC_GEOMETRY_COLUMN": "geom",
    "OGC_DEFAULT_LIMIT": "100",
    "OGC_MAX_LIMIT": "10000",
    "OGC_DEFAULT_PRECISION": "6",
    "OGC_ENABLE_VALIDATION": "true",
    "OGC_QUERY_TIMEOUT": "30",

    "STAC_CATALOG_ID": "rmh-geospatial-stac",
    "STAC_CATALOG_TITLE": "RMH Geospatial STAC API",
    "STAC_DESCRIPTION": "STAC catalog for geospatial raster and vector data"
  },
  "Host": {
    "CORS": "*",
    "CORSCredentials": false
  }
}
```

### Azure Production (Application Settings)

```bash
az functionapp config appsettings set \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --settings \
    POSTGIS_HOST="<your-postgresql-server>.postgres.database.azure.com" \
    POSTGIS_PORT="5432" \
    POSTGIS_DATABASE="<your-database>" \
    POSTGIS_USER="rmhpgflexreader" \
    USE_MANAGED_IDENTITY="true" \
    AZURE_CLIENT_ID="1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f" \
    OGC_SCHEMA="geo" \
    OGC_GEOMETRY_COLUMN="geom" \
    OGC_DEFAULT_LIMIT="100" \
    OGC_MAX_LIMIT="10000"
```

---

## Configuration Validation

The application validates configuration on startup. Check the logs for validation errors:

```bash
# Local development
func start

# Azure (view logs)
func azure functionapp logstream <your-function-app>
```

**Validation checks:**
- PostgreSQL connection parameters present
- Password required when `USE_MANAGED_IDENTITY=false`
- Managed identity client ID present when `USE_MANAGED_IDENTITY=true`
- Numeric values in valid ranges

---

## Environment-Specific Settings

### Development

```json
{
  "USE_MANAGED_IDENTITY": "false",
  "POSTGIS_PASSWORD": "dev-password",
  "OGC_ENABLE_VALIDATION": "true"
}
```

### Production

```json
{
  "USE_MANAGED_IDENTITY": "true",
  "AZURE_CLIENT_ID": "1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f",
  "OGC_ENABLE_VALIDATION": "false"
}
```

---

## Security Best Practices

1. **Never commit** `local.settings.json` to source control (already in `.gitignore`)
2. **Use managed identity** in production (no password storage)
3. **URL-encode passwords** with special characters
4. **Rotate credentials** regularly
5. **Limit CORS origins** to trusted domains in production
6. **Enable SSL/TLS** for all PostgreSQL connections (enforced by default)

---

## Troubleshooting Configuration Issues

### Issue: Configuration validation fails

**Solution**: Check that all required environment variables are set. Review startup logs for specific validation errors.

### Issue: Password authentication fails with special characters

**Solution**: Special characters in passwords must be URL-encoded when passed in connection strings. The application handles this automatically, but ensure the raw password is correct in settings.

### Issue: Managed identity not working

**Solution**: Verify:
1. `USE_MANAGED_IDENTITY=true`
2. `AZURE_CLIENT_ID` matches the managed identity
3. Identity is assigned to the Function App
4. PostgreSQL role exists (see [DB_READER_SQL.md](../DB_READER_SQL.md))

---

## Next Steps

- **[Authentication Guide](AUTHENTICATION.md)** - Set up managed identity
- **[Deployment Guide](DEPLOYMENT.md)** - Deploy to Azure
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues
