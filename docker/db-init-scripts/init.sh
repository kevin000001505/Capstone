#!/bin/bash
set -e


# ── 1. Create roles ──
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'readonly') THEN
            CREATE ROLE readonly WITH LOGIN PASSWORD '${READONLY_PASSWORD}';
        END IF;
    END \$\$;

    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DEVELOPER_USER}') THEN
            CREATE ROLE ${DEVELOPER_USER} WITH LOGIN CREATEDB PASSWORD '${DEVELOPER_PASSWORD}';
        END IF;
    END \$\$;
EOSQL

# ── 2. Create the app database owned by developer ──
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    SELECT 'CREATE DATABASE $DEVELOPER_DB OWNER $DEVELOPER_USER'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DEVELOPER_DB')\gexec
EOSQL

# ── 3. Grant database-level privileges ──
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE $DEVELOPER_DB TO $DEVELOPER_USER;
    GRANT CONNECT ON DATABASE $DEVELOPER_DB TO readonly;
EOSQL

# ── 4. Create PostGIS extension as SUPERUSER (prefect) ──
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DEVELOPER_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL

# ── 5. Create tables, indexes, functions as developer ──
psql -v ON_ERROR_STOP=1 --username "$DEVELOPER_USER" --dbname "$DEVELOPER_DB" <<-EOSQL

    -- ── Tables ──
    CREATE TABLE IF NOT EXISTS flight_states (
        time            TIMESTAMPTZ NOT NULL,
        icao24          CHAR(6) NOT NULL,
        callsign        VARCHAR(8),
        origin_country  VARCHAR(100),

        time_pos        TIMESTAMPTZ,
        lat             DOUBLE PRECISION,
        lon             DOUBLE PRECISION,
        geo_altitude    REAL,
        baro_altitude   REAL,

        velocity        REAL,
        heading         REAL,
        vert_rate       REAL,
        on_ground       BOOLEAN DEFAULT FALSE,

        squawk          VARCHAR(8),
        spi             BOOLEAN DEFAULT FALSE,
        source          SMALLINT,
        sensors         INTEGER[],

        geom            GEOMETRY(POINT, 4326),

        PRIMARY KEY (time, icao24)
    ) PARTITION BY RANGE (time);

    -- ── Indexes ──
    CREATE INDEX IF NOT EXISTS idx_flight_geom     ON flight_states USING GIST (geom);
    CREATE INDEX IF NOT EXISTS idx_flight_icao      ON flight_states (icao24);
    CREATE INDEX IF NOT EXISTS idx_flight_callsign  ON flight_states (callsign);

    -- ── Grants for readonly ──
    GRANT USAGE  ON SCHEMA public TO readonly;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;

    -- ── Partition function ──
    CREATE OR REPLACE FUNCTION create_partition_if_missing(date_val TIMESTAMPTZ)
    RETURNS void AS \$\$
    DECLARE
        start_date DATE := date_trunc('month', date_val);
        end_date   DATE := start_date + interval '1 month';
        table_name TEXT := 'flight_states_' || to_char(start_date, 'YYYY_MM');
    BEGIN
        IF NOT EXISTS (
            SELECT FROM pg_catalog.pg_tables
            WHERE tablename = table_name
        ) THEN
            EXECUTE format(
                'CREATE TABLE %I PARTITION OF flight_states FOR VALUES FROM (%L) TO (%L)',
                table_name, start_date, end_date
            );
        END IF;
    END;
    \$\$ LANGUAGE plpgsql;

EOSQL

echo "✅ Database initialization complete."
echo "   - Roles:     prefect (superuser), $DEVELOPER_USER (app admin), readonly"
echo "   - Databases: prefect (Prefect Server), $DEVELOPER_DB (flight data, owned by developer)"