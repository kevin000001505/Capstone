-- User and DB already created by environment variables
GRANT ALL PRIVILEGES ON DATABASE prefect TO prefect;

-- Create app database for your flows
CREATE DATABASE app OWNER prefect;
GRANT ALL PRIVILEGES ON DATABASE app TO prefect;

CREATE EXTENSION IF NOT EXISTS postgis;