""" To calculate various dividend summary """
from collections import defaultdict
import datetime
from decimal import Decimal
from typing import List

from capital_gain.model import Dividend, TransactionType


class DividendSummary:
    """calculate summary of dividend and withholding tax received during the period"""

    def __init__(
        self,
        dividend_list: List[Dividend],
        tax_year_start: datetime.date,
        tax_year_end: datetime.date,
    ):
        self.dividend_list = list(
            filter(
                lambda dividend: tax_year_end
                >= dividend.transaction_date
                >= tax_year_start,
                dividend_list,
            )
        )
        self.tax_year_start = tax_year_start
        self.tax_year_end = tax_year_end

    def get_dividend_by_country(self) -> defaultdict[str, List[Dividend]]:
        """get dividend and withholding tax by country code"""
        dividend_by_country: defaultdict[str, List[Dividend]] = defaultdict(list)
        for dividend in self.dividend_list:
            dividend_by_country[dividend.country].append(dividend)
        return dividend_by_country

    def show_dividend_total(self) -> str:
        """show total dividends"""
        dividend = self.get_dividend_total(self.dividend_list, TransactionType.DIVIDEND)
        dividend_in_lieu = self.get_dividend_total(
            self.dividend_list, TransactionType.DIVIDEND_IN_LIEU
        )
        total_dividend = dividend + dividend_in_lieu
        withholding_tax = self.get_dividend_total(
            self.dividend_list, TransactionType.WITHHOLDING
        )
        net_income = total_dividend - withholding_tax
        output_string = (
            f"Total dividends from {self.tax_year_start} to {self.tax_year_end}:\n"
        )
        output_string += (
            f"Total Dividends: £{total_dividend:.2f}\n"
            f"Foreign withholding tax: £{withholding_tax:.2f}\n"
            f"Net income received: £{net_income:.2f}\n\n"
        )
        return output_string

    @staticmethod
    def get_dividend_total(
        dividend_list: List[Dividend], transaction_type: TransactionType
    ) -> Decimal:
        """get the sum of value in Sterling regardless of transaction type"""
        return sum(
            [
                dividend.value.get_value()
                for dividend in dividend_list
                if dividend.transaction_type == transaction_type
            ],
            Decimal(0),
        )

    def show_dividend_by_country(self) -> str:
        """To show dividend summary grouped by the companies' country"""
        output_string = (
            f"Dividends by country from {self.tax_year_start} to {self.tax_year_end}:\n"
        )
        for country, dividend_list in self.get_dividend_by_country().items():
            dividend = self.get_dividend_total(dividend_list, TransactionType.DIVIDEND)
            dividend_in_lieu = self.get_dividend_total(
                dividend_list, TransactionType.DIVIDEND_IN_LIEU
            )
            total_dividend = dividend + dividend_in_lieu
            withholding_tax = self.get_dividend_total(
                dividend_list, TransactionType.WITHHOLDING
            )
            net_income = total_dividend - withholding_tax
            output_string += (
                f"Dividends for {country}:\n"
                f"Dividends: £{dividend:.2f}\n"
                f"Dividends in lieu: £{dividend_in_lieu:.2f}\n"
                f"Total Dividends: £{total_dividend:.2f}\n"
                f"Foreign withholding tax: £{withholding_tax:.2f}\n"
                f"Net income received: £{net_income:.2f}\n\n"
            )
        return output_string
