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


class MixedTickerError(Exception):
    """Trying to calculate a transaction list with mixed ticker"""

    def __init__(self, ticker1: str, ticker2: str) -> None:
        self.message = (
            f"Ticker {ticker1} and {ticker2} mixed in the transaction list,"
            f" all ticker should be the same."
        )
        super().__init__(self.message)
