""" Class model to match capital gain transactions """
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
import datetime
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import ClassVar, DefaultDict

from iso4217 import Currency

from .exception import OverMatchError


class CorporateActionType(Enum):
    """Enum of type of corporate actions"""

    SHARE_SPLIT = "Forward Split"
    SHARE_MERGE = "Reverse Split"
    CORP_ACTION_OTHER = "Other Corporate Action"


class DividendType(Enum):
    """Type of dividend transactions"""

    WITHHOLDING = "Withholding Tax"
    DIVIDEND = "Dividends"
    DIVIDEND_IN_LIEU = "Payment In Lieu Of Dividends"


class MatchType(Enum):
    """HMRC acquisition and disposal share matching rules"""

    SAME_DAY = "same day"
    BED_AND_BREAKFAST = "bed and breakfast"
    SECTION104 = "section 104"
    SHORT_COVER = "Cover sell short"


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
        prefix = f"{self.note}: " if self.note else ""
        fx_suffix = (
            (
                f" with exchange rate {self.exchange_rate} "
                f"converted to £{self.get_value():.2f}"
            )
            if self.currency != Currency("GBP")
            else ""
        )
        return prefix + f"{self.currency.code}{self.value:.2f}" + fx_suffix + "\n"


@dataclass
class CalculationStatus:
    """To keep track of buy and sell matching during calculation"""

    unmatched: Decimal
    comment: str = ""
    total_gain: Decimal = Decimal(0)
    allowable_cost: Decimal = Decimal(0)

    def reset_calculation(self, size: Decimal):
        """clear the calculation and reset unmatched size"""
        self.unmatched = size
        self.comment = ""

    def match(self, size: Decimal) -> None:
        """Update the transaction record when it is matched"""
        if size > self.unmatched:
            raise OverMatchError(self.unmatched, size)
        else:
            self.unmatched -= size


# mypy bug #5374
@dataclass  # type: ignore
class Transaction(ABC):
    """base class for all transactions"""

    ticker: str
    transaction_date: datetime.date
    transaction_id: int = field(init=False)
    transaction_id_counter: ClassVar[int] = 1

    def __post_init__(self) -> None:
        self.transaction_id = Transaction.transaction_id_counter
        Transaction.transaction_id_counter += 1

    def __lt__(self, other: Transaction) -> bool:
        """For sorting of Transaction for gain calculation"""
        # Corporate action take effect at the beginning of the day
        # if both are Corporate action then the order does not matter
        if self.transaction_date == other.transaction_date and isinstance(
            self, ShareReorg
        ):
            return True
        return self.transaction_date < other.transaction_date

    def __gt__(self, other: Transaction) -> bool:
        if self.transaction_date == other.transaction_date and isinstance(
            other, ShareReorg
        ):
            return False
        return self.transaction_date > other.transaction_date

    @abstractmethod
    def match_with_section104(self, section_104: Section104) -> None:
        """Subclass should implement this for handling of section 104"""


@dataclass
class Dividend:
    """Dataclass to store dividend information"""

    ticker: str
    transaction_date: datetime.date
    transaction_id: int = field(init=False)
    transaction_id_counter: ClassVar[int] = 1
    transaction_type: DividendType
    value: Money
    country: str
    description: str = field(default="")

    def __post_init__(self) -> None:
        self.transaction_id = Trade.transaction_id_counter
        Trade.transaction_id_counter += 1


@dataclass
class ShareReorg(Transaction):
    """Dataclass to store share split and merge events
    ratio: If there is a share split of 2 shares to 5, then the ratio would be 2.5
    """

    transaction_type: CorporateActionType
    size: Decimal
    ratio: Fraction = Fraction(1)
    description: str = ""
    comment: str = ""

    def clear_calculation(self):
        """discard old calculation and start anew"""
        self.comment = ""

    def __str__(self):
        return (
            f"Symbol: {self.ticker}\n"
            f"Trade Date: {self.transaction_date.strftime('%d %b %Y')}\n"
            f"Transaction Type: {self.transaction_type.value}\n"
            f"Description: {self.description}\n"
            f"\n{self.comment}"
        )

    def match_with_section104(self, section_104: Section104) -> None:
        """Changing section 104 pool due to share split/merge"""
        old_qty = section_104.get_qty(self.ticker)
        section_104.set_qty(
            self.ticker,
            old_qty * Decimal(self.ratio.numerator) / Decimal(self.ratio.denominator),
        )
        self.comment += (
            f"Share {self.ticker} split/merge at date {self.transaction_date} with "
            f"ratio {self.ratio.denominator} to {self.ratio.numerator}.\n"
            f"Old quantity of Section 104 is {old_qty:2f}\n"
            f"New quantity is now "
            f"{section_104.get_qty(self.ticker):2f}\n"
        )


