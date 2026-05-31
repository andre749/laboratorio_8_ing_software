"""AMQP topology and broker connection settings.

Names are unique per team because the course RabbitMQ server is shared by all
students. The host and credentials are read from environment variables, never
hardcoded (Security quality gate, RNF-04).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import pika

# --- AMQP topology (Exchange -> Routing key -> Queue), per Figure 1 ----------
EXCHANGE = "recompensas_exchange_Andre_Contreras_t1"
EXCHANGE_TYPE = "direct"

DINNER_QUEUE = "cenas_registradas_Andre_Contreras_t1"
DINNER_ROUTING_KEY = "cena.registrada"

NOTIFICATION_QUEUE = "notificaciones_Andre_Contreras_t1"
NOTIFICATION_ROUTING_KEY = "recompensa.procesada"


@dataclass(frozen=True)
class BrokerSettings:
    """RabbitMQ connection parameters loaded from the environment."""

    host: str
    port: int
    user: str
    password: str
    virtual_host: str

    @classmethod
    def from_env(cls) -> "BrokerSettings":
        return cls(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            user=os.getenv("RABBITMQ_USER", "students"),
            password=os.getenv("RABBITMQ_PASSWORD", ""),
            virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
        )

    def to_pika_parameters(self) -> pika.ConnectionParameters:
        """Build pika connection parameters from this settings object."""
        credentials = pika.PlainCredentials(self.user, self.password)
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.virtual_host,
            credentials=credentials,
        )


# Kept for backwards compatibility with existing infrastructure adapters.
def build_connection_parameters(settings: BrokerSettings) -> pika.ConnectionParameters:
    """Build pika connection parameters from broker settings."""
    return settings.to_pika_parameters()
