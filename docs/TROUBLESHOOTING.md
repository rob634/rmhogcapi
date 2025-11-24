# Troubleshooting Guide

Common issues and solutions for rmhogcapi.

---

## Quick Diagnostics

Start with these basic checks:

```bash
# 1. Check health endpoint
curl https://<your-function-app>.azurewebsites.net/api/health

# 2. View live logs
func azure functionapp logstream <your-function-app>

# 3. Check application settings
az functionapp config appsettings list \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --output table
```

---

## Database Connection Issues

### Issue: "Connection timeout" or "Connection refused"

**Symptoms**:
- Health endpoint returns error
- All API endpoints fail
- Logs show connection timeout

**Possible Causes**:
1. PostgreSQL firewall rules don't allow Function App IPs
2. Database server is down
3. Network configuration issues

**Solutions**:

1. **Check and add firewall rules**:
   ```bash
   # Get Function App outbound IPs
   az functionapp show \
     --name <your-function-app> \
     --resource-group <your-resource-group> \
     --query possibleOutboundIpAddresses \
     --output tsv

   # Add each IP to PostgreSQL firewall
   az postgres flexible-server firewall-rule create \
     --resource-group <your-resource-group> \
     --name rmhpgflex \
     --rule-name allow-function-app-1 \
     --start-ip-address <IP> \
     --end-ip-address <IP>
   ```

2. **Verify PostgreSQL server status**:
   ```bash
   az postgres flexible-server show \
     --resource-group <your-resource-group> \
     --name rmhpgflex \
     --query state
   ```

3. **Test connection locally** (if on home network):
   ```bash
   PGPASSWORD='password' psql \
     -h <your-postgresql-server>.postgres.database.azure.com \
     -U <your-db-user> \
     -d <your-database> \
     -c "SELECT version();"
   ```

---

### Issue: "password authentication failed"

**Symptoms**:
- Health endpoint returns error
- Logs show authentication failure
- Connection attempt fails with password error

**Possible Causes**:
1. Managed identity not set up correctly
2. PostgreSQL role doesn't exist or is not Entra ID-enabled
3. Wrong username in settings

**Solutions**:

1. **Verify managed identity settings**:
   ```bash
   az functionapp config appsettings list \
     --name <your-function-app> \
     --resource-group <your-resource-group> \
     --query "[?name=='USE_MANAGED_IDENTITY' || name=='AZURE_CLIENT_ID' || name=='POSTGIS_USER']"
   ```

   Expected:
   ```json
   {
     "USE_MANAGED_IDENTITY": "true",
     "AZURE_CLIENT_ID": "1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f",
     "POSTGIS_USER": "rmhpgflexreader"
   }
   ```

2. **Verify PostgreSQL role exists** (when on home network):
   ```bash
   TOKEN=$(az account get-access-token --resource-type oss-rdbms --query accessToken --output tsv)

   PGPASSWORD="$TOKEN" psql \
     -h <your-postgresql-server>.postgres.database.azure.com \
     -U "<your-admin-user>@<your-domain>.onmicrosoft.com" \
     -d postgres \
     -c "SELECT rolname FROM pg_roles WHERE rolname = 'rmhpgflexreader';"
   ```

3. **Recreate PostgreSQL role** if needed:

   See **[DB_READER_SQL.md](../DB_READER_SQL.md)** for complete setup instructions.

---

### Issue: "permission denied for schema" or "permission denied for table"

**Symptoms**:
- Health endpoint works
- Collections endpoint returns empty array
- Logs show "permission denied for schema geo"

**Possible Causes**:
1. Database permissions not granted
2. Permissions granted by wrong user
3. Permissions granted on wrong database

**Solutions**:

1. **Verify permissions** (when on home network):
   ```bash
   PGPASSWORD='password' psql \
     -h <your-postgresql-server>.postgres.database.azure.com \
     -U <your-db-user> \
     -d <your-database> \
     -c "SELECT
           n.nspname as schema,
           has_schema_privilege('rmhpgflexreader', n.nspname, 'USAGE') as has_usage
         FROM pg_namespace n
         WHERE n.nspname IN ('geo', 'pgstac', 'h3');"
   ```

2. **Re-grant permissions** (must be run by schema owner):
   ```bash
   PGPASSWORD='password' psql \
     -h <your-postgresql-server>.postgres.database.azure.com \
     -U <your-db-user> \
     -d <your-database> \
     -c "GRANT USAGE ON SCHEMA geo TO rmhpgflexreader;
         GRANT SELECT ON ALL TABLES IN SCHEMA geo TO rmhpgflexreader;
         GRANT USAGE ON SCHEMA pgstac TO rmhpgflexreader;
         GRANT SELECT ON ALL TABLES IN SCHEMA pgstac TO rmhpgflexreader;
         GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA pgstac TO rmhpgflexreader;"
   ```

---

## Empty or Missing Data Issues

### Issue: Collections endpoint returns empty array

**Symptoms**:
- Health endpoint shows `"available": true`
- Collections endpoint returns `{"collections": []}`
- No errors in logs

**Possible Causes**:
1. No tables in target schema
2. Tables missing geometry columns
3. Wrong schema configured

