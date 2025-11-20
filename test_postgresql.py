#!/usr/bin/env python
"""
Test PostgreSQL Repository

Tests the PostgreSQLRepository class with pgstac schema.
"""

import os
import json

# Load environment from local.settings.json
with open('local.settings.json') as f:
    settings = json.load(f)
    for key, value in settings['Values'].items():
        os.environ[key] = value

print("Environment loaded from local.settings.json")

from infrastructure.postgresql import PostgreSQLRepository

# Test connection to pgstac schema
print('\nTesting PostgreSQLRepository with pgstac schema...')
repo = PostgreSQLRepository(schema_name='pgstac')
print('✅ Repository initialized')

# Test table exists
collections_exist = repo._table_exists('collections')
print(f'✅ Collections table exists: {collections_exist}')

items_exist = repo._table_exists('items')
print(f'✅ Items table exists: {items_exist}')

# Test simple query
with repo._get_cursor() as cursor:
    cursor.execute('SELECT COUNT(*) as count FROM pgstac.collections')
    result = cursor.fetchone()
    print(f'✅ Collection count: {result["count"]}')

print('\n✅ All PostgreSQLRepository tests passed!')
