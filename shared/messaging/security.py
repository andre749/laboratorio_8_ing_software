"""Security helpers shared across services.

The card number is sensitive data and must never appear in plain text in logs
(Security quality gate, RNF-04).
"""

from __future__ import annotations

_VISIBLE_DIGITS = 4
_MASK_CHAR = "*"


def mask_card_number(card_number: str) -> str:
    """Return the card number with only its last 4 digits visible.

    Examples:
        ``"4111111111111111"`` -> ``"************1111"``
        ``"123"`` -> ``"***"`` (too short to reveal any digit)
    """
    if card_number is None:
        return ""
    if len(card_number) <= _VISIBLE_DIGITS:
        return _MASK_CHAR * len(card_number)
    hidden = _MASK_CHAR * (len(card_number) - _VISIBLE_DIGITS)
    return hidden + card_number[-_VISIBLE_DIGITS:]
