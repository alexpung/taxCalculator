"""Table representation of data"""
from typing import Union

from capital_gain.model import BuyTrade, Dividend, SellTrade, ShareReorg

trade_header = [
    "ID",
    "Symbol",
    "Transaction Date",
    "Transaction Type",
    "Quantity",
    "Gross Value",
    "Allowable fees and Taxes",
    "Capital gain (loss)",
]


def show_data_in_trade_table(row_data: Union[BuyTrade, SellTrade]):
    """Return Table representation of the transaction"""
    return (
        str(row_data.transaction_id),
        str(row_data.ticker),
        str(row_data.transaction_date.strftime("%d %b %Y")),
        row_data.transaction_type,
        f"{row_data.size:.2f}",
        f"{row_data.transaction_value.get_value():.2f}",
        f"{sum(fee.get_value() for fee in row_data.fee_and_tax):.2f}",
        f"{row_data.calculation_status.total_gain:.2f}",
    )


def show_corp_action_in_trade_table(row_data: ShareReorg):
    """Return Table representation of the transaction"""
    return (
        str(row_data.transaction_id),
        str(row_data.ticker),
        str(row_data.transaction_date.strftime("%d %b %Y")),
        str(row_data.transaction_type.value),
        f"{row_data.size:.2f}",
        "N/A",
        "N/A",
        "N/A",
    )


dividend_header = [
    "ticker",
    "description",
    "transaction date",
    "value",
    "currency",
    "exchange rate",
    "value in sterling",
    "country",
]


def show_data_in_dividend_table(row_data: Dividend):
    """Return table representation of dividend"""
    return (
        row_data.ticker,
        row_data.description,
        row_data.transaction_date,
        row_data.value.value,
        row_data.value.currency,
        row_data.value.exchange_rate,
        row_data.value.get_value(),
        row_data.country,
    )
