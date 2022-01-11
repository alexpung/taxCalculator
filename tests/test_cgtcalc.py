""" testing for capital gain matching module """
import datetime
from decimal import Decimal
from typing import Tuple
import unittest

from capital_gain.exception import MixedTickerError
from capital_gain.model import CgtCalculator, MatchType, Transaction, TransactionType


class TestCalculator(unittest.TestCase):
    """To test that capital gain is calculated correctly"""

    @staticmethod
    def _sum_match_type(transaction: Transaction) -> Tuple[Decimal, Decimal, Decimal]:
        bednbreakfast = sum(
            [
                match.size
                for match in transaction.match_status.record
                if match.type == MatchType.BED_AND_BREAKFAST
            ],
            Decimal(0),
        )
        sameday = sum(
            [
                match.size
                for match in transaction.match_status.record
                if match.type == MatchType.SAME_DAY
            ],
            Decimal(0),
        )
        return transaction.match_status.unmatched, sameday, bednbreakfast

    def test_unmatched_sell(self) -> None:
        """Test short sell"""
        trades = [
            Transaction(
                "AMD",
                datetime.date(2021, 10, 5),
                TransactionType.BUY,
                Decimal(100),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 6),
                TransactionType.SELL,
                Decimal(150),
                Decimal(10000),
            ),
        ]
        test = CgtCalculator(trades)
        test.calculate_tax()
        self.assertIn(
            "Sold shares not yet matched (short sale): 50.00",
            test.transaction_list[1].match_status.comment,
        )

    def test_mixed_ticker(self) -> None:
        """To test that an error is raised when transaction list has mixed ticker

        Expected result: Raise MixedTickerError since different Ticker is mixed in.
        """
        trades = [
            Transaction(
                "AMD",
                datetime.date(2021, 10, 5),
                TransactionType.BUY,
                Decimal(100),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 6),
                TransactionType.BUY,
                Decimal(100),
                Decimal(10000),
            ),
            Transaction(
                "JMD",
                datetime.date(2021, 10, 6),
                TransactionType.BUY,
                Decimal(100),
                Decimal(10000),
            ),
        ]
        self.assertRaises(MixedTickerError, CgtCalculator, trades)

    def test_unmixed_ticker(self) -> None:
        """To test that the calculator do not raise an error when no mixed tickers

        Expected result: No MixedTickerError is raised
        """
        trades = [
            Transaction(
                "AMD",
                datetime.date(2021, 10, 5),
                TransactionType.BUY,
                Decimal(100),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 6),
                TransactionType.BUY,
                Decimal(110),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 6),
                TransactionType.BUY,
                Decimal(100),
                Decimal(12000),
            ),
        ]
        try:
            CgtCalculator(trades)
        except MixedTickerError:
            self.fail("MixedTickerError raised with same tracker.")

    def test_same_day_matching(self) -> None:
        """To test that same day matching function works

        Expected result: 3rd, 4th and 5th transaction will match and leaving 30 shares
        that were sold unmatched
        """
        trades = [
            Transaction(
                "AMD",
                datetime.date(2021, 10, 5),
                TransactionType.BUY,
                Decimal(100),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 6),
                TransactionType.BUY,
                Decimal(110),
                Decimal(12100),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 7),
                TransactionType.BUY,
                Decimal(100),
                Decimal(12000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 7),
                TransactionType.SELL,
                Decimal(150),
                Decimal(19500),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 7),
                TransactionType.BUY,
                Decimal(20),
                Decimal(2800),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 8),
                TransactionType.BUY,
                Decimal(100),
                Decimal(15000),
            ),
        ]
        test = CgtCalculator(trades)
        test.match_same_day_disposal()
        self.assertEqual(
            self._sum_match_type(test.transaction_list[0]),
            (Decimal(100), Decimal(0), Decimal(0)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[1]),
            (Decimal(110), Decimal(0), Decimal(0)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[2]),
            (Decimal(0), Decimal(100), Decimal(0)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[3]),
            (Decimal(30), Decimal(120), Decimal(0)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[4]),
            (Decimal(0), Decimal(20), Decimal(0)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[5]),
            (Decimal(100), Decimal(0), Decimal(0)),
        )
        self.assertEqual(test.transaction_list[3].match_status.total_gain, 800)

    def test_bed_and_breakfast_matching(self) -> None:
        """To test bread and breakfast matching works and
        match buy transaction within 30 days of a sell

        Expected result: 3rd transaction will match with 2nd transaction
        6th and 7th (partial match) transaction will match with 5th transaction
        4th and 8th transaction will not match as they are outside 30 days limit
        """
        trades = [
            Transaction(
                "AMD",
                datetime.date(2021, 10, 5),
                TransactionType.BUY,
                Decimal(100),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 6),
                TransactionType.SELL,
                Decimal(50),
                Decimal(5000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 11, 5),
                TransactionType.BUY,
                Decimal(40),
                Decimal(3200),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 11, 6),
                TransactionType.BUY,
                Decimal(30),
                Decimal(3300),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 11, 7),
                TransactionType.SELL,
                Decimal(15),
                Decimal(2400),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 12, 6),
                TransactionType.BUY,
                Decimal(10),
                Decimal(1300),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 12, 7),
                TransactionType.BUY,
                Decimal(10),
                Decimal(1400),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 12, 8),
                TransactionType.BUY,
                Decimal(10),
                Decimal(1500),
            ),
        ]
        test = CgtCalculator(trades)
        test.match_bed_and_breakfast_disposal()
        self.assertEqual(
            self._sum_match_type(test.transaction_list[0]),
            (Decimal(100), Decimal(0), Decimal(0)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[1]),
            (Decimal(10), Decimal(0), Decimal(40)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[2]),
            (Decimal(0), Decimal(0), Decimal(40)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[3]),
            (Decimal(30), Decimal(0), Decimal(0)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[4]),
            (Decimal(0), Decimal(0), Decimal(15)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[5]),
            (Decimal(0), Decimal(0), Decimal(10)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[6]),
            (Decimal(5), Decimal(0), Decimal(5)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[7]),
            (Decimal(10), Decimal(0), Decimal(0)),
        )
        self.assertEqual(test.transaction_list[1].match_status.total_gain, 800)
        self.assertEqual(test.transaction_list[4].match_status.total_gain, 400)

    def test_sorted(self) -> None:
        """To test the sort function sort transaction list by date

        Expected result: Transactions are sorted in chronological order
        """
        trades = [
            Transaction(
                "AMD",
                datetime.date(2021, 1, 5),
                TransactionType.BUY,
                Decimal(100),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2022, 12, 6),
                TransactionType.SELL,
                Decimal(50),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 12, 8),
                TransactionType.BUY,
                Decimal(20),
                Decimal(12000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 11, 6),
                TransactionType.BUY,
                Decimal(30),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 12, 7),
                TransactionType.SELL,
                Decimal(10),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2020, 12, 7),
                TransactionType.BUY,
                Decimal(10),
                Decimal(12000),
            ),
        ]
        test = CgtCalculator(trades)
        self.assertEqual(
            datetime.date(2020, 12, 7), test.transaction_list[0].transaction_date
        )
        self.assertEqual(
            datetime.date(2021, 1, 5), test.transaction_list[1].transaction_date
        )
        self.assertEqual(
            datetime.date(2021, 11, 6), test.transaction_list[2].transaction_date
        )
        self.assertEqual(
            datetime.date(2021, 12, 7), test.transaction_list[3].transaction_date
        )
        self.assertEqual(
            datetime.date(2021, 12, 8), test.transaction_list[4].transaction_date
        )
        self.assertEqual(
            datetime.date(2022, 12, 6), test.transaction_list[5].transaction_date
        )

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

        trades = [
            Transaction(
                "Lobster plc",
                datetime.date(2014, 4, 1),
                TransactionType.BUY,
                Decimal(1000),
                Decimal(4150),  # £4*1000 + £150
            ),
            Transaction(
                "Lobster plc",
                datetime.date(2017, 9, 1),
                TransactionType.BUY,
                Decimal(500),
                Decimal(2130),  # £4.1*500 + £80
            ),
            Transaction(
                "Lobster plc",
                datetime.date(2020, 5, 1),
                TransactionType.SELL,
                Decimal(700),
                Decimal(3260),  # £3360 - £100
            ),
            Transaction(
                "Lobster plc",
                datetime.date(2021, 2, 1),
                TransactionType.SELL,
                Decimal(400),
                Decimal(1975),  # £2080 - £105
            ),
        ]
        test = CgtCalculator(trades)
        test.calculate_tax()
        self.assertEqual(int(test.section104.cost), int(Decimal(1674.66666666667)))
        self.assertEqual(test.section104.quantity, Decimal(400))
        self.assertEqual(int(test.transaction_list[2].match_status.total_gain), 329)
        self.assertEqual(int(test.transaction_list[3].match_status.total_gain), 300)
