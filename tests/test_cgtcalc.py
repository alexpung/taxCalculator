""" testing for capital gain matching module """
import datetime
from decimal import Decimal
from fractions import Fraction
from typing import Sequence
import unittest

from capital_gain.calculator import CgtCalculator
from capital_gain.model import (
    BuyTrade,
    CorporateActionType,
    Money,
    SellTrade,
    ShareReorg,
)


class TestCalculator(unittest.TestCase):
    """To test that capital gain is calculated correctly"""

    def test_unmatched_sell(self) -> None:
        """Test short sell"""
        trades: Sequence[BuyTrade | SellTrade] = [
            BuyTrade(
                "AMD",
                datetime.date(2021, 10, 5),
                Decimal(100),
                Money(Decimal(10000)),
            ),
            SellTrade(
                "AMD",
                datetime.date(2021, 10, 6),
                Decimal(150),
                Money(Decimal(10000)),
            ),
        ]
        test = CgtCalculator(trades)
        test.calculate_tax()
        self.assertEqual(
            50,
            trades[1].get_unmatched_share(),
        )

    def test_same_day_matching(self) -> None:
        """To test that same day matching function works

        Expected result: The sell trade will match with the third buy trade instead of
        the first trade. Netting 5000 capital gain and the cost of section 104 remains
        10000
        """
        trades: Sequence[BuyTrade | SellTrade] = [
            BuyTrade(
                "AMD",
                datetime.date(2021, 10, 5),
                Decimal(100),
                Money(Decimal(10000)),
            ),
            SellTrade(
                "AMD",
                datetime.date(2021, 10, 7),
                Decimal(100),
                Money(Decimal(25000)),
            ),
            BuyTrade(
                "AMD",
                datetime.date(2021, 10, 7),
                Decimal(100),
                Money(Decimal(20000)),
            ),
        ]
        test = CgtCalculator(trades)
        test.calculate_tax()
        section104_pool = test.get_section104()
        self.assertEqual(trades[1].get_total_gain_exclude_loss(), 5000)
        self.assertEqual(section104_pool.get_cost("AMD"), 10000)

    def test_bed_and_breakfast_matching(self) -> None:
        """To test bread and breakfast matching works and
        match buy transaction within 30 days of a sell

        Expected result: 3rd transaction will match with 2nd transaction
        6th and 7th (partial match) transaction will match with 5th transaction
        4th and 8th transaction will not match as they are outside 30 days limit
        """
        trades: Sequence[BuyTrade | SellTrade] = [
            BuyTrade(
                "AMD",
                datetime.date(2021, 10, 5),
                Decimal(100),
                Money(Decimal(10000)),
            ),
            SellTrade(
                "AMD",
                datetime.date(2021, 10, 6),
                Decimal(50),
                Money(Decimal(5000)),
            ),
            BuyTrade(
                "AMD",
                datetime.date(2021, 11, 5),
                Decimal(40),
                Money(Decimal(3200)),
            ),
            BuyTrade(
                "AMD",
                datetime.date(2021, 11, 6),
                Decimal(30),
                Money(Decimal(3300)),
            ),
            SellTrade(
                "AMD",
                datetime.date(2021, 11, 7),
                Decimal(15),
                Money(Decimal(2400)),
            ),
            BuyTrade(
                "AMD",
                datetime.date(2021, 12, 6),
                Decimal(10),
                Money(Decimal(1300)),
            ),
            BuyTrade(
                "AMD",
                datetime.date(2021, 12, 7),
                Decimal(10),
                Money(Decimal(1400)),
            ),
            BuyTrade(
                "AMD",
                datetime.date(2021, 12, 8),
                Decimal(10),
                Money(Decimal(1500)),
            ),
        ]
        test = CgtCalculator(trades)
        test.calculate_tax()
        self.assertEqual(trades[1].get_total_gain_exclude_loss(), 800)
        self.assertEqual(trades[4].get_total_gain_exclude_loss(), 400)

    def test_hmrc_example3(self) -> None:
        """
        In April 2014 Ms Pierson buys 1,000 Lobster plc shares for 400p per share plus
        dealing costs of £150 including VAT. This is
        her first acquisition of Lobster plc shares.
        In September 2017 she buys an additional 500 Lobster plc shares for 410p per
        share plus dealing costs of £80
        including VAT.
        In May 2020 she sells 700 Lobster plc shares for 480p per share
        (£3,360 disposal proceeds), incurring dealing costs of £100
        including VAT.
        In February 2021 she sells 400 Lobster plc shares for 520p per share
        (£2,080 disposal proceeds), incurring dealing costs of
        £105 including VAT."""

        trades: Sequence[BuyTrade | SellTrade] = [
            BuyTrade(
                "Lobster plc",
                datetime.date(2014, 4, 1),
                Decimal(1000),
                Money(Decimal(4000)),
                [Money(Decimal(150), note="Broker Commission")],
            ),
            BuyTrade(
                "Lobster plc",
                datetime.date(2017, 9, 1),
                Decimal(500),
                Money(Decimal(2050)),
                [Money(Decimal(80), note="Broker Commission")],
            ),
            SellTrade(
                "Lobster plc",
                datetime.date(2020, 5, 1),
                Decimal(700),
                Money(Decimal(3360)),
                [Money(Decimal(100), note="Broker Commission")],
            ),
            SellTrade(
                "Lobster plc",
                datetime.date(2021, 2, 1),
                Decimal(400),
                Money(Decimal(2080)),
                [Money(Decimal(105), note="Broker Commission")],
            ),
        ]
        test = CgtCalculator(trades)
        test.calculate_tax()
        self.assertEqual(
            int(test.section104.get_cost("Lobster plc")), int(Decimal(1674.66666666667))
        )
        self.assertEqual(test.section104.get_qty("Lobster plc"), Decimal(400))
        self.assertEqual(int(trades[2].get_total_gain_exclude_loss()), 329)
        self.assertEqual(int(trades[3].get_total_gain_exclude_loss()), 300)

    def test_share_split_bed_and_breakfast(self):
        """Testing an extreme case where 2 stock split occurs
        during bed and breakfast
        expected result:
        section104: (2000 - 216.666667) * 3 * 2 = 10700
        cgt of the sell: bnb match 33.33 shares with trade#3 £100 +
        bnb match with trade#6 (5400 buy shares = 900 sell shares) = £33.33 + £1800
        no gain for section104 match for the remaining 216.66... shares
        remaining cost section 104 pool:
        150 shares are removed from 2000 shares
        the remaining cost is 8000 - 8000 * 216.666/2000 = £7133.33...
        """
        trades: Sequence[BuyTrade | SellTrade] = [
            BuyTrade(
                "Lobster plc",  # £4 per share
                datetime.date(2020, 5, 1),
                Decimal(2000),
                Money(Decimal(8000)),
            ),
            SellTrade(
                "Lobster plc",  # £4 per share
                datetime.date(2020, 5, 2),
                Decimal(1150),
                Money(Decimal(4600)),
            ),
            BuyTrade(
                "Lobster plc",  # Share already split here, pre-split £3 per share
                datetime.date(2020, 5, 3),
                Decimal(100),
                Money(Decimal(100)),
            ),
            BuyTrade(
                "Lobster plc",  # £2 per share pre-split
                datetime.date(2020, 5, 5),
                Decimal(5400),
                Money(Decimal(1800)),
            ),
        ]
        share_reorg = [
            ShareReorg(
                "Lobster plc",
                datetime.date(2020, 5, 3),
                CorporateActionType.SHARE_SPLIT,
                Decimal(0),
                Fraction(3),
            ),
            ShareReorg(
                "Lobster plc",
                datetime.date(2020, 5, 4),
                CorporateActionType.SHARE_SPLIT,
                Decimal(0),
                Fraction(2),
            ),
        ]
        test = CgtCalculator(trades, share_reorg)
        test.calculate_tax()
        section104 = test.get_section104()
        self.assertAlmostEqual(
            Decimal("1833.3333333"), trades[1].calculation_status.total_gain
        )
        self.assertEqual(10700, section104.get_qty("Lobster plc"))
        self.assertAlmostEqual(
            Decimal("7133.3333333"), section104.get_cost("Lobster plc")
        )

    def test_share_split_section104(self):
        """Testing section104 handling when stock split occurs"""
        trades = [
            BuyTrade(
                "Lobster plc",
                datetime.date(2020, 5, 1),
                Decimal(2000),
                Money(Decimal(12000)),
            ),
            SellTrade(
                "Lobster plc",
                datetime.date(2020, 6, 2),
                Decimal(5400),
                Money(Decimal(21600)),
            ),
        ]
        share_reorg = [
            ShareReorg(
                "Lobster plc",
                datetime.date(2020, 5, 3),
                CorporateActionType.SHARE_SPLIT,
                Decimal(0),
                Fraction(1, 2),
            ),
            ShareReorg(
                "Lobster plc",
                datetime.date(2020, 5, 4),
                CorporateActionType.SHARE_SPLIT,
                Decimal(0),
                Fraction(6),
            ),
        ]
        test = CgtCalculator(trades, share_reorg)
        test.calculate_tax()
        section104 = test.get_section104()
        self.assertEqual(10800, trades[1].calculation_status.total_gain)
        self.assertEqual(600, section104.get_qty("Lobster plc"))
        self.assertEqual(1200, section104.get_cost("Lobster plc"))

    def test_share_reorg_accuracy(self):
        """test that section 104 pool retain good accuracy when
        one divided by three accuracy problem occurred"""
        trades = [
            BuyTrade(
                "Lobster plc",
                datetime.date(2020, 5, 1),
                Decimal(1000),
                Money(Decimal(10000)),
            ),
            SellTrade(
                "Lobster plc",
                datetime.date(2020, 6, 2),
                Decimal(1000),
                Money(Decimal(10000)),
            ),
            BuyTrade(
                "Lobster plc",
                datetime.date(2020, 6, 10),
                Decimal(1000),
                Money(Decimal(10000)),
            ),
            BuyTrade(
                "Lobster plc",
                datetime.date(2020, 6, 11),
                Decimal(1000),
                Money(Decimal(10000)),
            ),
            BuyTrade(
                "Lobster plc",
                datetime.date(2020, 6, 12),
                Decimal(1000),
                Money(Decimal(10000)),
            ),
        ]
        share_reorg = [
            ShareReorg(
                "Lobster plc",
                datetime.date(2020, 6, 9),
                CorporateActionType.SHARE_SPLIT,
                Decimal(0),
                Fraction(3, 1),
            )
        ]
        test = CgtCalculator(trades, share_reorg)
        test.calculate_tax()
        section104 = test.get_section104()
        self.assertAlmostEqual(3000, section104.get_qty("Lobster plc"))
        self.assertAlmostEqual(10000, section104.get_cost("Lobster plc"))
