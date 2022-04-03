""" testing for short sales """
import datetime
from decimal import Decimal
import unittest

from capital_gain.calculator import CgtCalculator
from capital_gain.model import BuyTrade, Money, SellTrade


class TestShortSales(unittest.TestCase):
    """Testing short sale rules"""

    def test_simple(self):
        """Test a cover short scenario
        After short sell 500 shares then buy back 1000 shares, there should be 500
        shares in Section104 pool.
        Capital gain should be £5000-£8000/2 = £1000
        Cost of section104 pool should be £4000
        """
        trades = [
            SellTrade(
                "Lobster plc",
                datetime.date(2020, 5, 1),
                Decimal(500),
                Money(Decimal(5000)),
            ),
            BuyTrade(
                "Lobster plc",
                datetime.date(2020, 6, 10),
                Decimal(1000),
                Money(Decimal(8000)),
            ),
        ]
        test = CgtCalculator(trades)
        test.calculate_tax()
        self.assertEqual(500, test.get_section104().get_qty("Lobster plc"))
        self.assertEqual(4000, test.get_section104().get_cost("Lobster plc"))
        self.assertEqual(1000, trades[0].get_total_gain_exclude_loss())

    def test_priority(self):
        """test that same day share matching take precedence over short cover
        First short trade should have 100 shares unmatched and 400 shares matched.
        Sell trade should have all share matched and capital gain of
        £4000-£8000*600/1000 = £-800
        """
        trades = [
            SellTrade(
                "Lobster plc",
                datetime.date(2020, 5, 1),
                Decimal(500),
                Money(Decimal(5000)),
            ),
            BuyTrade(
                "Lobster plc",
                datetime.date(2020, 6, 10),
                Decimal(1000),
                Money(Decimal(8000)),
            ),
            SellTrade(
                "Lobster plc",
                datetime.date(2020, 6, 10),
                Decimal(600),
                Money(Decimal(4000)),
            ),
        ]
        test = CgtCalculator(trades)
        test.calculate_tax()
        self.assertEqual(100, trades[0].get_unmatched_share())
        self.assertEqual(800, trades[0].get_total_gain_exclude_loss())
        self.assertEqual(-800, trades[2].get_capital_loss())