**Solutions**:

1. **Verify tables exist**:
   ```bash
   PGPASSWORD='password' psql \
     -h <your-postgresql-server>.postgres.database.azure.com \
     -U <your-db-user> \
     -d <your-database> \
     -c "SELECT schemaname, tablename
         FROM pg_tables
         WHERE schemaname = 'geo'
         ORDER BY tablename;"
   ```

2. **Check geometry columns**:
   ```bash
   PGPASSWORD='password' psql \
     -h <your-postgresql-server>.postgres.database.azure.com \
     -U <your-db-user> \
     -d <your-database> \
     -c "SELECT f_table_schema, f_table_name, f_geometry_column
         FROM geometry_columns
         WHERE f_table_schema = 'geo';"
   ```

3. **Verify OGC_SCHEMA setting**:
   ```bash
   az functionapp config appsettings list \
     --name <your-function-app> \
     --resource-group <your-resource-group> \
     --query "[?name=='OGC_SCHEMA']"
   ```

   Should be `"geo"` for PostGIS vector tables.

---

### Issue: STAC collections endpoint returns empty array

**Symptoms**:
- OGC Features works fine
- STAC collections returns `{"collections": []}`
- Health shows STAC as available

**Possible Causes**:
1. pgSTAC schema not installed
2. No collections in `pgstac.collections` table
3. Permission issues with pgstac schema

**Solutions**:

1. **Verify pgSTAC schema exists**:
   ```bash
   PGPASSWORD='password' psql \
     -h <your-postgresql-server>.postgres.database.azure.com \
     -U <your-db-user> \
     -d <your-database> \
     -c "SELECT schema_name
         FROM information_schema.schemata
         WHERE schema_name = 'pgstac';"
   ```

2. **Check for collections**:
   ```bash
   PGPASSWORD='password' psql \
     -h <your-postgresql-server>.postgres.database.azure.com \
     -U <your-db-user> \
     -d <your-database> \
     -c "SELECT id, content->>'title' as title
         FROM pgstac.collections
         LIMIT 10;"
   ```

3. **Install pgSTAC** if not present:
   ```bash
   # Follow pgSTAC installation guide
   # https://github.com/stac-utils/pgstac
   ```

---

## Deployment Issues

### Issue: "func azure functionapp publish" fails

**Symptoms**:
- Deployment command hangs or fails
- Error message about Python version
- Remote build fails

**Solutions**:

1. **Verify Python version**:
   ```bash
   python --version  # Should be 3.11.x
   ```

2. **Check Azure CLI login**:
   ```bash
   az account show
   ```

3. **Verify Function App exists**:
   ```bash
   az functionapp show \
     --name <your-function-app> \
     --resource-group <your-resource-group>
   ```

4. **Try deployment with additional logging**:
   ```bash
   func azure functionapp publish <your-function-app> --python --verbose
   ```

---

### Issue: Functions not visible after deployment

**Symptoms**:
- Deployment succeeds
- No endpoints listed in deployment output
- Portal shows no functions

**Possible Causes**:
1. Missing `function_app.py`
2. Syntax errors in code
3. Missing `host.json`

**Solutions**:

1. **Verify required files**:
   ```bash
   ls -la function_app.py host.json requirements.txt
   ```

2. **Check for syntax errors**:
   ```bash
   python -m py_compile function_app.py
   ```

3. **Review deployment logs**:
   ```bash
   az functionapp log deployment list \
     --name <your-function-app> \
     --resource-group <your-resource-group>
   ```

---

## Query and Performance Issues

### Issue: Queries timeout or are very slow

**Symptoms**:
- Requests take longer than 30 seconds
- 500 errors with timeout messages
- Some collections work, others don't

**Possible Causes**:
1. Missing spatial indexes
2. Large result sets without limits
3. Complex geometries without simplification
4. Database performance issues

**Solutions**:

