import pandas
from iso3166 import countries

from xml_import.xml_to_panda import read_all_xml
from .const import *
from .dividend_data_format import format_dividend_data, format_dividend_summary


def calculate_dividend(from_date, to_date):
    """
    Read all the XML files in the same directory and output to excel file as output.xlsx
    Dividend/Dividend in lieu/Withholding tax is combined to a single line
    There is a summary sheet listing dividend received/withholding tax paid by country of origin

    :param from_date: starting date of report: string of format 'YYYY-MM-DD'
    :param to_date: ending date of report: string of format 'YYYY-MM-DD'
    """
    # read all xml file in the directory
    df_dividends = read_all_xml('.//CashTransaction')
    df_company_info = read_all_xml('.//SecurityInfo')
    df_company_info.drop_duplicates(subset=ISIN, keep='last', inplace=True)
    df_company_info[COUNTRY] = df_company_info[ISIN].dropna().str[:2].apply(lambda x: countries.get(x).alpha3)
    df_dividends = df_dividends.merge(df_company_info[[ISIN, COUNTRY]], on=ISIN)
    df_dividends[SETTLE_DATE] = pandas.to_datetime(df_dividends[SETTLE_DATE])
    # filter only dividend and tax entries
    df_dividends = df_dividends[df_dividends[TYPE].isin(DIVIDEND_TYPE)]
    df_dividends = df_dividends[(df_dividends[SETTLE_DATE] > from_date) &
                                (df_dividends[SETTLE_DATE] < to_date)]
    df_dividends[GROSS_DIVIDEND] = df_dividends[df_dividends[TYPE].isin(
        [DIVIDENDS, IN_LIEU_OF_DIVIDENDS])][AMOUNT]
    df_dividends[DIVIDEND_IN_STERLING] = df_dividends[GROSS_DIVIDEND] * df_dividends[FX_RATE_TO_BASE]
    # multiply by -1 to change negative tax value to positive
    df_dividends[WITHHOLDING_TAX] = df_dividends[df_dividends[TYPE] == WITHHOLDING_TAX][AMOUNT] * -1
    df_dividends[TAX_IN_STERLING] = df_dividends[WITHHOLDING_TAX] * df_dividends[FX_RATE_TO_BASE]
    df_grouped = df_dividends.groupby([SETTLE_DATE, SYMBOL, COUNTRY, CURRENCY, FX_RATE_TO_BASE],
                                      as_index=False).sum()
    df_grouped = df_grouped.sort_values(SETTLE_DATE).drop(columns=AMOUNT)
    df_summary = df_grouped.groupby(COUNTRY).sum()[[DIVIDEND_IN_STERLING, TAX_IN_STERLING]]
    _write_dividend_data(df_grouped, df_summary)


def _write_dividend_data(df_dividend_data: pandas.DataFrame,
                         df_dividend_summary: pandas.DataFrame,
                         filename="output.xlsx"):
    # Write to excel sheet from dataframe
    dividend_data_sheet_name = DIVIDEND_DATA
    dividend_summary_sheet_name = DIVIDEND_SUMMARY

    with pandas.ExcelWriter(filename, engine='openpyxl') as xlsx:
        df_dividend_data.to_excel(xlsx, dividend_data_sheet_name, index=False)
        format_dividend_data(xlsx.sheets[dividend_data_sheet_name])
        df_dividend_summary.to_excel(xlsx, dividend_summary_sheet_name)
        format_dividend_summary(xlsx.sheets[dividend_summary_sheet_name])
