""" To calculate dividend and withholding tax made to each country"""
import datetime

from iso3166 import countries
import pandas

from dividend.const import (
    DIVIDEND_TYPE,
    INTEREST_COLUMN,
    INTEREST_INCOME,
    ColumnName,
    TransactionType,
)
from dividend.dividend_data_format import (
    format_dividend_data,
    format_dividend_summary,
    format_interest_data,
)
from excel_format.const import SheetNames
from excel_format.write_dataframe import write_dataframe
from xml_import.xml_to_panda import read_all_xml


def calculate_dividend_interest(
    from_date: datetime.date, to_date: datetime.date
) -> None:
    """
    Read all the XML files in the same directory and output to Excel file as output.xlsx
    Dividend/Dividend in lieu/Withholding tax is combined to a single line
    There is a summary sheet listing dividend received/withholding
    tax paid by country of origin

    :param from_date: starting date of report: string of format 'YYYY-MM-DD'
    :param to_date: ending date of report: string of format 'YYYY-MM-DD'
    """
    # read all xml file in the directory
    df_data = read_all_xml(".//CashTransaction")
    df_company_info = read_all_xml(".//SecurityInfo")
    df_company_info.drop_duplicates(subset=ColumnName.ISIN, keep="last", inplace=True)
    df_company_info[  # pylint: disable=unsupported-assignment-operation
        ColumnName.COUNTRY
    ] = (
        df_company_info[ColumnName.ISIN]  # pylint: disable=unsubscriptable-object
        .dropna()
        .str[:2]
        .apply(lambda x: countries.get(x).alpha3)
    )
    df_data = df_data.merge(
        df_company_info[  # pylint: disable=unsubscriptable-object
            [ColumnName.ISIN, ColumnName.COUNTRY]
        ],
        on=ColumnName.ISIN,
    )
    df_data[ColumnName.SETTLE_DATE] = pandas.to_datetime(
        df_data[ColumnName.SETTLE_DATE]
    )
    df_data = df_data[
        (df_data[ColumnName.SETTLE_DATE] > from_date)
        & (df_data[ColumnName.SETTLE_DATE] < to_date)
    ]
    # filter only dividend and tax entries
    df_dividends = df_data[df_data[ColumnName.TYPE].isin(DIVIDEND_TYPE)]
    df_dividends[ColumnName.GROSS_DIVIDEND] = df_dividends[
        df_dividends[ColumnName.TYPE].isin(
            [TransactionType.DIVIDENDS, TransactionType.IN_LIEU_OF_DIVIDENDS]
        )
    ][ColumnName.AMOUNT]
    df_dividends[ColumnName.DIVIDEND_IN_STERLING] = (
        df_dividends[ColumnName.GROSS_DIVIDEND]
        * df_dividends[ColumnName.FX_RATE_TO_BASE]
    )
    # multiply by -1 to change negative tax value to positive
    df_dividends[TransactionType.WITHHOLDING_TAX] = (
        df_dividends[df_dividends[ColumnName.TYPE] == TransactionType.WITHHOLDING_TAX][
            ColumnName.AMOUNT
        ]
        * -1
    )
    df_dividends[ColumnName.TAX_IN_STERLING] = (
        df_dividends[TransactionType.WITHHOLDING_TAX]
        * df_dividends[ColumnName.FX_RATE_TO_BASE]
    )
    df_grouped = df_dividends.groupby(
        [
            ColumnName.SETTLE_DATE,
            ColumnName.SYMBOL,
            ColumnName.COUNTRY,
            ColumnName.CURRENCY,
            ColumnName.FX_RATE_TO_BASE,
        ],
        as_index=False,
    ).sum()
    df_grouped = df_grouped.sort_values(ColumnName.SETTLE_DATE).drop(
        columns=ColumnName.AMOUNT
    )
    df_summary = (
        df_grouped.groupby(ColumnName.COUNTRY)
        .sum()[[ColumnName.DIVIDEND_IN_STERLING, ColumnName.TAX_IN_STERLING]]
        .reset_index()
    )

    # interest income data
    df_interest = df_data[df_data[ColumnName.TYPE].isin(INTEREST_INCOME)]
    df_interest[ColumnName.INTEREST_IN_STERLING] = (
        df_interest[ColumnName.AMOUNT] * df_interest[ColumnName.FX_RATE_TO_BASE]
    )

    write_dataframe(
        df_grouped, "output.xlsx", SheetNames.DIVIDEND_DATA, format_dividend_data
    )
    write_dataframe(
        df_summary, "output.xlsx", SheetNames.DIVIDEND_SUMMARY, format_dividend_summary
    )
    write_dataframe(
        df_interest[INTEREST_COLUMN],
        "output.xlsx",
        SheetNames.INTEREST_DATA,
        format_interest_data,
    )
