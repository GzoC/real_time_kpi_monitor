"""Initialize the database with required extensions and tables."""
import os
import logging
# import psycopg2 # Made conditional
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from urllib.parse import urlparse # For parsing DATABASE_URL

# Assuming Base is defined in src.db.models and can be imported
from src.db.models import Base

# Load environment variables
load_dotenv()

# Setup basic logging for the script
logging.basicConfig(level=os.getenv("LOG_LEVEL_INIT_DB", "INFO"), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Determine Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "postgres") 
DATABASE_URL_ENV = os.getenv("DATABASE_URL")

DB_NAME_FOR_LOGGING = "" 
ACTUAL_DATABASE_URL = "" 

if DATABASE_URL_ENV:
    ACTUAL_DATABASE_URL = DATABASE_URL_ENV
    if ACTUAL_DATABASE_URL.startswith("sqlite"):
        DB_TYPE = "sqlite"
        DB_NAME_FOR_LOGGING = ACTUAL_DATABASE_URL.split(":///")[1] if ":///" in ACTUAL_DATABASE_URL else "local_kpi_monitor.db"
    elif ACTUAL_DATABASE_URL.startswith("postgresql"):
        DB_TYPE = "postgres"
        try:
            DB_NAME_FOR_LOGGING = urlparse(ACTUAL_DATABASE_URL).path.lstrip('/')
        except Exception: # Broad exception if parsing fails for some reason
            DB_NAME_FOR_LOGGING = "kpi_monitor (from URL)"
    else:
        logger.warning(f"Unknown DB type inferred from DATABASE_URL: {DATABASE_URL_ENV}")
        DB_TYPE = "unknown" 
        DB_NAME_FOR_LOGGING = "unknown_db"
elif DB_TYPE == "sqlite":
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./local_kpi_monitor.db") # Allow path override
    ACTUAL_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"
    DB_NAME_FOR_LOGGING = SQLITE_DB_PATH
elif DB_TYPE == "postgres": # Default to PostgreSQL if DB_TYPE is 'postgres'
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5433")
    DB_NAME = os.getenv("DB_NAME", "kpi_monitor")
    ACTUAL_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DB_NAME_FOR_LOGGING = DB_NAME
else:
    logger.error(f"Unsupported DB_TYPE: {DB_TYPE} and DATABASE_URL not set. Exiting.")
    exit(1)


def init_db():
    """Initialize the database: create extensions (Postgres) and tables."""
    if not ACTUAL_DATABASE_URL:
        logger.error("DATABASE_URL is not configured. Cannot initialize database.")
        return

    logger.info(f"Initializing database: {DB_NAME_FOR_LOGGING} (Type: {DB_TYPE}) using URL: {ACTUAL_DATABASE_URL}")
    
    try:
        if DB_TYPE == "postgres":
            import psycopg2 # Import psycopg2 only when needed
            logger.info("PostgreSQL detected. Attempting to create TimescaleDB extension...")
            # Connect using the DATABASE_URL for creating extensions
            # psycopg2.connect can take the DSN URL directly
            conn_pg_initial = None
            try:
                conn_pg_initial = psycopg2.connect(ACTUAL_DATABASE_URL)
                conn_pg_initial.autocommit = True
                with conn_pg_initial.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
                    logger.info("TimescaleDB extension creation attempted (if not exists).")
            except psycopg2.Error as e_pg_connect:
                logger.error(f"Failed to connect to PostgreSQL or create extension using URL {ACTUAL_DATABASE_URL}: {e_pg_connect}")
                # Decide if you want to raise here or try to continue with table creation
                # For TimescaleDB, the extension is crucial.
                raise
            finally:
                if conn_pg_initial:
                    conn_pg_initial.close()
        
        # Use SQLAlchemy to create tables for both SQLite and PostgreSQL
        engine = create_engine(ACTUAL_DATABASE_URL)
        
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database tables created successfully for {DB_NAME_FOR_LOGGING}!")

        if DB_TYPE == "postgres":
            # Create hypertables (PostgreSQL/TimescaleDB specific)
            with engine.connect() as connection: # Use a new connection from the engine
                logger.info("Attempting to create hypertables for PostgreSQL...")
                connection.execute(text("SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);"))
                connection.execute(text("SELECT create_hypertable('kpi_values', 'time', if_not_exists => TRUE);"))
                connection.commit() 
                logger.info("Hypertables creation attempted (if not exists).")
            
    except Exception as e:
        logger.error(f"Error initializing database ({DB_TYPE}) at {DB_NAME_FOR_LOGGING}: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()
