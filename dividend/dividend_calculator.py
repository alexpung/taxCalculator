import pandas
import pandas as pd

from .dividend_data_format import format_dividend_data, format_dividend_summary


def calculate_dividend(year):
    """
    To set up Dataframe for dividend information from XML
    :param year: tax year
    TODO: handle tax year
    """
    # Setting up dividend table
    df_dividends = pandas.read_xml('data.xml', './/CashTransaction')
    df_dividends['settleDate'] = pd.to_datetime(df_dividends['settleDate'])
    df_dividends['Gross dividend'] = df_dividends[df_dividends['type'] != 'Withholding Tax']['amount']
    df_dividends['Gross dividend in Sterling'] = df_dividends['Gross dividend'] * df_dividends['fxRateToBase']
    # multiply by -1 to change negative tax value to positive
    df_dividends['Withholding tax'] = df_dividends[df_dividends['type'] == 'Withholding Tax']['amount'] * -1
    df_dividends['Withholding tax in Sterling'] = df_dividends['Withholding tax'] * df_dividends['fxRateToBase']
    df_grouped = df_dividends.groupby(['settleDate', 'symbol', 'listingExchange', 'currency', 'fxRateToBase'],
                                      as_index=False).sum()
    df_grouped = df_grouped.sort_values('settleDate').drop(columns='amount')

    # group dividend by currency type (should be ok with most companies except rare cases)
    # TODO how to solve companies paying dividend in currency different from its location,
    #  listing exchange is also not accurate
    df_summary = df_grouped.groupby('currency').sum()[['Gross dividend in Sterling', 'Withholding tax in Sterling']]
    _write_dividend_data(df_grouped, df_summary)


def _write_dividend_data(df_dividend_data: pd.DataFrame,
                         df_dividend_summary: pd.DataFrame,
                         filename="output.xlsx"):
    # Write to excel sheet from dataframe
    dividend_data_sheet_name = "dividend data"
    dividend_summary_sheet_name = "dividend summary"

    with pandas.ExcelWriter(filename, engine='openpyxl') as xlsx:
        df_dividend_data.to_excel(xlsx, dividend_data_sheet_name, index=False)
        format_dividend_data(xlsx.sheets[dividend_data_sheet_name])
        df_dividend_summary.to_excel(xlsx, dividend_summary_sheet_name)
        format_dividend_summary(xlsx.sheets[dividend_summary_sheet_name])



