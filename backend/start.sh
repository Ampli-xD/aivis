#!/bin/bash
set -e

# Render mounts the disk at /var/lib/postgresql/data
DATA_DIR="/var/lib/postgresql/data"
PG_CONF="/var/lib/postgresql/data/postgresql.conf"

# 1. Initialize Postgres if data directory is empty
if [ ! -s "$PG_CONF" ]; then
    echo "Initializing database..."
    # Ensure the directory exists and has correct permissions
    mkdir -p "$DATA_DIR"
    chown -R postgres:postgres "$DATA_DIR"
    
    # Run initdb as the postgres user
    su postgres -c "/usr/lib/postgresql/15/bin/initdb -D $DATA_DIR"
    
    # Allow connections from localhost
    echo "host all all 127.0.0.1/32 trust" >> "$DATA_DIR/pg_hba.conf"
fi

# Ensure permissions are correct every time (Render disk mounts can be tricky)
chown -R postgres:postgres "$DATA_DIR"

# 2. Cleanup stale pid file (critical for persistent disks on Render restarts)
if [ -f "$DATA_DIR/postmaster.pid" ]; then
    echo "Found stale postmaster.pid. Cleaning up..."
    rm -f "$DATA_DIR/postmaster.pid"
fi

# 3. Start Postgres server in the background
echo "Starting PostgreSQL..."
su postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D $DATA_DIR -l /var/log/postgresql/pg.log start"

# 4. Wait for Postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
until su postgres -c "pg_isready -h localhost" > /dev/null 2>&1; do
    echo "Postgres is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is up and running!"

# 5. Create User and Database if they don't exist
DB_USER=${POSTGRES_USER:-admin}
DB_NAME=${POSTGRES_DB:-aivis}
DB_PASS=${POSTGRES_PASSWORD:-password_dishant_29}

echo "Ensuring user and database exist..."
su postgres -c "psql -tc \"SELECT 1 FROM pg_user WHERE usename = '$DB_USER'\" | grep -q 1 || psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS' SUPERUSER;\""
su postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'\" | grep -q 1 || psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\""

# 6. Apply Schema
if [ -f "schema.sql" ]; then
    echo "Applying schema..."
    PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -f schema.sql
fi

# 7. Start FastAPI application
echo "Starting FastAPI app..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
