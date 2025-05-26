"""Database connection and models."""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__) # Assuming logger is configured elsewhere or add basicConfig

# Determine Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "postgres")
DATABASE_URL_ENV = os.getenv("DATABASE_URL")

ACTUAL_DATABASE_URL = ""
DB_FOR_LOGGING = ""

if DATABASE_URL_ENV:
    ACTUAL_DATABASE_URL = DATABASE_URL_ENV
    if ACTUAL_DATABASE_URL.startswith("sqlite"):
        DB_TYPE = "sqlite"
        DB_FOR_LOGGING = ACTUAL_DATABASE_URL.split(":///")[1] if ":///" in ACTUAL_DATABASE_URL else "local_kpi_monitor.db"
    elif ACTUAL_DATABASE_URL.startswith("postgresql"):
        DB_TYPE = "postgres"
        try:
            DB_FOR_LOGGING = urlparse(ACTUAL_DATABASE_URL).path.lstrip('/')
        except Exception:
            DB_FOR_LOGGING = "kpi_monitor (from URL)"
    else:
        logger.warning(f"Unknown DB type inferred from DATABASE_URL: {DATABASE_URL_ENV}")
        DB_TYPE = "unknown"
        DB_FOR_LOGGING = "unknown_db"

elif DB_TYPE == "sqlite":
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./local_kpi_monitor.db")
    ACTUAL_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"
    DB_FOR_LOGGING = SQLITE_DB_PATH
    logger.info(f"Using SQLite database: {ACTUAL_DATABASE_URL}")
elif DB_TYPE == "postgres": # Default to PostgreSQL
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
    DB_HOST = os.getenv("DB_HOST", "localhost") # Default for local, override in Docker
    DB_PORT = os.getenv("DB_PORT", "5433")     # Default for local, override in Docker
    DB_NAME = os.getenv("DB_NAME", "kpi_monitor")
    ACTUAL_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DB_FOR_LOGGING = DB_NAME
    logger.info(f"Using PostgreSQL database: {DB_FOR_LOGGING} at {DB_HOST}:{DB_PORT}")
else:
    logger.error(f"Unsupported DB_TYPE: {DB_TYPE} and DATABASE_URL not set. Exiting or defaulting to a fallback.")
    # Fallback or raise error
    ACTUAL_DATABASE_URL = "sqlite:///./fallback_kpi_monitor.db" # Fallback to a local SQLite
    DB_FOR_LOGGING = "fallback_kpi_monitor.db"
    logger.warning(f"Falling back to SQLite at {ACTUAL_DATABASE_URL}")


# Create SQLAlchemy engine
# For PostgreSQL, connect_args for client_encoding can be useful.
# For SQLite, they are not needed and might cause issues if present with some drivers.
engine_args = {}
if DB_TYPE == "postgres":
    engine_args['connect_args'] = {'client_encoding': 'utf8'}
    # engine_args['pool_pre_ping'] = True # Good for long-running apps

engine = create_engine(ACTUAL_DATABASE_URL, **engine_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for SQLAlchemy models
Base = declarative_base()

# Function to get a DB session (optional, can be used by other modules)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

logger.info(f"Database module configured for {DB_TYPE} using {DB_FOR_LOGGING}")
