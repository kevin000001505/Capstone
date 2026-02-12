from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from utils.db_tools import get_connection, get_pool, close_all_connections
from typing import List, Optional
from pydantic import BaseModel
import logging
import json
from contextlib import asynccontextmanager
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connection pool
    await get_pool()
    logger.info("Database connection pool initialized")
    yield
    # Shutdown: Close connection pool
    await close_all_connections()
    logger.info("Database connection pool closed")

app = FastAPI(
    title="D-RAP Data API",
    description="API for accessing D-RAP geomagnetic data and flight information",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response Models for Flight States
class FlightState(BaseModel):
    icao24: str
    callsign: Optional[str]
    time: str
    time_pos: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    geo_altitude: Optional[float]
    velocity: Optional[float]
    heading: Optional[float]
    vert_rate: Optional[float]
    on_ground: bool

class FlightStatesResponse(BaseModel):
    timestamp: str
    count: int
    flights: List[FlightState]
    query_time_ms: float  # Add query execution time
    total_time_ms: float  # Add total endpoint time

class DRAPResponse(BaseModel):
    type: str
    timestamp: str
    count: int
    features: List
    query_time_ms: float  # Add timing
    total_time_ms: float

@app.get("/")
async def root():
    return {"message": "D-RAP Data API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/flight-states/latest", response_model=FlightStatesResponse)
async def get_latest_flight_states():
    """
    Retrieve all flight states from the most recent timestamp.
    Uses optimized query with subquery for better performance.
    """
    start_time = time.time()
    
    async with get_connection() as conn:
        try:
            query_start = time.time()
            
            # Optimized single query: get max time and filter in one go
            rows = await conn.fetch("""
                WITH latest_time AS (
                    SELECT MAX(time) as max_time FROM flight_states
                )
                SELECT 
                    fs.icao24,
                    fs.callsign,
                    fs.time,
                    fs.time_pos,
                    ROUND(fs.lat::numeric, 4) AS lat,
                    ROUND(fs.lon::numeric, 4) AS lon,
                    ROUND(fs.geo_altitude::numeric, 2) AS geo_altitude,
                    ROUND(fs.velocity::numeric, 2) AS velocity,
                    ROUND(fs.heading::numeric, 2) AS heading,
                    ROUND(fs.vert_rate::numeric, 2) AS vert_rate,
                    fs.on_ground
                FROM flight_states fs
                CROSS JOIN latest_time lt
                WHERE fs.time = lt.max_time
                ORDER BY fs.callsign NULLS LAST, fs.icao24
            """)
            
            query_time_ms = (time.time() - query_start) * 1000
            
            if not rows:
                raise HTTPException(status_code=404, detail="No flight data available")
            
            # Get timestamp from first row
            latest_time = rows[0]['time']
            
            flights = []
            for row in rows:
                flights.append(FlightState(
                    icao24=row['icao24'],
                    callsign=row['callsign'],
                    time=row['time'].isoformat() if row['time'] else None,
                    time_pos=row['time_pos'].isoformat() if row['time_pos'] else None,
                    lat=row['lat'],
                    lon=row['lon'],
                    geo_altitude=row['geo_altitude'],
                    velocity=row['velocity'],
                    heading=row['heading'],
                    vert_rate=row['vert_rate'],
                    on_ground=row['on_ground'] if row['on_ground'] is not None else False,
                ))
            
            total_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Retrieved {len(flights)} flights - Query: {query_time_ms:.2f}ms, Total: {total_time_ms:.2f}ms")
            
            return FlightStatesResponse(
                timestamp=latest_time.isoformat(),
                count=len(flights),
                flights=flights,
                query_time_ms=round(query_time_ms, 2),
                total_time_ms=round(total_time_ms, 2),
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching flight states: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/v1/drap/latest", response_model=DRAPResponse)
async def get_latest_drap_geojson():
    start_time = time.time()
    
    sql = """
    WITH latest_time AS (
        SELECT MAX(observed_at) AS max_ts
        FROM drap_region
    ),
    features AS (
        SELECT jsonb_build_object(
            'type','Feature',
            'geometry', ST_AsGeoJSON(d.location::geometry)::jsonb,
            'properties', jsonb_build_object(
                'timestamp', d.observed_at,
                'frequency', d.frequency_mhz
            )
        ) AS feature
        FROM drap_region d
        CROSS JOIN latest_time lt
        WHERE d.observed_at = lt.max_ts
    )
    SELECT jsonb_build_object(
        'type', 'FeatureCollection',
        'timestamp', (SELECT max_ts FROM latest_time),
        'count', (SELECT COUNT(*) FROM features),
        'features', COALESCE(jsonb_agg(feature), '[]'::jsonb)
    ) AS fc
    FROM features;
    """

    try:
        query_start = time.time()
        
        async with get_connection() as conn:
            fc = await conn.fetchval(sql)

        query_time_ms = (time.time() - query_start) * 1000
        
        # asyncpg can return jsonb as str depending on codec/settings
        if isinstance(fc, str):
            fc = json.loads(fc)

        if not fc or fc.get("count", 0) == 0 or fc.get("timestamp") is None:
            raise HTTPException(status_code=404, detail="No D-RAP data available")

        total_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Retrieved {fc.get('count', 0)} D-RAP features - Query: {query_time_ms:.2f}ms, Total: {total_time_ms:.2f}ms")
        
        fc["query_time_ms"] = round(query_time_ms, 2)
        fc["total_time_ms"] = round(total_time_ms, 2)
        
        return fc

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")