"""Unit tests for RabbitMQNotificationPublisher (pika mocked)."""

from unittest.mock import MagicMock, patch

import pytest
from pika.exceptions import AMQPError

from rewards_service.application.ports import PublishError
from rewards_service.infrastructure.rabbitmq_notification_publisher import (
    RabbitMQNotificationPublisher,
)
from shared.messaging.events import RewardProcessedEvent
from shared.messaging.topology import BrokerSettings

_SETTINGS = BrokerSettings(host="localhost", port=5672, user="u", password="p", virtual_host="/")

_EVENT = RewardProcessedEvent(
    transaction_id="tx-001",
    card_number="4111111111111111",
    points=85,
    cashback=4.25,
    restaurant_code="REST-001",
    timestamp="2026-05-30T20:00:00Z",
)


@pytest.fixture()
def mock_connection():
    channel = MagicMock()
    connection = MagicMock()
    connection.channel.return_value = channel
    return connection, channel


class TestPublishSuccess:
    def test_publishes_to_notification_queue(self, mock_connection):
        connection, channel = mock_connection
        with patch("pika.BlockingConnection", return_value=connection):
            RabbitMQNotificationPublisher(_SETTINGS).publish(_EVENT)
        channel.basic_publish.assert_called_once()

    def test_closes_connection_after_publish(self, mock_connection):
        connection, _ = mock_connection
        with patch("pika.BlockingConnection", return_value=connection):
            RabbitMQNotificationPublisher(_SETTINGS).publish(_EVENT)
        connection.close.assert_called_once()

    def test_declares_exchange_and_notification_queue(self, mock_connection):
        connection, channel = mock_connection
        with patch("pika.BlockingConnection", return_value=connection):
            RabbitMQNotificationPublisher(_SETTINGS).publish(_EVENT)
        channel.exchange_declare.assert_called_once()
        channel.queue_declare.assert_called_once()
        channel.queue_bind.assert_called_once()


class TestPublishFailure:
    def test_amqp_error_raises_publish_error(self):
        with patch("pika.BlockingConnection", side_effect=AMQPError("refused")):
            with pytest.raises(PublishError, match="could not publish notification"):
                RabbitMQNotificationPublisher(_SETTINGS).publish(_EVENT)

    def test_connection_closed_even_when_publish_raises(self, mock_connection):
        connection, channel = mock_connection
        channel.basic_publish.side_effect = AMQPError("publish failed")
        with patch("pika.BlockingConnection", return_value=connection):
            with pytest.raises(PublishError):
                RabbitMQNotificationPublisher(_SETTINGS).publish(_EVENT)
        connection.close.assert_called_once()
