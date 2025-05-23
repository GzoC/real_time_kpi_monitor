"""Initialize the TimescaleDB database with required extensions and tables."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.db.models import Base
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters with default values
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "kpi_monitor")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def init_db():
    """Initialize the database with TimescaleDB extension and tables."""
    try:
        # First connect with psycopg2 to create extension
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Create TimescaleDB extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            print("TimescaleDB extension created successfully!")
            
        conn.close()
        
        # Then use SQLAlchemy to create tables
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
        # Create hypertables
        with engine.connect() as connection:
            connection.execute(text("""
                SELECT create_hypertable('sensor_readings', 'timestamp',
                                       if_not_exists => TRUE);
            """))
            connection.execute(text("""
                SELECT create_hypertable('kpi_values', 'timestamp',
                                       if_not_exists => TRUE);
            """))
            connection.commit()
            print("Hypertables created successfully!")
            
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()
