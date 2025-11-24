# Deployment Guide

Complete guide for deploying rmhogcapi to Azure.

---

## Prerequisites

Before deploying, ensure you have:

- **Azure subscription** with appropriate permissions
- **Azure CLI** installed and logged in (`az login`)
- **Azure Functions Core Tools** 4.x installed
- **Python 3.11** installed locally
- **PostgreSQL server** with PostGIS and pgSTAC extensions

---

## Deployment Overview

The deployment process involves:

1. Creating Azure resources (Function App, Storage Account)
2. Configuring PostgreSQL database access
3. Setting up managed identity authentication
4. Deploying application code
5. Configuring application settings
6. Testing endpoints

---

## Step 1: Create Azure Resources

### Create Resource Group (if needed)

```bash
az group create \
  --name <your-resource-group> \
  --location eastus
```

### Create Storage Account

Required for Azure Functions runtime.

```bash
az storage account create \
  --name <your-storage-account> \
  --resource-group <your-resource-group> \
  --location eastus \
  --sku Standard_LRS
```

### Create Function App

```bash
az functionapp create \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --storage-account <your-storage-account> \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux \
  --consumption-plan-location eastus
```

**Production Tier Options:**

For production workloads, consider upgrading from Consumption to a dedicated plan:

```bash
# Create App Service Plan (Basic B1)
az appservice plan create \
  --name <your-app-service-plan> \
  --resource-group <your-resource-group> \
  --location eastus \
  --sku B1 \
  --is-linux

# Create Function App on dedicated plan
az functionapp create \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --plan <your-app-service-plan> \
  --storage-account <your-storage-account> \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4
```

---

## Step 2: Set Up Managed Identity

### Create User-Assigned Managed Identity

```bash
az identity create \
  --name <your-reader-identity> \
  --resource-group <your-resource-group>
```

### Get Identity Details

```bash
# Get Client ID
CLIENT_ID=$(az identity show \
  --name <your-reader-identity> \
  --resource-group <your-resource-group> \
  --query clientId \
  --output tsv)

echo "Client ID: $CLIENT_ID"

# Get Resource ID
IDENTITY_ID=$(az identity show \
  --name <your-reader-identity> \
  --resource-group <your-resource-group> \
  --query id \
  --output tsv)

echo "Identity ID: $IDENTITY_ID"
```

### Assign Identity to Function App

```bash
az functionapp identity assign \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --identities "$IDENTITY_ID"
```

### Create PostgreSQL Database Role

See **[DB_READER_SQL.md](../DB_READER_SQL.md)** for complete instructions on creating the PostgreSQL role for the managed identity.

**Quick summary**:

```bash
# 1. Get Azure AD token
TOKEN=$(az account get-access-token --resource-type oss-rdbms --query accessToken --output tsv)

# 2. Connect to postgres database and create role
PGPASSWORD="$TOKEN" psql \
  -h <your-postgresql-server>.postgres.database.azure.com \
  -U "<your-admin-user>@<your-domain>.onmicrosoft.com" \
  -d postgres \
  -c "SELECT * FROM pgaadauth_create_principal('<your-reader-identity>', false, false);"

# 3. Grant permissions (connect to <your-database> database as schema owner)
PGPASSWORD='your-password' psql \
  -h <your-postgresql-server>.postgres.database.azure.com \
  -U <your-db-user> \
  -d <your-database> \
  -c "GRANT USAGE ON SCHEMA geo TO <your-reader-identity>;
      GRANT SELECT ON ALL TABLES IN SCHEMA geo TO <your-reader-identity>;
      GRANT USAGE ON SCHEMA pgstac TO <your-reader-identity>;
      GRANT SELECT ON ALL TABLES IN SCHEMA pgstac TO <your-reader-identity>;
      GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA pgstac TO <your-reader-identity>;"
```

---

## Step 3: Configure Application Settings

### Set Database Connection Settings

```bash
az functionapp config appsettings set \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --settings \
    POSTGIS_HOST="<your-postgresql-server>.postgres.database.azure.com" \
    POSTGIS_PORT="5432" \
    POSTGIS_DATABASE="<your-database>" \
    POSTGIS_USER="<your-reader-identity>" \
    USE_MANAGED_IDENTITY="true" \
    AZURE_CLIENT_ID="$CLIENT_ID"
```

### Set OGC Features Settings

