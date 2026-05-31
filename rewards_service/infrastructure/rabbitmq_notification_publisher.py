"""RabbitMQ implementation of ``NotificationPublisher``."""

from __future__ import annotations

import logging

from rewards_service.application.ports import NotificationPublisher, PublishError
from shared.messaging import topology
from shared.messaging.events import RewardProcessedEvent
from shared.messaging.rabbitmq_base import RabbitMQPublisherMixin
from shared.messaging.security import mask_card_number
from shared.messaging.serialization import serialize
from shared.messaging.topology import BrokerSettings

logger = logging.getLogger(__name__)


class RabbitMQNotificationPublisher(RabbitMQPublisherMixin, NotificationPublisher):
    """Publishes ``recompensa.procesada`` events to the notification queue."""

    def __init__(self, settings: BrokerSettings) -> None:
        self._settings = settings

    def publish(self, event: RewardProcessedEvent) -> None:
        self._do_publish(
            routing_key=topology.NOTIFICATION_ROUTING_KEY,
            queue=topology.NOTIFICATION_QUEUE,
            body=serialize(event),
            publish_error_cls=PublishError,
            error_message="could not publish notification",
        )
        logger.info(
            "Published reward notification card=%s points=%s",
            mask_card_number(event.card_number),
            event.points,
        )