1. **Add spatial indexes**:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_tablename_geom
   ON geo.tablename USING GIST (geom);
   ```

2. **Use pagination**:
   ```bash
   # Bad - requests all features
   curl "https://<your-function-app>.azurewebsites.net/api/features/collections/large_table/items"

   # Good - requests 100 features at a time
   curl "https://<your-function-app>.azurewebsites.net/api/features/collections/large_table/items?limit=100"
   ```

3. **Adjust query timeout**:
   ```bash
   az functionapp config appsettings set \
     --name <your-function-app> \
     --resource-group <your-resource-group> \
     --settings OGC_QUERY_TIMEOUT="60"
   ```

---

### Issue: "Invalid geometry" or geometry errors

**Symptoms**:
- Some features return null geometry
- GeoJSON validation errors
- Rendering issues in map clients

**Possible Causes**:
1. Invalid geometries in database
2. Wrong SRID (not EPSG:4326)
3. Coordinate order issues

**Solutions**:

1. **Validate and fix geometries**:
   ```sql
   -- Find invalid geometries
   SELECT id, ST_IsValid(geom) as valid, ST_IsValidReason(geom) as reason
   FROM geo.tablename
   WHERE NOT ST_IsValid(geom);

   -- Fix invalid geometries
   UPDATE geo.tablename
   SET geom = ST_MakeValid(geom)
   WHERE NOT ST_IsValid(geom);
   ```

2. **Transform to EPSG:4326**:
   ```sql
   -- Check current SRID
   SELECT DISTINCT ST_SRID(geom) FROM geo.tablename;

   -- Transform if needed
   UPDATE geo.tablename
   SET geom = ST_Transform(geom, 4326)
   WHERE ST_SRID(geom) != 4326;
   ```

---

## Managed Identity Issues

### Issue: "Could not acquire managed identity token"

**Symptoms**:
- Health endpoint fails immediately
- Logs show token acquisition error
- Application won't start

**Possible Causes**:
1. Managed identity not assigned to Function App
2. Wrong client ID configured
3. Identity doesn't exist

**Solutions**:

1. **Verify identity assignment**:
   ```bash
   az functionapp identity show \
     --name <your-function-app> \
     --resource-group <your-resource-group> \
     --query "userAssignedIdentities"
   ```

2. **Reassign identity**:
   ```bash
   IDENTITY_ID=$(az identity show \
     --name rmhpgflexreader \
     --resource-group <your-resource-group> \
     --query id \
     --output tsv)

   az functionapp identity assign \
     --name <your-function-app> \
     --resource-group <your-resource-group> \
     --identities "$IDENTITY_ID"
   ```

3. **Verify client ID**:
   ```bash
   # Get correct client ID
   az identity show \
     --name rmhpgflexreader \
     --resource-group <your-resource-group> \
     --query clientId \
     --output tsv

   # Update application setting
   az functionapp config appsettings set \
     --name <your-function-app> \
     --resource-group <your-resource-group> \
     --settings AZURE_CLIENT_ID="<correct-client-id>"
   ```

---

## CORS Issues

### Issue: "CORS policy blocked" in browser

**Symptoms**:
- API works in curl/Postman
- Browser shows CORS error
- JavaScript fetch fails

**Solutions**:

1. **Configure CORS in Azure**:
   ```bash
   az functionapp cors add \
     --name <your-function-app> \
     --resource-group <your-resource-group> \
     --allowed-origins "https://your-frontend-domain.com"
   ```

2. **Allow all origins** (development only):
   ```bash
   az functionapp cors add \
     --name <your-function-app> \
     --resource-group <your-resource-group> \
     --allowed-origins "*"
   ```

3. **Verify CORS settings**:
   ```bash
   az functionapp cors show \
     --name <your-function-app> \
     --resource-group <your-resource-group>
   ```

---

## Local Development Issues

### Issue: "No module named 'azure.identity'"

**Symptoms**:
- Local function app fails to start
- Import errors in logs

**Solution**:

```bash
pip install -r requirements.txt
```

---

### Issue: Local development works but Azure deployment doesn't

**Symptoms**:
- `func start` works locally
- Azure deployment fails or returns errors

**Possible Causes**:
1. Different environment variables
2. Missing dependencies in requirements.txt
3. Python version mismatch

**Solutions**:

1. **Verify requirements.txt**:
   ```bash
   pip freeze > requirements.txt
   ```

2. **Match Python versions**:
   ```bash
   python --version  # Should be 3.11.x
   ```

3. **Test with Azure settings locally**:

   Edit `local.settings.json` to match Azure settings, then test.

---

## Monitoring and Logging

### View Real-Time Logs

```bash
# Azure Functions logs
func azure functionapp logstream <your-function-app>

# Application Insights logs (Azure Portal)
# Navigate to: Function App → Application Insights → Live Metrics
```

### Query Logs

```bash
# Recent errors
az monitor app-insights query \
  --app <app-insights-id> \
  --analytics-query "traces | where severityLevel >= 3 | order by timestamp desc | take 20"
```

---

## Getting Help

If issues persist:

1. **Check Application Insights** for detailed error traces
2. **Review PostgreSQL logs** for database errors
3. **Test with curl** to isolate client vs server issues
4. **Verify configuration** matches [CONFIGURATION.md](CONFIGURATION.md)
5. **Review authentication setup** in [AUTHENTICATION.md](AUTHENTICATION.md)

---

## Common Error Messages

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| "Connection timeout" | Firewall rules | Add Function App IPs to PostgreSQL firewall |
| "password authentication failed" | Managed identity not set up | Follow [DB_READER_SQL.md](../DB_READER_SQL.md) |
| "permission denied for schema" | Missing permissions | Re-run GRANT statements as schema owner |
| "function pgaadauth_create_principal does not exist" | Wrong database | Connect to `postgres` database, not `<your-database>` |
| "Collections not found" | No tables in schema | Verify tables exist and have geometry columns |
| "Invalid geometry" | Bad geometries in database | Run ST_MakeValid() on geometries |
| "Could not acquire token" | Identity not assigned | Assign managed identity to Function App |

---

## Next Steps

- **[Quick Start](QUICKSTART.md)** - Get started with local development
- **[Configuration](CONFIGURATION.md)** - Review all settings
- **[Authentication](AUTHENTICATION.md)** - Managed identity details
- **[Deployment](DEPLOYMENT.md)** - Deploy to Azure
