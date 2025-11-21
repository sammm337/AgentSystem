import pika, json
from shared.utils.config import settings

class MQConsumer:
    def __init__(self, queue_name='traveler_events'):
        params = pika.URLParameters(settings.RABBITMQ_URL)
        self.conn = pika.BlockingConnection(params)
        self.ch = self.conn.channel()
        self.queue = queue_name
        self.ch.queue_declare(queue=self.queue, durable=True)
        # bind to exchange
        self.ch.exchange_declare(exchange="hyperlocal", exchange_type='topic', durable=True)
        self.ch.queue_bind(queue=self.queue, exchange="hyperlocal", routing_key="#")

    def start(self, callback):
        def on_message(ch, method, properties, body):
            payload = json.loads(body.decode('utf-8'))
            callback(method.routing_key, payload)
            ch.basic_ack(method.delivery_tag)
        self.ch.basic_consume(self.queue, on_message)
        try:
            self.ch.start_consuming()
        except KeyboardInterrupt:
            self.ch.stop_consuming()
