# Database Migrations

This directory contains database migrations for the Synergos application.

## How to use migrations

### Create a new migration

```bash
flask db migrate -m "Description of the migration"
```

### Apply migrations

```bash
flask db upgrade
```

### Downgrade to a previous version

```bash
flask db downgrade
```

## Migration Guidelines

1. Always review auto-generated migrations before applying them
2. Test migrations on development before production
3. Add detailed messages to help understand the purpose of each migration
4. Avoid making changes directly to migration files after they're applied to production 