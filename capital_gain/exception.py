""" Exception handling for capital gain calculation"""
from decimal import Decimal


class OverMatchError(Exception):
    """Trying to match too many shares"""

    def __init__(self, unmatched_qty: Decimal, attempted_match_qty: Decimal) -> None:
        self.message = (
            f"Matching too many shares. Try to match "
            f"{attempted_match_qty}, while {unmatched_qty} unmatched"
        )
        super().__init__(self.message)
