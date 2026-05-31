"""RabbitMQ implementation of the ``DinnerEventPublisher`` port."""

from __future__ import annotations

import logging

from restaurant_service.application.ports import DinnerEventPublisher, PublishError
from shared.messaging import topology
from shared.messaging.events import DinnerEvent
from shared.messaging.rabbitmq_base import RabbitMQPublisherMixin
from shared.messaging.security import mask_card_number
from shared.messaging.serialization import serialize
from shared.messaging.topology import BrokerSettings

logger = logging.getLogger(__name__)


class RabbitMQDinnerPublisher(RabbitMQPublisherMixin, DinnerEventPublisher):
    """Publishes dinner events to the ``direct`` exchange (Exchange -> Queue)."""

    def __init__(self, settings: BrokerSettings) -> None:
        self._settings = settings

    def publish(self, event: DinnerEvent) -> None:
        self._do_publish(
            routing_key=topology.DINNER_ROUTING_KEY,
            queue=topology.DINNER_QUEUE,
            body=serialize(event),
            publish_error_cls=PublishError,
            error_message="could not publish dinner event",
        )
        logger.info(
            "Published dinner event card=%s restaurant=%s",
            mask_card_number(event.card_number),
            event.restaurant_code,
        )
