""" Class model to match capital gain transactions """
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import ClassVar

from capital_gain.exception import MixedTickerError, OverMatchError


class TransactionType(Enum):
    """Enum of type of transactions"""

    BUY = auto()
    SELL = auto()
    CORPORATE_ACTION = auto()


class MatchType(Enum):
    """HMRC acquisition and disposal share matching rules"""

    SAME_DAY = auto()
    BED_AND_BREAKFAST = auto()
    SECTION104 = auto()


@dataclass
class HMRCMatchRecord:
    """Record of whether part or all of the transaction belongs to same day/
    bed and breakfast or section 104"""

    transaction: Transaction
    size: Decimal
    type: MatchType


@dataclass
class HMRCMatchStatus:
    """To keep track of buy and sell matching during calculation"""

    unmatched: Decimal
    record: list[HMRCMatchRecord] = field(default_factory=list)

    def match(
        self, size: Decimal, matched_transaction: Transaction, match_type: MatchType
    ) -> None:
        """Update the transaction record when it is matched"""
        if size > self.unmatched:
            raise OverMatchError(self.unmatched, size)
        else:
            self.record.append(HMRCMatchRecord(matched_transaction, size, match_type))
            self.unmatched -= size


@dataclass
class Transaction:
    """Transaction class to store transaction"""

    # pylint: disable=too-many-instance-attributes
    # It is not avoidable that a transaction have many attributes

    ticker: str
    transaction_date: datetime.date
    transaction_type: TransactionType
    size: Decimal  # for fractional shares
    transaction_value: Decimal
    match_status: HMRCMatchStatus = field(init=False)
    calculations_comment: str = ""
    transaction_id: int = field(init=False)
    transaction_id_counter: ClassVar[int] = 1

    def __post_init__(self) -> None:
        self.match_status = HMRCMatchStatus(self.size)
        self.transaction_id = Transaction.transaction_id_counter
        Transaction.transaction_id_counter += 1

    def __lt__(self, other: Transaction) -> bool:
        return self.transaction_date < other.transaction_date

    def __gt__(self, other: Transaction) -> bool:
        return self.transaction_date > other.transaction_date


@dataclass
class Section104:
    """Data class for storing section 104 pool of shares"""

    quantity: Decimal
    average_cost: Decimal


class CgtCalculator:
    """To calculate capital gain"""

    def __init__(self, transaction_list: list[Transaction]) -> None:
        ticker = transaction_list[0].ticker
        for transaction in transaction_list:
            if transaction.ticker != ticker:
                raise MixedTickerError(transaction.ticker, ticker)
        self.transaction_list = transaction_list
        self.transaction_list.sort()
        self.section104 = Section104(Decimal(0), Decimal(0))

    def calculate_tax(self) -> None:
        """To calculate chargeable gain and
        allowable loss of a list of same kind of shares"""
        # TODO same day matching/bed and breakfast/section 104

    @staticmethod
    def _match(
        transaction1: Transaction, transaction2: Transaction, match_type: MatchType
    ) -> None:
        """Calculate the size to be matched"""
        to_match = min(
            transaction1.match_status.unmatched, transaction2.match_status.unmatched
        )
        transaction1.match_status.match(to_match, transaction2, match_type)
        transaction2.match_status.match(to_match, transaction1, match_type)

    def match_same_day_disposal(self) -> None:
        """To match buy and sell transactions that occur in the same day"""
        for sell_transaction in self.transaction_list:
            if sell_transaction.transaction_type == TransactionType.SELL:
                matched_transactions_list = [
                    x
                    for x in self.transaction_list
                    if x.transaction_date == sell_transaction.transaction_date
                    and x.transaction_type == TransactionType.BUY
                ]
                for buy_transaction in matched_transactions_list:
                    self._match(sell_transaction, buy_transaction, MatchType.SAME_DAY)

    def match_bed_and_breakfast_disposal(self) -> None:
        """To match buy transactions that occur within 30 days of a sell transaction"""
        for sell_transaction in self.transaction_list:
            if sell_transaction.transaction_type == TransactionType.SELL:
                matched_transactions_list = [
                    x
                    for x in self.transaction_list
                    if 30
                    >= (x.transaction_date - sell_transaction.transaction_date).days
                    > 0
                    and x.transaction_type == TransactionType.BUY
                ]
                for buy_transaction in matched_transactions_list:
                    self._match(
                        sell_transaction, buy_transaction, MatchType.BED_AND_BREAKFAST
                    )
