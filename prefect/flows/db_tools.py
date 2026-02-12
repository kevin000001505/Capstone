import asyncpg
from contextlib import asynccontextmanager

# Singleton pool instance
_pool = None


async def get_pool():
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host="postgres",
            port=5432,
            user="developer",
            password="0000",
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


async def ensure_table_exists(conn, table_name: str, create_sql: str):
    """Check if table exists, create if it doesn't."""
    exists = await conn.fetchval(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = $1
        );
    """,
        table_name,
    )

    if not exists:
        await conn.execute(create_sql)
        return False
    return True


async def close_pool():
    """Close the pool (call on shutdown)."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def cleanup_old_data(conn, table_name: str, older_than_days: int):
    """Delete records older than a certain number of days."""
    await conn.execute(
        f"""
        DELETE FROM {table_name}
        WHERE observed_at < NOW() - INTERVAL '{older_than_days} days';
    """
    )
