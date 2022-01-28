""" To calculate summary of capital gain """
from decimal import Decimal
from typing import List, Union

from capital_gain.model import Trade, TransactionType


def number_of_disposal(trades: List[Trade], tax_year_start, tax_year_end) -> int:
    """count number of disposal for the duration specified"""
    count = set()
    for trade in trades:
        # trades on the same day, same symbol are count as one disposal
        if (
            (trade.ticker, trade.transaction_date) not in count
            and trade.transaction_type == TransactionType.SELL
            and (tax_year_start < trade.transaction_date < tax_year_end)
        ):
            count.add((trade.ticker, trade.transaction_date, trade.transaction_type))
    return len(count)


def disposal_proceeds(
    trades: List[Trade], tax_year_start, tax_year_end
) -> Union[Decimal, int]:
    """return the gross total disposal proceeds for the duration specified"""
    return sum(
        [
            trade.transaction_value.get_value()
            for trade in trades
            if trade.transaction_type == TransactionType.SELL
            and tax_year_start < trade.transaction_date < tax_year_end
        ]
    )


def allowable_cost(
    trades: List[Trade], tax_year_start, tax_year_end
) -> Union[Decimal, int]:
    """return the total allowable cost for the duration specified"""
    return sum(
        [
            trade.match_status.allowable_cost
            for trade in trades
            if trade.transaction_type == TransactionType.SELL
            and tax_year_start < trade.transaction_date < tax_year_end
        ]
    )


def total_gain_exclude_loss(
    trades: List[Trade], tax_year_start, tax_year_end
) -> Union[Decimal, int]:
    """return capital gain excluding loss for the duration specified"""
    return sum(
        [
            trade.match_status.total_gain
            for trade in trades
            if trade.transaction_type == TransactionType.SELL
            and tax_year_start < trade.transaction_date < tax_year_end
            and trade.match_status.total_gain > 0
        ]
    )


def capital_loss(
    trades: List[Trade], tax_year_start, tax_year_end
) -> Union[Decimal, int]:
    """return total capital loss for the duration specified"""
    return sum(
        [
            trade.match_status.total_gain
            for trade in trades
            if trade.transaction_type == TransactionType.SELL
            and tax_year_start < trade.transaction_date < tax_year_end
            and trade.match_status.total_gain < 0
        ]
    )
