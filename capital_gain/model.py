""" Class model to match capital gain transactions """
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import ClassVar, Union

from capital_gain import comments
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

    transaction: Transaction | None
    size: Decimal
    type: MatchType


@dataclass
class HMRCMatchStatus:
    """To keep track of buy and sell matching during calculation"""

    unmatched: Decimal
    record: list[HMRCMatchRecord] = field(default_factory=list)

    def match(
        self,
        size: Decimal,
        matched_transaction: Union[Transaction, None],
        match_type: MatchType,
    ) -> None:
        """Update the transaction record when it is matched"""
        if size > self.unmatched:
            raise OverMatchError(self.unmatched, size)
        else:
            self.record.append(HMRCMatchRecord(matched_transaction, size, match_type))
            self.unmatched -= size


@dataclass
class Transaction:
    """Transaction class to store transaction
    Ticker: A string represent the symbol of the security
    transaction_date: Datetime object representing the date of transaction
    Transaction_type: Buy/Sell/Dividend/Corporate action as defined in enum
    size: Number of shares
    Transaction value: Net value of transactions AFTER allowable dealing cost
    """

    # pylint: disable=too-many-instance-attributes
    # It is not avoidable that a transaction have many attributes

    ticker: str
    transaction_date: datetime.date
    transaction_type: TransactionType
    size: Decimal  # for fractional shares
    transaction_value: Decimal
    match_status: HMRCMatchStatus = field(init=False)
    calculations_comment: list[object] = field(default_factory=list)
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

    def get_partial_value(self, qty: Decimal) -> Decimal:
        """return the value for partial share matching for this transaction"""
        return qty * self.transaction_value / self.size


@dataclass
class Section104:
    """Data class for storing section 104 pool of shares"""

    quantity: Decimal
    cost: Decimal


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

    def _change_section104(self, qty: Decimal, cost: Decimal) -> None:
        self.section104.quantity += qty
        self.section104.cost += cost

    def match_same_day_disposal(self) -> None:
        """To match buy and sell transactions that occur in the same day"""
        for sell_transaction in [
            x
            for x in self.transaction_list
            if x.transaction_type == TransactionType.SELL
        ]:
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
        for sell_transaction in [
            x
            for x in self.transaction_list
            if x.transaction_type == TransactionType.SELL
        ]:
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

    def match_section104(self) -> None:
        """To handle section 104 share matching"""
        for transaction in self.transaction_list:
            if (
                transaction.transaction_type == TransactionType.BUY
                and transaction.match_status.unmatched > 0
            ):
                transaction.match_status.match(
                    transaction.match_status.unmatched,
                    None,
                    MatchType.BED_AND_BREAKFAST,
                )
                transaction.calculations_comment.append(
                    comments.AddToSection104(
                        self.section104.quantity,
                        self.section104.cost,
                        transaction.size,
                        transaction.get_partial_value(self.section104.quantity),
                    )
                )
                self._change_section104(
                    transaction.match_status.unmatched,
                    transaction.get_partial_value(self.section104.quantity),
                )
            elif (
                transaction.transaction_type == TransactionType.SELL
                and transaction.match_status.unmatched > 0
            ):
                matchable_shares = min(
                    transaction.match_status.unmatched, self.section104.quantity
                )
                transaction.match_status.match(
                    matchable_shares, None, MatchType.BED_AND_BREAKFAST
                )
                transaction.calculations_comment.append(
                    comments.RemoveFromSection104(
                        self.section104.quantity,
                        self.section104.cost,
                        matchable_shares,
                        transaction.get_partial_value(matchable_shares),
                    )
                )
                self._change_section104(
                    matchable_shares * -1,
                    transaction.get_partial_value(matchable_shares) * -1,
                )
