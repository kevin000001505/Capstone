GRANT ALL PRIVILEGES ON DATABASE prefect TO prefect;

-- Create app database for your flows
CREATE DATABASE app OWNER prefect;
GRANT ALL PRIVILEGES ON DATABASE app TO prefect;

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
        EXECUTE format('GRANT SELECT, INSERT ON %I TO developer', table_name);
    END IF;
END;
$$ LANGUAGE plpgsql;