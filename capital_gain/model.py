""" Class model to match capital gain transactions """
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import ClassVar, Tuple, Union

from iso4217 import Currency

from capital_gain import comments
from capital_gain.exception import OverMatchError


class TransactionType(Enum):
    """Enum of type of transactions"""

    BUY = "BUY"
    SELL = "SELL"
    CORPORATE_ACTION = auto()
    WITHHOLDING = "Withholding Tax"
    DIVIDEND = "Dividends"
    DIVIDEND_IN_LIEU = "Payment In Lieu Of Dividends"


class MatchType(Enum):
    """HMRC acquisition and disposal share matching rules"""

    SAME_DAY = "same day"
    BED_AND_BREAKFAST = "bed and breakfast"
    SECTION104 = "section 104"


@dataclass
class Money:
    """class to record monetary value of various currency"""

    value: Decimal
    exchange_rate: Decimal = field(default=Decimal(1))
    currency: Currency = field(default=Currency("GBP"))
    note: str = ""

    def get_value(self) -> Decimal:
        """return transaction value in GBP"""
        return self.value * self.exchange_rate


@dataclass
class HMRCMatchRecord:
    """Record of whether part or all of the transaction belongs to same day/
    bed and breakfast or section 104"""

    transaction: Trade | None
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
        matched_transaction: Union[Trade, None],
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
    """base class for all transactions"""

    ticker: str
    transaction_date: datetime.date
    transaction_type: TransactionType
    transaction_id: int = field(init=False)
    transaction_id_counter: ClassVar[int] = 1

    def __post_init__(self) -> None:
        self.transaction_id = Trade.transaction_id_counter
        Trade.transaction_id_counter += 1

    def __lt__(self, other: Trade) -> bool:
        return self.transaction_date < other.transaction_date

    def __gt__(self, other: Trade) -> bool:
        return self.transaction_date > other.transaction_date


@dataclass
class Dividend(Transaction):
    """Dataclass to store dividend information"""

    value: Money
    country: str
    description: str = field(default="")


@dataclass
class Trade(Transaction):
    """Dataclass to store transaction
    ticker: A string represent the symbol of the security
    size: Number of shares if buy/sell.
    transaction value: Gross value of the trade
    fee_and_tax: Note that fee could be negative due to rebates,
    here the convention is negative value means fee, and positive value mean credit
    (same as xml report)
    tax also would have a negative value
    """

    size: Decimal  # for fractional shares
    transaction_value: Money
    match_status: HMRCMatchStatus = field(init=False)
    fee_and_tax: list[Money] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.match_status = HMRCMatchStatus(self.size)

    def get_partial_value(self, qty: Decimal) -> Decimal:
        """return the value for partial share matching for this transaction"""
        net_value = self.transaction_value.get_value() + sum(
            fee.get_value() for fee in self.fee_and_tax
        )
        return net_value * qty / self.size

    def get_tuple_repr(self) -> Tuple[str, ...]:
        """Return Tuple representation of the transaction"""
        return (
            str(self.transaction_id),
            str(self.ticker),
            str(self.transaction_date.strftime("%d %b %Y")),
            str(self.transaction_type.value),
            f"{self.size:2f}",
            f"{self.transaction_value.get_value():.2f}",
            f"{sum(fee.get_value() for fee in self.fee_and_tax):.2f}",
            f"{self.match_status.total_gain:.2f}",
        )


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
        if qty > self.quantity:
            raise ValueError(
                f"Attempt to remove {qty} from {self.quantity} "
                f"from section 104 pool of {self.ticker}"
            )
        allowable_cost = self.cost * qty / self.quantity
        self.cost -= allowable_cost
        self.quantity -= qty
        return (
            comments.remove_from_section104(
                qty, allowable_cost, self.quantity, self.cost
            ),
            allowable_cost,
        )
