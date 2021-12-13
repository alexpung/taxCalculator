import datetime
import unittest
from capital_gain.model import *


class TestCalculator(unittest.TestCase):
    def test_mixed_ticker(self):
        trades = [
            Transaction("AMD", datetime.date(2021, 10, 5), TransactionType.BUY, Decimal(100), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 10, 6), TransactionType.BUY, Decimal(100), Decimal(10000)),
            Transaction("JMD", datetime.date(2021, 10, 6), TransactionType.BUY, Decimal(100), Decimal(10000)),
        ]
        self.assertRaises(MixedTickerError, CgtCalculator, trades)

    def test_unmixed_ticker(self):
        trades = [
            Transaction("AMD", datetime.date(2021, 10, 5), TransactionType.BUY, Decimal(100), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 10, 6), TransactionType.BUY, Decimal(110), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 10, 6), TransactionType.BUY, Decimal(100), Decimal(12000)),
        ]
        try:
            test = CgtCalculator(trades)
        except MixedTickerError:
            self.fail("MixedTickerError raised with same tracker.")

    def test_same_day_matching(self):
        trades = [
            Transaction("AMD", datetime.date(2021, 10, 5), TransactionType.BUY, Decimal(100), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 10, 6), TransactionType.BUY, Decimal(110), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 10, 7), TransactionType.BUY, Decimal(100), Decimal(12000)),
            Transaction("AMD", datetime.date(2021, 10, 7), TransactionType.SELL, Decimal(150), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 10, 7), TransactionType.BUY, Decimal(20), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 10, 8), TransactionType.BUY, Decimal(100), Decimal(12000)),
        ]
        test = CgtCalculator(trades)
        test.match_same_day_disposal()
        self.assertEqual(Decimal(100), test.transaction_list[0].match_status.unmatched)
        self.assertEqual(Decimal(0), test.transaction_list[0].match_status.same_day)
        self.assertEqual(Decimal(110), test.transaction_list[1].match_status.unmatched)
        self.assertEqual(Decimal(0), test.transaction_list[1].match_status.same_day)
        self.assertEqual(Decimal(0), test.transaction_list[2].match_status.unmatched)
        self.assertEqual(Decimal(100), test.transaction_list[2].match_status.same_day)
        self.assertEqual(Decimal(30), test.transaction_list[3].match_status.unmatched)
        self.assertEqual(Decimal(120), test.transaction_list[3].match_status.same_day)
        self.assertEqual(Decimal(0), test.transaction_list[4].match_status.unmatched)
        self.assertEqual(Decimal(20), test.transaction_list[4].match_status.same_day)
        self.assertEqual(Decimal(100), test.transaction_list[5].match_status.unmatched)
        self.assertEqual(Decimal(0), test.transaction_list[5].match_status.same_day)

    def test_bed_and_breakfast_matching(self):
        trades = [
            Transaction("AMD", datetime.date(2021, 10, 5), TransactionType.BUY, Decimal(100), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 10, 6), TransactionType.SELL, Decimal(50), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 11, 5), TransactionType.BUY, Decimal(20), Decimal(12000)),
            Transaction("AMD", datetime.date(2021, 11, 6), TransactionType.BUY, Decimal(30), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 11, 7), TransactionType.SELL, Decimal(20), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 12, 7), TransactionType.BUY, Decimal(10), Decimal(12000)),
            Transaction("AMD", datetime.date(2021, 12, 8), TransactionType.BUY, Decimal(10), Decimal(12000))
        ]
        test = CgtCalculator(trades)
        test.match_bed_and_breakfast_disposal()
        self.assertEqual(Decimal(100), test.transaction_list[0].match_status.unmatched)
        self.assertEqual(Decimal(0), test.transaction_list[0].match_status.bed_and_breakfast)
        self.assertEqual(Decimal(30), test.transaction_list[1].match_status.unmatched)
        self.assertEqual(Decimal(20), test.transaction_list[1].match_status.bed_and_breakfast)
        self.assertEqual(Decimal(0), test.transaction_list[2].match_status.unmatched)
        self.assertEqual(Decimal(20), test.transaction_list[2].match_status.bed_and_breakfast)
        self.assertEqual(Decimal(30), test.transaction_list[3].match_status.unmatched)
        self.assertEqual(Decimal(0), test.transaction_list[3].match_status.bed_and_breakfast)
        self.assertEqual(Decimal(10), test.transaction_list[4].match_status.unmatched)
        self.assertEqual(Decimal(10), test.transaction_list[4].match_status.bed_and_breakfast)
        self.assertEqual(Decimal(0), test.transaction_list[5].match_status.unmatched)
        self.assertEqual(Decimal(10), test.transaction_list[5].match_status.bed_and_breakfast)
        self.assertEqual(Decimal(10), test.transaction_list[6].match_status.unmatched)
        self.assertEqual(Decimal(0), test.transaction_list[6].match_status.bed_and_breakfast)

    def test_sorted(self):
        trades = [
            Transaction("AMD", datetime.date(2021, 1, 5), TransactionType.BUY, Decimal(100), Decimal(10000)),
            Transaction("AMD", datetime.date(2022, 12, 6), TransactionType.SELL, Decimal(50), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 12, 8), TransactionType.BUY, Decimal(20), Decimal(12000)),
            Transaction("AMD", datetime.date(2021, 11, 6), TransactionType.BUY, Decimal(30), Decimal(10000)),
            Transaction("AMD", datetime.date(2021, 12, 7), TransactionType.SELL, Decimal(10), Decimal(10000)),
            Transaction("AMD", datetime.date(2020, 12, 7), TransactionType.BUY, Decimal(10), Decimal(12000)),
        ]
        test = CgtCalculator(trades)
        self.assertEqual(datetime.date(2020, 12, 7), test.transaction_list[0].transaction_date)
        self.assertEqual(datetime.date(2021, 1, 5), test.transaction_list[1].transaction_date)
        self.assertEqual(datetime.date(2021, 11, 6), test.transaction_list[2].transaction_date)
        self.assertEqual(datetime.date(2021, 12, 7), test.transaction_list[3].transaction_date)
        self.assertEqual(datetime.date(2021, 12, 8), test.transaction_list[4].transaction_date)
        self.assertEqual(datetime.date(2022, 12, 6), test.transaction_list[5].transaction_date)
