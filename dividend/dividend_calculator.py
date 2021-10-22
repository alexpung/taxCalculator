import pandas
from iso3166 import countries

from excel_format.write_dataframe import write_dataframe
from xml_import.xml_to_panda import read_all_xml
from .const import *
from .dividend_data_format import *


def calculate_dividend_interest(from_date, to_date):
    """
    Read all the XML files in the same directory and output to excel file as output.xlsx
    Dividend/Dividend in lieu/Withholding tax is combined to a single line
    There is a summary sheet listing dividend received/withholding tax paid by country of origin

    :param from_date: starting date of report: string of format 'YYYY-MM-DD'
    :param to_date: ending date of report: string of format 'YYYY-MM-DD'
    """
    # read all xml file in the directory
    df_data = read_all_xml('.//CashTransaction')
    df_company_info = read_all_xml('.//SecurityInfo')
    df_company_info.drop_duplicates(subset=ISIN, keep='last', inplace=True)
    df_company_info[COUNTRY] = df_company_info[ISIN].dropna().str[:2].apply(lambda x: countries.get(x).alpha3)
    df_data = df_data.merge(df_company_info[[ISIN, COUNTRY]], on=ISIN)
    df_data[SETTLE_DATE] = pandas.to_datetime(df_data[SETTLE_DATE])
    df_data = df_data[(df_data[SETTLE_DATE] > from_date) &
                      (df_data[SETTLE_DATE] < to_date)]
    # filter only dividend and tax entries
    df_dividends = df_data[df_data[TYPE].isin(DIVIDEND_TYPE)]
    df_dividends[GROSS_DIVIDEND] = df_dividends[df_dividends[TYPE].isin(
        [DIVIDENDS, IN_LIEU_OF_DIVIDENDS])][AMOUNT]
    df_dividends[DIVIDEND_IN_STERLING] = df_dividends[GROSS_DIVIDEND] * df_dividends[FX_RATE_TO_BASE]
    # multiply by -1 to change negative tax value to positive
    df_dividends[WITHHOLDING_TAX] = df_dividends[df_dividends[TYPE] == WITHHOLDING_TAX][AMOUNT] * -1
    df_dividends[TAX_IN_STERLING] = df_dividends[WITHHOLDING_TAX] * df_dividends[FX_RATE_TO_BASE]
    df_grouped = df_dividends.groupby([SETTLE_DATE, SYMBOL, COUNTRY, CURRENCY, FX_RATE_TO_BASE],
                                      as_index=False).sum()
    df_grouped = df_grouped.sort_values(SETTLE_DATE).drop(columns=AMOUNT)
    df_summary = df_grouped.groupby(COUNTRY).sum()[[DIVIDEND_IN_STERLING, TAX_IN_STERLING]].reset_index()

    # interest income data
    df_interest = df_data[df_data[TYPE].isin(INTEREST_INCOME)]
    df_interest[INTEREST_IN_STERLING] = df_interest[AMOUNT] * df_interest[FX_RATE_TO_BASE]

    write_dataframe(df_grouped, 'output.xlsx', DIVIDEND_DATA, format_dividend_data)
    write_dataframe(df_summary, 'output.xlsx', DIVIDEND_SUMMARY, format_dividend_summary)
    write_dataframe(df_interest[INTEREST_COLUMN], 'output.xlsx', INTEREST_DATA, format_interest_data)
