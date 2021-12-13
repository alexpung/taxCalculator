import datetime
from enum import Enum, auto
from decimal import Decimal
from dataclasses import dataclass
from .exception import OverMatchError, MixedTickerError
import logging


class TransactionType(Enum):
    BUY = auto()
    SELL = auto()
    CORPORATE_ACTION = auto()


class MatchType(Enum):
    SAME_DAY = auto()
    BED_AND_BREAKFAST = auto()
    SECTION104 = auto()


@dataclass
class HMRCMatchStatus:
    unmatched: Decimal
    same_day: Decimal
    bed_and_breakfast: Decimal
    section104: Decimal

    def match(self, size: Decimal, match_type: MatchType):
        if size > self.unmatched:
            raise OverMatchError
        else:
            self.unmatched -= size
            if match_type == MatchType.SAME_DAY:
                self.same_day += size
            elif match_type == MatchType.BED_AND_BREAKFAST:
                self.bed_and_breakfast += size
            elif match_type == MatchType.SECTION104:
                self.section104 += size
            else:
                raise TypeError("Unknown Security Matching Type, Should be Bed&Breakfast/same day/section 104")


@dataclass
class Transaction:
    ticker: str
    transaction_date: datetime.date
    transaction_type: TransactionType
    size: Decimal  # for fractional shares
    transaction_value: Decimal
    match_status: HMRCMatchStatus | None = None
    calculations_comment: str | None = None

    def __post_init__(self):
        self.match_status = HMRCMatchStatus(self.size, Decimal(0), Decimal(0), Decimal(0))

    def __lt__(self, other):
        return self.transaction_date < other.transaction_date

    def __gt__(self, other):
        return self.transaction_date > other.transaction_date


@dataclass
class Section104:
    quantity: Decimal
    average_cost: Decimal


class CgtCalculator:
    def __init__(self, transaction_list: list[Transaction]):
        ticker = transaction_list[0].ticker
        for transaction in transaction_list:
            if transaction.ticker != ticker:
                raise MixedTickerError(transaction.ticker,  ticker)
        self.transaction_list = transaction_list
        self.transaction_list.sort()

    def calculate_tax(self):
        pass
        # TODO same day matching/bed and breakfast/section 104

    @staticmethod
    def _match(transaction1: Transaction, transaction2: Transaction, match_type: MatchType):
        if transaction1.match_status.unmatched <= transaction2.match_status.unmatched:
            to_match = transaction1.match_status.unmatched
        else:
            to_match = transaction2.match_status.unmatched
        transaction1.match_status.match(to_match, match_type)
        transaction2.match_status.match(to_match, match_type)

    def match_same_day_disposal(self):
        for sell_transaction in self.transaction_list:
            if sell_transaction.transaction_type == TransactionType.SELL:
                matched_transactions_list = [x for x in self.transaction_list
                                             if x.transaction_date == sell_transaction.transaction_date
                                             and x.transaction_type == TransactionType.BUY]
                for buy_transaction in matched_transactions_list:
                    self._match(sell_transaction, buy_transaction, MatchType.SAME_DAY)

    def match_bed_and_breakfast_disposal(self):
        for sell_transaction in self.transaction_list:
            if sell_transaction.transaction_type == TransactionType.SELL:
                matched_transactions_list = [x for x in self.transaction_list
                                             if 30 >= (x.transaction_date - sell_transaction.transaction_date).days > 0
                                             and x.transaction_type == TransactionType.BUY]
                for buy_transaction in matched_transactions_list:
                    self._match(sell_transaction, buy_transaction, MatchType.BED_AND_BREAKFAST)
