"""Entry points of the rewards service: the dinner consumer and the notifier."""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

from rewards_service.application.process_dinner import ProcessDinner
from rewards_service.infrastructure.database import init_db
from rewards_service.infrastructure.notifier import Notifier
from rewards_service.infrastructure.rabbitmq_consumer import DinnerConsumer
from rewards_service.infrastructure.rabbitmq_notification_publisher import (
    RabbitMQNotificationPublisher,
)
from rewards_service.infrastructure.sqlite_account_repository import (
    SqliteAccountRepository,
)
from rewards_service.infrastructure.sqlite_restaurant_repository import (
    SqliteRestaurantRepository,
)
from shared.messaging.topology import BrokerSettings


def run_consumer() -> None:  # pragma: no cover
    settings = BrokerSettings.from_env()
    db_path = os.getenv("REWARDS_DB_PATH", "rewards.db")
    init_db(db_path)
    use_case = ProcessDinner(
        restaurants=SqliteRestaurantRepository(db_path),
        accounts=SqliteAccountRepository(db_path),
        notifications=RabbitMQNotificationPublisher(settings),
    )
    DinnerConsumer(settings, use_case).start()


def run_notifier() -> None:  # pragma: no cover
    Notifier(BrokerSettings.from_env()).start()


def main() -> None:  # pragma: no cover
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    role = sys.argv[1] if len(sys.argv) > 1 else "consumer"
    if role == "notifier":
        run_notifier()
    else:
        run_consumer()


if __name__ == "__main__":  # pragma: no cover
    main()