```bash
az functionapp config appsettings set \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --settings \
    OGC_SCHEMA="geo" \
    OGC_GEOMETRY_COLUMN="geom" \
    OGC_DEFAULT_LIMIT="100" \
    OGC_MAX_LIMIT="10000" \
    OGC_DEFAULT_PRECISION="6" \
    OGC_ENABLE_VALIDATION="true" \
    OGC_QUERY_TIMEOUT="30"
```

### Set STAC Settings (optional)

```bash
az functionapp config appsettings set \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --settings \
    STAC_CATALOG_ID="rmh-geospatial-stac" \
    STAC_CATALOG_TITLE="RMH Geospatial STAC API" \
    STAC_DESCRIPTION="STAC catalog for geospatial raster and vector data"
```

---

## Step 4: Configure Network Access

### Allow Function App IP in PostgreSQL Firewall

```bash
# Get Function App outbound IPs
az functionapp show \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --query possibleOutboundIpAddresses \
  --output tsv

# Add firewall rules for each IP
az postgres flexible-server firewall-rule create \
  --resource-group <your-resource-group> \
  --name rmhpgflex \
  --rule-name allow-function-app \
  --start-ip-address <IP-ADDRESS> \
  --end-ip-address <IP-ADDRESS>
```

**Note**: For production, consider using VNet integration instead of public IPs.

---

## Step 5: Deploy Application Code

### Build and Deploy

```bash
# Navigate to project directory
cd rmhogcapi

# Deploy to Azure
func azure functionapp publish <your-function-app>
```

Expected output:

```
Getting site publishing info...
Creating archive for current directory...
Uploading 15.23 MB [###########################]
Upload completed successfully.
Deployment successful.
Remote build succeeded!
Syncing triggers...
Functions in <your-function-app>:
    health - [httpTrigger]
        Invoke url: https://<your-function-app>.azurewebsites.net/api/health

    ogc_features_landing - [httpTrigger]
        Invoke url: https://<your-function-app>.azurewebsites.net/api/features

    ... (and more)
```

---

## Step 6: Configure CORS (if needed)

For frontend applications accessing the API:

```bash
az functionapp cors add \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --allowed-origins "https://rmhazuregeo.z13.web.core.windows.net"
```

Or allow all origins (development only):

```bash
az functionapp cors add \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --allowed-origins "*"
```

---

## Step 7: Restart and Verify

### Restart Function App

```bash
az functionapp restart \
  --name <your-function-app> \
  --resource-group <your-resource-group>
```

### Test Health Endpoints

The application provides two health endpoints optimized for APIM integration:

```bash
# Wait for restart
sleep 15

# Public health check (minimal response for external callers)
curl https://<your-function-app>.azurewebsites.net/api/health

# Detailed health check (for APIM probes and operations)
curl https://<your-function-app>.azurewebsites.net/api/health/detailed
```

**Public health response** (`/api/health`):

```json
{
  "status": "healthy",
  "service": "rmhogcapi",
  "timestamp": "2025-11-24T12:00:00.000000"
}
```

**Detailed health response** (`/api/health/detailed`):

```json
{
  "status": "healthy",
  "service": "rmhogcapi",
  "version": "1.0.0",
  "timestamp": "2025-11-24T12:00:00.000000",
  "checks": {
    "database": {
      "status": "pass",
      "latency_ms": 45.2,
      "message": "Connected successfully",
      "details": {
        "host": "rmhpgflex.postgres.database.azure.com",
        "database": "geopgflex",
        "auth_method": "managed_identity"
      }
    },
    "geo_schema": {
      "status": "pass",
      "latency_ms": 12.3,
      "message": "5 collections available",
      "details": { "collection_count": 5 }
    },
    "pgstac_schema": {
      "status": "pass",
      "latency_ms": 18.7,
      "message": "5 collections, 18 items",
      "details": { "collection_count": 5, "item_count": 18 }
    },
    "api_modules": {
      "status": "pass",
      "latency_ms": 0.5,
      "message": "All modules loaded"
    }
  },
  "summary": {
    "total_checks": 4,
    "passed": 4,
    "failed": 0,
    "total_latency_ms": 76.7
  }
}
```

**Health Status Codes:**
- `200 OK` - Service is healthy or degraded (still operational)
- `503 Service Unavailable` - Service is unhealthy (detailed endpoint only)

**APIM Integration Note:** The `/api/health/detailed` endpoint should be accessible only to APIM probes via APIM policy rules. External traffic should use `/api/health` which returns minimal information.

### Test OGC Features

