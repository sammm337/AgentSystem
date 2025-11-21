# services/mq.py

import pika
import os
import json

class MQProducer:
    def __init__(self):
        RABBIT_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
        RABBIT_USER = os.getenv("RABBITMQ_USER", "guest")
        RABBIT_PASS = os.getenv("RABBITMQ_PASS", "guest")

        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)

        params = pika.ConnectionParameters(
            host=RABBIT_HOST,
            port=5672,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )

        self.conn = pika.BlockingConnection(params)
        self.channel = self.conn.channel()
        # Declare topic exchange
        self.channel.exchange_declare(exchange="hyperlocal", exchange_type="topic", durable=True)

    def publish(self, exchange: str, routing_key: str, payload: dict):
        """Publish message to exchange with routing key."""
        try:
            message = json.dumps(payload) if isinstance(payload, dict) else str(payload)
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)  # Persistent
            )
        except Exception as e:
            print(f"Failed to publish message: {e}")
            raise