@dataclass  # type: ignore
class Trade(Transaction, ABC):
    """Dataclass to store transaction
    ticker: A string represent the symbol of the security
    size: Number of shares if buy/sell.
    transaction value: Gross value of the trade
    fee_and_tax: Note that fee could be negative due to rebates,
    here the convention is positive value means fee, and negative value mean credit
    """

    size: Decimal
    calculation_status: CalculationStatus = field(init=False)
    transaction_value: Money
    fee_and_tax: list[Money] = field(default_factory=list)
    transaction_type: str = "Trade"

    def __post_init__(self) -> None:
        super().__post_init__()
        self.calculation_status = CalculationStatus(self.size)

    def clear_calculation(self):
        """discard old calculation and start anew"""
        self.calculation_status = CalculationStatus(self.size)

    def get_unmatched_share(self):
        """return the number of shares that are not yet accounted for in calculation"""
        return self.calculation_status.unmatched

    def get_partial_value(self, qty: Decimal) -> Decimal:
        """return the gross value for partial share matching for this transaction"""
        return self.transaction_value.get_value() * qty / self.size

    def get_partial_fee(self, qty: Decimal) -> Decimal:
        """return the allowable fee for partial share matching for this transaction"""
        return sum(fee.get_value() for fee in self.fee_and_tax) * qty / self.size

    def match_with_trade(self, trade_id: int, qty: Decimal, match_type: MatchType):
        """Note for buy trade to comment when the shares are matched for same day or
        bed and breakfast"""
        self.calculation_status.match(qty)
        self.calculation_status.comment += (
            f"{match_type.value} matched with trade ID"
            f" {trade_id} for {qty:.2f} share(s)"
        )

    def get_total_gain_exclude_loss(self):
        """This gives "Total gain exclude loss" section in the tax form
        I think even if part of the matching is a loss it can be offset by gain
        for example same day matching get £-100 loss and £400 gain for section104
        You should report £300 gain for this trade"""
        gain = self.calculation_status.total_gain
        return gain if gain >= 0 else 0

    def get_capital_loss(self):
        """Return a negative value as a loss if this trade incur capital loss"""
        loss = self.calculation_status.total_gain
        return loss if loss <= 0 else 0

    def __str__(self) -> str:
        fee_string = ""
        for fee in self.fee_and_tax:
            fee_string += str(fee)
        short_share = (
            f"Short shares that are unmatched: {self.calculation_status.unmatched}\n"
            if self.calculation_status.unmatched
            else ""
        )

        return (
            f"Symbol: {self.ticker}\n"
            f"Trade Date: {self.transaction_date.strftime('%d %b %Y')}\n"
            f"Transaction Type: {self.transaction_type}\n"
            f"Quantity: {self.size:2f}\n"
            f"Gross trade value: "
            f"£{self.transaction_value.get_value():2f}"
            f"\nTotal incidental cost: "
            f"£{sum(fee.get_value() for fee in self.fee_and_tax):.2f}\n"
            f"{fee_string}"
            f"{short_share}"
            f"Total capital gain (loss): £{self.calculation_status.total_gain:.2f}\n"
            f"\n{self.calculation_status.comment}"
        )


@dataclass
class BuyTrade(Trade):
    """Represent a buying trade"""

    transaction_type: str = "Buy"

    def match_with_section104(self, section_104: Section104) -> None:
        """Add all remaining shares to section 104"""
        remaining_shares = self.get_unmatched_share()
        if remaining_shares == 0:
            return
        fee_cost = self.get_partial_fee(remaining_shares)
        total_cost = self.get_partial_value(remaining_shares) + fee_cost
        old_qty = section_104.get_qty(self.ticker)
        old_cost = section_104.get_cost(self.ticker)
        section_104.add_to_section104(self.ticker, remaining_shares, total_cost)
        self.calculation_status.unmatched = Decimal(0)
        self.calculation_status.comment += (
            f"{remaining_shares:2f} share(s) added to Section104 pool "
            f"with allowable cost £{total_cost:.2f} "
            f"including dealing cost £{fee_cost:.2f}.\n"
            f"Total number of share(s) for section 104 "
            f"changes from {old_qty:2f} to {section_104.get_qty(self.ticker):2f}.\n"
            f"Total allowable cost change from £{old_cost:.2f} to "
            f"£{section_104.get_cost(self.ticker):.2f}\n\n"
        )


