""" To calculate summary of capital gain """
from decimal import Decimal
from typing import Sequence, Union

from capital_gain.model import SellTrade, Transaction


def get_number_of_disposal(
    trades: Sequence[SellTrade], tax_year_start, tax_year_end
) -> int:
    """count number of disposal for the duration specified"""
    count = set()
    for trade in trades:
        # trades on the same day, same symbol are count as one disposal
        if (
            (trade.ticker, trade.transaction_date) not in count
            and isinstance(trade, SellTrade)
            and (tax_year_start < trade.transaction_date <= tax_year_end)
        ):
            count.add((trade.ticker, trade.transaction_date))
    return len(count)


def get_disposal_proceeds(
    trades: Sequence[SellTrade], tax_year_start, tax_year_end
) -> Union[Decimal, int]:
    """return the gross total disposal proceeds for the duration specified"""
    return sum(
        [
            trade.get_disposal_proceeds()
            for trade in trades
            if tax_year_start < trade.transaction_date < tax_year_end
        ]
    )


def get_allowable_cost(
    trades: Sequence[SellTrade], tax_year_start, tax_year_end
) -> Union[Decimal, int]:
    """return the total allowable cost for the duration specified"""
    return sum(
        [
            trade.calculation_status.allowable_cost
            for trade in trades
            if tax_year_start < trade.transaction_date < tax_year_end
        ]
    )


def get_total_gain_exclude_loss(
    trades: Sequence[SellTrade], tax_year_start, tax_year_end
) -> Decimal:
    """return capital gain excluding loss for the duration specified"""
    return sum(
        [
            trade.get_total_gain_exclude_loss()
            for trade in trades
            if tax_year_start < trade.transaction_date < tax_year_end
        ],
        Decimal(0),
    )


def get_capital_loss(
    trades: Sequence[SellTrade], tax_year_start, tax_year_end
) -> Union[Decimal, int]:
    """return total capital loss for the duration specified"""
    return sum(
        [
            trade.get_capital_loss()
            for trade in trades
            if tax_year_start < trade.transaction_date < tax_year_end
        ]
    )


def get_text_summary(
    trades: Sequence[Transaction], tax_year_start, tax_year_end
) -> str:
    """get text summary for the calculated trade list"""
    sell_list = [
        sell_trade for sell_trade in trades if isinstance(sell_trade, SellTrade)
    ]
    number_of_disposal = get_number_of_disposal(sell_list, tax_year_start, tax_year_end)
    disposal_proceeds = get_disposal_proceeds(sell_list, tax_year_start, tax_year_end)
    allowable_cost = get_allowable_cost(sell_list, tax_year_start, tax_year_end)
    total_gain = get_total_gain_exclude_loss(sell_list, tax_year_start, tax_year_end)
    capital_loss = get_capital_loss(sell_list, tax_year_start, tax_year_end)
    return (
        f"Capital gain summary from {tax_year_start} to {tax_year_end}:\n"
        f"Number of disposal: {number_of_disposal}\n"
        f"Disposal proceeds: £{disposal_proceeds:.2f}\n"
        f"Allowable cost: £{allowable_cost:.2f}\n"
        f"Total gain exclude loss: £{total_gain:.2f}\n"
        f"Capital loss: £{capital_loss:.2f}\n\n"
    )
