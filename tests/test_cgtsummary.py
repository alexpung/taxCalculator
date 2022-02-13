""" testing for capital gain summary """
import datetime
from decimal import Decimal
from typing import Sequence, Union
import unittest

from capital_gain.calculator import CgtCalculator
import capital_gain.capital_summary as summary
from capital_gain.model import BuyTrade, Money, SellTrade


class TestCgtSummary(unittest.TestCase):
    """To test that capital gain summary is calculated correctly"""

    def test_summary(self) -> None:
        """test the calculation of capital gain summary"""
        tax_start_date = datetime.date(2021, 4, 6)
        tax_end_date = datetime.date(2022, 4, 5)
        trades: Sequence[Union[BuyTrade, SellTrade]] = [
            BuyTrade(
                "MMM",
                datetime.date(2021, 10, 5),
                Decimal(100),
                Money(Decimal(10000)),
                [Money(Decimal(50), note="Broker Commission")],
            ),
            SellTrade(
                "MMM",
                datetime.date(2021, 10, 5),
                Decimal(100),
                Money(Decimal(15000)),
                [Money(Decimal(50), note="Broker Commission")],
            ),
            BuyTrade(
                "MMM",
                datetime.date(2021, 10, 6),
                Decimal(50),
                Money(Decimal(5000)),
                [Money(Decimal(50), note="Broker Commission")],
            ),
            SellTrade(
                "MMM",
                datetime.date(2021, 11, 3),
                Decimal(30),
                Money(Decimal(5000)),
                [Money(Decimal(10), note="Broker Commission")],
            ),
            SellTrade(
                "MMM",
                datetime.date(2021, 12, 3),
                Decimal(20),
                Money(Decimal(1500)),
                [Money(Decimal(15), note="Broker Commission")],
            ),
        ]
        CgtCalculator(trades).calculate_tax()
        sell_list = [
            sell_trade for sell_trade in trades if isinstance(sell_trade, SellTrade)
        ]
        self.assertEqual(
            3,
            summary.get_number_of_disposal(sell_list, tax_start_date, tax_end_date),
        )
        # share cost = 15000 fee = 175, total allowable cost = 15175
        self.assertEqual(
            15175,
            summary.get_allowable_cost(sell_list, tax_start_date, tax_end_date),
        )
        # (15000-10000-50-50) + (5000-10) - 3030
        self.assertEqual(
            6860,
            summary.get_total_gain_exclude_loss(
                sell_list, tax_start_date, tax_end_date
            ),
        )
        # 1500 - 2000 - 15 - 20
        self.assertEqual(
            -535, summary.get_capital_loss(sell_list, tax_start_date, tax_end_date)
        )
        # 15000 + 5000 + 1500
        self.assertEqual(
            21500,
            summary.get_disposal_proceeds(sell_list, tax_start_date, tax_end_date),
        )

    def test_date_range(self) -> None:
        """test that only date inside date range is calculated"""
        tax_start_date = datetime.date(2021, 4, 6)
        tax_end_date = datetime.date(2022, 4, 5)
        trades: list[Union[BuyTrade, SellTrade]] = [
            BuyTrade(
                "MMM",
                datetime.date(2021, 10, 5),
                Decimal(100),
                Money(Decimal(9900)),
                [Money(Decimal(100), note="Broker Commission")],
            ),
            BuyTrade(
                "MMM",
                datetime.date(2021, 10, 5),
                Decimal(50),
                Money(Decimal(4900)),
                [Money(Decimal(100), note="Broker Commission")],
            ),
            BuyTrade(
                "MMM",
                datetime.date(2021, 10, 6),
                Decimal(50),
                Money(Decimal(4900)),
                [Money(Decimal(100), note="Broker Commission")],
            ),
            SellTrade(
                "MMM",
                datetime.date(2021, 11, 3),
                Decimal(150),
                Money(Decimal(16100)),
                [Money(Decimal(100), note="Broker Commission")],
            ),
            SellTrade(
                "MMM",
                datetime.date(2022, 4, 6),
                Decimal(50),
                Money(Decimal(5100)),
                [Money(Decimal(100), note="Broker Commission")],
            ),
        ]
        # put trades with the same symbol together and calculate tax
        CgtCalculator(trades).calculate_tax()
        sell_list = [
            sell_trade for sell_trade in trades if isinstance(sell_trade, SellTrade)
        ]
        self.assertEqual(
            1,
            summary.get_number_of_disposal(sell_list, tax_start_date, tax_end_date),
        )
        # share cost = 13000 fee = 140, total allowable cost = 13140
        self.assertEqual(
            15100,
            summary.get_allowable_cost(sell_list, tax_start_date, tax_end_date),
        )
        # (15000-10000-50-50) + (5000-10) - 3030
        self.assertEqual(
            1000,
            summary.get_total_gain_exclude_loss(
                sell_list, tax_start_date, tax_end_date
            ),
        )
        # the disposal with capital loss is outside tax date range, so 0
        self.assertEqual(
            0, summary.get_capital_loss(sell_list, tax_start_date, tax_end_date)
        )
        # 15000 + 5000 (1500 is outside date range)
        self.assertEqual(
            16100,
            summary.get_disposal_proceeds(sell_list, tax_start_date, tax_end_date),
        )
