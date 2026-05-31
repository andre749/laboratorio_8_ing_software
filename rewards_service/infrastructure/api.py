"""FastAPI adapter exposing the rewards query endpoint (RF-08)."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from rewards_service.application.ports import AccountRepository, RepositoryError


class BalanceResponse(BaseModel):
    """Customer reward account balance."""

    card_number: str
    total_points: int
    total_cashback: float


def create_app(accounts: AccountRepository) -> FastAPI:
    """Build the FastAPI app wired to the given repository (enables testing)."""
    app = FastAPI(title="Rewards Service", version="1.0.0")

    @app.get("/rewards/{card_number}")
    def get_balance(card_number: str) -> BalanceResponse:
        try:
            balance = accounts.get_balance(card_number)
        except RepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="storage unavailable",
            ) from exc
        if balance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="no account found for this card",
            )
        return BalanceResponse(
            card_number=card_number,
            total_points=balance.points,
            total_cashback=balance.cashback,
        )

    return app
