import json
import logging
from kafka import KafkaProducer
from datetime import datetime

class EventsProducer:
    def __init__(self, bootstrap_servers):
        """
        Initialize Kafka Producer with bootstrap servers
        
        :param bootstrap_servers: List of Kafka broker addresses (comma-separated)
        """
        self.logger = logging.getLogger(__name__)
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            client_id='self-awareness-producer',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'), # Serialize JSON
        )
        self.logger.info(f"EventsProducer initialized with bootstrap servers: {bootstrap_servers}")

    def validate_event_data(self, event_data):
        """
        Validate event data against the required schema
        
        :param event_data: Dictionary containing event details
        :raises ValueError: If required fields are missing or invalid
        """
        required_fields = ['module', 'priority', 'description', 'timestamp', 'topic', 'eventType', 'sourceComponent', 'smartService']
        
        # Check required fields
        for field in required_fields:
            if field not in event_data or not event_data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate priority
        if event_data.get('priority') not in ['LOW', 'MID', 'HIGH']:
            raise ValueError("Invalid priority. Must be LOW, MID, or HIGH")
        
        return event_data

    def produce_event(self, topic, event_data):
        """
        Produce a Kafka event to the specified topic
        
        :param topic: Kafka topic to send the event to
        :param event_data: Dictionary containing event details
        """

        # Add timestamp if not provided
        if 'timestamp' not in event_data:
            event_data['timestamp'] = datetime.utcnow().isoformat()

        # Make priority uppercase
        if 'priority' in event_data:
            event_data['priority'] = event_data['priority'].upper()
        
        # Validate event data
        validated_event = self.validate_event_data(event_data)

        try:
            # Log what we're about to send
            self.logger.info(f"=== KAFKA EVENT PRODUCTION ===")
            self.logger.info(f"Topic: {topic}")
            self.logger.info(f"Event Type: {validated_event.get('eventType', 'Unknown')}")
            self.logger.info(f"Priority: {validated_event.get('priority', 'Unknown')}")
            self.logger.debug(f"Full event data: {json.dumps(validated_event, indent=2, default=str)}")
            
            # Produce message to Kafka topic (value_serializer will handle JSON conversion)
            future = self.producer.send(
                topic,
                validated_event  # Send dict directly, serializer will convert to JSON
            )
            
            # Flush to ensure message is sent
            self.producer.flush()
            
            # Get the result to confirm successful sending
            record_metadata = future.get(timeout=10)
            self.logger.info(f"Event successfully sent to Kafka topic '{record_metadata.topic}' "
                           f"partition {record_metadata.partition} offset {record_metadata.offset}")
            
            return
        
        except Exception as e:
            self.logger.error(f"Failed to produce event to Kafka: {str(e)}")
            self.logger.error(f"Event data: {validated_event}")
            raise RuntimeError(f"Failed to produce event: {str(e)}")

    def close(self):
        """
        Close the Kafka producer
        """
        if self.producer:
            self.producer.flush()
            self.producer.close()