# Authentication Guide

Complete guide for configuring Azure Managed Identity authentication with PostgreSQL.

---

## Overview

rmhogcapi uses **Azure User-Assigned Managed Identity** for secure, passwordless PostgreSQL authentication. This eliminates the need to store database passwords in application settings and provides:

- **No Secrets Storage**: No passwords in environment variables or configuration
- **Automatic Token Refresh**: Azure handles token lifecycle (1-hour expiry)
- **Audit Trail**: All access logged through Azure AD and PostgreSQL
- **Shared Identity**: Single identity used across multiple apps (TiTiler, rmhogcapi, etc.)
- **Read-Only Access**: Database role has SELECT-only permissions

---

## Authentication Architecture

```
Azure Function App (<your-function-app>)
         ↓
User-Assigned Managed Identity (<your-reader-identity>)
         ↓
Azure AD Token Service
         ↓
PostgreSQL (Entra ID authentication)
         ↓
Database Role (read-only permissions)
```

---

## Current Configuration

### Production Setup (Active)

| Component | Value |
|-----------|-------|
| **Identity Name** | `<your-reader-identity>` |
| **Client ID** | `1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f` |
| **Principal ID** | `789cc11a-d667-4915-b4de-88e76eda1cfb` |
| **PostgreSQL User** | `<your-reader-identity>` |
| **Database Permissions** | SELECT on `geo`, `pgstac`, `h3` schemas |
| **Function App** | `<your-function-app>` |
| **Status** | ✅ **Active and Working** |

### Application Settings

```bash
USE_MANAGED_IDENTITY=true
AZURE_CLIENT_ID=1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f
POSTGIS_USER=<your-reader-identity>
POSTGIS_HOST=<your-postgresql-server>.postgres.database.azure.com
POSTGIS_DATABASE=<your-database>
# POSTGIS_PASSWORD - NOT SET (not needed with managed identity)
```

---

## How It Works

### 1. Token Acquisition

When the application starts or needs to connect to PostgreSQL:

```python
from azure.identity import ManagedIdentityCredential

# Create credential with user-assigned identity client ID
credential = ManagedIdentityCredential(
    client_id="1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f"
)

# Get token for PostgreSQL
token = credential.get_token(
    "https://ossrdbms-aad.database.windows.net/.default"
)
```

### 2. PostgreSQL Connection

The token is used as the password in the connection string:

```python
conn_string = (
    f"postgresql://{user}:{token.token}"
    f"@{host}:{port}/{database}"
    f"?sslmode=require"
)
```

### 3. Token Lifecycle

- **Expiry**: Tokens expire after approximately 1 hour
- **Refresh**: `azure-identity` SDK automatically handles refresh
- **Caching**: Tokens are cached and reused until near expiry

---

## Setting Up Managed Identity

### Prerequisites

1. Azure subscription with appropriate permissions
2. PostgreSQL Flexible Server with Entra ID authentication enabled
3. Entra ID administrator configured on PostgreSQL server
4. Azure CLI installed and logged in

### Complete Setup Guide

See **[DB_READER_SQL.md](../DB_READER_SQL.md)** for step-by-step instructions including:

1. Creating the user-assigned managed identity
2. Creating the PostgreSQL role with Entra ID authentication
3. Granting read-only permissions
4. Assigning identity to Function App
5. Configuring application settings
6. Testing the connection

**Quick Summary**:

```bash
# 1. Create managed identity
az identity create \
  --name <your-reader-identity> \
  --resource-group <your-resource-group>

# 2. Get Client ID
CLIENT_ID=$(az identity show \
  --name <your-reader-identity> \
  --resource-group <your-resource-group> \
  --query clientId \
  --output tsv)

# 3. Create PostgreSQL role (connect to postgres database as Entra ID admin)
TOKEN=$(az account get-access-token --resource-type oss-rdbms --query accessToken --output tsv)
PGPASSWORD="$TOKEN" psql \
  -h <your-postgresql-server>.postgres.database.azure.com \
  -U "<your-admin-user>@<your-domain>.onmicrosoft.com" \
  -d postgres \
  -c "SELECT * FROM pgaadauth_create_principal('<your-reader-identity>', false, false);"

# 4. Grant permissions (connect to <your-database> as schema owner)
PGPASSWORD='password' psql \
  -h <your-postgresql-server>.postgres.database.azure.com \
  -U <your-db-user> \
  -d <your-database> \
  -c "GRANT USAGE ON SCHEMA geo TO <your-reader-identity>;
      GRANT SELECT ON ALL TABLES IN SCHEMA geo TO <your-reader-identity>;
      GRANT USAGE ON SCHEMA pgstac TO <your-reader-identity>;
      GRANT SELECT ON ALL TABLES IN SCHEMA pgstac TO <your-reader-identity>;
      GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA pgstac TO <your-reader-identity>;"

# 5. Assign identity to Function App
IDENTITY_ID=$(az identity show \
  --name <your-reader-identity> \
  --resource-group <your-resource-group> \
  --query id \
  --output tsv)

az functionapp identity assign \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --identities "$IDENTITY_ID"

# 6. Configure application settings
az functionapp config appsettings set \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --settings \
    USE_MANAGED_IDENTITY="true" \
    AZURE_CLIENT_ID="$CLIENT_ID" \
    POSTGIS_USER="<your-reader-identity>"

# 7. Restart and test
az functionapp restart \
  --name <your-function-app> \
  --resource-group <your-resource-group>

curl https://<your-function-app>.azurewebsites.net/api/health
```

