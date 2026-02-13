import asyncpg
from datetime import datetime, timezone

create_table_sql = """
CREATE TABLE IF NOT EXISTS drap_region (
    observed_at timestamptz NOT NULL,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    absorption double precision NOT NULL,
    PRIMARY KEY (observed_at, location)
);

CREATE INDEX IF NOT EXISTS absorption_grid_loc_gix
ON drap_region
USING GIST (location);

CREATE INDEX IF NOT EXISTS absorption_grid_time_idx
ON drap_region (observed_at);
"""


async def insert_drap_data(df_long, conn: asyncpg.Connection):
    """Load DRAP data into PostgreSQL."""
    observed_at = datetime.now(timezone.utc)
    sql = """
    INSERT INTO drap_region (observed_at, location, absorption)
    VALUES (
        $1,
        ST_SetSRID(ST_MakePoint($2, $3), 4326)::geography,
        $4
    )
    ON CONFLICT (observed_at, location)
    DO UPDATE SET absorption = EXCLUDED.absorption
    """

    records = [
        (
            observed_at,
            float(row["Longitude"]),
            float(row["Latitude"]),
            float(row["Absorption"]),
        )
        for _, row in df_long.iterrows()
        if float(row["Absorption"]) > 0
    ]

    await conn.executemany(sql, records)
