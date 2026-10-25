from collections.abc import Callable
import pika
from config.settings import AppConfig
from pika.adapters.blocking_connection import (
    BlockingChannel,
    BlockingConnection,
)
from typing import Literal


class Queue:

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.channel: BlockingChannel | None = None
        self.connection: BlockingConnection | None = None

    def create_exchange(
        self,
        queue_name: Literal["SEARCH", "BOOKING", "LOST_ITEM", "MANUAL"],
        exchange_name: str,
        exchange_type: str,
        key: str,
    ):
        try:
            connection_params = pika.URLParameters(self.cfg.amqp_url)
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            # accept only one unack-ed message at a time
            self.channel.basic_qos(prefetch_count=1)
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                passive=True,
            )
            self.channel.queue_bind(
                queue=queue_name, exchange=exchange_name, routing_key=key
            )
        except Exception as e:
            self.cfg.logger.error(f"Connection is not established. {e}")

    def listen_to_queue(
        self,
        queue_name: Literal["SEARCH", "BOOKING", "LOST_ITEM", "MANUAL"],
        call_back: Callable,
    ) -> None:
        try:
            if not self.channel:
                raise Exception("Connection is not established.")
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=call_back,
            )
            self.cfg.logger.info(
                f"[*] Worker Waiting for JOB on Queue: {queue_name}",
            )
            self.channel.start_consuming()
        except KeyboardInterrupt:
            if self.channel:
                self.channel.stop_consuming()
            self.close_connection()
            self.cfg.logger.warning("[+] KeyboardInterruption")
        except Exception as e:
            self.cfg.logger.error(f"[+] Consumer Exception: {e}")
            self.close_connection()

    def send_message(
        self,
        exchange_name: str,
        key: str,
        message: bytes,
    ) -> None:
        try:
            if not self.channel:
                raise Exception("Connection is not established.")
            self.channel.basic_publish(
                exchange_name,
                key,
                body=message,
                properties=pika.spec.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ),
            )
        except Exception as e:
            self.cfg.logger.error(f"[+] Publisher Exception: {e}")

    def close_connection(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
