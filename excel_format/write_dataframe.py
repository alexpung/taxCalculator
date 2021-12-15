from typing import Callable

from openpyxl import load_workbook
from pandas import DataFrame, ExcelWriter


def write_dataframe(df: DataFrame, filename: str, sheet_name: str, formatter: Callable):
    """
    Write a Dataframe to a new excel sheet
    :param df: The dataframe to be written
    :param filename: filename of the workbook
    :param sheet_name: name of the excel sheet
    :param formatter: The function to be called to format the sheet
    """
    try:
        book = load_workbook(filename)
    except FileNotFoundError:
        book = None
    with ExcelWriter(filename, engine='openpyxl') as xlsx:
        if book is not None:
            xlsx.book = book
        df.to_excel(xlsx, sheet_name, index=False)
        formatter(xlsx.sheets[sheet_name])
