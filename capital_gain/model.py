""" Class model to match capital gain transactions """
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import ClassVar, Tuple, Union

from capital_gain import comments
from capital_gain.exception import OverMatchError


class TransactionType(Enum):
    """Enum of type of transactions"""

    BUY = auto()
    SELL = auto()
    CORPORATE_ACTION = auto()


class MatchType(Enum):
    """HMRC acquisition and disposal share matching rules"""

    SAME_DAY = "same day"
    BED_AND_BREAKFAST = "bed and breakfast"
    SECTION104 = "section 104"


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
    comment: str = ""
    total_gain: Decimal = Decimal(0)

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
    size: Number of shares if buy/sell. 0 otherwise
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

    ticker: str
    quantity: Decimal
    cost: Decimal

    def add_to_section104(self, qty: Decimal, cost: Decimal) -> str:
        """Handle adding shares to section 104 pool and return a comment string"""
        self.quantity += qty
        self.cost += cost
        return comments.add_to_section104(qty, cost, self.quantity, self.cost)

    def remove_from_section104(self, qty: Decimal) -> Tuple[str, Decimal]:
        """Handle removing shares to section 104 pool
        return a comment string and the allowable cost of the removed shares
        """
        allowable_cost = self.cost * qty / self.quantity
        self.cost -= allowable_cost
        self.quantity -= qty
        return (
            comments.remove_from_section104(
                qty, allowable_cost, self.quantity, self.cost
            ),
            allowable_cost,
        )
