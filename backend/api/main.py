from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from shared.db_utils import get_connection, ensure_table_exists, cleanup_old_data
from typing import List, Optional
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="D-RAP Data API",
    description="API for accessing D-RAP geomagnetic data and flight information",
    version="1.0.0",
)

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
    origin_country: Optional[str]
    time: str
    time_pos: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    geo_altitude: Optional[float]
    baro_altitude: Optional[float]
    velocity: Optional[float]
    heading: Optional[float]
    vert_rate: Optional[float]
    on_ground: bool
    squawk: Optional[str]
    spi: bool
    source: int

class FlightStatesResponse(BaseModel):
    timestamp: str
    count: int
    flights: List[FlightState]

# Response Models for D-RAP Data
class DRAPData(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    absorption_value: float
    frequency: Optional[float]
    region: Optional[str]

class DRAPResponse(BaseModel):
    timestamp: str
    count: int
    data: List[DRAPData]

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
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Optimized single query: get max time and filter in one go
        cursor.execute("""
            WITH latest_time AS (
                SELECT MAX(time) as max_time FROM flight_states
            )
            SELECT 
                fs.icao24,
                fs.callsign,
                fs.origin_country,
                fs.time,
                fs.time_pos,
                fs.lat,
                fs.lon,
                fs.geo_altitude,
                fs.baro_altitude,
                fs.velocity,
                fs.heading,
                fs.vert_rate,
                fs.on_ground,
                fs.squawk,
                fs.spi,
                fs.source
            FROM flight_states fs
            CROSS JOIN latest_time lt
            WHERE fs.time = lt.max_time
            ORDER BY fs.callsign NULLS LAST, fs.icao24
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No flight data available")
        
        # Get timestamp from first row
        latest_time = rows[0]['time']
        
        flights = []
        for row in rows:
            flights.append(FlightState(
                icao24=row['icao24'],
                callsign=row['callsign'],
                origin_country=row['origin_country'],
                time=row['time'].isoformat() if row['time'] else None,
                time_pos=row['time_pos'].isoformat() if row['time_pos'] else None,
                lat=row['lat'],
                lon=row['lon'],
                geo_altitude=row['geo_altitude'],
                baro_altitude=row['baro_altitude'],
                velocity=row['velocity'],
                heading=row['heading'],
                vert_rate=row['vert_rate'],
                on_ground=row['on_ground'] if row['on_ground'] is not None else False,
                squawk=row['squawk'],
                spi=row['spi'] if row['spi'] is not None else False,
                source=row['source'] if row['source'] is not None else 0
            ))
        
        logger.info(f"Retrieved {len(flights)} flights from {latest_time}")
        
        return FlightStatesResponse(
            timestamp=latest_time.isoformat(),
            count=len(flights),
            flights=flights
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching flight states: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/api/v1/drap/latest", response_model=DRAPResponse)
async def get_latest_drap_data():
    """
    Retrieve all D-RAP data from the most recent timestamp.
    Uses optimized query with CTE for better performance.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Optimized single query: get max timestamp and filter in one go
        cursor.execute("""
            WITH latest_time AS (
                SELECT MAX(timestamp) as max_timestamp FROM d_rap
            )
            SELECT 
                d.timestamp,
                d.latitude,
                d.longitude,
                d.absorption_value,
                d.frequency,
                d.region
            FROM d_rap d
            CROSS JOIN latest_time lt
            WHERE d.timestamp = lt.max_timestamp
            ORDER BY d.latitude DESC, d.longitude
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No D-RAP data available")
        
        # Get timestamp from first row
        latest_time = rows[0]['timestamp']
        
        drap_data = []
        for row in rows:
            drap_data.append(DRAPData(
                timestamp=row['timestamp'].isoformat() if row['timestamp'] else None,
                latitude=row['latitude'],
                longitude=row['longitude'],
                absorption_value=row['absorption_value'],
                frequency=row['frequency'],
                region=row['region']
            ))
        
        logger.info(f"Retrieved {len(drap_data)} D-RAP measurements from {latest_time}")
        
        return DRAPResponse(
            timestamp=latest_time.isoformat(),
            count=len(drap_data),
            data=drap_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching D-RAP data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()
