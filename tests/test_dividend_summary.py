""" To test dividend summary """
import datetime
from decimal import Decimal
import unittest

from iso4217 import Currency

from capital_gain.dividend_summary import DividendSummary
from capital_gain.model import Dividend, Money, TransactionType


class TestCalculator(unittest.TestCase):
    """To test dividend summary"""

    def setUp(self) -> None:
        """create dividend objects for test"""
        self.dividends = [
            Dividend(
                "ABC",
                datetime.date(2021, 4, 5),
                TransactionType.DIVIDEND,
                Money(Decimal(100), Decimal("0.5"), Currency("USD")),
                "USA",
            ),
            Dividend(
                "ABC",
                datetime.date(2021, 4, 6),
                TransactionType.DIVIDEND,
                Money(Decimal(200), Decimal("0.5"), Currency("USD")),
                "USA",
            ),
            Dividend(
                "ABC",
                datetime.date(2021, 4, 6),
                TransactionType.WITHHOLDING,
                Money(Decimal(20), Decimal("0.5"), Currency("USD")),
                "USA",
            ),
            Dividend(
                "EFG",
                datetime.date(2021, 5, 5),
                TransactionType.DIVIDEND,
                Money(Decimal(250), Decimal("2"), Currency("CAD")),
                "CAN",
            ),
            Dividend(
                "EFG",
                datetime.date(2021, 8, 5),
                TransactionType.DIVIDEND,
                Money(Decimal(500), Decimal("2"), Currency("CAD")),
                "CAN",
            ),
            Dividend(
                "EFG",
                datetime.date(2021, 8, 5),
                TransactionType.WITHHOLDING,
                Money(Decimal(200), Decimal("2"), Currency("CAD")),
                "CAN",
            ),
            Dividend(
                "GHI",
                datetime.date(2021, 4, 20),
                TransactionType.DIVIDEND_IN_LIEU,
                Money(Decimal(100), Decimal("0.2"), Currency("HKD")),
                "HKG",
            ),
            Dividend(
                "GHI",
                datetime.date(2022, 4, 5),
                TransactionType.DIVIDEND,
                Money(Decimal(200), Decimal("0.2"), Currency("HKD")),
                "HKG",
            ),
            Dividend(
                "GHI",
                datetime.date(2022, 4, 6),
                TransactionType.DIVIDEND,
                Money(Decimal(300), Decimal("0.2"), Currency("HKD")),
                "HKG",
            ),
        ]

    def test_dividend_by_country(self):
        """To test the text output of dividend summary by country"""
        data = DividendSummary(
            self.dividends, datetime.date(2021, 4, 6), datetime.date(2022, 4, 5)
        )
        result = data.show_dividend_by_country()
        expected_output = """Dividends by country from 2021-04-06 to 2022-04-05:
Dividends for USA:
Dividends: £100.00
Dividends in lieu: £0.00
Total Dividends: £100.00
Foreign withholding tax: £10.00
Net income received: £90.00

Dividends for CAN:
Dividends: £1500.00
Dividends in lieu: £0.00
Total Dividends: £1500.00
Foreign withholding tax: £400.00
Net income received: £1100.00

Dividends for HKG:
Dividends: £40.00
Dividends in lieu: £20.00
Total Dividends: £60.00
Foreign withholding tax: £0.00
Net income received: £60.00

"""
        self.assertEqual(expected_output, result)

    def test_dividend_sum(self):
        """To test summing up of dividends in correct period"""
        data = DividendSummary(
            self.dividends, datetime.date(2021, 4, 6), datetime.date(2022, 4, 5)
        )
        result = data.show_dividend_total()
        expected_result = """Total dividends from 2021-04-06 to 2022-04-05:
Total Dividends: £1660.00
Foreign withholding tax: £410.00
Net income received: £1250.00

"""
        self.assertEqual(expected_result, result)