@dataclass
class SellTrade(Trade):
    """Represent a selling trade"""

    transaction_type: str = "Sell"

    def get_disposal_proceeds(self) -> Decimal:
        """Buy trade do not have disposal"""
        return self.get_partial_value(self.size)

    def match_with_section104(self, section_104: Section104) -> None:
        """Matching a disposal with section104 pool"""
        if self.get_unmatched_share() == 0:
            return
        matched_qty = min(self.get_unmatched_share(), section_104.get_qty(self.ticker))
        if matched_qty == 0:
            return
        buy_cost = section_104.remove_from_section104(self.ticker, matched_qty)
        self.calculation_status.match(matched_qty)
        self.calculation_status.comment += (
            f"{matched_qty:.2f} share(s) removed from Section104 pool "
            f"with allowable cost £{buy_cost:.2f}.\n"
            f"New total number of share(s) for section 104 "
            f"is {section_104.get_qty(self.ticker):.2f}.\n"
            f"New total allowable cost is £{section_104.get_cost(self.ticker):.2f}\n\n"
        )
        self.capital_gain_calc(matched_qty, buy_cost)

    def capital_gain_calc(
        self,
        qty: Decimal,
        buy_cost: Decimal,
        trade_cost_buy: Decimal = Decimal(0),
    ) -> None:
        """Comments to show capital gain calculation
        transaction_id: pass None if it is a section104 match
        """
        proceeds = self.get_partial_value(qty)
        trade_cost_sell = self.get_partial_fee(qty)
        capital_gain = proceeds - buy_cost - trade_cost_buy - trade_cost_sell
        buy_cost_comment = (
            f"Minus allowable acquisition dealing cost: £{trade_cost_buy:.2f}\n"
            if trade_cost_buy
            else ""
        )
        sell_cost_comment = (
            f"Minus allowable disposal dealing cost: £{trade_cost_sell:.2f}\n"
            if trade_cost_sell
            else ""
        )
        self.calculation_status.allowable_cost += (
            buy_cost + trade_cost_buy + trade_cost_sell
        )
        self.calculation_status.total_gain += capital_gain
        self.calculation_status.comment += (
            f"Gross proceeds is £{proceeds:.2f}.\n"
            f"Minus cost of buying: £{buy_cost:.2f}\n"
            + buy_cost_comment
            + sell_cost_comment
            + f"Capital gain = £{capital_gain:.2f}\n\n"
        )

    def share_adjustment(
        self, ratio: Fraction, to_match_sell: Decimal, to_match_buy: Decimal
    ):
        """Comment when a share split occurs during bed and breakfast matching"""
        self.calculation_status.comment += (
            f"Acquisition of size {to_match_buy:.2f} is matched to disposal of "
            f"size {to_match_sell:.2f} due to forward/reverse split "
            f"with ratio {ratio}.\n"
        )


class Section104:
    """Data class for storing section 104 pool of shares"""

    def __init__(self):
        self.section104_list: DefaultDict[str, Section104Value] = defaultdict(
            Section104Value
        )

    def add_to_section104(self, symbol: str, qty: Decimal, cost: Decimal) -> None:
        """Handle adding shares to section 104 pool"""

        self.section104_list[symbol].cost += cost
        self.section104_list[symbol].quantity += qty

    def remove_from_section104(self, symbol: str, qty: Decimal) -> Decimal:
        """Handle removing shares to section 104 pool
        return allowable cost of the removed shares
        """
        if qty > self.section104_list[symbol].quantity:
            raise ValueError(
                f"Attempt to remove {qty:2f} from "
                f"{self.section104_list[symbol].quantity} "
                f"from section 104 pool of {symbol}"
            )
        allowable_cost = (
            self.section104_list[symbol].cost
            * qty
            / self.section104_list[symbol].quantity
        )
        self.section104_list[symbol].cost -= allowable_cost
        self.section104_list[symbol].quantity -= qty
        return allowable_cost

    def get_qty(self, symbol):
        """Return number of shares in the section104 pool of a symbol"""
        return self.section104_list[symbol].quantity

    def set_qty(self, symbol, qty):
        """Setting the number of shares in the section104 pool, in case of
        stock split"""
        self.section104_list[symbol].quantity = qty

    def get_cost(self, symbol):
        """Return the allowable cost in the section104 pool of a symbol"""
        return self.section104_list[symbol].cost


@dataclass
class Section104Value:
    """dataclass to store quantity and allowable cost for section 104"""

    quantity: Decimal = Decimal(0)
    cost: Decimal = Decimal(0)
