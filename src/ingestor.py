# src/ingestor.py
import json
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Kafka broker from environment variable or use default
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
DEFAULT_TOPIC = 'sensor_data'

def get_kafka_producer():
    """Creates and returns a KafkaProducer instance."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5, # Retry sending messages up to 5 times
            acks='all' # Wait for all replicas to acknowledge
        )
        logger.info(f"Successfully connected to Kafka broker at {KAFKA_BROKER}")
        return producer
    except KafkaError as e:
        logger.error(f"Failed to connect to Kafka broker: {e}")
        return None

def publish_message(producer, topic, key, value):
    """
    Publishes a message to a given Kafka topic.

    :param producer: KafkaProducer instance.
    :param topic: The Kafka topic to publish to.
    :param key: The key for the Kafka message (can be None).
    :param value: The value for the Kafka message (dictionary).
    """
    if producer is None:
        logger.error("Kafka producer is not available. Cannot publish message.")
        return

    try:
        # Send the message
        future = producer.send(topic, key=key.encode('utf-f8') if key else None, value=value)
        # Wait for the message to be sent (optional, provides synchronous sending)
        record_metadata = future.get(timeout=10)
        logger.info(f"Message published successfully to topic '{record_metadata.topic}' partition {record_metadata.partition} offset {record_metadata.offset}")
    except KafkaError as e:
        logger.error(f"Failed to publish message to topic {topic}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # Example usage:
    producer_instance = get_kafka_producer()

    if producer_instance:
        test_topic = DEFAULT_TOPIC
        test_key = "test_sensor_id_123"
        test_value = {
            "sensor_id": "SENSOR_001",
            "value": 25.5,
            "unit": "Celsius",
            "timestamp": "2023-01-01T12:00:00Z"
        }
        
        logger.info(f"Attempting to send a test message to topic '{test_topic}'...")
        publish_message(producer_instance, test_topic, test_key, test_value)

        # Close the producer
        producer_instance.flush() # Ensure all pending messages are sent
        producer_instance.close()
        logger.info("Kafka producer closed.")
    else:
        logger.error("Failed to create Kafka producer. Exiting example.")
