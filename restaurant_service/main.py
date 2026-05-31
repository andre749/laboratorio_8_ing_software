"""Entry point of the restaurant service (producer)."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from restaurant_service.application.register_dinner import RegisterDinner
from restaurant_service.infrastructure.api import create_app
from restaurant_service.infrastructure.rabbitmq_publisher import (
    RabbitMQDinnerPublisher,
)
from shared.messaging.topology import BrokerSettings

load_dotenv()
logging.basicConfig(level=logging.INFO)

publisher = RabbitMQDinnerPublisher(BrokerSettings.from_env())
app = create_app(RegisterDinner(publisher))


def main() -> None:  # pragma: no cover
    import uvicorn

    host = os.getenv("APP_HOST", "localhost")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()
