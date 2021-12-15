class OverMatchError(Exception):
    """Trying to match too many shares"""

    def __init__(self, unmatched_qty, attempted_match_qty):
        self.message = f"Matching too many shares. Try to match {attempted_match_qty}, while {unmatched_qty} unmatched"
        super().__init__(self.message)


class MixedTickerError(Exception):
    """Trying to calculate a transaction list with mixed ticker"""

    def __init__(self, ticker1, ticker2):
        self.message = f"Ticker {ticker1} and {ticker2} mixed in the transaction list, all ticker should be the same."
        super().__init__(self.message)