```bash
# List collections
curl https://<your-function-app>.azurewebsites.net/api/features/collections | jq '.collections | length'

# Query features
curl "https://<your-function-app>.azurewebsites.net/api/features/collections/{collection-id}/items?limit=10"
```

### Test STAC API

```bash
# List STAC collections
curl https://<your-function-app>.azurewebsites.net/api/stac/collections | jq '.collections | length'

# Query STAC items
curl "https://<your-function-app>.azurewebsites.net/api/stac/collections/{collection-id}/items?limit=10"
```

---

## Step 8: Monitor and Troubleshoot

### View Live Logs

```bash
func azure functionapp logstream <your-function-app>
```

### View Application Insights

```bash
# Get Application Insights key
az functionapp config appsettings list \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --query "[?name=='APPINSIGHTS_INSTRUMENTATIONKEY'].value" \
  --output tsv
```

View logs in Azure Portal:
1. Navigate to Function App → Application Insights
2. View "Live Metrics" for real-time monitoring
3. Use "Logs" for detailed query analysis

---

## Deployment Checklist

Use this checklist to ensure successful deployment:

- [ ] Azure Function App created (Linux, Python 3.11)
- [ ] Storage account created and linked
- [ ] User-assigned managed identity created
- [ ] Managed identity assigned to Function App
- [ ] PostgreSQL role created for managed identity
- [ ] Database permissions granted (geo, pgstac, h3 schemas)
- [ ] PostgreSQL firewall rules configured
- [ ] Application settings configured:
  - [ ] `USE_MANAGED_IDENTITY=true`
  - [ ] `AZURE_CLIENT_ID` set
  - [ ] `POSTGIS_*` settings configured
  - [ ] `OGC_*` settings configured
- [ ] Application code deployed (`func azure functionapp publish`)
- [ ] CORS configured (if needed)
- [ ] Function App restarted
- [ ] Public health endpoint (`/api/health`) returns "healthy"
- [ ] Detailed health endpoint (`/api/health/detailed`) shows all checks passing
- [ ] OGC collections endpoint returns data
- [ ] STAC collections endpoint returns data
- [ ] Application Insights monitoring enabled

---

## Updating Deployment

### Update Application Code

```bash
# Make code changes locally
# Test locally with `func start`

# Deploy updates
func azure functionapp publish <your-function-app>

# Verify deployment
curl https://<your-function-app>.azurewebsites.net/api/health
```

### Update Application Settings

```bash
# Update single setting
az functionapp config appsettings set \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --settings OGC_DEFAULT_LIMIT="200"

# Restart to apply changes
az functionapp restart \
  --name <your-function-app> \
  --resource-group <your-resource-group>
```

---

## CI/CD Pipeline (Optional)

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure Functions

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Deploy to Azure Functions
      run: |
        func azure functionapp publish <your-function-app> --python
```

---

## Production Best Practices

1. **Use Dedicated Hosting Plan**: Upgrade from Consumption to Basic or Premium plan for consistent performance
2. **Enable Application Insights**: Monitor performance and diagnose issues
3. **Configure VNet Integration**: Secure database access without public IPs
4. **Set up Alerts**: Monitor health endpoint and error rates
5. **Use Deployment Slots**: Test updates in staging slot before production
6. **Implement API Management**: Add rate limiting, caching, and custom domains
7. **Enable HTTPS Only**: Enforce secure connections
8. **Regular Security Updates**: Keep Python runtime and dependencies updated

---

## Scaling Considerations

### Horizontal Scaling

Azure Functions automatically scales based on load (Consumption plan).

For dedicated plans:

```bash
az appservice plan update \
  --name <your-app-service-plan> \
  --resource-group <your-resource-group> \
  --number-of-workers 3
```

### Database Optimization

- Ensure spatial indexes on geometry columns
- Monitor query performance with Application Insights
- Consider read replicas for high-traffic scenarios
- Use connection pooling for dedicated plans

---

## Troubleshooting Deployment

See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for common deployment issues.

**Quick fixes:**

- **Deployment fails**: Check Python version matches (3.11)
- **Functions not visible**: Check `function_app.py` and `host.json` are included
- **Connection errors**: Verify firewall rules and managed identity setup
- **Empty responses**: Check database has data in `geo` and `pgstac` schemas

---

## Next Steps

- **[Authentication Guide](AUTHENTICATION.md)** - Manage database access
- **[Configuration](CONFIGURATION.md)** - Adjust settings
- **[API Reference](API_REFERENCE.md)** - Explore endpoints
- **[Troubleshooting](TROUBLESHOOTING.md)** - Resolve issues
