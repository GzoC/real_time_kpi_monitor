"""Initialize the TimescaleDB database with required extensions and tables."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from src.db.models import Base

# Load environment variables
load_dotenv()

# Database connection parameters
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "kpi_monitor")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def init_db():
    """Initialize the database with TimescaleDB extension and tables."""
    # Create engine with explicit encoding settings
    engine = create_engine(
        DATABASE_URL,
        encoding='utf-8',
        connect_args={'client_encoding': 'utf8'}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Create TimescaleDB extension
        session.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
        
        # Create hypertables
        session.execute(text("""
            SELECT create_hypertable('sensor_readings', 'timestamp', 
                                   if_not_exists => TRUE);
        """))
        
        session.execute(text("""
            SELECT create_hypertable('kpi_values', 'timestamp',
                                   if_not_exists => TRUE);
        """))
        
        session.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
