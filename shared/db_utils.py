import asyncpg
import os
from typing import Optional

# Initialize connection pool
connection_pool: Optional[asyncpg.Pool] = None

async def init_connection_pool():
    """Initialize the PostgreSQL connection pool."""
    global connection_pool
    if connection_pool is None:
        connection_pool = await asyncpg.create_pool(
            host="postgis",
            port=5432,
            user=os.getenv("DEVELOPER_USER"),
            password=os.getenv("DEVELOPER_PASSWORD"),
            database=os.getenv("DEVELOPER_DB"),
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
    return connection_pool

def get_connection():
    """
    Get a connection from the pool.
    Use within async context manager: async with get_connection() as conn:
    
    Not async - returns the context manager directly.
    """
    if connection_pool is None:
        raise RuntimeError("Connection pool not initialized. Call init_connection_pool() first.")
    
    return connection_pool.acquire()

async def ensure_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    async with connection_pool.acquire() as conn:
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_tables
                WHERE tablename = $1
            )
        """, table_name)
        return result

async def cleanup_old_data(table_name: str, days: int = 30) -> int:
    """Remove data older than specified days from a table."""
    async with connection_pool.acquire() as conn:
        result = await conn.execute(f"""
            DELETE FROM {table_name}
            WHERE time < NOW() - INTERVAL '{days} days'
        """)
        deleted = int(result.split()[-1]) if result else 0
        return deleted

async def close_all_connections():
    """Close all connections in the pool."""
    global connection_pool
    if connection_pool:
        await connection_pool.close()
        connection_pool = None