#!/bin/bash

# CineScope Database Restore Script
# Usage: ./scripts/restore_db.sh <backup_file.sql.gz>

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore_db.sh <backup_file.sql.gz>"
    echo "Available backups:"
    ls -lh backups/
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "WARNING: This will drop and recreate the database!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo "Stopping backend..."
docker-compose stop backend

echo "Dropping existing database..."
docker exec cinescope_db psql -U cinescopeuser -d postgres -c "DROP DATABASE IF EXISTS cinescope;"

echo "Creating fresh database..."
docker exec cinescope_db psql -U cinescopeuser -d postgres -c "CREATE DATABASE cinescope;"

echo "Restoring from backup..."
gunzip -c $BACKUP_FILE | docker exec -i cinescope_db psql -U cinescopeuser -d cinescope

echo "Starting backend..."
docker-compose start backend

echo "Restore completed!"