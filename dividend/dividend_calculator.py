import pandas
import pandas as pd

from .dividend_data_format import format_dividend_data


def calculate_dividend(year):
    """
    To set up Dataframe for dividend information from XML
    :param year: tax year
    """
    # Setting up dividend table
    df_dividends = pandas.read_xml('data.xml', './/CashTransaction')
    df_dividends['settleDate'] = pd.to_datetime(df_dividends['settleDate'])
    df_dividends['Gross dividend'] = df_dividends[df_dividends['type'] != 'Withholding Tax']['amount']
    df_dividends['Gross dividend in Sterling'] = df_dividends['Gross dividend'] * df_dividends['fxRateToBase']
    # multiply by -1 to change negative tax value to positive
    df_dividends['Withholding tax'] = df_dividends[df_dividends['type'] == 'Withholding Tax']['amount'] * -1
    df_dividends['Withholding tax in Sterling'] = df_dividends['Withholding tax'] * df_dividends['fxRateToBase']
    df_grouped = df_dividends.groupby(['settleDate', 'symbol', 'listingExchange', 'currency', 'fxRateToBase']).sum()
    df_grouped = df_grouped.reset_index().sort_values('settleDate').drop(columns='amount')
    _write_dividend_data(df_grouped)


def _write_dividend_data(df: pd.DataFrame, filename="output.xlsx", sheet_name="dividend data"):
    # Write to excel sheet from dataframe
    with pandas.ExcelWriter(filename, engine='openpyxl') as xlsx:
        df.to_excel(xlsx, sheet_name, index=False)
        ws = xlsx.sheets[sheet_name]
        format_dividend_data(ws)

