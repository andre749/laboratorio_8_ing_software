"""Use case: register a dinner and publish its event (CU-01)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_service.application.ports import DinnerEventPublisher
from restaurant_service.domain.dinner import Dinner
from shared.messaging.events import DinnerEvent


@dataclass(frozen=True)
class RegisterDinnerCommand:
    """Input data for registering a dinner."""

    amount: float
    card_number: str
    restaurant_code: str
    timestamp: str


class RegisterDinner:
    """Validates a dinner and publishes the ``cena.registrada`` event."""

    def __init__(self, publisher: DinnerEventPublisher) -> None:
        self._publisher = publisher

    def execute(self, command: RegisterDinnerCommand) -> DinnerEvent:
        dinner = Dinner(
            amount=command.amount,
            card_number=command.card_number,
            restaurant_code=command.restaurant_code,
            timestamp=command.timestamp,
        )
        event = DinnerEvent(
            transaction_id=str(uuid.uuid4()),
            amount=dinner.amount,
            card_number=dinner.card_number,
            restaurant_code=dinner.restaurant_code,
            timestamp=dinner.timestamp,
        )
        self._publisher.publish(event)
        return event
