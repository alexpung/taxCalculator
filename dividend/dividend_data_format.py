"""
Collection of excel sheet formatting for writing Pandas Dataframe to excel
"""
from openpyxl.styles import Alignment


def format_dividend_data(ws) -> None:
    """
    excel formatting for dividend data sheet
    """
    # Set format for dividend and withholding tax
    for row in ws['F:I']:
        for cell in row:
            cell.number_format = '#,##0.00'
    # Set format for settleDate
    for cell in ws['A']:
        cell.number_format = 'DD/MM/YY'
    # calculate suitable column width length+2 * 1.2
    dims = {}
    for row in ws.rows:
        for cell in row:
            if cell.value:
                dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), (len(str(cell.value))+2) * 1.2))
    for col, value in dims.items():
        ws.column_dimensions[col].width = value
    # Set center alignment for row A to D
    for row in ws['A:D']:
        for cell in row:
            cell.alignment = Alignment(horizontal='center')
