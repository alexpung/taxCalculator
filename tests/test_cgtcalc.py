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
                Decimal(10000),
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
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 7),
                TransactionType.BUY,
                Decimal(20),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 10, 8),
                TransactionType.BUY,
                Decimal(100),
                Decimal(12000),
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

    def test_bed_and_breakfast_matching(self) -> None:
        """To test bread and breakfast matching works and
        match buy transaction within 30 days of a sell

        Expected result: 3rd transaction will match with 2nd transaction
        6th transaction will match with 5th transaction
        4th and 7th transaction will not match as they are outside 30 days limit
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
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 11, 5),
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
                datetime.date(2021, 11, 7),
                TransactionType.SELL,
                Decimal(20),
                Decimal(10000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 12, 7),
                TransactionType.BUY,
                Decimal(10),
                Decimal(12000),
            ),
            Transaction(
                "AMD",
                datetime.date(2021, 12, 8),
                TransactionType.BUY,
                Decimal(10),
                Decimal(12000),
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
            (Decimal(30), Decimal(0), Decimal(20)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[2]),
            (Decimal(0), Decimal(0), Decimal(20)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[3]),
            (Decimal(30), Decimal(0), Decimal(0)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[4]),
            (Decimal(10), Decimal(0), Decimal(10)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[5]),
            (Decimal(0), Decimal(0), Decimal(10)),
        )
        self.assertEqual(
            self._sum_match_type(test.transaction_list[6]),
            (Decimal(10), Decimal(0), Decimal(0)),
        )

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