---

## Authentication Modes

rmhogcapi supports two authentication modes:

### 1. Managed Identity (Production - Recommended)

**Use when**: Deploying to Azure

**Configuration**:
```json
{
  "USE_MANAGED_IDENTITY": "true",
  "AZURE_CLIENT_ID": "1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f",
  "POSTGIS_USER": "<your-reader-identity>"
}
```

**Advantages**:
- No password storage
- Automatic token rotation
- Centralized access management
- Audit trail via Azure AD

**Requirements**:
- User-assigned managed identity created
- Identity assigned to Function App
- PostgreSQL role created with `pgaadauth_create_principal`
- Database permissions granted

### 2. Password-Based (Local Development)

**Use when**: Running locally for development

**Configuration**:
```json
{
  "USE_MANAGED_IDENTITY": "false",
  "POSTGIS_USER": "<your-db-user>",
  "POSTGIS_PASSWORD": "your-password"
}
```

**Note**: Never use password authentication in production Azure deployments.

---

## Database Permissions

The `<your-reader-identity>` identity has **read-only** access:

### Granted Permissions

| Schema | Tables | Functions | Sequences |
|--------|--------|-----------|-----------|
| `geo` | SELECT | - | - |
| `pgstac` | SELECT | EXECUTE | - |
| `h3` | SELECT | EXECUTE | - |

### NOT Granted

- INSERT, UPDATE, DELETE on any tables
- CREATE on any schemas
- TRUNCATE, REFERENCES, TRIGGER
- ALTER, DROP on any objects

This ensures the API can only **read** data, never modify it.

---

## Security Best Practices

### 1. Use Separate Identities for Different Access Levels

| Identity | Client ID | Permissions | Use Case |
|----------|-----------|-------------|----------|
| `<your-reader-identity>` | `1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f` | Read-only | APIs, tile servers |
| `rmhpgflexadmin` | `a533cb80-a590-4fad-8e52-1eb1f72659d7` | ALL PRIVILEGES | ETL, management |

See **[DB_ADMIN_SQL.md](../DB_ADMIN_SQL.md)** for admin identity setup.

### 2. Principle of Least Privilege

- Read-only APIs use `<your-reader-identity>` (SELECT only)
- ETL systems use `rmhpgflexadmin` (full access)
- Never grant more permissions than needed

### 3. Network Security

- Enable Entra ID authentication on PostgreSQL server
- Use SSL/TLS for all connections (`sslmode=require`)
- Restrict PostgreSQL firewall rules to Function App IPs
- Consider VNet integration for production

### 4. Monitoring and Auditing

- Enable Application Insights for Function App
- Monitor PostgreSQL logs for access patterns
- Review Azure AD sign-in logs for token requests
- Set up alerts for authentication failures

---

## Troubleshooting

### Issue: "password authentication failed for user <your-reader-identity>"

**Cause**: PostgreSQL role not created as Entra ID principal.

**Solution**: Role must be created using `pgaadauth_create_principal()` on the `postgres` database, not with regular `CREATE ROLE` command.

```bash
# Correct way:
PGPASSWORD="$TOKEN" psql -h <server> -U <admin> -d postgres \
  -c "SELECT * FROM pgaadauth_create_principal('<your-reader-identity>', false, false);"

# Wrong way:
PGPASSWORD="$TOKEN" psql -h <server> -U <admin> -d <your-database> \
  -c "CREATE ROLE <your-reader-identity>;"
```

### Issue: "function pgaadauth_create_principal does not exist"

**Cause**: Connected to wrong database.

**Solution**: `pgaadauth_*` functions only exist in the `postgres` system database, not user databases.

