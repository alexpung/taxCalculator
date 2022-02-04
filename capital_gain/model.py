""" Class model to match capital gain transactions """
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import datetime
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import ClassVar, List, Tuple, Union

from iso4217 import Currency

from capital_gain import comments
from capital_gain.exception import OverMatchError


class TransactionType(Enum):
    """Enum of type of transactions"""

    BUY = "BUY"
    SELL = "SELL"
    SHARE_SPLIT = "Forward Split"
    SHARE_MERGE = "Reverse Split"
    CORP_ACTION_OTHER = "Other Corporate Action"
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

    def __str__(self) -> str:
        if self.note:
            prefix = f"{self.note}: "
        else:
            prefix = ""
        return (
            prefix + f"{self.currency.code}{self.value:.2f}"
            f" with exchange rate {self.exchange_rate}"
            f" Converted to £{self.get_value():.2f}\n"
        )


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
    allowable_cost: Decimal = Decimal(0)

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


# mypy false positive https://github.com/python/mypy/issues/5374 so ignore
@dataclass  # type:ignore
class Transaction(ABC):
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

    @abstractmethod
    def get_table_repr(self):
        """subclass should return a row representation for displaying in a table"""

    @property
    @abstractmethod
    def table_header(self) -> List[str]:
        """subclass should show the header when displaying in a table"""


@dataclass
class Dividend(Transaction):
    """Dataclass to store dividend information"""

    value: Money
    country: str
    description: str = field(default="")
    table_header = [
        "ticker",
        "description",
        "transaction date",
        "value",
        "currency",
        "exchange rate",
        "value in sterling",
        "country",
    ]

    def get_table_repr(self):
        """return data to display in the table"""
        return (
            self.ticker,
            self.description,
            self.transaction_date,
            self.value.value,
            self.value.currency,
            self.value.exchange_rate,
            self.value.get_value(),
            self.country,
        )


@dataclass  # type:ignore
class TradeWithTableHeader(Transaction, ABC):
    """Abstract class with table header for trade data display"""

    size: Decimal
    match_status: HMRCMatchStatus = field(init=False)
    table_header: ClassVar = [
        "ID",
        "Symbol",
        "Transaction Date",
        "Transaction Type",
        "Quantity",
        "Gross Value",
        "Allowable fees and Taxes",
        "Capital gain (loss)",
    ]


@dataclass
class ShareReorg(TradeWithTableHeader):
    """Dataclass to store share split and merge events
    ratio: If there is a share split of 2 shares to 5, then the ratio would be 2.5
    """

    ratio: Fraction
    description: str = ""
    # just to store comments during calculation

    def __post_init__(self) -> None:
        super().__post_init__()
        self.match_status = HMRCMatchStatus(Decimal(0))

    # cannot just call __post_init__ as trade ID do not change
    def clear_calculation(self):
        """discard old calculation and start anew"""
        self.match_status = HMRCMatchStatus(Decimal(0))

    def get_table_repr(self) -> Tuple[str, ...]:
        """Return Tuple representation of the transaction"""
        return (
            str(self.transaction_id),
            str(self.ticker),
            str(self.transaction_date.strftime("%d %b %Y")),
            str(self.transaction_type.value),
            f"{self.size:.2f}",
            "N/A",
            "N/A",
            "N/A",
        )

    def __str__(self):
        return (
            f"Symbol: {self.ticker}\n"
            f"Trade Date: {self.transaction_date.strftime('%d %b %Y')}\n"
            f"Transaction Type: {self.transaction_type.value}\n"
            f"Description: {self.description}\n"
            f"\n{self.match_status.comment}"
        )


@dataclass
class Trade(TradeWithTableHeader):
    """Dataclass to store transaction
    ticker: A string represent the symbol of the security
    size: Number of shares if buy/sell.
    transaction value: Gross value of the trade
    fee_and_tax: Note that fee could be negative due to rebates,
    here the convention is positive value means fee, and negative value mean credit
    """

    transaction_value: Money
    fee_and_tax: list[Money] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.match_status = HMRCMatchStatus(self.size)

    def clear_calculation(self):
        """discard old calculation and start anew"""
        self.match_status = HMRCMatchStatus(self.size)

    def get_partial_value(self, qty: Decimal) -> Decimal:
        """return the gross value for partial share matching for this transaction"""
        return self.transaction_value.get_value() * qty / self.size

    def get_partial_fee(self, qty: Decimal) -> Decimal:
        """return the allowable fee for partial share matching for this transaction"""
        return sum(fee.get_value() for fee in self.fee_and_tax) * qty / self.size

    def get_table_repr(self) -> Tuple[str, ...]:
        """Return Tuple representation of the transaction"""
        return (
            str(self.transaction_id),
            str(self.ticker),
            str(self.transaction_date.strftime("%d %b %Y")),
            str(self.transaction_type.value),
            f"{self.size:.2f}",
            f"{self.transaction_value.get_value():.2f}",
            f"{sum(fee.get_value() for fee in self.fee_and_tax):.2f}",
            f"{self.match_status.total_gain:.2f}",
        )

    def __str__(self) -> str:
        fee_string = ""
        for fee in self.fee_and_tax:
            fee_string += str(fee)
        short_share = (
            f"Short shares that are unmatched: {self.match_status.unmatched}\n"
            if self.match_status.unmatched
            else ""
        )

        return (
            f"Symbol: {self.ticker}\n"
            f"Trade Date: {self.transaction_date.strftime('%d %b %Y')}\n"
            f"Transaction Type: {self.transaction_type.value}\n"
            f"Quantity: {self.size:2f}\n"
            f"Gross trade value:\n"
            f"{self.transaction_value}"
            f"\nTotal incidental cost: "
            f"£{sum(fee.get_value() for fee in self.fee_and_tax):.2f}\n"
            f"{fee_string}"
            f"{short_share}"
            f"\n{self.match_status.comment}"
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
