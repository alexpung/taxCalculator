"""Capital gain related data output generation"""
from collections import defaultdict

import xlsxwriter

from capital_gain.model import ShareReorg, Trade, Transaction
from excel_output.utility import make_table


def write_capital_gain_list(transaction_list: list[Transaction]):
    """Write a list of dividend and tax to a file"""
    workbook = xlsxwriter.Workbook(
        "CapitalGain.xlsx", {"default_date_format": "d mmm yyyy"}
    )
    transaction_list.sort()
    grouped_transaction_list: defaultdict[str, list[Transaction]] = defaultdict(list)
    for transaction in transaction_list:
        grouped_transaction_list[transaction.ticker].append(transaction)
    for ticker, table in grouped_transaction_list.items():
        make_table(workbook, ticker, map(_set_trade_data, table))
    workbook.close()


def _set_trade_data(transaction: Transaction):
    if isinstance(transaction, Trade):
        return {
            "Symbol": transaction.ticker,
            "Trade Date": transaction.transaction_date,
            "Transaction Type": transaction.transaction_type,
            "Quantity": transaction.size,
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
            "Symbol": transaction.ticker,
            "Trade Date": transaction.transaction_date,
            "Transaction Type": transaction.transaction_type.value,
            "Quantity": "",
            "Gross trade value in Sterling": "",
            "Incidental cost in Sterling": "",
            "Unmatched shares": "",
            "Total capital gain (loss)": "",
            "Comment": transaction.comment,
        }
