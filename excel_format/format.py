from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Alignment


class ExcelFormatter(object):
    """ Helper class to format excel sheet """
    @staticmethod
    def format_cell(ws: Worksheet, cell_range: str, date_format: str) -> None:
        """
        Set format of Dates/number in selected column
        :param ws: Openpyxl Worksheet object
        :param cell_range: Range of cell to be formatted
        :param date_format: Date in excel notation e.g. 'DD/MM/YY'
        """
        if ':' in cell_range:
            for row in ws[cell_range]:
                for cell in row:
                    cell.number_format = date_format
        else:
            for cell in ws[cell_range]:
                cell.number_format = date_format

    @staticmethod
    def auto_size_column(ws: Worksheet) -> None:
        """
        Set size of column according to longest length of string in that column
        :param ws: Openpyxl Worksheet object
        """
        # calculate suitable column width length+2 * 1.2
        dims = {}
        for row in ws.rows:
            for cell in row:
                if cell.value:
                    dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), (len(str(cell.value)) + 2) * 1.2))
        for col, value in dims.items():
            ws.column_dimensions[col].width = value

    @staticmethod
    def set_alignment(ws: Worksheet, cell_range: str, horizontal_alignment: str) -> None:
        """
        set alignment of cells
        :param ws: Openpyxl Worksheet object
        :param cell_range: Range of cell to be formatted
        :param horizontal_alignment:
        """
        if ':' in cell_range:
            for row in ws[cell_range]:
                for cell in row:
                    cell.alignment = Alignment(horizontal=horizontal_alignment)
