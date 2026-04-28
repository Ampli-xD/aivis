#!/bin/bash
set -e

# Render mounts the disk at /var/lib/postgresql/data
DATA_DIR="/var/lib/postgresql/data"
PG_CONF="/var/lib/postgresql/data/postgresql.conf"
LOG_FILE="$DATA_DIR/pg_log.txt"

echo "Custom setup for Render Combo Container..."

# 1. Ensure required directories exist and are writable by postgres
mkdir -p /var/run/postgresql
chown -R postgres:postgres /var/run/postgresql

# 2. Initialize Postgres if data directory is empty
if [ ! -s "$PG_CONF" ]; then
    echo "Initializing database for the first time..."
    mkdir -p "$DATA_DIR"
    chown -R postgres:postgres "$DATA_DIR"
    su postgres -c "/usr/lib/postgresql/15/bin/initdb -D $DATA_DIR"
    echo "host all all 127.0.0.1/32 trust" >> "$DATA_DIR/pg_hba.conf"
fi

# Always fix permissions for the data dir
chown -R postgres:postgres "$DATA_DIR"

# 3. Cleanup stale pid file
if [ -f "$DATA_DIR/postmaster.pid" ]; then
    echo "Found stale postmaster.pid. Cleaning up..."
    rm -f "$DATA_DIR/postmaster.pid"
fi

# 4. Start Postgres server
echo "Starting PostgreSQL (logging to $LOG_FILE)..."
if ! su postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D $DATA_DIR -l $LOG_FILE start" ; then
    echo "FAILED TO START POSTGRES. Printing logs:"
    cat "$LOG_FILE"
    exit 1
fi

# 5. Wait for Postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
until su postgres -c "pg_isready -h localhost" > /dev/null 2>&1; do
    echo "Postgres is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is up and running!"

# 6. Create User and Database
DB_USER=${POSTGRES_USER:-admin}
DB_NAME=${POSTGRES_DB:-aivis}
DB_PASS=${POSTGRES_PASSWORD:-password_dishant_29}

echo "Ensuring user and database exist..."
su postgres -c "psql -tc \"SELECT 1 FROM pg_user WHERE usename = '$DB_USER'\" | grep -q 1 || psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS' SUPERUSER;\""
su postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'\" | grep -q 1 || psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\""

# 7. Apply Schema
if [ -f "schema.sql" ]; then
    echo "Applying schema..."
    PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -f schema.sql
fi

# 8. Start FastAPI application
echo "Starting FastAPI app..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
