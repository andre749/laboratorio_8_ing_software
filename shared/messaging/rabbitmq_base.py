"""Base helpers for RabbitMQ adapters.

Centralises the repetitive connect-publish-close and channel-declare-bind
patterns so individual publisher/consumer adapters stay thin.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import pika
from pika.exceptions import AMQPError

from shared.messaging.topology import EXCHANGE, EXCHANGE_TYPE, BrokerSettings

logger = logging.getLogger(__name__)

_DELIVERY_MODE_PERSISTENT = 2


@contextmanager
def rabbitmq_channel(
    settings: BrokerSettings,
) -> Generator[pika.adapters.blocking_connection.BlockingChannel, None, None]:
    """Context manager: open a connection, yield a channel, then close cleanly.

    Usage::

        with rabbitmq_channel(settings) as channel:
            channel.basic_publish(...)
    """
    connection = pika.BlockingConnection(settings.to_pika_parameters())
    try:
        yield connection.channel()
    finally:
        connection.close()


def declare_exchange_queue_binding(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    queue: str,
    routing_key: str,
) -> None:
    """Declare the shared exchange, a durable queue and bind them together.

    Idempotent: safe to call multiple times or from either side of the broker.
    """
    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type=EXCHANGE_TYPE,
        durable=True,
    )
    channel.queue_declare(queue=queue, durable=True)
    channel.queue_bind(queue=queue, exchange=EXCHANGE, routing_key=routing_key)


def publish_message(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    routing_key: str,
    body: bytes,
) -> None:
    """Publish a single persistent JSON message to the shared exchange."""
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=_DELIVERY_MODE_PERSISTENT,
            content_type="application/json",
        ),
    )


class RabbitMQPublisherMixin:
    """Mixin that wires ``rabbitmq_channel`` + AMQPError -> PublishError.

    Subclasses must define ``_settings: BrokerSettings`` and call
    ``_do_publish(routing_key, body, PublishError)`` instead of managing the
    connection lifecycle themselves.
    """

    _settings: BrokerSettings

    def _do_publish(
        self,
        routing_key: str,
        queue: str,
        body: bytes,
        publish_error_cls: type[Exception],
        error_message: str | None = None,
    ) -> None:
        try:
            with rabbitmq_channel(self._settings) as channel:
                declare_exchange_queue_binding(channel, queue, routing_key)
                publish_message(channel, routing_key, body)
        except AMQPError as exc:
            msg = error_message or f"could not publish to {routing_key}"
            raise publish_error_cls(f"{msg}: {exc}") from exc
