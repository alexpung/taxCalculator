""" To calculate summary of capital gain """
from decimal import Decimal
from typing import Sequence, Union

from capital_gain.model import SellTrade


def get_number_of_disposal(trades: Sequence[SellTrade]) -> int:
    """count number of disposal for the duration specified"""
    count = set()
    for trade in trades:
        # trades on the same day, same symbol are count as one disposal
        if (trade.ticker, trade.transaction_date) not in count:
            count.add((trade.ticker, trade.transaction_date))
    return len(count)


def get_disposal_proceeds(trades: Sequence[SellTrade]) -> Union[Decimal, int]:
    """return the gross total disposal proceeds for the duration specified"""
    return sum([trade.get_disposal_proceeds() for trade in trades], Decimal(0))


def get_allowable_cost(trades: Sequence[SellTrade]) -> Union[Decimal, int]:
    """return the total allowable cost for the duration specified"""
    return sum(
        [trade.calculation_status.allowable_cost for trade in trades], Decimal(0)
    )


def get_total_gain_exclude_loss(trades: Sequence[SellTrade]) -> Decimal:
    """return capital gain excluding loss for the duration specified"""
    return sum([trade.get_total_gain_exclude_loss() for trade in trades], Decimal(0))


def get_capital_loss(trades: Sequence[SellTrade]) -> Union[Decimal, int]:
    """return total capital loss for the duration specified"""
    return sum([trade.get_capital_loss() for trade in trades])
