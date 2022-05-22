"""Capital gain related data output generation"""
from collections import defaultdict
from typing import Any

import xlsxwriter

from capital_gain.capital_summary import (
    get_allowable_cost,
    get_capital_loss,
    get_disposal_proceeds,
    get_number_of_disposal,
    get_total_gain_exclude_loss,
)
from capital_gain.model import (
    Section104,
    Section104Value,
    SellTrade,
    ShareReorg,
    Trade,
    Transaction,
)
from const import get_tax_year
from excel_output.utility import make_table


def write_capital_gain_excels(
    transaction_list: list[Transaction], section104: Section104
):
    """Write a list of trades and capital gain summary to a file"""
    transaction_list.sort()
    _write_trade_by_ticker(transaction_list)
    _write_cgt_per_year_and_summary(transaction_list)
    _write_section104(section104)


def _write_trade_by_ticker(transaction_list: list[Transaction]):
    trade_workbook = xlsxwriter.Workbook(
        "TradesByTicker.xlsx", {"default_date_format": "d mmm yyyy"}
    )
    grouped_list_ticker: defaultdict[str, list[Transaction]] = defaultdict(list)
    for transaction in transaction_list:
        grouped_list_ticker[transaction.ticker].append(transaction)
    for ticker, grouped_list in grouped_list_ticker.items():
        make_table(trade_workbook, ticker, map(_set_trade_data, grouped_list))
    trade_workbook.close()


def _write_cgt_per_year_and_summary(transaction_list: list[Transaction]):
    cgt_workbook = xlsxwriter.Workbook(
        "CgtPerYearAndSummary.xlsx", {"default_date_format": "d mmm yyyy"}
    )
    grouped_list_year: defaultdict[int, list[Transaction]] = defaultdict(list)
    summary_data = []
    for transaction in transaction_list:
        grouped_list_year[get_tax_year(transaction.transaction_date)].append(
            transaction
        )
    for year, grouped_list in grouped_list_year.items():
        sell_trades = [x for x in grouped_list if isinstance(x, SellTrade)]
        summary_data.append(_set_capital_gain_summary(year, sell_trades))
        make_table(cgt_workbook, str(year), map(_set_trade_data, grouped_list))
    make_table(cgt_workbook, "Summary", summary_data)
    cgt_workbook.close()


def _write_section104(section104: Section104):
    section104_workbook = xlsxwriter.Workbook(
        "Section104.xlsx", {"default_date_format": "d mmm yyyy"}
    )
    table_list = []
    for item in section104.section104_list.items():
        table_list.append(_set_section104(*item))
    make_table(section104_workbook, "Section104", table_list)
    make_table(
        section104_workbook, "Short trade", map(_set_trade_data, section104.short_list)
    )
    section104_workbook.close()


def _set_section104(
    section104_key: str, section104_value: Section104Value
) -> dict[str, Any]:
    return {
        "Symbol": section104_key,
        "Quantity": section104_value.quantity,
        "Allowable cost": section104_value.cost,
    }


def _set_capital_gain_summary(
    year: int, transaction_list: list[SellTrade]
) -> dict[str, Any]:
    """Data for writing capital gain summary table"""
    return {
        "Tax year": year,
        "Number of disposal": get_number_of_disposal(transaction_list),
        "Disposal proceeds": get_disposal_proceeds(transaction_list),
        "Allowable_cost": get_allowable_cost(transaction_list),
        "Total gain exclude loss": get_total_gain_exclude_loss(transaction_list),
        "Capital loss": get_capital_loss(transaction_list),
    }


def _set_trade_data(transaction: Transaction) -> dict[str, Any]:
    """Data for writing trade data table"""
    if isinstance(transaction, Trade):
        return {
            "ID": transaction.transaction_id,
            "Symbol": transaction.ticker,
            "Trade Date": transaction.transaction_date,
            "Description": transaction.description,
            "Transaction Type": transaction.transaction_type,
            "Quantity": transaction.size,
            "Currency": transaction.transaction_value.currency.value,
            "Gross trade value in local Currency": transaction.transaction_value.value,
            "Gross trade value in Sterling": transaction.transaction_value.get_value(),
            "Incidental cost in Sterling": sum(
                fee.get_value() for fee in transaction.fee_and_tax
            ),
            "Unmatched shares": transaction.calculation_status.unmatched,
            "Total capital gain (loss)": transaction.calculation_status.total_gain,
            "Comment": transaction.calculation_status.comment,
        }
    elif isinstance(transaction, ShareReorg):
        return {
            "ID": transaction.transaction_id,
            "Symbol": transaction.ticker,
            "Trade Date": transaction.transaction_date,
            "Description": transaction.description,
            "Transaction Type": "",
            "Quantity": "",
            "Currency": "",
            "Gross trade value in local Currency": "",
            "Gross trade value in Sterling": "",
            "Incidental cost in Sterling": "",
            "Unmatched shares": "",
            "Total capital gain (loss)": "",
            "Comment": transaction.comment,
        }
    else:
        raise TypeError(f"Incorrect class {type(transaction)}passed")
