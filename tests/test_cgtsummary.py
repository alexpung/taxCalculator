""" testing for capital gain summary """
from collections import defaultdict
import datetime
from decimal import Decimal
import unittest

from capital_gain.calculator import CgtCalculator
from capital_gain.capital_summary import CgtTaxSummary
from capital_gain.model import Money, Trade, TransactionType


class TestCgtSummary(unittest.TestCase):
    """To test that capital gain summary is calculated correctly"""

    def test_summary(self) -> None:
        """test the calculation of capital gain summary"""
        tax_start_date = datetime.date(2021, 4, 6)
        tax_end_date = datetime.date(2022, 4, 5)
        trades = [
            Trade(
                "AMD",
                datetime.date(2021, 10, 5),
                TransactionType.BUY,
                Decimal(100),
                Money(Decimal(10000)),
                [Money(Decimal(50), note="Broker Commission")],
            ),
            Trade(
                "AMD",
                datetime.date(2021, 10, 5),
                TransactionType.SELL,
                Decimal(100),
                Money(Decimal(15000)),
                [Money(Decimal(50), note="Broker Commission")],
            ),
            Trade(
                "MMM",
                datetime.date(2021, 10, 6),
                TransactionType.BUY,
                Decimal(50),
                Money(Decimal(5000)),
                [Money(Decimal(50), note="Broker Commission")],
            ),
            Trade(
                "MMM",
                datetime.date(2021, 11, 3),
                TransactionType.SELL,
                Decimal(30),
                Money(Decimal(5000)),
                [Money(Decimal(10), note="Broker Commission")],
            ),
            Trade(
                "MMM",
                datetime.date(2021, 12, 3),
                TransactionType.SELL,
                Decimal(20),
                Money(Decimal(1500)),
                [Money(Decimal(15), note="Broker Commission")],
            ),
        ]
        trade_bucket = defaultdict(list)
        # put trades with the same symbol together and calculate tax
        for trade in trades:
            trade_bucket[trade.ticker].append(trade)
        for _, trade_list in trade_bucket.items():
            CgtCalculator(trade_list).calculate_tax()
        self.assertEqual(
            3,
            CgtTaxSummary.get_number_of_disposal(trades, tax_start_date, tax_end_date),
        )
        # share cost = 15000 fee = 175, total allowable cost = 15175
        self.assertEqual(
            15175,
            CgtTaxSummary.get_allowable_cost(trades, tax_start_date, tax_end_date),
        )
        # (15000-10000-50-50) + (5000-10) - 3030
        self.assertEqual(
            6860,
            CgtTaxSummary.get_total_gain_exclude_loss(
                trades, tax_start_date, tax_end_date
            ),
        )
        # 1500 - 2000 - 15 - 20
        self.assertEqual(
            -535, CgtTaxSummary.get_capital_loss(trades, tax_start_date, tax_end_date)
        )
        # 15000 + 5000 + 1500
        self.assertEqual(
            21500,
            CgtTaxSummary.get_disposal_proceeds(trades, tax_start_date, tax_end_date),
        )

    def test_date_range(self) -> None:
        """test that only date inside date range is calculated"""
        tax_start_date = datetime.date(2021, 4, 6)
        tax_end_date = datetime.date(2022, 4, 5)
        trades = [
            Trade(
                "AMD",
                datetime.date(2021, 10, 5),
                TransactionType.BUY,
                Decimal(100),
                Money(Decimal(10000)),
                [Money(Decimal(50), note="Broker Commission")],
            ),
            Trade(
                "AMD",
                datetime.date(2021, 10, 5),
                TransactionType.SELL,
                Decimal(100),
                Money(Decimal(15000)),
                [Money(Decimal(50), note="Broker Commission")],
            ),
            Trade(
                "MMM",
                datetime.date(2021, 10, 6),
                TransactionType.BUY,
                Decimal(50),
                Money(Decimal(5000)),
                [Money(Decimal(50), note="Broker Commission")],
            ),
            Trade(
                "MMM",
                datetime.date(2021, 11, 3),
                TransactionType.SELL,
                Decimal(30),
                Money(Decimal(5000)),
                [Money(Decimal(10), note="Broker Commission")],
            ),
            Trade(
                "MMM",
                datetime.date(2022, 4, 6),
                TransactionType.SELL,
                Decimal(20),
                Money(Decimal(1500)),
                [Money(Decimal(15), note="Broker Commission")],
            ),
        ]
        trade_bucket = defaultdict(list)
        # put trades with the same symbol together and calculate tax
        for trade in trades:
            trade_bucket[trade.ticker].append(trade)
        for _, trade_list in trade_bucket.items():
            CgtCalculator(trade_list).calculate_tax()
        self.assertEqual(
            2,
            CgtTaxSummary.get_number_of_disposal(trades, tax_start_date, tax_end_date),
        )
        # share cost = 13000 fee = 140, total allowable cost = 13140
        self.assertEqual(
            13140,
            CgtTaxSummary.get_allowable_cost(trades, tax_start_date, tax_end_date),
        )
        # (15000-10000-50-50) + (5000-10) - 3030
        self.assertEqual(
            6860,
            CgtTaxSummary.get_total_gain_exclude_loss(
                trades, tax_start_date, tax_end_date
            ),
        )
        # the disposal with capital loss is outside tax date range, so 0
        self.assertEqual(
            0, CgtTaxSummary.get_capital_loss(trades, tax_start_date, tax_end_date)
        )
        # 15000 + 5000 (1500 is outside date range)
        self.assertEqual(
            20000,
            CgtTaxSummary.get_disposal_proceeds(trades, tax_start_date, tax_end_date),
        )
