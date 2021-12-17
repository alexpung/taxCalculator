""" Function to write pandas dataframe to excel """

from typing import Callable

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from pandas import DataFrame, ExcelWriter

from excel_format.const import SheetNames


def write_dataframe(
    data_frame: DataFrame,
    filename: str,
    sheet_name: SheetNames,
    formatter: Callable[[Worksheet], None],
) -> None:
    """
    Write a Dataframe to a new excel sheet
    :param data_frame: The dataframe to be written
    :param filename: filename of the workbook
    :param sheet_name: name of the excel sheet
    :param formatter: The function to be called to format the sheet
    """
    try:
        book = load_workbook(filename)
    except FileNotFoundError:
        book = None
    with ExcelWriter(  # pylint: disable=abstract-class-instantiated
        filename, engine="openpyxl"
    ) as xlsx:
        if book is not None:
            xlsx.book = book
        data_frame.to_excel(xlsx, sheet_name, index=False)
        formatter(xlsx.sheets[sheet_name])
