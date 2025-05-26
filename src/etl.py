# src/etl.py
import json
import os
import logging
from sqlalchemy import create_engine, text 
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from datetime import datetime

# Conditional import for Kafka related modules
ETL_INPUT_SOURCE = os.getenv("ETL_INPUT_SOURCE", "kafka").lower()
KAFKA_TOPIC = os.getenv('KAFKA_ETL_TOPIC', 'sensor_data')
KAFKA_CONSUMER_GROUP = os.getenv('KAFKA_ETL_CONSUMER_GROUP', 'etl_consumer_group')
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092') # Still needed if Kafka is an option

if ETL_INPUT_SOURCE == "kafka":
    try:
        from kafka import KafkaConsumer
        from kafka.errors import KafkaError
    except ImportError:
        logging.error("Failed to import Kafka modules. Ensure 'kafka-python' is installed if ETL_INPUT_SOURCE is kafka.")
        # This will cause an error later if Kafka mode is selected and imports failed.

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL_ETL", "INFO"), 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database Configuration (copied from previous version, should be robust)
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
            from urllib.parse import urlparse
            DB_NAME_FOR_LOGGING = urlparse(ACTUAL_DATABASE_URL).path.lstrip('/')
        except Exception:
            DB_NAME_FOR_LOGGING = "kpi_monitor (from URL)"
    else:
        DB_TYPE = "unknown"
        DB_NAME_FOR_LOGGING = "unknown_db"
elif DB_TYPE == "sqlite":
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./local_kpi_monitor.db")
    ACTUAL_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"
    DB_NAME_FOR_LOGGING = SQLITE_DB_PATH
else: 
    DB_TYPE = "postgres"
    DB_USER_ETL = os.getenv("DB_USER", "admin")
    DB_PASSWORD_ETL = os.getenv("DB_PASSWORD", "admin123")
    DB_HOST_ETL = os.getenv("DB_HOST", "timescaledb") 
    DB_PORT_ETL = os.getenv("DB_PORT", "5432") 
    DB_NAME_ETL = os.getenv("DB_NAME", "kpi_monitor")
    ACTUAL_DATABASE_URL = f"postgresql://{DB_USER_ETL}:{DB_PASSWORD_ETL}@{DB_HOST_ETL}:{DB_PORT_ETL}/{DB_NAME_ETL}"
    DB_NAME_FOR_LOGGING = DB_NAME_ETL

# Input file path for file-based ETL
INPUT_FILE_PATH = os.getenv("ETL_INPUT_FILE", "./sensor_data_simulation.jsonl")


def get_kafka_consumer(topic, group_id):
    """Initializes and returns a KafkaConsumer if Kafka is the source."""
    if ETL_INPUT_SOURCE != "kafka":
        return None # Should not be called if not in Kafka mode
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=group_id,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=10000 
        )
        logger.info(f"Successfully connected to Kafka topic '{topic}' with group '{group_id}' at {KAFKA_BROKER}")
        return consumer
    except NameError: # KafkaConsumer or KafkaError not defined
        logger.error("Kafka modules (KafkaConsumer/KafkaError) not available. Cannot create Kafka consumer.")
        return None
    except KafkaError as e:
        logger.error(f"Failed to connect to Kafka topic '{topic}': {e}")
        return None

def get_db_engine():
    """Initializes and returns a SQLAlchemy engine based on DB_TYPE."""
    if not ACTUAL_DATABASE_URL:
        logger.error("Database URL is not configured. Cannot create DB engine.")
        return None
    logger.info(f"ETL getting DB engine for type: {DB_TYPE}, URL: {ACTUAL_DATABASE_URL}")
    try:
        engine = create_engine(ACTUAL_DATABASE_URL)
        with engine.connect() as connection: # Test connection
            logger.info(f"Successfully created DB engine and connected to database: {DB_NAME_FOR_LOGGING}")
        return engine
    except SQLAlchemyError as e:
        logger.error(f"Failed to connect to database ({DB_NAME_FOR_LOGGING}): {e}")
        return None

