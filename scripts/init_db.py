"""Initialize the TimescaleDB database with required extensions and tables."""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database connection parameters
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def init_db():
    """Initialize the database with TimescaleDB extension."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create TimescaleDB extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
        
        # Create hypertables for time-series data
        conn.execute(text("""
            SELECT create_hypertable('sensor_readings', 'timestamp', 
                                   if_not_exists => TRUE);
        """))
        
        conn.execute(text("""
            SELECT create_hypertable('kpi_values', 'timestamp',
                                   if_not_exists => TRUE);
        """))
        
        conn.commit()

if __name__ == "__main__":
    init_db()
