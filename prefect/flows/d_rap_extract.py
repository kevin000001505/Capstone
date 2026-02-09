from prefect import flow, task, get_run_logger
from prefect.variables import Variable

from db_tools import get_connection, ensure_table_exists
from d_rap_etl import extractors, transformers, loaders

d_rap_url = "https://services.swpc.noaa.gov/text/drap_global_frequencies.txt"


@task(log_prints=True, retries=3, retry_delay_seconds=5)
async def extract_data():
    """Extract data from API."""
    data_string = extractors.extract_drap_data(d_rap_url)
    metadata, df_wide, df_long = transformers.parse_drap_data(data_string)
    return (metadata, df_wide, df_long)


@task(log_prints=True)
async def extract_db_info(data: list):
    """Testing connection to PostgreSQL."""
    logger = get_run_logger()
    try:
        async with get_connection() as conn:
            # Test 1: Simple query
            result = await conn.fetchval("SELECT version();")
            logger.info(f"✓ Connection successful!")
            logger.info(f"PostgreSQL version: {result}")

            # Test 2: Current database
            current_db = await conn.fetchval("SELECT current_database();")
            logger.info(f"✓ Current database: {current_db}")

            # Test 3: List databases
            databases = await conn.fetch(
                "SELECT datname FROM pg_database WHERE datistemplate = false;"
            )
            logger.info(f"✓ Found {len(databases)} databases:")
            for db in databases:
                logger.info(f"  - {db['datname']}")

            # Test 4: List tables in current database
            tables = await conn.fetch(
                """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public';
            """
            )
            logger.info(f"✓ Found {len(tables)} tables in 'public' schema:")
            for table in tables:
                logger.info(f"  - {table['tablename']}")

            logger.info("✓ All database tests passed!")
            return True

    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise


@task(log_prints=True)
async def load_data(df_long):
    """Load data into PostgreSQL."""
    logger = get_run_logger()
    try:
        async with get_connection() as conn:
            await ensure_table_exists(conn, "drap", loaders.create_table_sql)
            logger.info("Loading data into PostgreSQL...")

            await loaders.insert_drap_data(df_long, conn)
            logger.info("✓ Data loading completed successfully!")
    except Exception as e:
        logger.error(f"✗ Data loading failed: {e}")
        raise


@flow(
    log_prints=True,
    description="ETL flow for D-RAP data extraction, transformation, and loading.",
)
async def rap_extract_flow():
    last_seen = await Variable.get("data_last_updated", default=None)
    metadata, df_wide, df_long = await extract_data()
    current_updated = metadata.get("valid_at", "Unknown")

    logger = get_run_logger()
    logger.info(f"Last seen: '{last_seen}' (type: {type(last_seen)})")
    logger.info(f"Current: '{current_updated}' (type: {type(current_updated)})")

    if last_seen == current_updated:
        logger.info("No new data available. Last updated at: %s", last_seen)
    else:
        logger.info("New data detected. Loading...")
        await load_data(df_long)
        await Variable.set("data_last_updated", current_updated)
        logger.info("Metadata: %s", metadata)
        logger.info("Wide DataFrame:\n%s", df_wide.head())
        logger.info("Long DataFrame:\n%s", df_long.head())