def insert_sensor_reading(engine, data):
    """Inserts a single sensor reading into the database."""
    if not isinstance(data, dict):
        logger.error(f"Invalid data format for insertion: {data}")
        return

    sensor_id = data.get('sensor_id')
    value = data.get('value')
    unit = data.get('unit')
    timestamp_str = data.get('timestamp') 

    if not all([sensor_id, value is not None, unit, timestamp_str]):
        logger.warning(f"Missing required fields in data: {data}. Skipping insertion.")
        return

    try:
        time_obj = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError as e:
        logger.error(f"Invalid timestamp format: {timestamp_str} for data {data}. Error: {e}. Skipping insertion.")
        return
    
    insert_stmt_sql = ""
    if DB_TYPE == "postgres":
        insert_stmt_sql = """
            INSERT INTO sensor_readings (time, sensor_id, value, unit)
            VALUES (:time, :sensor_id, :value, :unit)
            ON CONFLICT (time, sensor_id) DO NOTHING; 
        """
    else: # For SQLite
        insert_stmt_sql = """
            INSERT INTO sensor_readings (time, sensor_id, value, unit)
            VALUES (:time, :sensor_id, :value, :unit);
        """
        # For SQLite, to prevent duplicates if there's a UNIQUE constraint on (time, sensor_id)
        # an alternative would be "INSERT OR IGNORE INTO ..." but SQLAlchemy's text()
        # might not directly support OR IGNORE in a dialect-agnostic way easily.
        # Handling IntegrityError on execute is a common pattern for SQLite.
    
    insert_stmt = text(insert_stmt_sql)

    try:
        with engine.connect() as connection:
            connection.execute(insert_stmt, {
                "time": time_obj,
                "sensor_id": sensor_id,
                "value": value,
                "unit": unit
            })
            connection.commit()
    except SQLAlchemyError as e:
        if DB_TYPE == "sqlite" and "UNIQUE constraint failed" in str(e):
            logger.debug(f"Duplicate entry for SQLite, skipping: {sensor_id} at {time_obj}.")
        else:
            logger.error(f"Database error while inserting {data} into {DB_NAME_FOR_LOGGING}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during insertion of {data} into {DB_NAME_FOR_LOGGING}: {e}")

def main():
    logger.info(f"Starting ETL process. Input source: {ETL_INPUT_SOURCE}")
    engine = get_db_engine()
    if not engine:
        logger.error("Failed to initialize DB engine. Exiting ETL process.")
        return

    processed_messages = 0
    
    if ETL_INPUT_SOURCE == "file":
        logger.info(f"Processing data from file: {INPUT_FILE_PATH}")
        try:
            with open(INPUT_FILE_PATH, "r") as f:
                for line_number, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        insert_sensor_reading(engine, data)
                        processed_messages += 1
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping line {line_number} due to JSON decode error: {e} - Line: '{line.strip()}'")
                    except Exception as e: 
                        logger.error(f"Error processing data from line {line_number} ('{line.strip()}'): {e}", exc_info=True)
            logger.info(f"Finished processing file {INPUT_FILE_PATH}. Processed {processed_messages} records.")
        except FileNotFoundError:
            logger.error(f"Input file {INPUT_FILE_PATH} not found. Please ensure the simulator has run and produced the file.")
        except Exception as e: 
            logger.error(f"An error occurred during file processing from {INPUT_FILE_PATH}: {e}", exc_info=True)
    
    elif ETL_INPUT_SOURCE == "kafka":
        consumer = get_kafka_consumer(KAFKA_TOPIC, KAFKA_CONSUMER_GROUP)
        if not consumer:
            logger.error("Failed to initialize Kafka consumer. Exiting ETL process.")
            if engine: engine.dispose() # Dispose engine if Kafka fails
            return
        
        logger.info(f"Consuming messages from Kafka topic '{KAFKA_TOPIC}'...")
        try:
            for message in consumer:
                logger.debug(f"Received message: Topic {message.topic}, Partition {message.partition}, Offset {message.offset}, Key {message.key}, Value {message.value}")
                data = message.value 
                insert_sensor_reading(engine, data)
                processed_messages += 1
        except KeyboardInterrupt:
            logger.info("ETL process (Kafka) interrupted by user.")
        except Exception as e:
            logger.error(f"An error occurred during Kafka message consumption: {e}", exc_info=True)
        finally:
            if consumer: # This variable is only defined in Kafka path
                consumer.close()
                logger.info("Kafka consumer closed.")
    else:
        logger.error(f"Invalid ETL_INPUT_SOURCE: {ETL_INPUT_SOURCE}. Must be 'kafka' or 'file'. Exiting.")
        if engine: engine.dispose() # Dispose engine if config is invalid
        return
    
    # Common cleanup for engine and final logging
    if engine: 
        engine.dispose()
        logger.info("Database engine disposed.")
    logger.info(f"ETL process finished. Total processed messages: {processed_messages} from {ETL_INPUT_SOURCE}.")

if __name__ == '__main__':
    main()
