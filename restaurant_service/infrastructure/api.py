"""FastAPI adapter exposing the dinner registration endpoint (CU-01)."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from restaurant_service.application.ports import PublishError
from restaurant_service.application.register_dinner import (
    RegisterDinner,
    RegisterDinnerCommand,
)
from restaurant_service.domain.dinner import DinnerValidationError


class DinnerRequest(BaseModel):
    """HTTP payload to register a dinner."""

    amount: float = Field(..., description="Amount consumed by the customer")
    card_number: str = Field(..., description="Customer card number")
    restaurant_code: str = Field(..., description="Affiliated restaurant code")
    timestamp: str = Field(..., description="ISO-8601 transaction date and time")


class DinnerResponse(BaseModel):
    """Confirmation returned after a dinner is accepted."""

    status: str
    restaurant_code: str


def create_app(register_dinner: RegisterDinner) -> FastAPI:
    """Build the FastAPI app wired to the given use case (enables testing)."""
    app = FastAPI(title="Restaurant Service", version="1.0.0")

    @app.post("/dinners", status_code=status.HTTP_202_ACCEPTED)
    def register(request: DinnerRequest) -> DinnerResponse:
        command = RegisterDinnerCommand(
            amount=request.amount,
            card_number=request.card_number,
            restaurant_code=request.restaurant_code,
            timestamp=request.timestamp,
        )
        try:
            event = register_dinner.execute(command)
        except DinnerValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc
        except PublishError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="messaging broker unavailable",
            ) from exc
        return DinnerResponse(status="accepted", restaurant_code=event.restaurant_code)

    return app
