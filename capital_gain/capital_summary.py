""" To calculate summary of capital gain """
from decimal import Decimal
from typing import List, Union

from capital_gain.model import Trade, TransactionType


class CgtTaxSummary:
    """functions to calculate capital gain summary and output as text"""

    @staticmethod
    def get_number_of_disposal(
        trades: List[Trade], tax_year_start, tax_year_end
    ) -> int:
        """count number of disposal for the duration specified"""
        count = set()
        for trade in trades:
            # trades on the same day, same symbol are count as one disposal
            if (
                (trade.ticker, trade.transaction_date) not in count
                and trade.transaction_type == TransactionType.SELL
                and (tax_year_start < trade.transaction_date < tax_year_end)
            ):
                count.add(
                    (trade.ticker, trade.transaction_date, trade.transaction_type)
                )
        return len(count)

    @staticmethod
    def get_disposal_proceeds(
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

    @staticmethod
    def get_allowable_cost(
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

    @staticmethod
    def get_total_gain_exclude_loss(
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

    @staticmethod
    def get_capital_loss(
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

    @classmethod
    def get_text_summary(cls, trades: List[Trade], tax_year_start, tax_year_end) -> str:
        """get text summary for the calculated trade list"""
        number_of_disposal = cls.get_number_of_disposal(
            trades,
            tax_year_start,
            tax_year_end,
        )
        disposal_proceeds = cls.get_disposal_proceeds(
            trades,
            tax_year_start,
            tax_year_end,
        )
        allowable_cost = cls.get_allowable_cost(
            trades,
            tax_year_start,
            tax_year_end,
        )
        total_gain = cls.get_total_gain_exclude_loss(
            trades,
            tax_year_start,
            tax_year_end,
        )
        capital_loss = cls.get_capital_loss(
            trades,
            tax_year_start,
            tax_year_end,
        )
        return (
            "Capital gain summary:\n"
            f"Number of disposal: {number_of_disposal}\n"
            f"Disposal proceeds: £{disposal_proceeds:.2f}\n"
            f"Allowable cost: £{allowable_cost:.2f}\n"
            f"Total gain exclude loss: £{total_gain:.2f}\n"
            f"Capital loss: £{capital_loss:.2f}\n\n"
        )
