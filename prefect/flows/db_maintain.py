from db_tools import get_connection, cleanup_old_data
from prefect import flow


@flow(log_prints=True)
async def db_maintenance_flow():
    """Flow to perform database maintenance tasks."""
    print("Starting database maintenance flow...")
    try:
        async with get_connection() as conn:
            print("Cleaning up old DRAP data...")
            await cleanup_old_data(conn, "drap_region", older_than_days=1)
            print("Old data cleanup completed successfully!")

    except Exception as e:
        print(f"Database maintenance failed: {e}")
