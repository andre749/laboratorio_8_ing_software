"""Notifier: consumes ``recompensa.procesada`` and simulates the delivery (CU-03).

The notification is simulated by logging it (with the card number masked); no
real email/SMS provider is contacted.
"""

from __future__ import annotations

import logging

import pika

from shared.messaging import topology
from shared.messaging.events import RewardProcessedEvent
from shared.messaging.rabbitmq_base import declare_exchange_queue_binding
from shared.messaging.security import mask_card_number
from shared.messaging.serialization import SerializationError, deserialize
from shared.messaging.topology import BrokerSettings

logger = logging.getLogger(__name__)


class Notifier:
    """Consumes reward notifications and simulates sending them to the customer."""

    def __init__(self, settings: BrokerSettings) -> None:
        self._settings = settings

    def on_message(self, channel, method, _properties, body: bytes) -> None:
        """Handle one notification: deserialize, simulate delivery, acknowledge."""
        try:
            event = deserialize(body, RewardProcessedEvent)
        except SerializationError:
            logger.warning("Discarding malformed notification message")
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info(
            "Notification sent to customer card=%s: +%s points, +%.2f cashback",
            mask_card_number(event.card_number),
            event.points,
            event.cashback,
        )
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start(self) -> None:  # pragma: no cover - requires a live broker
        connection = pika.BlockingConnection(self._settings.to_pika_parameters())
        channel = connection.channel()
        declare_exchange_queue_binding(
            channel, topology.NOTIFICATION_QUEUE, topology.NOTIFICATION_ROUTING_KEY
        )
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=topology.NOTIFICATION_QUEUE, on_message_callback=self.on_message
        )
        logger.info("Waiting for reward notifications. Press CTRL+C to exit.")
        channel.start_consuming()
