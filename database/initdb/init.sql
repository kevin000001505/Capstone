-- Prefect role
ALTER ROLE prefect WITH PASSWORD :'PREFECT_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE prefect TO prefect;


-- backend role for the application
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'bk') THEN
    CREATE ROLE bk WITH LOGIN PASSWORD :'BK_PASSWORD';
  END IF;
END
$$;


CREATE DATABASE app OWNER bk;
GRANT ALL PRIVILEGES ON DATABASE app TO bk;


CREATE EXTENSION IF NOT EXISTS postgis;


CREATE TABLE IF NOT EXISTS flight_states (
    time        TIMESTAMPTZ NOT NULL, -- Maps to 'timestamp' (last_contact)
    icao24      CHAR(6) NOT NULL,     -- Fixed 6-char Hex
    callsign    VARCHAR(8),           -- Max 8 chars
    origin_country VARCHAR(100),      -- Country of origin
    
    -- Position Data
    time_pos    TIMESTAMPTZ,          -- Maps to 'last_position'
    lat         DOUBLE PRECISION,     -- Latitude and Longitude as DOUBLE PRECISION for better accuracy
    lon         DOUBLE PRECISION,
    geo_altitude REAL,                -- Geometric altitude (meters)
    baro_altitude REAL,               -- Barometric altitude (meters)
    
    -- Movement Data
    velocity    REAL,                 -- Groundspeed (m/s)
    heading     REAL,                 -- Track (degrees)
    vert_rate   REAL,                 -- Vertical rate (m/s)
    on_ground   BOOLEAN DEFAULT FALSE,-- True if the aircraft is on the ground
    
    -- Metadata
    squawk      VARCHAR(8),           -- Transponder code
    spi         BOOLEAN DEFAULT FALSE,-- Special Purpose Indicator
    source      SMALLINT,             -- 0=ADS-B, 1=ASTERIX, 2=MLAT, 3=FLARM
    sensors     INTEGER[],            -- Array of sensor IDs
    
    -- Spatial Index Column
    geom        GEOMETRY(POINT, 4326),-- PostGIS geometry column for spatial queries using WGS 84 coordinate system (SRID 4326)

    -- Combination of time and icao24 as PRIMARY KEY for uniqueness
    PRIMARY KEY (time, icao24)
) PARTITION BY RANGE (time);

-- Transfer table ownership to the App User
ALTER TABLE flight_states OWNER TO flight_app;

-- INDEXES for performance optimization
CREATE INDEX idx_flight_geom ON flight_states USING GIST (geom);
CREATE INDEX idx_flight_icao ON flight_states (icao24);
CREATE INDEX idx_flight_callsign ON flight_states (callsign);

-- AUTOMATION: Partition data by month
CREATE OR REPLACE FUNCTION create_partition_if_missing(date_val TIMESTAMPTZ)
RETURNS void AS $$
DECLARE
    start_date DATE := date_trunc('month', date_val);
    end_date DATE := start_date + interval '1 month';
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
$$ LANGUAGE plpgsql;


-- Developer role: can create tables, insert/update/select, but NOT delete
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'developer') THEN
    CREATE ROLE developer WITH LOGIN PASSWORD :'DEVELOPER_PASSWORD';
  END IF;
END
$$;


-- Grant connect to app database only
GRANT CONNECT ON DATABASE app TO developer;
-- Allow usage and creation in public schema
GRANT USAGE, CREATE ON SCHEMA public TO developer;
-- Grant SELECT, INSERT, UPDATE on existing tables (no DELETE)
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO developer;
-- Grant usage on sequences (for auto-increment columns)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO developer;
-- Apply same privileges to future tables created by bk
ALTER DEFAULT PRIVILEGES FOR ROLE bk IN SCHEMA public 
    GRANT SELECT, INSERT, UPDATE ON TABLES TO developer;
ALTER DEFAULT PRIVILEGES FOR ROLE bk IN SCHEMA public 
    GRANT USAGE ON SEQUENCES TO developer;
-- Note: No DELETE or DROP privileges granted