import asyncpg
from contextlib import asynccontextmanager

# Singleton pool instance
_pool = None


async def get_pool():
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host="postgis",
            port=5432,
            user="developer",
            password="zxc123",
            database="app",
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
    return _pool


@asynccontextmanager
async def get_connection():
    """Get a connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn

async def ensure_table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.
    """
    async with get_connection() as conn:
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_tables
                WHERE tablename = $1
            )
        """, table_name)
        return result

async def cleanup_old_data(table_name: str, days: int = 30) -> int:
    """
    Remove data older than specified days from a table.
    Returns number of rows deleted.
    """
    async with get_connection() as conn:
        result = await conn.execute(f"""
            DELETE FROM {table_name}
            WHERE time < NOW() - INTERVAL '{days} days'
        """)
        # Parse "DELETE N" to get N
        deleted = int(result.split()[-1]) if result else 0
        return deleted

async def close_all_connections():
    """Close all connections in the pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None