```bash
# Correct - connects to postgres database
psql -d postgres -c "SELECT * FROM pgaadauth_create_principal(...);"

# Wrong - connects to <your-database>
psql -d <your-database> -c "SELECT * FROM pgaadauth_create_principal(...);"
```

### Issue: "Could not validate AAD user"

**Cause**: Managed identity name doesn't match PostgreSQL role name.

**Solution**: Ensure:
1. PostgreSQL role name matches managed identity name exactly
2. `POSTGIS_USER` setting matches the role name
3. `AZURE_CLIENT_ID` matches the identity's client ID

### Issue: "permission denied for schema"

**Cause**: Permissions not granted or granted by wrong user.

**Solution**: Re-run GRANT statements as the schema owner (usually the user who created the schema).

### Issue: Token acquisition fails

**Cause**: Managed identity not assigned to Function App.

**Solution**:
```bash
# Verify identity assignment
az functionapp identity show \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --query "userAssignedIdentities"

# Should show <your-reader-identity> in the list
```

---

## Verifying Authentication

### Check Application Settings

```bash
az functionapp config appsettings list \
  --name <your-function-app> \
  --resource-group <your-resource-group> \
  --query "[?name=='USE_MANAGED_IDENTITY' || name=='AZURE_CLIENT_ID' || name=='POSTGIS_USER'].{name:name, value:value}" \
  --output table
```

Expected output:
```
Name                  Value
--------------------  ------------------------------------
POSTGIS_USER          <your-reader-identity>
USE_MANAGED_IDENTITY  true
AZURE_CLIENT_ID       1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f
```

### Test Endpoints

```bash
# Health check
curl https://<your-function-app>.azurewebsites.net/api/health

# OGC Features
curl https://<your-function-app>.azurewebsites.net/api/features/collections

# STAC API
curl https://<your-function-app>.azurewebsites.net/api/stac/collections
```

If all endpoints return data, managed identity authentication is working correctly.

---

## Code Implementation

### Configuration Module ([config.py](../config.py))

The application handles managed identity authentication in `config.py`:

```python
from azure.identity import ManagedIdentityCredential
from urllib.parse import quote_plus

def _build_managed_identity_connection_string(config: AppConfig) -> str:
    """Build connection string with Azure AD token."""

    # Create credential with user-assigned identity
    credential = ManagedIdentityCredential(
        client_id=config.azure_client_id
    )

    # Acquire token for PostgreSQL
    token = credential.get_token(
        "https://ossrdbms-aad.database.windows.net/.default"
    )

    # URL-encode token (may contain special characters)
    encoded_token = quote_plus(token.token)

    # Build connection string with token as password
    conn_string = (
        f"postgresql://{config.postgis_user}:{encoded_token}"
        f"@{config.postgis_host}:{config.postgis_port}"
        f"/{config.postgis_database}"
        f"?sslmode=require"
    )

    return conn_string
```

### Environment Variables

```python
class AppConfig(BaseSettings):
    # PostgreSQL connection
    postgis_host: str
    postgis_port: int = 5432
    postgis_database: str
    postgis_user: str
    postgis_password: Optional[str] = None

    # Authentication mode
    use_managed_identity: bool = False
    azure_client_id: Optional[str] = None

    @model_validator(mode='after')
    def validate_auth_config(self):
        """Ensure password provided when not using managed identity."""
        if not self.use_managed_identity and not self.postgis_password:
            raise ValueError(
                "POSTGIS_PASSWORD required when USE_MANAGED_IDENTITY=false"
            )
        return self
```

---

## Related Identities

| Identity | Client ID | Purpose | Status |
|----------|-----------|---------|--------|
| `<your-reader-identity>` | `1c79a2fe-42cb-4f30-8fe9-c1dfc04f142f` | Read-only API access | ✅ Active |
| `rmhpgflexadmin` | `a533cb80-a590-4fad-8e52-1eb1f72659d7` | Admin ETL access | Available |
| `rmhtitileridentity` | `191869d4-fd0b-4b18-a058-51adc2dbd54b` | Legacy | Deprecated |

---

## References

- **[DB_READER_SQL.md](../DB_READER_SQL.md)** - Complete setup guide for read-only identity
- **[DB_ADMIN_SQL.md](../DB_ADMIN_SQL.md)** - Complete setup guide for admin identity
- **[Microsoft Docs - Connect with Managed Identity](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-connect-with-managed-identity)**
- **[Microsoft Docs - Manage Entra ID Users](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-manage-azure-ad-users)**
- **[Azure Identity SDK for Python](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme)**

---

## Next Steps

- **[Configuration Guide](CONFIGURATION.md)** - Environment variable reference
- **[Deployment Guide](DEPLOYMENT.md)** - Deploy to Azure
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues
